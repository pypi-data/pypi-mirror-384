# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from dataclasses import dataclass
from typing import Dict

import torch
from ...olympus.evaluators.base import BaseOlympusEvaluator, CleanPredictions


@dataclass
class MedSamPredictions:
    logits: torch.Tensor
    labels: torch.Tensor
    gold_labels: torch.Tensor


class MedSamEvaluator(BaseOlympusEvaluator[MedSamPredictions]):

    def postprocess(self, model_outputs):
        low_res_pred = torch.sigmoid(model_outputs)
        medsam_seg = (low_res_pred > 0.5).int()
        return medsam_seg

    def predict(self, model: torch.nn.Module, batch: dict) -> MedSamPredictions:
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

        predictions = MedSamPredictions(
            logits=logits, labels=outputs, gold_labels=gold_labels
        )
        return predictions

    def evaluate(
        self,
        batch: dict,
        predictions: MedSamPredictions,
        loss_function: torch.nn.Module,
        metric_stage: str = "test",
    ) -> Dict[str, torch.Tensor]:
        # given a batch and pre-computed predictions, return a dictionary of metrics
        # that includes the loss in the "loss" key

        if "labels" not in batch:
            raise ValueError("Batch does not contain 'labels' key")

        metrics = {}
        loss = loss_function(predictions.logits, predictions.gold_labels)
        metrics["test_loss"] = loss
        num_samples = predictions.gold_labels.size(0)
        metrics["sum_num_samples"] = num_samples

        base_metrics = self._get_core_metrics(
            predictions.labels, predictions.gold_labels, metric_stage=metric_stage
        )
        metrics.update(base_metrics)

        return metrics

    def clean_predictions(self, predictions: MedSamPredictions) -> CleanPredictions:
        # given precomputed predictions, return a list of per-item results to save.
        # These should be JSON-serialable dictionaries.
        batch_outputs = [
            {"predicted": label.tolist(), "gold": gold.tolist()}
            for label, gold in zip(predictions.labels, predictions.gold_labels)
        ]
        return batch_outputs
