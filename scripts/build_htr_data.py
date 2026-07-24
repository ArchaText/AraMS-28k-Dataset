"""
ArMan Unified → Kraken Dataset Builder
========================================
Reads *_unified.json files (built by build_unified_books.py) and produces
cropped line images + manifests for kraken fine-tuning.


Includes BOTH main and margin lines by default. Use --exclude_margins to
skip margin lines.

Usage:
    python build_htr_data.py \
        --input_dir ./annotations \
        --images_root . \
        --output_dir ./AraMS-28k-HTR \
        --split_cfg split.json

    # To exclude margin lines:
    python build_htr_data.py \
        --input_dir ./annotations  \
        --images_root . \
        --output_dir ./AraMS-28k-HTR \
        --split_cfg split.json \
        --exclude_margins

Folder layout expected:
    ./annotations/book_03_unified.json
   
    
    ./images/book_03/book_03_page_001.jpg
    ./images/book_03/book_03_page_002.jpg
    ...
"""

import json, argparse, os, csv, glob
from pathlib import Path
import cv2
import numpy as np

# ── Default split (same as original builder) ───────────────────────────────
SPLIT_CONFIG = {
    "train": ["book_27", "book_10", "book_12", "book_16", "book_17",
              "book_19", "book_20", "book_24", "book_21"],
    "val":   ["book_06", "book_11"],
    "test":  ["book_09", "book_03", "book_05"],
}

import re

# ── GT cleaning ─────────────────────────────────────────────────────────────
# Tashkil (harakat + shadda + tanwin + tatweel)
_TASHKIL = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]')
# Keep only Arabic letters (0621–063A, 0641–064A) and spaces; strip everything else
_KEEP    = re.compile(r'[^\u0621-\u063A\u0641-\u064A ]')


def clean_gt(text):
    text = _TASHKIL.sub('', text)   # strip tashkil first
    text = _KEEP.sub('', text)      # strip everything non-Arabic
    text = re.sub(r' +', ' ', text).strip()  # collapse multiple spaces
    return text

def resolve_image_path(page_image, images_root):
    """
    Try multiple strategies to find the image.
    page_image is like 'images/book_10/book_10_page_001.jpg'
    images_root is the base directory.
    """
    candidates = [
        # Direct join: images_root + page_image
        os.path.join(images_root, page_image),
        # If page_image already starts with 'images/' and images_root also ends with 'images/'
        # try stripping the leading 'images/' from page_image
        os.path.join(images_root, page_image.replace("images/", "", 1).lstrip("/")),
        # Try just the basename
        os.path.join(images_root, Path(page_image).name),
        # Try page_image as absolute (if images_root is empty)
        page_image,
    ]
    # Also try stripping one directory level at a time from page_image
    parts = Path(page_image).parts
    for i in range(1, len(parts)):
        candidates.append(os.path.join(images_root, *parts[i:]))

    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]  # return first candidate even if not found


# ── Crop helpers ──────────────────────────────────────────────────────────

def crop_bbox(img, bbox, pad=2):
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = img.shape[:2]
    return img[max(0, y1 - pad):min(h, y2 + pad),
               max(0, x1 - pad):min(w, x2 + pad)]


def crop_polygon(img, polygon_pts, pad=4):
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


# ═══════════════════════════════════════════════════════════════════════════
# Per-book processing
# ═══════════════════════════════════════════════════════════════════════════

def process_book(unified_path, images_root, images_out, split_map, exclude_margins=False):
    """
    Reads a *_unified.json file and returns list of kraken-ready records.
    """
    book_id = Path(unified_path).stem.replace("_unified", "")

    with open(unified_path, encoding="utf-8") as f:
        data = json.load(f)

    records = []
    img_cache = {}
    stats = {"saved": 0, "deleted": 0, "empty_gt": 0, "no_geom": 0, "no_img": 0, "empty_crop": 0, "margin_skipped": 0}

    for rec in data:
        # ── Skip deleted lines ──
        review = rec.get("review", {})
        if review.get("deleted", False):
            stats["deleted"] += 1
            continue

        page_id = rec["page_id"]
        line_idx = rec["line_idx"]
        line_type = rec.get("line_type", "main")

        # ── Skip margin lines if requested ──
        if exclude_margins and line_type == "margin":
            stats["margin_skipped"] += 1
            continue

        # ── Clean GT ──
        gt_raw = rec.get("text", {}).get("gt_raw", "")
        gt_text = clean_gt(gt_raw)
        if not gt_text:
            stats["empty_gt"] += 1
            continue

        # ── Geometry ──
        geo = rec.get("geometry", {})
        bbox = geo.get("bounding_box")
        poly = geo.get("boundary_polygon", [])

        if bbox and len(bbox) == 4:
            src = "bbox"
        elif poly:
            src = "poly"
            bbox = None
        else:
            stats["no_geom"] += 1
            continue

        # ── Resolve image path ──
        page_image = rec.get("page_image", "")
        img_path = resolve_image_path(page_image, images_root)
        if not os.path.exists(img_path):
            stats["no_img"] += 1
            if stats["no_img"] <= 3:
                print(f"    [WARN] Image not found: tried {img_path}")
            continue

        # ── Load & cache image ──
        if img_path not in img_cache:
            img_cache[img_path] = cv2.imread(img_path)
        img = img_cache[img_path]
        if img is None:
            stats["no_img"] += 1
            continue

        # ── Crop ──
        if src == "bbox":
            crop = crop_bbox(img, bbox)
        else:
            crop = crop_polygon(img, poly)

        if crop is None or crop.size == 0:
            stats["empty_crop"] += 1
            continue

        # ── Write files ──
        stem = f"{book_id}__{page_id}_line{line_idx:03d}"
        img_dest = os.path.join(images_out, f"{stem}.png")
        txt_dest = os.path.join(images_out, f"{stem}.gt.txt")

        cv2.imwrite(img_dest, crop)
        with open(txt_dest, "w", encoding="utf-8") as f:
            f.write(gt_text + "")

        # ── Split ──
        split = rec.get("split", split_map.get(book_id, "train"))

        records.append({
            "img_path": img_dest,
            "gt_text": gt_text,
            "book_id": book_id,
            "page_id": page_id,
            "line_idx": line_idx,
            "line_type": line_type,
            "crop_src": src,
            "split": split,
        })
        stats["saved"] += 1

    print(f"  {book_id}: saved={stats['saved']}  deleted_skipped={stats['deleted']}  "
          f"empty_gt={stats['empty_gt']}  no_geom={stats['no_geom']}  "
          f"no_img={stats['no_img']}  empty_crop={stats['empty_crop']}  "
          f"margin_skipped={stats['margin_skipped']}")
    return records


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def build(input_dir, images_root, output_dir, split_cfg_path, exclude_margins=False):
    images_out = os.path.join(output_dir, "images")
    os.makedirs(images_out, exist_ok=True)

    # load split config
    split = SPLIT_CONFIG.copy()
    if split_cfg_path and os.path.exists(split_cfg_path):
        with open(split_cfg_path, encoding="utf-8") as f:
            split = json.load(f)
        print(f"Loaded split config from {split_cfg_path}")

    book_to_split = {}
    for sname, books in split.items():
        for b in books:
            book_to_split[b] = sname

    all_records = []

    files = sorted(glob.glob(os.path.join(input_dir, "*_unified.json")))
    if not files:
        print(f"[WARN] No *_unified.json files found in {input_dir}")
        return

    for path in files:
        print(f"Processing {os.path.basename(path)}")
        recs = process_book(path, images_root, images_out, book_to_split, exclude_margins=exclude_margins)
        all_records.extend(recs)

    if not all_records:
        print("No records saved. Check your paths.")
        return

    # ── manifests ──
    splits_found = sorted(set(r["split"] for r in all_records))
    manifests = {}
    for sname in splits_found:
        path = os.path.join(output_dir, f"{sname}_manifest.txt")
        manifests[sname] = path
        split_paths = [r["img_path"] for r in all_records if r["split"] == sname]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(split_paths) + "\n")
        print(f"  {sname}_manifest.txt: {len(split_paths)} lines")

    # ── metadata CSV ──
    meta_path = os.path.join(output_dir, "metadata.csv")
    fieldnames = ["book_id", "page_id", "line_idx", "line_type", "split",
                  "crop_src", "gt_text", "img_path"]
    with open(meta_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in all_records:
            w.writerow({k: r[k] for k in fieldnames})

    # ── split config used ──
    used_split_path = os.path.join(output_dir, "split_used.json")
    with open(used_split_path, "w", encoding="utf-8") as f:
        json.dump(split, f, indent=2, ensure_ascii=False)

    # ── stats ──
    stats_path = os.path.join(output_dir, "dataset_stats.json")
    book_stats = {}
    for r in all_records:
        b = r["book_id"]
        if b not in book_stats:
            book_stats[b] = {"split": r["split"], "lines": 0, "pages": set()}
        book_stats[b]["lines"] += 1
        book_stats[b]["pages"].add(r["page_id"])

    split_stats = {s: {"lines": 0, "books": 0, "pages": set()} for s in splits_found}
    for b, bs in book_stats.items():
        s = bs["split"]
        split_stats[s]["lines"] += bs["lines"]
        split_stats[s]["books"] += 1
        split_stats[s]["pages"] |= bs["pages"]
        bs["pages"] = len(bs["pages"])

    for s in split_stats:
        split_stats[s]["pages"] = len(split_stats[s]["pages"])

    full_stats = {
        "total_lines": len(all_records),
        "total_books": len(book_stats),
        "splits": split_stats,
        "per_book": book_stats,
    }
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(full_stats, f, indent=2, ensure_ascii=False)

    # ── summary ──
    print(f"\n{'='*60}")
    print(f"  Total line images : {len(all_records)}")
    for s in splits_found:
        ss = split_stats[s]
        books_in = [b for b, bs in book_stats.items() if bs["split"] == s]
        print(f"  {s:6s}  : {ss['lines']:5d} lines  "
              f"{ss['books']} books ({', '.join(sorted(books_in))})")
    print(f"{'='*60}")
    print(f"\nOutputs:")
    print(f"  images/           → {len(all_records)} .png + .gt.txt pairs")
    for s, p in manifests.items():
        print(f"  {s}_manifest.txt  → {p}")
    print(f"  metadata.csv      → full record for paper/analysis")
    print(f"  dataset_stats.json→ per-book and per-split counts")
    print(f"  split_used.json   → exact split for reproducibility")
    print(f"\nTo fine-tune kraken:")
    print(f"  ketos train ")
    print(f"    --load  YOUR_BASE_MODEL.mlmodel ")
    print(f"    -t {manifests.get('train','')} ")
    print(f"    -e {manifests.get('val','')}")
    print(f"\nTo compile to binary first (faster):")
    print(f"  ketos compile -f binary -o {output_dir}/train.arrow $(cat {manifests.get('train','')})")
    print(f"  ketos compile -f binary -o {output_dir}/val.arrow   $(cat {manifests.get('val','')})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input_dir",  required=True,
                   help="Directory containing *_unified.json files")
    p.add_argument("--images_root", required=True,
                   help="Root directory for resolving page_image paths")
    p.add_argument("--output_dir", default="./arman_kraken_dataset")
    p.add_argument("--split_cfg",  default=None,
                   help="Optional JSON file to override SPLIT_CONFIG")
    p.add_argument("--exclude_margins", action="store_true",
                   help="Skip lines with line_type='margin'")
    args = p.parse_args()
    build(args.input_dir, args.images_root, args.output_dir, args.split_cfg, exclude_margins=args.exclude_margins)


if __name__ == "__main__":
    main()
