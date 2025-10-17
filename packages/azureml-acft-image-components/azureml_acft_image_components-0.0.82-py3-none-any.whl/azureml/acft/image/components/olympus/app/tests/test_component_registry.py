# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from typing import Any
from hydra.utils import instantiate
from hydra.errors import InstantiationException
from omegaconf import OmegaConf, DictConfig
import pytest
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from ..component_registry import ComponentRegistry


@dataclass
class MyOb:
    param_a: Any
    param_b: Any


def test_component_registry():
    # Use a config to instantiate a component and register it
    param_val = 0.001
    registry_config = OmegaConf.create(
        {
            "ob_a": {
                "_target_": f"{MyOb.__module__}.{MyOb.__name__}",
                "param_a": param_val,
                "param_b": "hello",
            },
        }
    )

    ComponentRegistry.reset()
    ComponentRegistry.from_config(registry_config)

    assert ComponentRegistry.get("ob_a").__class__.__name__ == "MyOb"

    # Use custom resolver to access a registered component, as well as an attribute of a
    # registered component
    config = OmegaConf.create(
        {
            "my_ob": "${oly.registry:ob_a}",
            "my_ob_param": "${oly.registry:ob_a.param_a}",
        }
    )
    instantiated_config = instantiate(config, _convert_="object")
    assert instantiated_config["my_ob"].__class__.__name__ == "MyOb"
    assert instantiated_config["my_ob_param"] == param_val


def test_component_registry_ordering():
    # Test specifying the order of instantiation. In this case,
    # ob_a refers to ob_b, so ob_b must be instantiated first.
    registry_config = OmegaConf.create(
        {
            "ob_a": {
                "_target_": f"{MyOb.__module__}.{MyOb.__name__}",
                "param_a": "${oly.registry:ob_b}",
                "param_b": "foo",
            },
            "ob_b": {
                "_target_": f"{MyOb.__module__}.{MyOb.__name__}",
                "param_a": "bar",
                "param_b": "baz",
            },
        }
    )
    # without specifying order, we expect an InstantiationException
    ComponentRegistry.reset()
    with pytest.raises(InstantiationException):
        ComponentRegistry.from_config(registry_config)

    # add ordering and everything should work
    ComponentRegistry.reset()
    registry_config["_order"] = ["ob_b", "ob_a"]
    ComponentRegistry.from_config(registry_config)
    ob_a = ComponentRegistry.get("ob_a")
    assert ob_a.param_a.param_a == "bar"
