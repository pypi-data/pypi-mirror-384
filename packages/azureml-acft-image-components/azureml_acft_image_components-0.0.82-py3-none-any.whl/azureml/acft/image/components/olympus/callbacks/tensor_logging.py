# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import collections

from lightning import Callback
from torch import nn


def print_trainable(m: nn.Module):
    n_elements = 0
    n_trainable = 0
    for p in m.parameters():
        # test if trainable:
        n_el = p.numel()
        if p.requires_grad:
            n_trainable += n_el
        n_elements += n_el
    print(
        f"Total elements: {n_elements}, trainable: {n_trainable}, "
        f"percentage: {n_trainable/n_elements:.2%}"
    )


def count_param_types(m: nn.Module):
    count = collections.defaultdict(int)
    for p in m.parameters():
        count[(str(p.device), str(p.dtype))] += p.numel()
    count = dict(count)
    print(f"Total elements: {count}")
    return count


class TensorLogging(Callback):
    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx) -> None:
        if batch_idx == 0 and trainer.model is not None:
            print_trainable(trainer.model)
            count_param_types(trainer.model)
