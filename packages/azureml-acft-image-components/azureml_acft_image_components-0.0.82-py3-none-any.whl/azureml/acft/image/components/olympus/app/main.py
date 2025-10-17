# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Mapping, Optional

import hydra
import lightning as L
from dotenv import find_dotenv, load_dotenv
from omegaconf import DictConfig, OmegaConf

from ..core import OlympusLightningModule
from ..evaluators import BaseOlympusEvaluator
from ..loaders import OlympusRecoverTrainingCheckpointLoader
from ..utils.hydra_utils import get_by_path, print_cfg
from .app_utils import get_default_callbacks, get_loggers, print_environment_variables
from .component_registry import ComponentRegistry
from .olympus_config import OlympusConfig, OlympusMode, _OlympusCheckpoint

os.environ["HYDRA_FULL_ERROR"] = "1"
# os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
logger = logging.getLogger(__name__)


def _qualified_classname(class_type: type) -> str:
    return class_type.__module__ + "." + class_type.__name__


@dataclass
class OlympusExperiment:
    trainer: L.Trainer
    model: OlympusLightningModule
    data: L.LightningDataModule
    evaluator: Optional[BaseOlympusEvaluator]
    mode: OlympusMode
    olympus_checkpoint: _OlympusCheckpoint
    experiment_output_dir: str


def _flat_config(cfg: Mapping) -> Dict[str, str]:
    flat = {}
    for key, value in cfg.items():
        if isinstance(value, Mapping):
            flat.update({f"{key}.{k}": v for k, v in _flat_config(value).items()})
        else:
            flat[key] = value
    return flat


def _save_resolved_config(
    experiment: OlympusExperiment,
    resolved_config: dict,
    out_file: str = "resolved_config.json",
):
    out_fname = os.path.join(experiment.experiment_output_dir, out_file)
    logger.info(f"Saving resolved config to {out_fname}")
    try:
        with open(out_fname, "w") as f:
            json.dump(resolved_config, f, indent=2)
    except Exception:
        logger.exception(f"Failed to save resolved config to {out_fname}")


def save_parameters(raw_config: DictConfig, experiment: OlympusExperiment) -> None:
    if experiment.trainer.global_rank != 0:
        return
    try:
        resolved_config: dict = OmegaConf.to_container(
            raw_config, resolve=True
        )  # type:ignore
        # remove 'scratch' entries from resolved config
        resolved_config.pop("scratch", None)
        _save_resolved_config(experiment, resolved_config)
        flat_config = _flat_config(resolved_config)  # type:ignore
        _save_resolved_config(experiment, flat_config, out_file="flat_config.json")
        if len(flat_config) > 200:
            # AML only allows 200 hyperparameters per run :(
            logger.warning(
                f"Too many hyperparameters to save: {len(flat_config)}, "
                "saving only the first 200"
            )
            flat_config = dict(list(flat_config.items())[:200])
        experiment.model.save_hyperparameters(flat_config)
    except Exception:
        logger.exception("Failed to save hyperparameters")


def parse_config(cfg: DictConfig) -> OlympusExperiment:
    if "config" in cfg:
        cfg = cfg.config
    # save all parameters as hyperparameters
    raw_config = cfg.copy()
    # 'shallow' instantiation -- fields are still DictConfigs
    config: OlympusConfig = hydra.utils.instantiate(
        cfg, _target_="azureml.acft.image.components.olympus.app.main.OlympusConfig", _recursive_=False
    )

    logger.info(f"project name: {config.project_name}")
    logger.info(f"experiment name: {config.experiment_name}")
    logger.info(f"job name: {config.job_name}")
    logger.info(f"experiment output directory: {config.experiment_output_dir}")
    # finish parsing config
    experiment = _parse_config(config)

    save_parameters(raw_config, experiment)

    return experiment


def _hydra_instantiate(cfg: DictConfig, **kwargs):
    return hydra.utils.instantiate(cfg, **kwargs, _recursive_=True, _convert_="object")


def _parse_config(config: OlympusConfig) -> OlympusExperiment:
    # This function takes a partially-constructed OlympusConfig, where parameters are
    # just DictConfig objects that need to be instantiated. It constructs the
    # sub-objects, some of which cannot be directly constructed.

    # load any resources prior to instantiating the experiment
    if config.registry is not None:
        ComponentRegistry.from_config(config.registry)  # type:ignore

    if config.experiment_output_dir is None:
        if not config.external_mount:
            raise ValueError(
                "Either experiment_output_dir or external_mount must be set"
            )
        if not config.experiment_name:
            # try to get from environment
            config.experiment_name = os.environ["AMLT_EXPERIMENT_NAME"]
        if not config.experiment_name:
            raise ValueError(
                "if experiment_output_dir not set, experiment_name must be set"
            )
        config.experiment_output_dir = os.path.join(
            config.external_mount, config.experiment_name
        )

    trainer_loggers = get_loggers(config.experiment_output_dir)
    enable_checkpointing = config.trainer.get(  # type:ignore
        "enable_checkpointing", True
    )
    callbacks = []
    if not config.disable_default_callbacks:
        default_callbacks = get_default_callbacks(
            config.experiment_output_dir, enable_checkpointing=enable_checkpointing
        )
        callbacks.extend(
            default_callbacks
        )  # this should be an extend not an append since default_callbacks returns a list
    if config.callbacks:
        config.callbacks = _hydra_instantiate(config.callbacks)  # type:ignore
    callbacks.extend(config.callbacks.values())

    trainer_kwargs = {"logger": trainer_loggers, "callbacks": callbacks}
    trainer = _hydra_instantiate(config.trainer, **trainer_kwargs)  # type:ignore
    print(f"[Main] Trainer strategy: {trainer.strategy}")

    if "_target_" not in config.olympus_checkpoint:  # type:ignore
        config.olympus_checkpoint["_target_"] = _qualified_classname(  # type:ignore
            _OlympusCheckpoint
        )
    olympus_checkpoint = _hydra_instantiate(config.olympus_checkpoint)  # type:ignore

    datamodule = _hydra_instantiate(config.datamodule)  # type:ignore

    model = config.model  # type:ignore
    evaluator = _hydra_instantiate(config.evaluator)  # type:ignore
    loss_function = _hydra_instantiate(config.loss)  # type:ignore
    optimizer_factory = _hydra_instantiate(config.optimizer)  # type:ignore
    lr_scheduler_factory = None
    if config.lr_scheduler:
        lr_scheduler_factory = _hydra_instantiate(config.lr_scheduler)  # type:ignore

    lightning_module = OlympusLightningModule(
        model_config=model,
        evaluator=evaluator,
        loss_function=loss_function,
        optimizer_factory=optimizer_factory,
        lr_scheduler_factory=lr_scheduler_factory,
    )

    mode = OlympusMode(config.mode)

    return OlympusExperiment(
        trainer=trainer,
        model=lightning_module,
        data=datamodule,
        evaluator=evaluator,
        olympus_checkpoint=olympus_checkpoint,
        mode=mode,
        experiment_output_dir=config.experiment_output_dir,
    )


@hydra.main(config_path="conf", config_name="main", version_base="1.3")
def main(cfg: DictConfig) -> None:

    dotenv_file = find_dotenv()
    if dotenv_file:
        logger.info(f"Loading environment variables from {dotenv_file}")
    else:
        logger.info("No .env file found")
    load_dotenv(dotenv_path=dotenv_file)

    if "print" in cfg:
        # standard values meaning 'just print the config'
        if cfg.print not in ["", None, "true", "True", "1", 1, True]:
            # try to get sub-path in config based on value of print
            # e.g. +print=foo.bar will print cfg.foo.bar
            try:
                sub_cfg = get_by_path(cfg, cfg.print)
            except Exception as e:
                print(
                    f"Failed to get config path {cfg.print}, was this meant to be a"
                    " key? If not use '+print=true'"
                )
                raise e
            cfg = sub_cfg
        print_cfg(cfg)
        return

    print("=== Environment ===")
    print_environment_variables()
    print("=== End Environment ===")

    config = parse_config(cfg)

    olympus_checkpoint_path = None
    if config.olympus_checkpoint.load_checkpoint and config.olympus_checkpoint.loader:
        if isinstance(
            config.olympus_checkpoint.loader, OlympusRecoverTrainingCheckpointLoader
        ):
            # load with the Trainer checkpoint loading mechanism
            olympus_checkpoint_path = config.olympus_checkpoint.loader.checkpoint_path
        else:
            config.model.configure_model()
            config.olympus_checkpoint.loader.load(
                model=config.model, trainer=config.trainer
            )

    if config.mode == OlympusMode.predict:
        config.trainer.predict(
            model=config.model,
            datamodule=config.data,
            ckpt_path=olympus_checkpoint_path,
        )
    elif config.mode == OlympusMode.test:
        config.trainer.test(
            model=config.model,
            datamodule=config.data,
            ckpt_path=olympus_checkpoint_path,
        )
    elif config.mode == OlympusMode.train:
        config.trainer.fit(
            model=config.model,
            datamodule=config.data,
            ckpt_path=olympus_checkpoint_path,
        )
        if cfg.get("datamodule", {}).get("datasets", {}).get("test"):
            config.trainer.test(model=config.model, datamodule=config.data)
    else:
        raise ValueError(f"Unsupported mode {config.mode}")


if __name__ == "__main__":
    main()
