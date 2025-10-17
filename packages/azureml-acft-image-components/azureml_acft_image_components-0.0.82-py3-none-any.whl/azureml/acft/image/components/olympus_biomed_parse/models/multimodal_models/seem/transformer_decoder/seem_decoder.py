# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import fvcore.nn.weight_init as weight_init
import torch
import torch.nn as nn
import torch.nn.functional as F
from timm.models.layers import trunc_normal_

from .attention_data_struct_seem_v1 import AttentionDataStruct
from .position_encoding import PositionEmbeddingSine
from .modules import (
    CustomSelfAttentionLayer,
    CrossAttentionLayer,
    FFNLayer,
    MLP,
)

ATTENTION_ARCH = {
    "VARIABLE": {
        "queries": ["object", "grounding", "spatial"],
        "tokens": ["grounding", "spatial"],
        "memories": ["spatial"],
    },
    "SELF_ATTENTION": {
        "queries": {
            "object": ["queries_object"],
            "grounding": ["queries_grounding", "tokens_grounding"],
            "spatial": ["queries_spatial", "tokens_spatial", "memories_spatial"],
        },
        "tokens": {
            "grounding": ["queries_grounding", "tokens_grounding"],
            "spatial": ["tokens_spatial"],
        },
        "memories": {"spatial": ["memories_spatial"]},
    },
    "CROSS_ATTENTION": {
        "queries": {"object": True, "grounding": True, "spatial": True},
        "memories": {"spatial": True},
        "tokens": {"grounding": False, "spatial": False},
    },
    "MASKING": ["tokens_spatial", "tokens_grounding"],
    "DUPLICATION": {
        "queries": {"grounding": "queries_object", "spatial": "queries_object"}
    },
    "SPATIAL_MEMORIES": 32,
    "QUERY_NUMBER": 3,
}


class SEEMDecoder(nn.Module):
    def __init__(
        self,
        language_encoder: nn.Module,
        in_channels=256,
        mask_classification=True,
        hidden_dim: int = 256,
        dim_proj: int = 256,
        num_queries: int = 100,
        nheads: int = 8,
        dim_feedforward: int = 2048,
        dec_layers: int = 10,
        pre_norm: bool = False,
        mask_dim: int = 256,
        task_switch: dict = {
            "mask": True,
            "bbox": False,
            "grounding": True,
            "spatial": False,
        },
        enforce_input_project: bool = False,
        attn_arch: dict = ATTENTION_ARCH,
    ):
        super().__init__()

        self.language_encoder = language_encoder
        self.in_channels = in_channels
        self.mask_classification = mask_classification
        self.hidden_dim = hidden_dim
        self.dim_proj = dim_proj
        self.num_queries = num_queries
        self.nheads = nheads
        self.dim_feedforward = dim_feedforward
        self.dec_layers = dec_layers
        self.pre_norm = pre_norm
        self.mask_dim = mask_dim
        self.task_switch = task_switch
        self.enforce_input_project = enforce_input_project

        assert mask_classification, "Only support mask classification model"
        self.mask_classification = mask_classification

        # positional encoding
        N_steps = hidden_dim // 2
        self.pe_layer = PositionEmbeddingSine(N_steps, normalize=True)

        # define Transformer decoder here
        self.num_heads = nheads
        self.num_layers = dec_layers
        self.transformer_self_attention_layers = nn.ModuleList()
        self.transformer_cross_attention_layers = nn.ModuleList()
        self.transformer_ffn_layers = nn.ModuleList()

        for _ in range(self.num_layers):
            self.transformer_self_attention_layers.append(
                CustomSelfAttentionLayer(
                    d_model=hidden_dim,
                    nhead=nheads,
                    dropout=0.0,
                    normalize_before=pre_norm,
                )
            )

            self.transformer_cross_attention_layers.append(
                CrossAttentionLayer(
                    d_model=hidden_dim,
                    nhead=nheads,
                    dropout=0.0,
                    normalize_before=pre_norm,
                )
            )

            self.transformer_ffn_layers.append(
                FFNLayer(
                    d_model=hidden_dim,
                    dim_feedforward=dim_feedforward,
                    dropout=0.0,
                    normalize_before=pre_norm,
                )
            )

        self.decoder_norm = nn.LayerNorm(hidden_dim)

        self.num_queries = num_queries
        # learnable query features
        self.query_feat = nn.Embedding(num_queries, hidden_dim)
        # learnable query p.e.
        self.query_embed = nn.Embedding(num_queries, hidden_dim)

        # level embedding (we always use 3 scales)
        self.num_feature_levels = 3
        self.level_embed = nn.Embedding(self.num_feature_levels, hidden_dim)
        self.input_proj = nn.ModuleList()

        for _ in range(self.num_feature_levels):
            if in_channels != hidden_dim or enforce_input_project:
                self.input_proj.append(
                    nn.Conv2d(in_channels, hidden_dim, kernel_size=1)
                )
                weight_init.c2_xavier_fill(self.input_proj[-1])
            else:
                self.input_proj.append(nn.Sequential())

        self.task_switch = task_switch
        self.query_index = {}

        self.language_encoder = language_encoder
        self.mask_embed = MLP(hidden_dim, hidden_dim, mask_dim, 3)
        self.class_embed = nn.Parameter(torch.empty(hidden_dim, dim_proj))
        trunc_normal_(self.class_embed, std=0.02)

        if task_switch["bbox"]:
            self.bbox_embed = MLP(hidden_dim, hidden_dim, 4, 3)

        attn_arch["NUM_LAYERS"] = self.num_layers
        self.attention_data = AttentionDataStruct(attn_arch, task_switch)
        self.sample_size = attn_arch["QUERY_NUMBER"]

    def forward(
        self,
        x,  # x is a list of multi-scale features
        mask_features,
        mask=None,
        extra={},
    ):
        assert len(x) == self.num_feature_levels
        src = []
        pos = []
        size_list = []

        # Disable mask, it does not affect performance
        del mask

        grounding_extra_flag = "grounding_tokens" in extra.keys()

        flags = {
            "spatial": False,
            "grounding": grounding_extra_flag,
            "memories_spatial": False,
        }
        self.attention_data.reset(flags, "grounding", extra)

        for i in range(self.num_feature_levels):
            size_list.append(x[i].shape[-2:])
            pos_embed = self.pe_layer(x[i], None).flatten(2).permute(2, 0, 1)
            pos.append(pos_embed)
            proj_src = (
                self.input_proj[i](x[i]).flatten(2)
                + self.level_embed.weight[i][None, :, None]
            )
            src.append(proj_src.permute(2, 0, 1))

        _, bs, _ = src[0].shape

        query_embed = self.query_embed.weight.unsqueeze(1).repeat(1, bs, 1)
        output = self.query_feat.weight.unsqueeze(1).repeat(1, bs, 1)
        self.attention_data.set("queries_object", "queries", output, query_embed)

        if self.task_switch["grounding"] and grounding_extra_flag:
            # Get grounding tokens
            grounding_tokens = extra["grounding_tokens"]
            _grounding_tokens = grounding_tokens.detach().clone()

            # Check for NaNs in grounding tokens
            assert not torch.isnan(
                grounding_tokens
            ).any(), "NaN detected in grounding_tokens"
            assert not torch.isnan(
                _grounding_tokens
            ).any(), "NaN detected in _grounding_tokens"

            self.attention_data.set(
                "tokens_grounding", "tokens", grounding_tokens, _grounding_tokens
            )
            self.attention_data.set("queries_grounding", "queries")
            self.attention_data.set_maskings(
                "tokens_grounding", extra["grounding_nonzero_mask"]
            )

        # Cross-attention operation
        output, query_embed = self.attention_data.cross_attn_variables()
        assert not torch.isnan(output).any(), "NaN detected after cross_attn_variables"
        assert not torch.isnan(
            query_embed
        ).any(), "NaN detected in query_embed after cross_attn"

        # Initial prediction heads
        results = self.forward_prediction_heads(
            output, mask_features, attn_mask_target_size=size_list[0]
        )
        self.attention_data.set_results(results)

        for i in range(self.num_layers):
            level_index = i % self.num_feature_levels
            # CROSS ATTENTION
            output, avg_attn = self.transformer_cross_attention_layers[i](
                output,
                src[level_index],
                memory_mask=self.attention_data.cross_attn_mask(
                    size_list[level_index], self.num_heads
                ),
                memory_key_padding_mask=None,  # here we do not apply masking on padded region
                pos=pos[level_index],
                query_pos=query_embed,
            )
            self.attention_data.update_variables(output, "cross_attn")
            assert not torch.isnan(
                output
            ).any(), f"NaN detected after cross_attention in layer {i}"

            # Self Attention
            self_attn_mask = torch.zeros(
                (bs, self.num_queries, self.num_queries), device=query_embed.device
            ).bool()
            output, query_embed, self_attn_mask = self.attention_data.self_attn(
                bs, self.num_heads
            )
            assert not torch.isnan(
                output
            ).any(), f"NaN detected after self_attn_variables in layer {i}"
            assert not torch.isnan(
                query_embed
            ).any(), f"NaN detected in query_embed after self_attn in layer {i}"

            output = self.transformer_self_attention_layers[i](
                output,
                tgt_mask=self_attn_mask,
                tgt_key_padding_mask=None,
                query_pos=query_embed,
            )
            assert not torch.isnan(
                output
            ).any(), f"NaN detected after self_attention in layer {i}"

            # FFN Layer
            output = self.transformer_ffn_layers[i](output)
            assert not torch.isnan(output).any(), f"NaN detected after FFN in layer {i}"

            self.attention_data.update_variables(output, "self_attn")
            output, query_embed = self.attention_data.cross_attn_variables()

            results = self.forward_prediction_heads(
                output,
                mask_features,
                attn_mask_target_size=size_list[(i + 1) % self.num_feature_levels],
                layer_id=i,
            )
            self.attention_data.set_results(results)

        # Collect final outputs
        return self.attention_data.organize_output()

    def forward_prediction_heads(
        self, output, mask_features, attn_mask_target_size, layer_id=-1
    ):
        decoder_output = self.decoder_norm(output)
        assert not torch.isnan(
            decoder_output
        ).any(), f"NaN detected after decoder_norm in layer {layer_id}"
        decoder_output = decoder_output.transpose(0, 1)

        class_embed = decoder_output @ self.class_embed
        assert not torch.isnan(
            class_embed
        ).any(), f"NaN detected in class_embed in layer {layer_id}"
        outputs_class = self.language_encoder.compute_similarity(class_embed)

        mask_embed = self.mask_embed(decoder_output)
        outputs_mask = torch.einsum("bqc,bchw->bqhw", mask_embed, mask_features)

        outputs_bbox = None
        if self.task_switch["bbox"]:
            outputs_bbox = self.bbox_embed(decoder_output)
            assert not torch.isnan(
                outputs_bbox
            ).any(), f"NaN detected in bbox_embed in layer {layer_id}"

        attn_mask = F.interpolate(
            outputs_mask,
            size=attn_mask_target_size,
            mode="bilinear",
            align_corners=False,
        )
        attn_mask = (
            attn_mask.sigmoid()
            .flatten(2)
            .unsqueeze(1)
            .repeat(1, self.num_heads, 1, 1)
            .flatten(0, 1)
            < 0.0
        ).bool()
        attn_mask = attn_mask.detach()
        # masked_ratio = 1 - attn_mask.float().mean()
        # print("attn_mask", attn_mask.shape, masked_ratio)
        assert not torch.isnan(
            attn_mask
        ).any(), f"NaN detected in attn_mask in layer {layer_id}"

        outputs_caption = class_embed
        results = {
            "attn_mask": attn_mask,
            "predictions_class": outputs_class,
            "predictions_mask": outputs_mask,
            "predictions_bbox": outputs_bbox,
            "predictions_caption": outputs_caption,
            "predictions_maskemb": mask_embed,
        }

        return results

    @torch.jit.unused
    def _set_aux_loss(self, outputs_class, outputs_seg_masks):
        # this is a workaround to make torchscript happy, as torchscript
        # doesn't support dictionary with non-homogeneous values, such
        # as a dict having both a Tensor and a list.
        if self.mask_classification:
            return [
                {"pred_logits": a, "pred_masks": b}
                for a, b in zip(outputs_class[:-1], outputs_seg_masks[:-1])
            ]
        else:
            return [{"pred_masks": b} for b in outputs_seg_masks[:-1]]

    def override_in_channels(self, in_channels):
        # reinitialize the model with a new input shape but use all other remaining parameters
        # this is useful for model conversion
        self.__init__(
            language_encoder=self.language_encoder,
            in_channels=in_channels,
            mask_classification=self.mask_classification,
            hidden_dim=self.hidden_dim,
            dim_proj=self.dim_proj,
            num_queries=self.num_queries,
            nheads=self.nheads,
            dim_feedforward=self.dim_feedforward,
            dec_layers=self.dec_layers,
            pre_norm=self.pre_norm,
            mask_dim=self.mask_dim,
            task_switch=self.task_switch,
            enforce_input_project=self.enforce_input_project,
        )
