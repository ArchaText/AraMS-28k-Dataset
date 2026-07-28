"""Image path resolution and cropping helpers."""

import os
from pathlib import Path

import cv2
import numpy as np

from htr_builder.constants import BBOX_PAD, POLYGON_PAD


def resolve_image_path(page_image, images_root):
    """Try several path layouts to find the page image on disk."""
    candidates = [
        os.path.join(images_root, page_image),
        os.path.join(images_root, page_image.replace("images/", "", 1).lstrip("/")),
        os.path.join(images_root, Path(page_image).name),
        page_image,
    ]

    parts = Path(page_image).parts
    for i in range(1, len(parts)):
        candidates.append(os.path.join(images_root, *parts[i:]))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


def crop_bbox(img, bbox, pad=BBOX_PAD):
    """Crop an image using [x1, y1, x2, y2] coordinates."""
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = img.shape[:2]
    return img[max(0, y1 - pad):min(h, y2 + pad), max(0, x1 - pad):min(w, x2 + pad)]


def crop_polygon(img, polygon_pts, pad=POLYGON_PAD):
    """Crop an image around a polygon and paint the outside white."""
    pts = np.array(polygon_pts, dtype=np.int32)
    x, y, w, h = cv2.boundingRect(pts)
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(img.shape[1], x + w + pad)
    y2 = min(img.shape[0], y + h + pad)
    crop = img[y1:y2, x1:x2].copy()
    shifted = pts - np.array([x1, y1])
    mask = np.zeros(crop.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [shifted], 255)
    crop[mask == 0] = 255
    return crop
