# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import re

from lightning.pytorch.callbacks import Callback


class DatasetNameLoggerCallback(Callback):
    def on_test_end(self, trainer, pl_module):
        # Access datamodule
        datamodule = getattr(trainer, "datamodule", None)
        if not datamodule:
            return

        # Get dataset names from datamodule
        dataset_names = getattr(datamodule, "test_dataset_names", None)
        if not dataset_names:
            return

        # Get all logged metrics
        metrics = trainer.callback_metrics

        # Create a list of keys to update to avoid modifying the dict during iteration
        keys_to_update = []
        for key in metrics.keys():
            if "dataloader_idx" in key:
                for idx, name in enumerate(dataset_names):
                    pattern = re.compile(f"dataloader_idx_{idx}(?!\\d)")
                    if pattern.search(key):
                        new_key = pattern.sub(name, key)
                        keys_to_update.append((key, new_key))

        # Update the keys in the existing metrics dictionary
        # trainer.callback_metrics.clear()

        for old_key, new_key in keys_to_update:
            if old_key in metrics:
                metrics[new_key] = metrics[old_key]

        # Update the trainer's logger
        for logger in trainer.loggers:
            if hasattr(logger, "log_metrics"):
                logger.log_metrics(metrics)
