# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
# avoid circular imports due to typedefs
from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Dict, Generic, List, Optional, TypeVar, Union

import torch
from torchmetrics import Metric

if TYPE_CHECKING:
    from ..core.olympus_lightning_module import OlympusLightningModule

logger = logging.getLogger(__name__)


ResultType = TypeVar("ResultType")
# cleaned predictions should be a list of json-serializable dicts
CleanPredictions = List[dict]


class BaseOlympusEvaluator(Generic[ResultType]):
    """
    Class providing the interface for custom prediction and evaluation.
    For basic use, override 'predict', 'evauate', and 'clean_predictions' methods.

    This class will be used in evaluation as:
    predictions = evaluator.predict(model, batch)
    metrics = evaluator.evaluate(batch, predictions, loss_function)
    # metrics are logged
    cleaned_predictions = evaluator.clean_predictions(predictions)

    or for prediction as:
    predictions = evaluator.predict(model, batch)
    cleaned_predictions = evaluator.clean_predictions(predictions)
    """

    def __init__(
        self,
        predictions_fmt: Optional[str] = "predictions_device_{global_idx:02d}.json",
        predictions_batch_fmt: Optional[
            str
        ] = "predictions_batch_{batch_idx:04d}_device{global_idx:02d}.json",
    ) -> None:
        self.predictions_fmt = predictions_fmt
        self.predictions_batch_fmt = predictions_batch_fmt
        self._saved_predictions: CleanPredictions = []
        if self.predictions_fmt:
            if not self.predictions_fmt.endswith(".json"):
                raise ValueError("only .json format suppored for saved predictions")
            # check that the format string has the correct fields
            try:
                self.predictions_fmt.format(global_idx=0)
            except KeyError as e:
                raise ValueError(
                    f"predictions_fmt must contain the field 'global_idx': {e}"
                )

        if self.predictions_batch_fmt:
            # check that the format string has the correct fields
            if not self.predictions_batch_fmt.endswith(".json"):
                raise ValueError("only .json format suppored for saved predictions")
            try:
                self.predictions_batch_fmt.format(batch_idx=0, global_idx=0)
            except KeyError as e:
                raise ValueError(
                    "predictions_batch_fmt must contain the field 'global_idx' and "
                    f"'batch_idx': {e}"
                )

    def setup(self, lightning_module: OlympusLightningModule) -> None:
        if self.predictions_batch_fmt:
            # create the directory for the batch predictions
            sample_name = self.predictions_batch_fmt.format(batch_idx=0, global_idx=0)
            output_dir = os.path.dirname(sample_name)
            if output_dir:
                logger.info(f"Creating directory for batch predictions: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)

        if self.predictions_fmt:
            # create the directory for the batch predictions
            sample_name = self.predictions_fmt.format(global_idx=0)
            output_dir = os.path.dirname(sample_name)
            if output_dir:
                logger.info(f"Creating directory for batch predictions: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)

    def predict(self, model: torch.nn.Module, batch: dict) -> ResultType:
        # given a model and a batch, return the model's predictions as a custom
        # ResultType
        raise NotImplementedError("This function should be implemented by the subclass")

    def evaluate(
        self,
        batch: dict,
        predictions: ResultType,
        loss_function: torch.nn.Module,
        metric_stage: str = "test",
    ) -> Dict[str, Union[torch.Tensor, Metric]]:
        # given a batch and pre-computed predictions, return a dictionary of metrics
        # that includes the loss in the "loss" key
        raise NotImplementedError("This function should be implemented by the subclass")

    def finish_evaluate(self, metric_stage: str = "test") -> Dict[str, torch.Tensor]:
        # called at the end of each evaluation / epoch so that evaluations with internal
        # state can log their results. Not necessary for automaticaly-reduced metrics
        # returned at each step by evaluate().
        return {}

    def clean_predictions(self, predictions: ResultType) -> CleanPredictions:
        # given precomputed predictions, return a list of per-item results to save.
        # These should be JSON-serialable dictionaries.
        raise NotImplementedError("This function should be implemented by the subclass")

    def save_batch_predictions(
        self, predictions: ResultType, batch_idx: int, global_idx: int
    ) -> CleanPredictions:
        # Save the predictions for this batch. This is called by OlympusLightningModule,
        # and should not be called directly. Users can override to provide custom
        # functionality.
        batch_predictions = self.clean_predictions(predictions)
        if self.predictions_fmt:
            self._saved_predictions.extend(batch_predictions)
        if self.predictions_batch_fmt:
            batch_predictions_path = self.predictions_batch_fmt.format(
                batch_idx=batch_idx, global_idx=global_idx
            )
            logger.debug(f"Saving batch predictions to {batch_predictions_path}")
            with open(batch_predictions_path, "w") as f:
                json.dump(batch_predictions, f)
        return batch_predictions

    def save_predictions(self, global_idx: int) -> None:
        # Save the cached predictions. This is called by OlympusLightningModule,
        # and should not be called directly. Users can override to provide custom
        # functionality.
        if self.predictions_fmt:
            predictions_path = self.predictions_fmt.format(global_idx=global_idx)
            logger.info(f"Saving predictions to {predictions_path}")
            with open(predictions_path, "w") as f:
                json.dump(self._saved_predictions, f)
        # clear the saved predictions (probably unnecessary)
        self._saved_predictions = []

    def _get_core_metrics(
        self, outputs: torch.Tensor, labels: torch.Tensor, metric_stage="test"
    ):
        # this is a dummy function that should be implemented by the subclass
        metrics = {}
        non_batch_axes = tuple(range(1, labels.dim()))
        accuracy = (outputs == labels).float().mean(dim=non_batch_axes).mean()
        metrics[f"{metric_stage}_accuracy"] = accuracy

        intersection = (
            ((outputs == labels) & (outputs > 0) & (labels > 0))
            .float()
            .sum(dim=non_batch_axes)
        )
        label_sum = (labels > 0).float().sum(dim=non_batch_axes)
        prediction_sum = (outputs > 0).float().sum(dim=non_batch_axes)
        dice_score = (2 * intersection + 1e-6) / (label_sum + prediction_sum + 1e-6)
        metrics[f"{metric_stage}_dice_score"] = dice_score.mean()

        union = (outputs | labels).float().sum(dim=non_batch_axes)
        iou = intersection / (union + 1e-6)
        metrics[f"{metric_stage}_iou"] = iou.mean()

        TP = ((outputs > 0) & (labels > 0)).float().sum(dim=non_batch_axes)
        FP = ((outputs > 0) & (labels == 0)).float().sum(dim=non_batch_axes)
        TN = ((outputs == 0) & (labels == 0)).float().sum(dim=non_batch_axes)
        FN = ((outputs == 0) & (labels > 0)).float().sum(dim=non_batch_axes)

        sensitivity = TP / (TP + FN + 1e-6)
        metrics[f"{metric_stage}_sensitivity"] = sensitivity.mean()

        specificity = TN / (TN + FP + 1e-6)
        metrics[f"{metric_stage}_specificity"] = specificity.mean()

        precision = TP / (TP + FP + 1e-6)
        metrics[f"{metric_stage}_precision"] = precision.mean()

        f1_score = 2 * (precision * sensitivity) / (precision + sensitivity + 1e-6)
        metrics[f"{metric_stage}_f1_score"] = f1_score.mean()

        sq = iou.mean()
        rq = TP / (TP + 0.5 * FP + 0.5 * FN + 1e-6)
        pq = sq * rq
        metrics[f"{metric_stage}_pq"] = pq.mean()

        return metrics
