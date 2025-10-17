# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
import time
from typing import Any

import lightning as L
from lightning.pytorch.utilities.data import extract_batch_size

logger = logging.getLogger(__name__)


class TrainThroughputMonitor(L.Callback):
    """Log the throughput of data items in the training loop in items per second."""

    def __init__(
        self, on_step: bool = True, on_epoch: bool = True, sync_dist: bool = False
    ):
        self.on_step = on_step
        self.on_epoch = on_epoch
        self.sync_dist = sync_dist
        self._step_start = None

    def on_train_batch_start(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        batch: Any,
        batch_idx: int,
    ) -> None:
        assert self._step_start is None
        self._step_start = time.time()

    def on_train_batch_end(
        self,
        trainer: L.Trainer,
        pl_module: L.LightningModule,
        outputs: Any,
        batch: Any,
        batch_idx: int,
    ) -> None:
        assert self._step_start is not None
        step_time = time.time() - self._step_start
        self._step_start = None
        if step_time <= 0:
            logger.warning("Step time is zero or negative, setting throughput to zero to avoid division by zero.")
            throughput = 0
        else:
            batch_size = extract_batch_size(batch)
            throughput = batch_size / step_time

        if not self.sync_dist:
            metric_name = f"data_item_throughput.device_{trainer.global_rank:02d}"
        else:
            metric_name = "data_item_throughput"

        trainer.lightning_module.log(
            name=metric_name,
            value=throughput,
            sync_dist=self.sync_dist,
            on_step=True,
            on_epoch=True,
            reduce_fx="mean",
        )
