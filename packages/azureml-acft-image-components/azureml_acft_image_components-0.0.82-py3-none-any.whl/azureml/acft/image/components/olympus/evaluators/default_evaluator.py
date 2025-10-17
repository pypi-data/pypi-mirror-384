# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from dataclasses import dataclass
from typing import Dict

import torch

from .base import BaseOlympusEvaluator, CleanPredictions


@dataclass
class ModelPredictions:
    logits: torch.Tensor
    labels: torch.Tensor
    gold_labels: torch.Tensor


class DefaultEvaluator(BaseOlympusEvaluator[ModelPredictions]):

    def postprocess(self, outputs):
        return outputs.argmax(dim=1)

    def predict(self, model: torch.nn.Module, batch: dict) -> ModelPredictions:
        # given a model and a batch, return the model's predictions as a custom
        # ResultType
        outputs = model(batch)

        gold_labels = batch.get("labels", None)
        if type(outputs) is tuple:
            logits, updated_labels = outputs
        elif type(outputs) is dict:
            logits = outputs["logits"]
            updated_labels = outputs.get("labels", None)
        else:
            logits = outputs
            updated_labels = None

        if updated_labels is not None:
            gold_labels = updated_labels

        gold_labels = gold_labels.to(logits.device)

        outputs = self.postprocess(logits)

        predictions = ModelPredictions(
            logits=logits, labels=outputs, gold_labels=gold_labels
        )
        return predictions

    def evaluate(
        self,
        batch: dict,
        predictions: ModelPredictions,
        loss_function: torch.nn.Module,
        metric_stage="test",
    ) -> Dict[str, torch.Tensor]:
        # given a batch and pre-computed predictions, return a dictionary of metrics
        # that includes the loss in the "loss" key

        if "labels" not in batch:
            raise ValueError("Batch does not contain 'labels' key")

        # Note: validation loss is computed in the OlympusLightningModule
        # validation_step
        metrics = {}
        num_samples = predictions.gold_labels.size(0)
        metrics[f"sum_num_samples_{metric_stage}"] = num_samples

        base_metrics = self._get_core_metrics(
            predictions.labels, predictions.gold_labels, metric_stage=metric_stage
        )
        metrics.update(base_metrics)

        return metrics

    def clean_predictions(self, predictions: ModelPredictions) -> CleanPredictions:
        # given precomputed predictions, return a list of per-item results to save.
        # These should be JSON-serialable dictionaries.
        batch_outputs = [
            {"predicted": label.tolist(), "gold": gold.tolist()}
            for label, gold in zip(predictions.labels, predictions.gold_labels)
        ]
        return batch_outputs
