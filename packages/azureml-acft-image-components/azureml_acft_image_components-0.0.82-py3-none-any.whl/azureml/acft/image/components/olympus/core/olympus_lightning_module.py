# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import lightning as L
import torch
import hydra
import torch.nn as nn
from lightning.pytorch.utilities.types import OptimizerLRSchedulerConfig
from torchmetrics import Metric
from omegaconf import DictConfig

from ..evaluators import BaseOlympusEvaluator
from ..optimizers import OlympusLRSchedulerFactoryBase, OlympusOptimizerFactoryBase

logger = logging.getLogger(__name__)


class TestMetrics(nn.Module):
    def __init__(self, test: List[Metric]):
        super().__init__()
        self.test = nn.ModuleList(test)


class OlympusLightningModule(L.LightningModule):
    def __init__(
        self,
        model_config: DictConfig,
        evaluator: BaseOlympusEvaluator,
        loss_function: nn.Module,
        optimizer_factory: OlympusOptimizerFactoryBase,
        lr_scheduler_factory: Optional[OlympusLRSchedulerFactoryBase] = None,
    ) -> None:
        super().__init__()
        self.model_config = model_config
        # self.model = nn.Identity() # will be built later
        self.evaluator = evaluator
        self.loss_function = loss_function
        self.optimizer_factory = optimizer_factory
        self.lr_scheduler_factory = lr_scheduler_factory
        self.model = None


    def configure_model(self):
        if self.model is None:
            self.model = hydra.utils.instantiate(
                config=self.model_config,
                _recursive_=True,
                _convert_="object",
            ) 
        print(self.model)

        

    def convert_inputs_to_device(self, inputs: Any) -> Any:
        if isinstance(inputs, dict):
            for key, value in inputs.items():
                if isinstance(value, torch.Tensor):
                    inputs[key] = value.to(self.device)
                else:
                    inputs[key] = value
        return inputs

    def forward(self, inputs: Any) -> Any:
        # Move inputs to the correct device
        inputs = self.convert_inputs_to_device(inputs)
        return self.model(inputs)

    def on_train_start(self) -> None:
        print(f"[Rank {self.global_rank}]  Model type at start of training: {type(self.model)}")
        self.train()

    def on_validation_start(self) -> None:
        self.eval()

    def on_test_start(self) -> None:
        self.eval()

    def on_predict_start(self) -> None:
        """Called at the beginning of predicting."""
        self.eval()

    def get_predictions_and_labels(
        self, batch: Any
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        outputs = self(inputs=batch)
        if type(outputs) is tuple:
            predictions, updated_labels = outputs
        elif type(outputs) is dict:
            predictions = outputs["predictions"]
            updated_labels = outputs.get("labels", None)
        else:
            predictions = outputs
            updated_labels = None
        return predictions, updated_labels

    def training_step(self, batch: Any, batch_idx: int) -> torch.Tensor:
        if "labels" in batch:
            labels = batch["labels"]
        else:
            raise ValueError("Batch does not contain 'labels' key")
        
        logger.info(
            f"[Rank {self.global_rank}] Before Forward Pass: Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB, "
            f"Reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

        # sometimes the model has to further process the labels.
        predictions, updated_labels = self.get_predictions_and_labels(batch)
        if updated_labels is not None:
            labels = updated_labels
        labels = labels.to(self.device)
        logger.info(
            f"[Rank {self.global_rank}] After Forward Pass: Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB, "
            f"Reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")
        loss = self.loss_function(predictions, labels)
        batch_size = labels.size(0)
        self.log(
            "global_step",
            self.global_step,
            on_step=True,
            on_epoch=False,
            sync_dist=False,
        )
        self.log(
            "train_loss",
            loss,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
            batch_size=batch_size,
        )
        return loss

    def validation_step(
        self, batch: Any, batch_idx: int
    ) -> Dict[str, Union[torch.Tensor, Metric]]:

        if "labels" in batch:
            labels = batch["labels"]
        else:
            raise ValueError("Batch does not contain 'labels' key")
        # sometimes the model has to further process the labels.
        predictions, updated_labels = self.get_predictions_and_labels(batch)
        if updated_labels is not None:
            labels = updated_labels
        labels = labels.to(self.device)
        loss = self.loss_function(predictions, labels)
        self.log(
            "validation_loss",
            loss,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            sync_dist=True,
            batch_size=labels.size(0),
        )

        batch = self.convert_inputs_to_device(batch)
        predictions = self.evaluator.predict(self.model, batch)
        # self.evaluator.save_batch_predictions(
        #     predictions, batch_idx=batch_idx, global_idx=self.trainer.global_rank
        # )
        metrics = self.evaluator.evaluate(
            batch=batch,
            predictions=predictions,
            loss_function=self.loss_function,
            metric_stage="validate",
        )

        for metric_name, metric_value in metrics.items():
            reduce_fx = "mean"
            if metric_name.startswith("sum_"):
                reduce_fx = "sum"

            self.log(
                metric_name, value=metric_value, reduce_fx=reduce_fx, sync_dist=True
            )
        
        return metrics

    def test_step(
        self, batch: Any, batch_idx: int, dataloader_idx: int = 0
    ) -> Dict[str, Any]:

        batch = self.convert_inputs_to_device(batch)
        predictions = self.evaluator.predict(self.model, batch)
        self.evaluator.save_batch_predictions(
            predictions, batch_idx=batch_idx, global_idx=self.trainer.global_rank
        )
        metrics = self.evaluator.evaluate(
            batch=batch, predictions=predictions, loss_function=self.loss_function
        )
        for metric_name, metric_value in metrics.items():
            reduce_fx = "mean"
            if metric_name.startswith("sum_"):
                reduce_fx = "sum"

            self.log(
                metric_name, value=metric_value, reduce_fx=reduce_fx, sync_dist=True
            )
        return metrics

    def on_validation_epoch_start(self) -> None:
        # setup output directories, etc.
        self.evaluator.setup(self)

    def on_validation_epoch_end(self) -> None:

        # compute and log validation metrics from the evaluator
        evaluator_metrics = self.evaluator.finish_evaluate(metric_stage="validate")
        for metric_name, metric_value in evaluator_metrics.items():
            self.log(
                metric_name,
                value=metric_value,
                on_step=False,
                on_epoch=True,
                # Note that not syncing works fine for torchmetrics (they sync across
                # devices internally), but likely not for arbitrary metrics
                sync_dist=False,
                rank_zero_only=True,
            )

        # Collect validation metrics logged during validaiton epoch
        validation_metrics = {
            key: value
            for key, value in self.trainer.callback_metrics.items()
            if key.startswith("validate")
        }
        # Add metrics from the evaluator
        validation_metrics.update(evaluator_metrics)

        # Print summary in a nice format
        print("\n" + "=" * 40)
        print("Validation Metrics Summary (End of Epoch)")
        print("=" * 40)
        for metric_name, metric_value in validation_metrics.items():
            # Convert tensor to float if necessary
            metric_value = (
                metric_value.item()
                if isinstance(metric_value, torch.Tensor)
                else metric_value
            )
            print(f"{metric_name:25}: {metric_value:.4f}")
        print("=" * 40 + "\n")

    def on_test_epoch_start(self) -> None:
        # setup output directories, etc.
        self.evaluator.setup(self)  # type: ignore

    def on_test_epoch_end(self) -> None:
        # evaluator caches cleaned predictions, this saves them all at the end
        metrics = self.evaluator.finish_evaluate(metric_stage="test")
        for metric_name, metric_value in metrics.items():
            self.log(
                metric_name,
                value=metric_value,
                on_step=False,
                on_epoch=True,
                # Note that not syncing works fine for torchmetrics (they sync across
                # devices internally), but likely not for arbitrary metrics
                sync_dist=False,
                rank_zero_only=True,
            )

        self.evaluator.save_predictions(global_idx=self.trainer.global_rank)

    def predict_step(self, batch: Any, batch_idx: int) -> Any:
        batch = self.convert_inputs_to_device(batch)
        predictions = self.evaluator.predict(self.model, batch)
        clean_predictions = self.evaluator.save_batch_predictions(
            predictions, batch_idx=batch_idx, global_idx=self.trainer.global_rank
        )
        return clean_predictions

    def on_predict_epoch_start(self) -> None:
        # setup output directories
        self.evaluator.setup(self)

    def on_predict_epoch_end(self) -> None:
        # evaluator caches cleaned predictions, this saves them all at the end
        self.evaluator.save_predictions(global_idx=self.trainer.global_rank)

    @property
    def num_training_steps(self) -> int:
        """Get number of training steps"""
        if self.trainer.max_steps > -1:
            return self.trainer.max_steps

        self.trainer.fit_loop.setup_data()
        dataset_size = len(self.trainer.train_dataloader)
        n_epochs = self.trainer.max_epochs or 1
        grad_accumlation_steps = self.trainer.accumulate_grad_batches or 1
        num_steps = dataset_size * n_epochs // grad_accumlation_steps

        return num_steps

    def configure_optimizers(self) -> OptimizerLRSchedulerConfig:
        params_to_optimize = [
            param for param in self.model.parameters() if param.requires_grad
        ]
        # just assumes the first argument is the parameters to optimize
        optimizer = self.optimizer_factory.get_optimizer(params_to_optimize)
        output: OptimizerLRSchedulerConfig = {"optimizer": optimizer}
        if self.lr_scheduler_factory:
            total_steps = self.num_training_steps
            scheduler = self.lr_scheduler_factory.get_scheduler(optimizer, total_steps)
            output["lr_scheduler"] = {
                "scheduler": scheduler,
                "interval": "step",
                "frequency": 1,
            }

        return output

    # def setup(self, stage=None):
    #     Move the model to the correct device required for deepspeed cpu offloading.
    #     if stage == "test" or stage == "predict":
    #         self._move_to_device(self.model, self.device)

    @staticmethod
    def _move_to_device(module, device):
        for param in module.parameters():
            param.data = param.data.to(device)
            if param._grad is not None:
                param._grad.data = param._grad.data.to(device)
        for buffer in module.buffers():
            buffer.data = buffer.data.to(device)
        module.to(device)
