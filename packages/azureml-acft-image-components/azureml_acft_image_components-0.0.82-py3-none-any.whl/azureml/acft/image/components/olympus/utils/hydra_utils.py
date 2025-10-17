# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
from pathlib import Path
from typing import Union

import yaml
from omegaconf import DictConfig, ListConfig

logger = logging.getLogger(__name__)


def get_by_path(obj, path):
    if not path:
        return obj
    if isinstance(path, str):
        path = path.split(".")
    cur_key = path[0]
    remaining_path = path[1:]
    if not isinstance(obj, (dict, list, DictConfig, ListConfig)):
        logger.warning(f"Expected object to be dict or list, found {type(obj)}")
    if isinstance(obj, (list, ListConfig)):
        cur_key = int(cur_key)
    return get_by_path(obj[cur_key], remaining_path)  # type:ignore


def _validate_leaf(value):
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    return str(value)


def cfg_to_json_dict(cfg: Union[DictConfig, ListConfig]):
    """This prints 'interpolated' (${...}) values, which is useful for debugging."""
    if isinstance(cfg, ListConfig):
        result = []
        for value in cfg:
            if isinstance(value, (DictConfig, ListConfig)):
                result.append(cfg_to_json_dict(value))
            else:
                result.append(_validate_leaf(value))
    elif isinstance(cfg, DictConfig):
        result = {}
        for key, value in cfg.items():
            if isinstance(value, (DictConfig, ListConfig)):
                result[key] = cfg_to_json_dict(value)
            else:
                result[key] = _validate_leaf(value)
    else:
        logger.warning(f"Got non-Config value {type(cfg)} in print_cfg")


def read_config(run_dir: Union[str, Path]) -> DictConfig:
    """Load a saved config from a run"""
    run_dir = Path(run_dir)
    config_dir = run_dir / "hydra" / ".hydra"
    config_file = config_dir / "config.yaml"
    return DictConfig(yaml.safe_load(config_file.open()))


INDENT_SIZE = 2
INDENT = " " * INDENT_SIZE


def print_cfg(cfg: Union[DictConfig, ListConfig], indent: int = 0):
    """This prints 'interpolated' (${...}) values, which is useful for debugging."""
    if isinstance(cfg, ListConfig):
        for value in cfg:
            if isinstance(value, (DictConfig, ListConfig)):
                print(INDENT * indent + "-")
                print_cfg(value, indent + 1)
            else:
                print(INDENT * indent + "- " + str(value))
    elif isinstance(cfg, DictConfig):
        for key, value in cfg.items():
            if isinstance(value, (DictConfig, ListConfig)):
                print(INDENT * indent + str(key) + ": ")
                print_cfg(value, indent + 1)
            else:
                print(INDENT * indent + str(key) + ": " + str(value))
    else:
        logger.warning(f"Got non-Config value {type(cfg)} in print_cfg")
        print(INDENT * indent + str(cfg))
