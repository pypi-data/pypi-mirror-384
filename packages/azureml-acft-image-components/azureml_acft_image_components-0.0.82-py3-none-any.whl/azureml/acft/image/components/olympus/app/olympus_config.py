# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
# Filename: train.py
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import lightning as L
import torch
from lightning.pytorch.callbacks import Callback

from ..evaluators import BaseOlympusEvaluator
from ..loaders import ModelCheckpointLoaderBase
from ..optimizers import OlympusLRSchedulerFactoryBase, OlympusOptimizerFactoryBase

os.environ["HYDRA_FULL_ERROR"] = "1"
logger = logging.getLogger(__name__)


class OlympusMode(Enum):
    train = "train"
    predict = "predict"
    test = "test"


@dataclass
class _OlympusCheckpoint:
    load_checkpoint: bool = False
    loader: Optional[ModelCheckpointLoaderBase] = None


@dataclass
class OlympusConfig:
    trainer: L.Trainer
    datamodule: L.LightningDataModule
    loss: torch.nn.Module
    optimizer: OlympusOptimizerFactoryBase
    evaluator: Optional[BaseOlympusEvaluator]
    model: torch.nn.Module
    mode: OlympusMode

    # Checkpoint to load
    olympus_checkpoint: _OlympusCheckpoint
    # By default, we add a 'last' model checkpointer and early stopping, but if we're
    # using custom callbacks we probably want to disable the defaults.
    disable_default_callbacks: bool = False

    # optional fields
    lr_scheduler: Optional[OlympusLRSchedulerFactoryBase] = None

    # old-style mount points where only external_mount and output_mount are allowed
    external_mount: Optional[str] = None
    output_mount: Optional[str] = None
    # prefer using 'mounts' now, which is just a mapping of names to paths
    mounts: Optional[Dict[str, str]] = None
    # experiment_name is meant to be set per-run, not hard-coded in the config
    experiment_name: Optional[str] = None
    # job_name is meant to be set per-run, not hard-coded in the config
    job_name: Optional[str] = None
    # by default, becomes part of the output directory tree
    project_name: str = "olympus"
    # if unset, a reasonable default will be used
    experiment_output_dir: Optional[str] = None

    # named callbacks to be used in the Trainer, but names can be arbitrary
    callbacks: Dict[str, Callback] = field(default_factory=dict)

    # Registry of named objects. These are instantiated in order and can be referenced
    # thoruoghout the config. This is a way to guarantee instantiation order avoid
    # re-instantiation
    registry: Optional[Dict[str, Any]] = None

    # Arbitrary key-value pairs that can be referenced in the config. Only for
    # simplifying config instantiations, not used by python code.
    scratch: Optional[Dict[str, Any]] = None
