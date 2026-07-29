"""Line-image dataset for HATFormer, reading the manifest + split directly.

The image pipeline mirrors the original HATFormer preprocessing exactly:
resize to a fixed height, flip horizontally (Arabic is RTL), then paste into a
square `canvas`x`canvas` image, stacking lines wider than the canvas as rows.
Because the canvas is already exactly `canvas` px, the ViT/TrOCR image
normalization (rescale 1/255, then mean/std 0.5) is applied directly here — this
is identical to TrOCRProcessor("microsoft/trocr-base-stage1") output and needs
no network download or local ./trocr folder.
"""
import os

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

# trocr-base-stage1 / ViT image processor constants
_IMG_MEAN = 0.5
_IMG_STD = 0.5


def hatformer_canvas(img, height=64, canvas=384, rtl_flip=True):
    """Replicate HATFormer line preprocessing -> a single `canvas`x`canvas` RGB image."""
    img = img.convert("RGB")
    w, h = img.size
    new_w = max(1, int(height * (w / h)))
    resized = img.resize((new_w, height))
    if rtl_flip:
        resized = resized.transpose(Image.FLIP_LEFT_RIGHT)

    out = Image.new("RGB", (canvas, canvas), (0, 0, 0))
    if resized.width <= canvas:
        out.paste(resized, (0, 0))
    else:
        n = (resized.width + canvas - 1) // canvas
        for i in range(n):
            left = i * canvas
            seg = resized.crop((left, 0, min(left + canvas, resized.width), height))
            out.paste(seg, (0, i * height))  # rows beyond canvas//height are clipped (as in the original)
    return out


def to_pixel_values(pil_img):
    """HWC uint8 RGB -> CHW float32 tensor, normalized like the ViT image processor."""
    arr = np.asarray(pil_img, dtype=np.float32) / 255.0
    arr = (arr - _IMG_MEAN) / _IMG_STD
    arr = np.transpose(arr, (2, 0, 1))
    return torch.from_numpy(np.ascontiguousarray(arr))


def load_manifest_split(metadata_csv, split, exclude_books=None):
    """Filter metadata.csv by split, dropping empty transcriptions."""
    df = pd.read_csv(metadata_csv)
    df = df[df["split"] == split]
    if exclude_books:
        df = df[~df["book_id"].isin(exclude_books)]
    df = df.dropna(subset=["img_path", "gt_text"])
    df = df[df["gt_text"].astype(str).str.strip().astype(bool)]
    return df.reset_index(drop=True)


class HatformerLineDataset(Dataset):
    def __init__(self, df, tokenizer, max_text_length, image_cfg, root="."):
        self.df = df.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_text_length = max_text_length
        self.image_cfg = dict(image_cfg)
        self.root = root

    def __len__(self):
        return len(self.df)

    def _resolve(self, p):
        if os.path.isabs(p):
            return p
        return os.path.normpath(os.path.join(self.root, p))

    def __getitem__(self, i):
        row = self.df.iloc[i]
        with Image.open(self._resolve(row["img_path"])) as im:
            canvas = hatformer_canvas(im, **self.image_cfg)
        pixel_values = to_pixel_values(canvas)

        ids = self.tokenizer(
            str(row["gt_text"]),
            padding="max_length",
            max_length=self.max_text_length,
            truncation=True,
        ).input_ids
        labels = [t if t != self.tokenizer.pad_token_id else -100 for t in ids]

        return {
            "pixel_values": pixel_values,
            "labels": torch.tensor(labels, dtype=torch.long),
        }
