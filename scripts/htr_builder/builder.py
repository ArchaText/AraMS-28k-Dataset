"""Main build flow for generating the HTR dataset."""

import glob
import json
import os
from pathlib import Path

import cv2

from htr_builder.constants import IMAGES_DIRNAME
from htr_builder.image_utils import crop_bbox, crop_polygon, resolve_image_path
from htr_builder.split_utils import build_book_to_split, load_split_config
from htr_builder.text_utils import clean_gt
from htr_builder.writer import (
    compute_dataset_stats,
    print_summary,
    write_dataset_stats,
    write_manifests,
    write_metadata_csv,
    write_split_used,
)


def process_book(unified_path, images_root, images_out, split_map, exclude_margins=False):
    """Read a single `*_unified.json` file and build kraken-ready records."""
    book_id = Path(unified_path).stem.replace("_unified", "")

    with open(unified_path, encoding="utf-8") as handle:
        data = json.load(handle)

    records = []
    img_cache = {}
    stats = {
        "saved": 0,
        "deleted": 0,
        "empty_gt": 0,
        "no_geom": 0,
        "no_img": 0,
        "empty_crop": 0,
        "margin_skipped": 0,
    }

    for record in data:
        review = record.get("review", {})
        if review.get("deleted", False):
            stats["deleted"] += 1
            continue

        page_id = record["page_id"]
        line_idx = record["line_idx"]
        line_type = record.get("line_type", "main")

        if exclude_margins and line_type == "margin":
            stats["margin_skipped"] += 1
            continue

        gt_raw = record.get("text", {}).get("gt_raw", "")
        gt_text = clean_gt(gt_raw)
        if not gt_text:
            stats["empty_gt"] += 1
            continue

        geometry = record.get("geometry", {})
        bbox = geometry.get("bounding_box")
        polygon = geometry.get("boundary_polygon", [])

        if bbox and len(bbox) == 4:
            crop_source = "bbox"
        elif polygon:
            crop_source = "poly"
            bbox = None
        else:
            stats["no_geom"] += 1
            continue

        page_image = record.get("page_image", "")
        img_path = resolve_image_path(page_image, images_root)
        if not os.path.exists(img_path):
            stats["no_img"] += 1
            if stats["no_img"] <= 3:
                print(f"    [WARN] Image not found: tried {img_path}")
            continue

        if img_path not in img_cache:
            img_cache[img_path] = cv2.imread(img_path)
        img = img_cache[img_path]
        if img is None:
            stats["no_img"] += 1
            continue

        if crop_source == "bbox":
            crop = crop_bbox(img, bbox)
        else:
            crop = crop_polygon(img, polygon)

        if crop is None or crop.size == 0:
            stats["empty_crop"] += 1
            continue

        stem = f"{book_id}__{page_id}_line{line_idx:03d}"
        img_dest = os.path.join(images_out, f"{stem}.png")
        txt_dest = os.path.join(images_out, f"{stem}.gt.txt")

        cv2.imwrite(img_dest, crop)
        with open(txt_dest, "w", encoding="utf-8") as handle:
            handle.write(gt_text)

        split = record.get("split", split_map.get(book_id, "train"))
        records.append(
            {
                "img_path": img_dest,
                "gt_text": gt_text,
                "book_id": book_id,
                "page_id": page_id,
                "line_idx": line_idx,
                "line_type": line_type,
                "crop_src": crop_source,
                "split": split,
            }
        )
        stats["saved"] += 1

    print(
        f"  {book_id}: saved={stats['saved']}  deleted_skipped={stats['deleted']}  "
        f"empty_gt={stats['empty_gt']}  no_geom={stats['no_geom']}  "
        f"no_img={stats['no_img']}  empty_crop={stats['empty_crop']}  "
        f"margin_skipped={stats['margin_skipped']}"
    )
    return records


def build(input_dir, images_root, output_dir, split_cfg_path, exclude_margins=False):
    """Build the full HTR dataset from the unified annotation files."""
    images_out = os.path.join(output_dir, IMAGES_DIRNAME)
    os.makedirs(images_out, exist_ok=True)

    split_config = load_split_config(split_cfg_path)
    book_to_split = build_book_to_split(split_config)

    all_records = []
    files = sorted(glob.glob(os.path.join(input_dir, "*_unified.json")))
    if not files:
        print(f"[WARN] No *_unified.json files found in {input_dir}")
        return

    for path in files:
        print(f"Processing {os.path.basename(path)}")
        book_records = process_book(
            path,
            images_root,
            images_out,
            book_to_split,
            exclude_margins=exclude_margins,
        )
        all_records.extend(book_records)

    if not all_records:
        print("No records saved. Check your paths.")
        return

    manifests, splits_found = write_manifests(output_dir, all_records)
    write_metadata_csv(output_dir, all_records)
    write_split_used(output_dir, split_config)
    stats = compute_dataset_stats(all_records, splits_found)
    write_dataset_stats(output_dir, stats)
    print_summary(output_dir, all_records, manifests, stats, splits_found)
