# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import random

import numpy as np
import torch
from omegaconf import DictConfig
from torch.utils.data import Dataset

DEFAULT_SEED = 42  # Default seed value


class RandomImageDataset(Dataset):
    def __init__(self, num_samples=1000, seed=DEFAULT_SEED):
        self.num_samples = num_samples
        self.input_dim = 28 * 28
        self.seed = seed

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        if self.seed is not None:
            torch.manual_seed(self.seed + idx)
        image = torch.randn(self.input_dim)
        return image


class RandomTextDataset(Dataset):
    def __init__(self, num_samples=1000, seq_len=50, vocab_size=100, seed=DEFAULT_SEED):
        self.num_samples = num_samples
        self.seq_len = seq_len
        self.vocab_size = vocab_size
        self.seed = seed

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        if self.seed is not None:
            torch.manual_seed(self.seed + idx)
        sequence = torch.randint(0, self.vocab_size, (self.seq_len,))
        return sequence


class RandomLabelDataset(Dataset):
    def __init__(self, num_samples=1000, num_classes=10, seed=DEFAULT_SEED):
        self.num_samples = num_samples
        self.num_classes = num_classes
        self.seed = seed

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        if self.seed is not None:
            torch.manual_seed(self.seed + idx)
        label = torch.randint(0, self.num_classes, ())
        return label


class RandomMultimodalDataset(Dataset):
    def __init__(self, datasets: DictConfig, seed=DEFAULT_SEED):
        self.datasets = {name: dataset for name, dataset in datasets.items()}
        self.dataset_length = len(next(iter(self.datasets.values())))
        self.seed = seed

    def __len__(self):
        return self.dataset_length

    def __getitem__(self, idx) -> dict:
        if self.seed is not None:
            torch.manual_seed(self.seed + idx)
            random.seed(self.seed + idx)
            np.random.seed(self.seed + idx)
        return {name: dataset[idx] for name, dataset in self.datasets.items()}
