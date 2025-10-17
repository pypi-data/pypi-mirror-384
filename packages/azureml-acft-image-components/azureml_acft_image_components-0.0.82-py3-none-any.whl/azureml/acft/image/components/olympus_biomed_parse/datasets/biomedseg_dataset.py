# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import json
import os
import random

import cv2
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

# Determine the data directory dynamically
# amlt_data_dir = os.getenv("AMLT_DATA_DIR", "/mnt/default/data")
# path_to_check = "/mnt/external/data"
# DATA_DIR = path_to_check if os.path.exists(path_to_check) else amlt_data_dir


class BiomedSegDataset(Dataset):
    def __init__(
        self,
        root_dir,
        split="train",
        transforms=None,
        img_size=(1024, 1024),
        interpolate_mask_size=(512, 512),
        name=None,
    ):
        self.root_dir = root_dir
        self.split = split
        self.transforms = transforms
        self.img_size = img_size
        self.interpolate_mask_size = interpolate_mask_size
        self.json_file = os.path.join(root_dir, f"{split}.json")
        self.name = name if name else os.path.basename(os.path.normpath(root_dir))

        with open(self.json_file, "r") as file:
            data = json.load(file)
            self.data_info = data.get("annotations", [])
            self.images_info = {img["id"]: img for img in data.get("images", [])}

        self.images_dir = os.path.join(root_dir, split)
        self.masks_dir = os.path.join(root_dir, f"{split}_mask")

    def __len__(self):
        return len(self.data_info)

    def __getitem__(self, idx):
        ann_info = self.data_info[idx]
        img_info = self.images_info.get(ann_info.get("image_id"))

        if img_info and "file_name" in img_info:
            try:
                img_path = os.path.join(self.images_dir, img_info["file_name"])
                image = Image.open(img_path).convert("RGB")
            except (IOError, FileNotFoundError):
                image = Image.new("RGB", self.img_size, (0, 0, 0))
        else:
            image = Image.new("RGB", self.img_size, (0, 0, 0))

        mask_path = os.path.join(self.masks_dir, ann_info.get("mask_file", ""))
        try:
            mask_orig = Image.open(mask_path).convert("L")
        except (IOError, FileNotFoundError):
            mask_orig = Image.new("L", self.img_size, 0)

        selected_sentence = random.choice(
            ann_info.get("sentences", [{"sent": "None"}])
        )["sent"]

        if self.transforms:
            image, mask_orig = self.transforms(np.array(image), np.array(mask_orig))

        image = np.transpose(image, (2, 0, 1))
        mask_orig = np.array(mask_orig)

        if (
            mask_orig.shape[0] != self.interpolate_mask_size[0]
            or mask_orig.shape[1] != self.interpolate_mask_size[1]
        ):
            # To match the shape of low_res_masks
            mask = cv2.resize(
                mask_orig,
                (self.interpolate_mask_size[0], self.interpolate_mask_size[1]),
                interpolation=cv2.INTER_NEAREST,
            ).astype(np.uint8)
        else:
            mask = mask_orig.astype(np.uint8)

        label_id = 0
        # Create a binary mask where the selected label is 1, others are 0
        mask = np.uint8(mask != label_id)

        return {
            "image": torch.tensor(image.copy(), dtype=torch.float32),
            "labels": torch.tensor(mask.copy(), dtype=torch.long)[None, :, :],
            "text": selected_sentence,
        }



class DataAugmentation:
    def __init__(
        self,
        prob=0.5,
        rotate=True,
        flip=False,
        pixel_shift=False,
        pixel_shift_ratio=0.1,
        crop=True,
        crop_ratio=0.1,
    ):
        self.prob = prob
        self.rotate = rotate
        self.flip = flip
        self.pixel_shift = pixel_shift
        self.pixel_shift_ratio = pixel_shift_ratio
        self.crop = crop
        self.crop_ratio = crop_ratio

    def __call__(self, img, mask):
        if random.random() < self.prob:
            # Rotate the image
            if self.rotate:
                rotate_times = random.randint(0, 3)
                img = np.rot90(img, rotate_times, (0, 1))
                mask = np.rot90(mask, rotate_times)
            # Flip the image
            if self.flip:
                flip = random.choice([0, 1, -1])
                img = cv2.flip(img, flip)
                mask = cv2.flip(mask, flip)

            # Crop the image
            if self.crop and random.random() < self.prob:
                h, w = img.shape[:2]
                c = np.array([h, w]) / 2
                # pad the image with zeros
                pad = int(2 * h * self.crop_ratio + 1)
                img = np.pad(img, ((pad, pad), (pad, pad), (0, 0)), mode="constant")
                mask = np.pad(mask, ((pad, pad), (pad, pad)), mode="constant")

                # crop the image
                scale = 1 + np.random.uniform(-self.crop_ratio, self.crop_ratio)
                new_h, new_w = np.array([h, w]) * scale
                new_c = c + np.random.uniform(
                    -self.crop_ratio, self.crop_ratio, size=2
                ) * np.array([h, w])
                x1, x2 = new_c[0] - new_h / 2, new_c[0] + new_h / 2
                y1, y2 = new_c[1] - new_w / 2, new_c[1] + new_w / 2
                x1 = pad + int(x1)
                x2 = pad + int(x2)
                y1 = pad + int(y1)
                y2 = pad + int(y2)
                img = img[x1:x2, y1:y2, :]
                mask = mask[x1:x2, y1:y2]

                # resize the image
                img = cv2.resize(img, (h, w), interpolation=cv2.INTER_LINEAR)
                mask = cv2.resize(mask, (h, w), interpolation=cv2.INTER_NEAREST)

            # Shift pixel values
            if self.pixel_shift:
                pixel_max = np.max(img)
                pixel_min = np.min(img)
                scale = pixel_max - pixel_min
                shift = np.random.uniform(-scale, scale) * self.pixel_shift_ratio
                img = img + shift

        return img, mask
