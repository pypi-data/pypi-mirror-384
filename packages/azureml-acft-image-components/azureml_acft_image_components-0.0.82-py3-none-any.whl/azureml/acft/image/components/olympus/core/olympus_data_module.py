# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from dataclasses import dataclass
from typing import Callable, List, Optional, Union

import lightning as L
from torch.utils.data import DataLoader, Dataset, random_split

from ..datasets import EmptyDataset

DatasetCreator = Callable[[], Dataset]
DataLoaderCreator = Callable[[Dataset], DataLoader]


@dataclass
class ModuleDatasets:
    train: Optional[DatasetCreator] = None
    validate: Optional[DatasetCreator] = None
    test: Optional[List[DatasetCreator]] = None
    predict: Optional[DatasetCreator] = None


@dataclass
class ModuleDataLoaders:
    train: Optional[DataLoaderCreator] = None
    validate: Optional[DataLoaderCreator] = None
    test: Optional[DataLoaderCreator] = None
    predict: Optional[DataLoaderCreator] = None


class OlympusDataModule(L.LightningDataModule):
    def __init__(
        self,
        datasets: ModuleDatasets,
        dataloaders: Optional[ModuleDataLoaders] = None,
        split_train_validate: bool = False,
        validate_split_ratio: float = 0.2,
    ) -> None:
        super().__init__()
        self.datasets = datasets
        if dataloaders is None:
            dataloaders = ModuleDataLoaders()
        self.dataloaders = dataloaders
        self.split_train_validate = split_train_validate
        self.validate_split_ratio = validate_split_ratio
        # Initialize dataset attributes to None
        self.train_dataset: Optional[Dataset] = None
        self.validate_dataset: Optional[Dataset] = None
        self.test_datasets: Optional[List[Dataset]] = None
        self.predict_dataset: Optional[Dataset] = None
        self.test_dataset_names: Optional[List[str]] = None

    def setup(self, stage: Optional[str] = None) -> None:
        # Setup for training dataset
        if stage in ("fit", None) and self.datasets.train:
            self.train_dataset = self.datasets.train()
            if self.split_train_validate and self.datasets.validate is None:
                total_len = len(self.train_dataset)
                validate_len = int(total_len * self.validate_split_ratio)
                train_len = total_len - validate_len
                self.train_dataset, self.validate_dataset = random_split(
                    self.train_dataset, [train_len, validate_len]
                )
        # Setup for validation dataset
        if stage in ("fit", "validate", None) and self.datasets.validate:
            self.validate_dataset = self.datasets.validate()
        # Setup for test datasets
        if stage in ("test", None) and self.datasets.test:
            self.test_datasets = []
            self.test_dataset_names = []
            for idx, test_creator in enumerate(self.datasets.test):
                test_dataset = test_creator()
                self.test_datasets.append(test_dataset)
                self.test_dataset_names.append(
                    getattr(test_dataset, "name", f"test_dataset_{idx}")
                )

        if stage in ("predict", None) and self.datasets.predict:
            self.predict_dataset = self.datasets.predict()

    def train_dataloader(self) -> Union[DataLoader, DataLoader[EmptyDataset]]:
        if self.train_dataset is not None:
            if not self.dataloaders.train:
                raise ValueError("'train' dataloader must be defined")
            dataloader = self.dataloaders.train(self.train_dataset)
        else:
            dataloader = DataLoader(dataset=EmptyDataset())
        return dataloader

    def val_dataloader(self) -> Union[DataLoader, DataLoader[EmptyDataset]]:
        if self.validate_dataset is not None:
            if not self.dataloaders.validate:
                raise ValueError("'validate' dataloader must be defined")
            dataloader = self.dataloaders.validate(self.validate_dataset)
        else:
            dataloader = DataLoader(dataset=EmptyDataset())
        return dataloader

    def test_dataloader(self) -> List[DataLoader]:
        if self.test_datasets is not None:
            if self.dataloaders.test is None:
                raise ValueError("'test' dataloader must be defined")
            dataloaders = [
                self.dataloaders.test(test_dataset)
                for test_dataset in self.test_datasets
            ]
        else:
            dataloaders = [DataLoader(dataset=EmptyDataset())]
        return dataloaders

    def predict_dataloader(self) -> Union[DataLoader, DataLoader[EmptyDataset]]:
        if self.predict_dataset is not None:
            if not self.dataloaders.predict:
                raise ValueError("'predict' dataloader must be defined")
            dataloader = self.dataloaders.predict(self.predict_dataset)
        else:
            dataloader = DataLoader(dataset=EmptyDataset())
        return dataloader
