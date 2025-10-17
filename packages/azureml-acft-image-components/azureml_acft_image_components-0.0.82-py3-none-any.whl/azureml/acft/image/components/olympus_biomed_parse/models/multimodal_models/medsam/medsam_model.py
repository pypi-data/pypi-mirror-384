# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
# %% set up model
import torch
import torch.nn as nn
import logging

logger = logging.getLogger(__name__)


class MedSAMModel(nn.Module):
    def __init__(
        self,
        image_encoder,
        mask_decoder,
        prompt_encoder,
        freeze_prompt_encoder=False,
        freeze_image_encoder=False,
        model_checkpoint_path=None,
    ):
        super().__init__()
        self.image_encoder = image_encoder
        self.mask_decoder = mask_decoder
        self.prompt_encoder = prompt_encoder

        # freeze prompt encoder
        self.freeze_prompt_encoder = freeze_prompt_encoder
        if self.freeze_prompt_encoder:
            for param in self.prompt_encoder.parameters():
                param.requires_grad = False

        self.freeze_image_encoder = freeze_image_encoder
        if self.freeze_image_encoder:
            for param in self.image_encoder.parameters():
                param.requires_grad = False

        if model_checkpoint_path:
            model_dict = self.state_dict()  # base model params
            pretrained_dict = torch.load(
                model_checkpoint_path
            )  # pretrained model params
            for k, v in pretrained_dict.items():
                if k in model_dict and model_dict[k].shape == v.shape:
                    model_dict[k] = v
                else:
                    logger.info(
                        f"skipping {k} from {model_checkpoint_path}, v.shape: {v.shape}"
                    )
            # print(pretrained_dict.keys())
            # update the base model params with the pretrained model params
            # model_dict.update(pretrained_dict)
            self.load_state_dict(model_dict, strict=True)

    def forward(self, inputs: dict):
        image = inputs["image"] if "image" in inputs else None
        points = inputs["points"] if "points" in inputs else None
        boxes = inputs["bboxes"] if "bboxes" in inputs else None
        masks = inputs["masks"] if "masks" in inputs else None
        tokens = inputs["tokens"] if "tokens" in inputs else None

        if image is None:
            raise ValueError("Image is required input")

        # do not compute gradients for image encoder
        # with torch.no_grad():
        image_embedding = self.image_encoder(image)  # (B, 256, 64, 64)

        sparse_embeddings, dense_embeddings = self.prompt_encoder(
            points=points,
            boxes=boxes,
            masks=masks,
            tokens=tokens,
        )
        low_res_masks, _ = self.mask_decoder(
            image_embeddings=image_embedding,  # (B, 256, 64, 64)
            image_pe=self.prompt_encoder.get_dense_pe(),  # (1, 256, 64, 64)
            sparse_prompt_embeddings=sparse_embeddings,  # (B, 2, 256)
            dense_prompt_embeddings=dense_embeddings,  # (B, 256, 64, 64)
            multimask_output=False,
        )
        # ori_res_masks = F.interpolate(
        #     low_res_masks,
        #     size=(image.shape[2], image.shape[3]),
        #     mode="bilinear",
        #     align_corners=False,
        # )
        return low_res_masks
