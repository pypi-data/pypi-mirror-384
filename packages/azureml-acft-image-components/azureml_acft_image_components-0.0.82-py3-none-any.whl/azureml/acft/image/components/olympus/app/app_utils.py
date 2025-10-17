# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
import os
from typing import List

from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from lightning.pytorch.loggers import CSVLogger, Logger, MLFlowLogger
from ..callbacks import DatasetNameLoggerCallback, TensorLogging

from .mlflow_utils import create_local_run, get_aml_mlflow_tracking_uri

logger = logging.getLogger(__name__)

DEFAULT_EXTERNAL_DIR = "/mnt/external"
DEFAULT_OUTPUT_DIR = "/mnt/output"


def get_loggers(experiment_output_dir: str) -> List[Logger]:
    logs_dir_path = os.path.join(experiment_output_dir, "logs")
    csv_logger = CSVLogger(save_dir=logs_dir_path, name="csv_logs")
    loggers: List[Logger] = [csv_logger]

    mlflow_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", None)
    mlflow_run_id = os.environ.get("MLFLOW_RUN_ID", None)

    if not mlflow_tracking_uri:
        # try creating a new mlflow job for logging
        mlflow_tracking_uri = get_aml_mlflow_tracking_uri()
        if mlflow_tracking_uri is None:
            logger.warning(
                "MLFlow tracking URI is not set, MLFlow logging will be disabled."
            )
        else:
            mlflow_run_id = create_local_run(mlflow_tracking_uri=mlflow_tracking_uri)

    if mlflow_tracking_uri:
        # experiment_name = os.environ.get("AMLT_EXPERIMENT_NAME", "local_experiment")
        # job_name = os.environ.get("AMLT_JOB_NAME", "local_experiment")
        mlf_logger = MLFlowLogger(
            # setting experiment_name and run_name doesn't work, the AML job has already
            # been created by amulet during job submission and we can't change it here.
            # experiment_name=experiment_name,
            # run_name=job_name,
            tracking_uri=mlflow_tracking_uri,
        )
        if mlflow_run_id:
            mlf_logger._run_id = mlflow_run_id
        loggers.append(mlf_logger)

    return loggers


def get_default_callbacks(
    experiment_output_dir: str,
    use_early_stopping: bool = False,
    enable_checkpointing: bool = True,
):
    callbacks = [
        TensorLogging(),
        DatasetNameLoggerCallback(),
    ]

    checkpoint_dir_path = os.path.join(experiment_output_dir, "checkpoints")

    os.makedirs(checkpoint_dir_path, exist_ok=True)

    if enable_checkpointing:
        callbacks.append(
            ModelCheckpoint(
                dirpath=checkpoint_dir_path, every_n_epochs=5, save_last=True
            )
        )

    if use_early_stopping:
        callbacks.append(
            EarlyStopping(monitor="validate_loss", patience=3, verbose=True, mode="min")
        )

    return callbacks


def print_environment_variables():
    for key, value in os.environ.items():
        print(f"{key}: {value}")


def merge_callbacks(default_callbacks, user_callbacks):
    return default_callbacks + user_callbacks
