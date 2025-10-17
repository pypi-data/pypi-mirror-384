# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
from typing import Any, Dict

from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)

ORDER_KEY = "_order"


class ComponentRegistry:

    registered_components: Dict[str, Any] = {}

    @classmethod
    def from_config(cls, config: DictConfig):
        """Instantiate and register components from a config, with optional ordering
        (specified in the _order key of config)"""
        if not isinstance(config, DictConfig):
            raise ValueError(f"Invalid config {type(config)}, expected DictConfig")

        # set up ordering

        ordered_names = config.get(ORDER_KEY, [])
        for name in config.keys():
            if name == ORDER_KEY:
                continue
            if name not in ordered_names:
                ordered_names.append(name)

        for name in ordered_names:
            resource = config.get(name)
            if resource is None:
                logger.warning(f"Expected resource '{name}' is None, skipping")
                continue
            if "_target_" not in resource:
                raise ValueError(f"Resource config {name} missing _target_ key")
            logger.info(f"Instantiating resource {name}")
            cls.register(str(name), instantiate(resource, _convert_="object"))

    @classmethod
    def register(cls, name: str, component: Any):
        if name in cls.registered_components:
            raise ValueError(
                f"Component with name {name} already registered: {component}"
            )
        cls.registered_components[name] = component

    @classmethod
    def get(cls, name: str) -> Any:
        return cls.registered_components[name]

    @classmethod
    def reset(cls) -> None:
        cls.registered_components = {}


def resolve_attr(ob: Any, attr: str) -> Any:
    attr_chain = attr.split(".")
    for idx, a in enumerate(attr_chain):
        try:
            ob = getattr(ob, a)
        except AttributeError:
            cur_attr = ".".join(attr_chain[: idx + 1])
            raise AttributeError(f"Failed to resolve attribute {cur_attr}")
    return ob


def resolve_registry(resource_ref: str) -> DictConfig:
    resource_components = resource_ref.split(".")
    resource_name = resource_components[0]
    attrs = resource_components[1:]

    registry_reference = {
        "_target_": "azureml.acft.image.components.olympus.app.component_registry.ComponentRegistry.get",
        "name": resource_name,
    }
    if attrs:
        attr = ".".join(resource_components[1:])
        registry_reference = {
            "_target_": "azureml.acft.image.components.olympus.app.component_registry.resolve_attr",
            "ob": registry_reference,
            "attr": attr,
        }
    return OmegaConf.create(registry_reference)


# OmegaConf interpolation to access the registry via ${registry:resource_name}
OmegaConf.register_new_resolver("oly.registry", resolve_registry)
