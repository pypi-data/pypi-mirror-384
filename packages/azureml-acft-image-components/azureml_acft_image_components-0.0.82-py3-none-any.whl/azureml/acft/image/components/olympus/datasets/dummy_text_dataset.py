# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from torch.utils.data import Dataset, DataLoader
import torch
from transformers import AutoTokenizer
from typing import Optional

class DummyTextDataset(Dataset):
    def __init__(
        self,
        model_name_or_path: str,  # Consistent with model init
        num_samples: int = 1000,
        max_length: int = 20,
        padding: str = "max_length",
        truncation: bool = True,
        **kwargs,  # Additional tokenizer args
    ):
        """
        Dummy dataset for text-based models.

        Args:
            model_name_or_path (str): Name or path of the pretrained tokenizer.
            num_samples (int): Number of dummy samples.
            max_length (int): Maximum sequence length.
            padding (str): Padding strategy (e.g., "max_length", "longest").
            truncation (bool): Whether to truncate longer sequences.
            **kwargs: Additional tokenizer arguments.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.num_samples = num_samples
        self.max_length = max_length
        self.padding = padding
        self.truncation = truncation

        # Create raw dummy text data
        self.texts = [f"This is a test sample {i}" for i in range(num_samples)]

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        """
        Tokenizes text dynamically at retrieval time.
        """
        text = self.texts[idx]
        tokenized = self.tokenizer(
            text,
            padding=self.padding,
            truncation=self.truncation,
            max_length=self.max_length,
            return_tensors="pt",
        )

        return {
            "input_ids": tokenized["input_ids"].squeeze(0),
            "attention_mask": tokenized["attention_mask"].squeeze(0),
            "labels": tokenized["input_ids"].squeeze(0),  # Using input_ids as labels for simplicity
        }