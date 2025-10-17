# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from torch.utils.data import Dataset


class EmptyDataset(Dataset):
    def __init__(self):
        self.length = 0

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        return {}
