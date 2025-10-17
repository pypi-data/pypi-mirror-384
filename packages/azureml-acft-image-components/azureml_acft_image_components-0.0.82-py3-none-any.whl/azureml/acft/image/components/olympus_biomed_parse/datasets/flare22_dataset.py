# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
# %% setup environment
import glob
import os
import random

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import CLIPTokenizer

amlt_data_dir = os.getenv("AMLT_DATA_DIR", "/mnt/default/data")

path_to_check = "/mnt/external/data"

if os.path.exists(path_to_check):
    DATA_DIR = path_to_check
else:
    DATA_DIR = amlt_data_dir


class FLARE22Dataset(Dataset):
    def __init__(
        self,
        data_root=os.path.join(DATA_DIR, "MedSam/npy/CT_Abd"),
        data_aug=True,
        image_size=1024,
    ):
        self.data_root = data_root
        self.gt_path = os.path.join(self.data_root, "gts")
        self.img_path = os.path.join(self.data_root, "imgs")
        self.gt_path_files = sorted(
            glob.glob(os.path.join(self.gt_path, "**/*.npy"), recursive=True)
        )
        self.gt_path_files = [
            file
            for file in self.gt_path_files
            if os.path.isfile(os.path.join(self.img_path, os.path.basename(file)))
        ]
        self.image_size = image_size
        self.data_aug = data_aug
        self.tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch16")
        self.label_dict = {
            1: ["Liver", "liver"],
            2: ["Right Kidney", "right kidney", "kidney"],
            3: ["Spleen", "spleen"],
            4: ["Pancreas", "pancreas"],
            5: ["Aorta", "aorta"],
            6: [
                "Inferior Vena Cava",
                "IVC",
                "inferior vena cava",
                "ivc",
                "vena cava",
                "vena",
                "cava",
            ],
            7: [
                "Right Adrenal Gland",
                "RAG",
                "right adrenal gland",
                "rag",
                "adrenal gland",
                "adrenal",
            ],
            8: [
                "Left Adrenal Gland",
                "LAG",
                "left adrenal gland",
                "lag",
                "adrenal gland",
                "adrenal",
            ],
            9: ["Gallbladder", "gallbladder"],
            10: ["Esophagus", "esophagus"],
            11: ["Stomach", "stomach"],
            12: ["Duodenum", "duodenum"],
            13: ["Left Kidney", "left kidney", "kidney"],
        }

    def __len__(self):
        return len(self.gt_path_files)

    def __getitem__(self, index):
        # load npy image (1024, 1024, 3), [0,1]
        img_name = os.path.basename(self.gt_path_files[index])
        img_1024 = np.load(
            os.path.join(self.img_path, img_name), "r", allow_pickle=True
        )  # (H, W, 3)
        # convert the shape to (3, H, W)
        img_1024 = np.transpose(img_1024, (2, 0, 1))
        assert (
            np.max(img_1024) <= 1.0 and np.min(img_1024) >= 0.0
        ), "image should be normalized to [0, 1]"
        gt = np.load(
            self.gt_path_files[index], "r", allow_pickle=True
        )  # multiple labels [0, 1,4,5...], (256,256)
        assert img_name == os.path.basename(self.gt_path_files[index]), (
            "img gt name error" + self.gt_path_files[index] + self.npy_files[index]
        )

        if gt.shape[0] != 256 or gt.shape[1] != 256:
            # To match the shape of low_res_masks
            gt_resize = cv2.resize(
                gt, (256, 256), interpolation=cv2.INTER_NEAREST
            ).astype(np.uint8)
        else:
            gt_resize = gt.astype(np.uint8)
        label_ids = np.unique(gt_resize)[1:]
        label_id = random.choice(label_ids.tolist())
        try:
            gt2D = np.uint8(gt_resize == label_id)  # only one label, (256, 256)
        except Exception:
            label_id = np.max(gt)
            gt2D = np.uint8(gt_resize == label_id)  # only one label, (256, 256)
        # add data augmentation: random fliplr and random flipud
        if self.data_aug:
            if random.random() > 0.5:
                img_1024 = np.ascontiguousarray(np.flip(img_1024, axis=-1))
                gt2D = np.ascontiguousarray(np.flip(gt2D, axis=-1))
            if random.random() > 0.5:
                img_1024 = np.ascontiguousarray(np.flip(img_1024, axis=-2))
                gt2D = np.ascontiguousarray(np.flip(gt2D, axis=-2))
        gt2D = np.uint8(gt2D > 0)

        # Randomly select a synonym of the label
        caption = random.choice(self.label_dict[label_id])
        text_token = self.tokenize_text(caption)
        return {
            "image": torch.tensor(img_1024).float(),
            "labels": torch.tensor(gt2D[None, :, :]).long(),
            "text": [caption],
            "tokens": text_token,
        }

    def tokenize_text(self, text):
        """
        Tokenize text using CLIP tokenizer
        """
        return self.tokenizer(
            text,
            max_length=self.tokenizer.model_max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        ).input_ids.squeeze(0)
