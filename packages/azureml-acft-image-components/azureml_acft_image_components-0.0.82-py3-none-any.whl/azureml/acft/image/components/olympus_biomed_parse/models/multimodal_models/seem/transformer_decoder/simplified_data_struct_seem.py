# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import torch
import torch.nn as nn
import torch.nn.functional as F

predict_name_matcher = {
    "predictions_class": ["pred_logits"],
    "predictions_mask": ["pred_masks", "pred_gmasks", "pred_smasks"],
    "predictions_caption": ["pred_captions", "pred_gtexts", "pred_stexts"],
    "predictions_maskemb": ["pred_smaskembs"],
    "predictions_pos_spatial": ["pred_pspatials"],
    "predictions_neg_spatial": ["pred_nspatials"],
}

predict_index_matcher = {
    "predictions_class": ["queries_object"],
    "predictions_mask": ["queries_object", "queries_grounding", "queries_spatial"],
    "predictions_caption": ["queries_object", "queries_grounding", "queries_spatial"],
    "predictions_maskemb": ["queries_spatial"],
    "predictions_pos_spatial": ["all"],
    "predictions_neg_spatial": ["all"],
}


class Variable:
    """
    Store dataset variable for attention.
    output: embedding that accumulates during cross/self attention.
    pos: positional embedding that is fixed during cross/self attention.
    name: name of the variable.
    type: type of the variable, e.g., queries, tokens.
    attn_mask: attention mask for cross attention.
    masking: masking for padding.
    """

    def __init__(self, output, name, _type, pos=None):
        self.output = output
        self.pos = pos
        self.name = name
        self.type = _type
        self.attn_mask = None
        self.masking = None

    def copy(self):
        output = self.output.clone() if self.output is not None else None
        pos = self.pos.clone() if self.pos is not None else None
        return Variable(output, self.name, self.type, pos)

    def rand_sample(self, max_len):
        rand_idx = torch.randint(0, len(self.pos), (max_len,))
        self.output = self.output[rand_idx]
        self.pos = self.pos[rand_idx]
        return self


class AttentionDataStruct(nn.Module):
    """
    Store dataset structure for cross/self attention.
    Dynamically configures the attention architecture based on task_switch and flags.
    """

    def __init__(self, attn_mask, task_switch, num_layers):
        super(AttentionDataStruct, self).__init__()
        self.task_switch = task_switch
        self.build_dynamic_architecture()
        self.num_layers = num_layers

    def build_dynamic_architecture(self):
        # Dynamically create architecture configuration based on task_switch
        self.p_attn_variables = {"queries": [], "tokens": [], "memories": []}
        self.p_self_attn = {"queries": {}, "tokens": {}, "memories": {}}
        self.p_cross_attn = {"queries": {}, "tokens": {}, "memories": {}}
        self.p_masking = []
        self.p_duplication = {"queries": {}}

        # Example dynamic setup based on task switch
        if self.task_switch.get("grounding", False):
            self.setup_grounding_attention()

        if self.task_switch.get("spatial", False):
            self.setup_spatial_attention()

        if self.task_switch.get("mask", False):
            self.setup_mask_attention()

        # Additional setups can be added here as needed based on task_switch

    def setup_grounding_attention(self):
        self.p_attn_variables["queries"].append("grounding")
        self.p_attn_variables["tokens"].append("grounding")
        self.p_self_attn["queries"]["grounding"] = [
            "queries_grounding",
            "tokens_grounding",
        ]
        self.p_self_attn["tokens"]["grounding"] = [
            "queries_grounding",
            "tokens_grounding",
        ]
        self.p_cross_attn["queries"]["grounding"] = True
        self.p_cross_attn["tokens"]["grounding"] = True
        self.p_masking.append("tokens_grounding")
        self.p_duplication["queries"]["grounding"] = "queries_object"

    def setup_spatial_attention(self):
        self.p_attn_variables["queries"].append("spatial")
        self.p_attn_variables["tokens"].append("spatial")
        self.p_attn_variables["memories"].append("spatial")
        self.p_self_attn["queries"]["spatial"] = [
            "queries_spatial",
            "tokens_spatial",
            "memories_spatial",
        ]
        self.p_self_attn["tokens"]["spatial"] = ["tokens_spatial"]
        self.p_self_attn["memories"]["spatial"] = ["memories_spatial"]
        self.p_cross_attn["queries"]["spatial"] = True
        self.p_cross_attn["memories"]["spatial"] = True
        self.p_cross_attn["tokens"]["spatial"] = False
        self.p_masking.append("tokens_spatial")
        self.p_duplication["queries"]["spatial"] = "queries_object"

    def setup_mask_attention(self):
        self.p_attn_variables["queries"].append("object")
        self.p_self_attn["queries"]["object"] = ["queries_object"]
        self.p_cross_attn["queries"]["object"] = True

    def reset(self, flags, task, extra):
        # Reset variables
        self.attn_variables = {}
        self.cross_attn_dict = {}
        self.self_attn_dict = {}
        self.duplication_dict = {}
        self.query_index = {}
        self.output = {}
        self.flags = flags
        self.spatial_memory = {}
        self.extra = extra
        self.task = task

        # Initialize duplication and flags
        self.initialize_duplication()
        self.initialize_flags()

        # Initialize output and spatial memory based on task_switch
        self.initialize_output_and_memory()

        # Initialize cross_attn and self_attn configurations
        self.initialize_cross_and_self_attn()

    def initialize_duplication(self):
        for key, values in self.p_duplication.items():
            for name in values:
                self.duplication_dict[f"{key}_{name}"] = self.p_duplication[key][name]

    def initialize_flags(self):
        self.flags.setdefault("object", True)

    def initialize_output_and_memory(self):
        # Initialize output
        if self.task_switch.get("mask"):
            self.output["predictions_class"] = []
            self.output["predictions_mask"] = []

        if self.task_switch.get("bbox"):
            self.output["predictions_bbox"] = []

        if self.task_switch.get("grounding") and self.flags.get("grounding"):
            self.output["predictions_caption"] = []

        if self.task_switch.get("spatial") and self.flags.get("spatial"):
            self.output["predictions_maskemb"] = []
            self.output["predictions_pos_spatial"] = []
            self.output["predictions_neg_spatial"] = []

        if self.task_switch.get("spatial") and self.flags.get("memories_spatial"):
            self.spatial_memory["prev_batch_mask"] = self.extra.get("prev_mask", None)

    def initialize_cross_and_self_attn(self):
        # Initialize cross_attn and self_attn
        for key, values in self.p_cross_attn.items():
            for name in values:
                self.cross_attn_dict[f"{key}_{name}"] = values[name]

        for key, values in self.p_self_attn.items():
            for name in values:
                self.self_attn_dict[f"{key}_{name}"] = values[name]

        self.masking = self.p_masking
        self.query_index = {"all": [0, None]}

    def set(self, name, _type, output=None, pos=None, var=None, sample_size=None):
        if var is not None:
            self.attn_variables[name] = var
        elif name in self.duplication_dict:
            base_var = self.attn_variables[self.duplication_dict[name]]
            var = base_var.copy()
            if sample_size:
                var = var.rand_sample(sample_size)
            self.attn_variables[name] = var
        else:
            self.attn_variables[name] = Variable(output, name, _type, pos)

    def set_results(self, results):
        for name in self.cross_attn_name:
            var = self.attn_variables[name]
            var.attn_mask = results["attn_mask"][
                :, self.query_index[name][0] : self.query_index[name][1]
            ]

        for key, value_list in self.output.items():
            value_list.append(results[key])

    def set_maskings(self, name, masking):
        if name in self.attn_variables:
            self.attn_variables[name].masking = masking

    def set_extra(self, extra):
        self.extra.update(extra)

    def cross_attn_variables(self):
        cross_attn_names = self.get_active_variables(self.cross_attn_dict)
        self.cross_attn_name = cross_attn_names

        outputs = [self.attn_variables[name].output for name in cross_attn_names]
        pos_embs = [self.attn_variables[name].pos for name in cross_attn_names]
        output = torch.cat(outputs)
        pos_emb = torch.cat(pos_embs)

        self.query_index = self.compute_query_indices(cross_attn_names)
        return output, pos_emb

    def compute_query_indices(self, variable_names):
        query_index = {}
        index = 0
        for name in variable_names:
            var_length = self.attn_variables[name].output.shape[0]
            query_index[name] = [index, index + var_length]
            index += var_length
        return query_index

    def get_active_variables(self, attn_dict):
        return [
            key
            for key, active in attn_dict.items()
            if active
            and key in self.attn_variables
            and (key not in self.flags or self.flags[key])
        ]

    def cross_attn_mask(self, size, num_heads):
        attn_mask = torch.cat(
            [self.attn_variables[name].attn_mask for name in self.cross_attn_name],
            dim=1,
        )
        # Additional processing for memories_spatial if needed
        attn_mask = self.process_memories_spatial(attn_mask, size, num_heads)
        attn_mask[attn_mask.sum(-1) == attn_mask.shape[-1]] = False
        return attn_mask

    def process_memories_spatial(self, attn_mask, size, num_heads):
        if "memories_spatial" in self.cross_attn_name:
            memory_attn_mask = self.spatial_memory["prev_batch_mask"]
            bs, c, _, _ = memory_attn_mask.shape
            memory_attn_mask = (
                F.interpolate(
                    memory_attn_mask, size, mode="bilinear", align_corners=False
                )
                .sigmoid()
                .flatten(2)
                .unsqueeze(1)
                .repeat(1, num_heads, 1, 1)
                .flatten(0, 1)
                < 0.5
            )
            memory_attn_mask = memory_attn_mask.bool().detach()
            repeat = (
                self.query_index["memories_spatial"][1]
                - self.query_index["memories_spatial"][0]
            ) // c
            mem_len = (
                self.query_index["memories_spatial"][1]
                - self.query_index["memories_spatial"][0]
            )
            probs = torch.full((c,), 1.0 / repeat)
            indices = torch.multinomial(
                probs, num_samples=mem_len, replacement=True
            ).sort()[0]
            attn_mask[
                :,
                self.query_index["memories_spatial"][0] : self.query_index[
                    "memories_spatial"
                ][1],
            ] = memory_attn_mask[:, indices]
            self.extra["memory_indices"] = indices
        return attn_mask

    def self_attn(self, bs, num_heads):
        self_attn_names = self.get_active_variables(self.self_attn_dict)
        self.self_attn_name = self_attn_names

        outputs = [self.attn_variables[name].output for name in self_attn_names]
        pos_embs = [self.attn_variables[name].pos for name in self_attn_names]
        output = torch.cat(outputs)
        pos_emb = torch.cat(pos_embs)

        self.query_index = self.compute_query_indices(self_attn_names)

        self_attn_mask = self.build_self_attn_mask(bs, num_heads)
        return output, pos_emb, self_attn_mask

    def build_self_attn_mask(self, bs, num_heads):
        total_length = sum(
            var.output.shape[0]
            for var in self.attn_variables.values()
            if var.name in self.self_attn_name
        )
        self_attn_mask = torch.ones(
            (bs, total_length, total_length),
            dtype=torch.bool,
            device=next(iter(self.attn_variables.values())).output.device,
        )
        self.configure_self_attn_mask(self_attn_mask)
        self_attn_mask = self_attn_mask.repeat_interleave(num_heads, dim=0)
        return self_attn_mask

    def configure_self_attn_mask(self, mask):
        for key1, values in self.self_attn_dict.items():
            for key2 in values:
                if key1 not in self.self_attn_name or key2 not in self.self_attn_name:
                    continue
                mask[
                    :,
                    self.query_index[key1][0] : self.query_index[key1][1],
                    self.query_index[key2][0] : self.query_index[key2][1],
                ] = False
                if key1 in self.masking or key2 in self.masking:
                    mask[
                        :,
                        self.query_index[key1][0] : self.query_index[key1][1],
                        self.query_index[key2][0] : self.query_index[key2][1],
                    ].transpose(1, 2)[self.attn_variables[key2].masking] = True

    def update_variables(self, output, mode):
        name_set = self.self_attn_name if mode == "self_attn" else self.cross_attn_name
        for key in name_set:
            self.attn_variables[key].output = output[
                self.query_index[key][0] : self.query_index[key][1]
            ]

    def update_spatial_results(self, results):
        v_emb = results["pred_smaskembs"]
        pred_smasks = results["pred_smasks"]

        s_emb = results["pred_pspatials"]
        diag_mask = ~(
            torch.eye(
                self.extra["spatial_query_number"], device=s_emb.device
            ).repeat_interleave(self.extra["sample_size"], dim=0)
        ).bool()
        offset = torch.zeros_like(diag_mask, device=s_emb.device).float()
        offset.masked_fill_(diag_mask, float("-inf"))

        pred_logits = v_emb @ s_emb.transpose(1, 2) + offset[None]
        bs, _, ns = pred_logits.shape
        _, _, h, w = pred_smasks.shape

        logits_idx_y = pred_logits.max(dim=1)[1]
        logits_idx_x = torch.arange(len(logits_idx_y), device=logits_idx_y.device)[
            :, None
        ].repeat(1, logits_idx_y.shape[1])
        logits_idx = torch.stack([logits_idx_x, logits_idx_y]).view(2, -1).tolist()
        pred_masks_pos = pred_smasks[logits_idx].reshape(bs, ns, h, w)
        extra = {"prev_mask": pred_masks_pos}
        return extra

    def organize_output(self):
        outputs = {"aux_outputs": [{} for _ in range(self.num_layers)]}
        for key, values in self.output.items():
            for _key, idx_name in zip(
                predict_name_matcher[key], predict_index_matcher[key]
            ):
                if idx_name not in self.query_index:
                    continue
                outputs[_key] = self.output[key][-1][
                    :, self.query_index[idx_name][0] : self.query_index[idx_name][1]
                ]
                for idx, aux_values in enumerate(self.output[key][:-1]):
                    outputs["aux_outputs"][idx][_key] = aux_values[
                        :, self.query_index[idx_name][0] : self.query_index[idx_name][1]
                    ]
        if self.task in ["spatial", "refimg"]:
            outputs.update(self.update_spatial_results(outputs))
        return outputs
