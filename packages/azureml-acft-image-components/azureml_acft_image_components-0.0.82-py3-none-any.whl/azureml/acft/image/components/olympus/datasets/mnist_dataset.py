# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import os

import numpy as np
import torch
from torch.utils.data import Dataset

amlt_data_dir = os.getenv("AMLT_DATA_DIR", "/mnt/default/data")

path_to_check = "/mnt/external/data"

if os.path.exists(path_to_check):
    DATA_DIR = path_to_check
else:
    DATA_DIR = amlt_data_dir


class MNISTDataset(Dataset):
    def __init__(self, data_path, labels_path):

        # AMLT_DATA_DIR is where the data is stored, if not found use default parent_dir
        data_path = os.path.join(DATA_DIR, data_path)
        with open(data_path, "rb") as f:
            magic, size, rows, cols = np.fromfile(f, dtype=np.dtype(">i4"), count=4)
            self.images = (
                np.fromfile(f, dtype=np.ubyte)
                .reshape(size, rows, cols)
                .astype(np.float32)
                / 255.0
            )  # Normalize images

        labels_path = os.path.join(DATA_DIR, labels_path)
        with open(labels_path, "rb") as f:
            magic, size = np.fromfile(f, dtype=np.dtype(">i4"), count=2)
            self.labels = np.fromfile(f, dtype=np.ubyte)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        img = self.images[idx]
        label = self.labels[idx]
        img = torch.from_numpy(img).unsqueeze(0)
        return {"image": img, "labels": label}
