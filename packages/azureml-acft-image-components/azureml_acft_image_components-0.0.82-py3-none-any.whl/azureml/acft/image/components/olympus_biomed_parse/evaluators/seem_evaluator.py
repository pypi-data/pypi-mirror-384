# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from dataclasses import dataclass
from typing import Dict

import torch
from torch.nn import functional as F
from ...olympus.evaluators.base import BaseOlympusEvaluator, CleanPredictions


@dataclass
class SEEMPredictions:
    predictions: Dict
    labels: torch.Tensor
    gold_labels: torch.Tensor


class SEEMEvaluator(BaseOlympusEvaluator[SEEMPredictions]):

    def postprocess(self, model_outputs):
        low_res_pred = torch.sigmoid(model_outputs)
        image_seg = (low_res_pred > 0.5).int()
        return image_seg

    def predict(self, model: torch.nn.Module, batch: dict) -> SEEMPredictions:
        # given a model and a batch, return the model's predictions as a custom
        # ResultType
        outputs = model(batch, mode="eval")

        predictions = outputs["predictions"]

        gold_labels = batch.get("labels", None)

        batch_size, num_masks, height, width = predictions.shape
        mask_pred_results = []
        for idx in range(batch_size):
            pred_gmasks = predictions[idx]
            mask_pred_results.append(pred_gmasks)

        if height != gold_labels.shape[-2] or width != gold_labels.shape[-1]:
            for i in range(len(mask_pred_results)):
                mask_pred_results[i] = F.interpolate(
                    mask_pred_results[i][None,],
                    size=gold_labels.shape[-2:],
                    mode="bicubic",
                    align_corners=False,
                    antialias=True,
                )[0]

        mask_preds = torch.stack(mask_pred_results, dim=0)

        gold_labels = gold_labels.to(pred_gmasks.device)

        predicted_labels = self.postprocess(mask_preds)

        predictions = SEEMPredictions(
            predictions=predictions, labels=predicted_labels, gold_labels=gold_labels
        )
        return predictions

    def evaluate(
        self,
        batch: dict,
        predictions: SEEMPredictions,
        loss_function: torch.nn.Module,
        metric_stage: str = "test",
    ) -> Dict[str, torch.Tensor]:
        # given a batch and pre-computed predictions, return a dictionary of metrics
        # that includes the loss in the "loss" key

        if "labels" not in batch:
            raise ValueError("Batch does not contain 'labels' key")

        metrics = {}
        loss = loss_function(predictions.predictions, predictions.gold_labels)
        metrics["test_loss"] = loss
        num_samples = predictions.gold_labels.size(0)
        metrics["sum_num_samples"] = num_samples

        base_metrics = self._get_core_metrics(
            predictions.labels, predictions.gold_labels, metric_stage=metric_stage
        )
        metrics.update(base_metrics)

        return metrics

    def clean_predictions(self, predictions: SEEMPredictions) -> CleanPredictions:
        # given precomputed predictions, return a list of per-item results to save.
        # These should be JSON-serialable dictionaries.
        batch_outputs = [
            {"predicted": label.tolist(), "gold": gold.tolist()}
            for label, gold in zip(predictions.labels, predictions.gold_labels)
        ]
        return batch_outputs
