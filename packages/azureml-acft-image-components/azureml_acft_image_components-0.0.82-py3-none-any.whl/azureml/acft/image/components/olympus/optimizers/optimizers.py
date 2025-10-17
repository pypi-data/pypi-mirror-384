# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from typing import Iterable, Type, Union

from hydra.utils import get_class
from torch import nn
from torch.optim import Optimizer
from torch.optim.lr_scheduler import LRScheduler
from transformers.optimization import get_scheduler


class OlympusOptimizerFactoryBase:
    def get_optimizer(self, params: Iterable[nn.parameter.Parameter]) -> Optimizer:
        raise NotImplementedError


class OlympusLRSchedulerFactoryBase:
    def get_scheduler(self, optimizer: Optimizer, total_steps: int) -> LRScheduler:
        raise NotImplementedError


class TorchOptimizer(OlympusOptimizerFactoryBase):
    def __init__(self, opt_class: Union[Type[Optimizer], str], **kwargs):
        if isinstance(opt_class, str):
            opt_class = get_class(opt_class)
        self._opt_class = opt_class
        self._opt_args = kwargs

    def get_optimizer(self, params: Iterable[nn.parameter.Parameter]) -> Optimizer:
        return self._opt_class(params=params, **self._opt_args)


class DeepSpeedOptimizer(OlympusOptimizerFactoryBase):
    def __init__(self, opt_class: Union[Type[Optimizer], str], **kwargs):
        if isinstance(opt_class, str):
            opt_class = get_class(opt_class)
        self._opt_class = opt_class
        self._opt_args = kwargs

    def get_optimizer(self, params: Iterable[nn.parameter.Parameter]) -> Optimizer:
        # DeepSpeed optimizers take input model_params instead of params
        return self._opt_class(model_params=params, **self._opt_args)


class TorchSchedulerFactory(OlympusLRSchedulerFactoryBase):
    def __init__(self, scheduler_name: str, warmup_ratio: float, **kwargs):
        self._scheduler_name = scheduler_name
        self._warmup_ratio = warmup_ratio
        self._scheduler_args = kwargs

    def get_scheduler(self, optimizer: Optimizer, total_steps: int) -> LRScheduler:
        return get_scheduler(
            name=self._scheduler_name,
            optimizer=optimizer,
            num_warmup_steps=int(total_steps * self._warmup_ratio),
            num_training_steps=total_steps,
            **self._scheduler_args,
        )
