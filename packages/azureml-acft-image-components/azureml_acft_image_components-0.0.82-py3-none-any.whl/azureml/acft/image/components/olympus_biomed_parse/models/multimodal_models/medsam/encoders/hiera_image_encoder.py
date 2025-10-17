# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import torch
import torch.nn as nn
from hydra.utils import instantiate
import logging

# Assuming you already have Hiera, FpnNeck, and PositionEmbeddingSine imports
logger = logging.getLogger(__name__)


class MedSamHieraEncoder(nn.Module):
    def __init__(
        self,
        trunk,  # Trunk (Hiera)
        neck,  # Neck (FpnNeck)
        scalp: int = 1,  # Scalp parameter
        ckpt_path: str = None,  # Optional checkpoint path
    ):
        super().__init__()

        # Assigning the trunk, neck, and scalp
        self.trunk = trunk
        self.neck = neck
        self.scalp = scalp

        # Ensure trunk and neck have matching channel lists
        assert (
            self.trunk.channel_list == self.neck.backbone_channel_list
        ), f"Channel dims of trunk and neck do not match. Trunk: {self.trunk.channel_list}, Neck: {self.neck.backbone_channel_list}"

        # If a checkpoint path is provided, load the pretrained weights
        if ckpt_path is not None:
            self.load_pretrained_weights(ckpt_path)

    def forward(self, sample: torch.Tensor):
        # Forward pass through ImageEncoder components
        features, pos = self.neck(self.trunk(sample))
        if self.scalp > 0:
            # Optionally discard the lowest resolution features
            features, pos = features[: -self.scalp], pos[: -self.scalp]

        # Return only 'vision_features'
        return features[-1]

    def load_pretrained_weights(self, ckpt_path: str):
        """
        Loads pretrained weights from a checkpoint, extracting the image_encoder parts.
        """
        # Load the full checkpoint
        checkpoint = torch.load(ckpt_path, map_location="cpu")
        sam2_checkpoint = checkpoint["model"]

        image_encoder_state_dict = self.state_dict()
        model_keys = set(image_encoder_state_dict.keys())

        # Extract image_encoder weights from the checkpoint
        new_state_dict = {}
        for k, v in sam2_checkpoint.items():
            if (
                k.startswith("image_encoder.")
                and v.shape
                == image_encoder_state_dict[k.replace("image_encoder.", "")].shape
            ):
                new_state_dict[k.replace("image_encoder.", "")] = v
                logging.info(f"Extracted {k} for image_encoder")

        # Update the image_encoder state_dict
        difference = model_keys - set(new_state_dict.keys())
        logging.info(f"Difference in new_state_dict: {difference}")

        # Load the extracted image_encoder weights into the model
        self.load_state_dict(new_state_dict, strict=True)
        logging.info(
            f"Loaded pretrained weights for hiera image encoder from {ckpt_path}"
        )
