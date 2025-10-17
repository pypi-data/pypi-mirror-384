# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
from typing import Dict, List, Optional

import lightning as L
import torch
from torch.utils.data import DataLoader

from ..core import OlympusLightningModule
from ..datasets import EmptyDataset
from ..utils.state_dict_utils import remap_state_dict

logger = logging.getLogger(__name__)


class ModelCheckpointLoaderBase:
    def __init__(
        self,
        strict: bool = True,
        assign: bool = False,
        checkpoint_path: Optional[str] = None,
    ):
        """basic model checkpoint loading"""
        self.strict = strict
        self.assign = assign
        if checkpoint_path is None:
            raise ValueError("checkpoint_path must be provided")
        self.checkpoint_path = checkpoint_path

    def load(self, model: OlympusLightningModule, trainer: L.Trainer):
        logger.info(f"Loading checkpoint from {self.checkpoint_path}")
        state_dict = torch.load(self.checkpoint_path, map_location=torch.device("cpu"))

        # This is added for some checkpoints (e.g., llava-ct) that stored state_dict
        # inside a dictionary
        if state_dict.get("state_dict"):
            state_dict = state_dict.get("state_dict")

        model.load_state_dict(state_dict, strict=self.strict, assign=self.assign)


class RemappingModelCheckpointLoader(ModelCheckpointLoaderBase):
    def __init__(
        self,
        strict: bool = True,
        assign: bool = False,
        param_prefix_remapping: Optional[Dict[str, str]] = None,
        param_prefixes_to_drop: Optional[List[str]] = None,
        checkpoint_path: Optional[str] = None,
    ):
        """Model checkpoint loading with remapping and/or dropping of parameters based
        on name prefixes"""
        super().__init__(strict, assign, checkpoint_path)
        self.param_prefix_remapping = param_prefix_remapping or {}
        self.param_prefixes_to_drop = param_prefixes_to_drop or []

    def load(self, model: OlympusLightningModule, trainer: L.Trainer):
        logger.info(f"Loading checkpoint from {self.checkpoint_path}")
        state_dict = torch.load(self.checkpoint_path, map_location=torch.device("cpu"))

        # This is added for some checkpoints (e.g., llava-ct) that stored state_dict
        # inside a dictionary
        if state_dict.get("state_dict"):
            print("state_dict found in checkpoint")
            state_dict = state_dict.get("state_dict")

        updated_state_dict = remap_state_dict(
            state_dict,
            param_prefix_remapping=self.param_prefix_remapping,
            param_prefixes_to_drop=self.param_prefixes_to_drop,
        )
        model.load_state_dict(
            updated_state_dict, strict=self.strict, assign=self.assign
        )


class OlympusDeepspeedCheckpointLoader(ModelCheckpointLoaderBase):
    def __init__(
        self,
        strict: bool = True,
        assign: bool = False,
        checkpoint_path: Optional[str] = None,
    ):
        super().__init__(strict, assign, checkpoint_path)

    def load(self, model: OlympusLightningModule, trainer: L.Trainer):
        # run a dummy fit to load the model from the checkpoint
        logger.info(f"Loading deepspeed checkpoint from {self.checkpoint_path}")
        trainer.fit(
            model=model,
            train_dataloaders=DataLoader(dataset=EmptyDataset()),
            val_dataloaders=DataLoader(dataset=EmptyDataset()),
            ckpt_path=self.checkpoint_path,
        )


class OlympusRecoverTrainingCheckpointLoader(ModelCheckpointLoaderBase):
    def __init__(
        self,
        strict: bool = True,
        assign: bool = False,
        checkpoint_path: Optional[str] = None,
    ):
        super().__init__(strict, assign, checkpoint_path)

    def load(self, model: OlympusLightningModule, trainer: L.Trainer):
        # just get the checkpoint path
        logger.info(f"Loading previous run checkpoint from {self.checkpoint_path}")
