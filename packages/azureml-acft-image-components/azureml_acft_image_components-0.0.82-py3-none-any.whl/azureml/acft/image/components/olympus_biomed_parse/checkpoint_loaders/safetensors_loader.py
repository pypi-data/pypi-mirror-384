# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import os
import lightning as L
import torch
from azureml.dataprep.api._loggerfactory import _LoggerFactory
from safetensors.torch import load_file, save_file
from ...olympus.core import OlympusLightningModule
from ...olympus.loaders import ModelCheckpointLoaderBase

logger = _LoggerFactory.get_logger(__name__)

def strip_prefix_if_present(state_dict, prefixes=("model.", "module.")):
    """Remove unwanted prefixes from state_dict keys."""
    new_state_dict = {}
    for k, v in state_dict.items():
        if isinstance(v, torch.Tensor):
            for prefix in prefixes:
                if k.startswith(prefix):
                    k = k[len(prefix):]
                    break
            new_state_dict[k] = v
    return new_state_dict

def convert_ckpt_to_safetensor(ckpt_path, output_path=None):    
    logger.info(f"Loading checkpoint from: {ckpt_path}")
    state_dict = torch.load(ckpt_path, map_location="cpu")

    # Handle Lightning or Trainer wrapped checkpoint
    if "state_dict" in state_dict:
        logger.info("Detected Lightning-style checkpoint. Extracting 'state_dict'.")
        state_dict = state_dict["state_dict"]

    # Strip common prefixes like "model." or "module."
    tensor_state_dict = strip_prefix_if_present(state_dict)

    # Set output path
    if output_path is None:
        output_path = os.path.splitext(ckpt_path)[0] + ".safetensors"

    # Save as .safetensors
    logger.info(f"Saving .safetensors to: {output_path}")
    save_file(tensor_state_dict, output_path)
    logger.info("Conversion complete.")

class SafeTensorsLoader(ModelCheckpointLoaderBase):
    def __init__(self, strict=False, assign=False, checkpoint_path=None):
        super().__init__(strict=strict, assign=assign, checkpoint_path=checkpoint_path)

    def load(self, model: OlympusLightningModule, trainer: L.Trainer):
        logger.info(f"Loading SafeTensors from {self.checkpoint_path}")
        
        state_dict = load_file(self.checkpoint_path)
        state_dict.pop('loss_function.loss.dice_loss.class_weight', None) # equals 1, no need to update
                
        model.model.load_state_dict(state_dict, strict=self.strict, assign=self.assign)