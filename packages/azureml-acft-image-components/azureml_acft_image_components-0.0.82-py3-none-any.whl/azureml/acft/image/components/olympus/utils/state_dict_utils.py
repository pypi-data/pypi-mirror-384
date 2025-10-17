# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import collections
import math
from dataclasses import dataclass
from pprint import PrettyPrinter
from typing import Dict, Iterable, Optional, Set

import torch
from torch import nn

pp = PrettyPrinter(indent=2)


@dataclass(frozen=True)
class TensorTypeInfo:
    dtype: torch.dtype
    device: torch.device
    requires_grad: bool


@dataclass
class TensorInfo:
    type: TensorTypeInfo
    shape: tuple


def _tensor_info(t: torch.Tensor | nn.Parameter) -> TensorInfo:
    ti = TensorTypeInfo(
        dtype=t.dtype,
        device=t.device,
        requires_grad=t.requires_grad,
    )
    return TensorInfo(type=ti, shape=t.shape)


def _get_tensor_info(t: nn.Module | dict, k: str) -> TensorInfo:
    if isinstance(t, nn.Module):
        p = t.get_parameter(k)
    else:
        p = t[k]
    return _tensor_info(p)


def _get_keys(t: nn.Module | dict) -> Set[str]:
    if isinstance(t, nn.Module):
        return set(t.state_dict().keys())
    return set(t.keys())


def tensor_info(
    state_dict: nn.Module | dict,
    prefix: Optional[str] = None,
    short: bool = False,
    keys: Optional[Iterable[str]] = None,
):
    keys = _get_keys(state_dict)
    if prefix:
        keys = [k for k in keys if k.startswith(prefix)]
    print(f"{prefix or 'All'} tensors: {len(keys)}")
    if short:
        return
    nel = collections.defaultdict(int)
    for k in keys:
        ti = _get_tensor_info(state_dict, k)
        nel[ti.type] += math.prod(ti.shape)
    nel = {k: v for k, v in nel.items()}
    print(f"{prefix or 'All'} elements:")
    pp.pprint(nel)


def hierarchical_state_dict(
    state_dict: nn.Module | dict,
    prefix: Optional[str] = None,
    max_depth: Optional[int] = None,
    short: bool = False,
    keys: Optional[Iterable[str]] = None,
):
    if keys is None:
        keys = _get_keys(state_dict)
    tensor_info(state_dict, prefix, keys=keys, short=short)
    prefix = f"{prefix}." if prefix else ""
    if prefix:
        keys = [k for k in keys if k.startswith(prefix)]
    if max_depth is not None and max_depth <= 1:
        return
    split_keys = [k[len(prefix) :].split(".") for k in keys]
    top_level_names = set([k[0] for k in split_keys])
    print("------")
    for idx, n in enumerate(top_level_names):
        if idx != 0:
            print("---")
        cur_prefix = f"{prefix}{n}"
        next_max_depth = max_depth - 1 if max_depth is not None else None
        hierarchical_state_dict(
            state_dict, cur_prefix, keys=keys, max_depth=next_max_depth, short=short
        )


def remap_state_dict(
    state_dict: Dict[str, torch.Tensor],
    param_prefix_remapping: Optional[Dict[str, str]] = None,
    param_prefixes_to_drop: Optional[Iterable[str]] = None,
) -> dict[str, torch.Tensor]:
    param_prefix_remapping = param_prefix_remapping or {}
    param_prefixes_to_drop = param_prefixes_to_drop or []
    filtered_state_dict = {
        name: tensor
        for name, tensor in state_dict.items()
        if not any(name.startswith(prefix) for prefix in param_prefixes_to_drop)
    }
    updated_state_dict = {}
    for name, tensor in filtered_state_dict.items():
        for old_prefix, new_prefix in param_prefix_remapping.items():
            if name.startswith(old_prefix):
                new_name = name.replace(old_prefix, new_prefix)
                updated_state_dict[new_name] = tensor
                break
        else:
            updated_state_dict[name] = tensor
    return updated_state_dict
