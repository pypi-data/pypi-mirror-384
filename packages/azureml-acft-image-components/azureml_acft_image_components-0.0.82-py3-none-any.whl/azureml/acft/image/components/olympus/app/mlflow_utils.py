# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
import os
from dataclasses import dataclass
from typing import Optional

import mlflow
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


@dataclass
class AMLParameters:
    subscription_id: Optional[str]
    resource_group: Optional[str]
    workspace_name: Optional[str]


def _get_var(var: str, raise_error: bool) -> Optional[str]:
    val = os.environ.get(var, None)
    if val is None and raise_error:
        raise ValueError(f"Required environment variable {var} is not set.")
    return val


def get_aml_parameters_from_dot_env(raise_error: bool = True) -> AMLParameters:
    subscription_id = _get_var("AZURE_SUBSCRIPTION_ID", raise_error=raise_error)
    resource_group = _get_var("AML_WORKSPACE_RESOURCE_GROUP", raise_error=raise_error)
    workspace_name = _get_var("AML_WORKSPACE_NAME", raise_error=raise_error)
    return AMLParameters(
        subscription_id=subscription_id,
        resource_group=resource_group,
        workspace_name=workspace_name,
    )


def get_ml_client(raise_error: bool = False) -> MLClient:
    # client_id = _get_var("AZURE_CLIENT_ID", raise_error=raise_error)
    # os.environ["AZURE_CLIENT_ID"] = client_id
    credential = DefaultAzureCredential()

    # Enter details of your AzureML workspace
    aml_params = get_aml_parameters_from_dot_env(raise_error=raise_error)
    ml_client = MLClient(
        credential=credential,
        subscription_id=aml_params.subscription_id,
        resource_group_name=aml_params.resource_group,
        workspace_name=aml_params.workspace_name,
    )
    return ml_client


def get_aml_mlflow_tracking_uri(ml_client: Optional[MLClient] = None) -> Optional[str]:
    try:
        if ml_client is None:
            ml_client = get_ml_client(raise_error=True)
        aml_workspace = ml_client.workspaces.get(ml_client.workspace_name)
        if aml_workspace is None:
            raise ValueError(f"Could not get AML workspace {ml_client.workspace_name}.")
        mlflow_tracking_uri = aml_workspace.mlflow_tracking_uri
    except Exception:
        logger.exception("Error getting MLFlow tracking URI")
        mlflow_tracking_uri = None

    return mlflow_tracking_uri


def create_local_run(
    mlflow_tracking_uri: str,
    experiment_name="olympus_local_runs",
    run_name="local_run",
) -> int:
    # We create a run here so that lightning can attach to it
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    experiment = mlflow.set_experiment(experiment_name=experiment_name)
    active_run = mlflow.start_run(
        experiment_id=experiment.experiment_id, run_name=run_name
    )
    return active_run.info.run_id
