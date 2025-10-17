# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import pytest
import torch
import torch.nn as nn
import os
from tempfile import TemporaryDirectory
from lightning import Trainer
from ...loaders import ModelCheckpointLoaderBase
from ...app.main import OlympusLightningModule


# Define dummy evaluator, optimizer factory, and LR scheduler factory
class BaseOlympusEvaluator:
    def evaluate(self, model, data_loader):
        pass


class OlympusOptimizerFactoryBase:
    def create_optimizer(self, parameters):
        return torch.optim.SGD(parameters, lr=0.01)


class OlympusLRSchedulerFactoryBase:
    def create_scheduler(self, optimizer):
        return torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)


class DummyLinearModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(10, 1)

    def forward(self, x):
        return self.linear(x)


# Define a dummy model
class DummyModel(OlympusLightningModule):
    def __init__(self):
        super().__init__(
            model_config=DummyLinearModel(),
            evaluator=BaseOlympusEvaluator(),
            loss_function=nn.MSELoss(),
            optimizer_factory=OlympusOptimizerFactoryBase(),
            lr_scheduler_factory=OlympusLRSchedulerFactoryBase(),
        )


@pytest.fixture
def temporary_checkpoint():
    with TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_model_checkpoint_loader(temporary_checkpoint):
    temp_dir = temporary_checkpoint

    # Create first instance of DummyModel
    model_1 = DummyModel()

    # Save its state_dict
    checkpoint_path = os.path.join(temp_dir, "checkpoint.pth")
    torch.save(model_1.state_dict(), checkpoint_path)

    # Create second instance of DummyModel
    model_2 = DummyModel()

    # Verify model_2's weights are not the same as model_1's initially
    for p1, p2 in zip(model_1.parameters(), model_2.parameters()):
        assert not torch.equal(p1, p2), "Model weights should be different initially."

    # Instantiate the ModelCheckpointLoaderBase and load weights
    checkpoint_loader = ModelCheckpointLoaderBase(
        strict=True, assign=False, checkpoint_path=checkpoint_path
    )
    trainer = (
        Trainer()
    )  # Mock a trainer if needed, or pass None if it's unused in your implementation
    checkpoint_loader.load(model_2, trainer)

    # Verify model_2's weights match model_1's after loading
    for p1, p2 in zip(model_1.parameters(), model_2.parameters()):
        assert torch.equal(p1, p2), "Model weights should match after loading."
