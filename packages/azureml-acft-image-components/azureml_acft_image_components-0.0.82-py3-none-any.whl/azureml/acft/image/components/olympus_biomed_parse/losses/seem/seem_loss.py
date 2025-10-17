# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import torch
import torch.nn as nn
from scipy.optimize import linear_sum_assignment

# Assuming MedSamLoss and DiceLoss classes are imported or defined above


class HungarianMatcher(nn.Module):
    def __init__(self):
        super(HungarianMatcher, self).__init__()

    def forward(self, pred_masks, target_masks):
        batch_size, num_queries, height, width = pred_masks.shape
        pred_masks_flat = pred_masks.view(
            batch_size, num_queries, -1
        )  # Flatten height and width
        target_masks_flat = target_masks.view(
            batch_size, -1
        ).float()  # Flatten height and width and convert to float

        matched_pred_indices = []
        matched_target_indices = []

        for i in range(batch_size):
            pred_flat = pred_masks_flat[i]
            target_flat = target_masks_flat[i]

            # Calculate pairwise cost
            cost_matrix = torch.cdist(pred_flat, target_flat.unsqueeze(0), p=2).squeeze(
                0
            )

            # Hungarian matching
            row_ind, col_ind = linear_sum_assignment(cost_matrix.detach().cpu().numpy())
            matched_pred_indices.append(torch.tensor(row_ind, device=pred_masks.device))
            matched_target_indices.append(
                torch.tensor(col_ind, device=target_masks.device)
            )

        return matched_pred_indices, matched_target_indices


class SEEMLoss(nn.Module):
    def __init__(self, matcher=None, loss=None):
        super(SEEMLoss, self).__init__()
        self.matcher = matcher if matcher else HungarianMatcher()
        self.loss = loss if loss else torch.nn.CrossEntropyLoss()

    def forward(self, predictions, labels):

        # temperature = predictions["logit_scale"]
        # # pred_masks = predictions["pred_masks"]
        target_masks = labels

        # matched_pred_indices, matched_target_indices = self.matcher(
        #     pred_masks, target_masks
        # )

        # batch_size = len(matched_pred_indices)

        batch_size, num_masks, height, width = predictions.shape
        mask_pred_results = []
        for idx in range(batch_size):
            pred_gmasks = predictions[idx]
            if height != target_masks.shape[-2] or width != target_masks.shape[-1]:
                pred_gmasks = torch.nn.functional.interpolate(
                    pred_gmasks[None,],
                    size=target_masks.shape[-2:],
                    mode="bicubic",
                    align_corners=False,
                    antialias=True,
                )[0]
            # v_emb = predictions["pred_gtexts"][idx]
            # t_emb = predictions["class_emb"][idx]

            # # v1 similarity
            # t_emb = t_emb / (t_emb.norm(dim=-1, keepdim=True) + 1e-7)
            # v_emb = v_emb / (v_emb.norm(dim=-1, keepdim=True) + 1e-7)

            # logits = torch.matmul(v_emb, t_emb.t())
            # out_prob = temperature.exp().clamp(max=100) * logits
            # matched_id = out_prob.max(0)[1]
            # matched_mask = pred_gmasks[matched_id, :, :][None, :, :]
            mask_pred_results.append(pred_gmasks)

            # losses = []
            # for i in range(batch_size):
            #     pred_indices = matched_pred_indices[i]
            #     # print(pred_indices)
            #     target_indices = matched_target_indices[i]

            #     selected_pred_masks = pred_masks[i, pred_indices]
            #     selected_target_masks = target_masks[i, target_indices]

            #     # cross entropy between logits and selected target masks
            #     pred_gmasks = predictions["pred_gmasks"][i]
            #     v_emb = predictions["pred_gtexts"][i]
            #     t_emb = predictions["class_emb"][i]

            #     t_emb = t_emb / (t_emb.norm(dim=-1, keepdim=True) + 1e-7)
            #     v_emb = v_emb / (v_emb.norm(dim=-1, keepdim=True) + 1e-7)

            #     logits = torch.matmul(v_emb, t_emb.t())  # [101]
            #     logits = logits.unsqueeze(0)

            #     ce = torch.nn.CrossEntropyLoss()
            #     ce_loss = ce(logits, pred_indices)

            # Register a hook on the tensors only if they require gradients
            # if selected_pred_masks.requires_grad:
            #     selected_pred_masks.register_hook(
            #         lambda grad: print(f"Grad of selected_pred_masks: {grad}")
            #     )

            # Note: We do not register a hook on `selected_target_masks` because it typically does not require gradients

            # loss = self.loss(selected_pred_masks, selected_target_masks) + ce_loss
            # losses.append(loss)
        mask_preds = torch.stack(mask_pred_results, dim=0)
        total_loss = self.loss(mask_preds, target_masks)

        # # Register a hook on the total loss
        # if total_loss.requires_grad:
        #     total_loss.register_hook(lambda grad: print(f"Grad of total_loss: {grad}"))

        return total_loss
