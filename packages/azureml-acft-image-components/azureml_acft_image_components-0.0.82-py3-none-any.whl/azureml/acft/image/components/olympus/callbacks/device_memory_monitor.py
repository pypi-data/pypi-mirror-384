# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging

import torch
from lightning import Callback

logger = logging.getLogger(__name__)


class DeviceMemoryMonitor(Callback):
    """Logs cuda max memory usage for each GPU during training."""

    def __init__(
        self, on_step: bool = True, on_epoch: bool = True, sync_dist: bool = False
    ):
        self.on_step = on_step
        self.on_epoch = on_epoch
        self.sync_dist = sync_dist

    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx) -> None:
        gpu_idx = trainer.local_rank
        max_memory = torch.cuda.max_memory_allocated(device=gpu_idx)
        max_memory_mb = max_memory / 1024**2
        logger.info(f"GPU {gpu_idx} max memory: {max_memory / 1024 ** 2:.2f} MB")
        trainer.lightning_module.log(
            name=f"device_{gpu_idx:02d}_max_memory_MB",
            value=max_memory_mb,
            sync_dist=self.sync_dist,
            on_step=self.on_step,
            on_epoch=self.on_epoch,
            reduce_fx="max",
        )
