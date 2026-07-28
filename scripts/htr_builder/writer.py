"""Output writers for manifests, metadata, and dataset stats."""

import csv
import json
import os

from htr_builder.constants import (
    DATASET_STATS_FILENAME,
    METADATA_FILENAME,
    SPLIT_USED_FILENAME,
)


def write_manifests(output_dir, all_records):
    """Write one manifest file per discovered split."""
    splits_found = sorted(set(record["split"] for record in all_records))
    manifests = {}

    for split_name in splits_found:
        manifest_path = os.path.join(output_dir, f"{split_name}_manifest.txt")
        manifests[split_name] = manifest_path
        split_paths = [
            record["img_path"] for record in all_records if record["split"] == split_name
        ]
        with open(manifest_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(split_paths) + "\n")
        print(f"  {split_name}_manifest.txt: {len(split_paths)} lines")

    return manifests, splits_found


def write_metadata_csv(output_dir, all_records):
    """Write the per-line metadata CSV."""
    metadata_path = os.path.join(output_dir, METADATA_FILENAME)
    fieldnames = [
        "book_id",
        "page_id",
        "line_idx",
        "line_type",
        "split",
        "crop_src",
        "gt_text",
        "img_path",
    ]

    with open(metadata_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in all_records:
            writer.writerow({key: record[key] for key in fieldnames})

    return metadata_path


def write_split_used(output_dir, split_config):
    """Persist the effective split config for reproducibility."""
    split_used_path = os.path.join(output_dir, SPLIT_USED_FILENAME)
    with open(split_used_path, "w", encoding="utf-8") as handle:
        json.dump(split_config, handle, indent=2, ensure_ascii=False)
    return split_used_path


def compute_dataset_stats(all_records, splits_found):
    """Aggregate per-book and per-split dataset counts."""
    book_stats = {}
    for record in all_records:
        book_id = record["book_id"]
        if book_id not in book_stats:
            book_stats[book_id] = {"split": record["split"], "lines": 0, "pages": set()}
        book_stats[book_id]["lines"] += 1
        book_stats[book_id]["pages"].add(record["page_id"])

    split_stats = {
        split_name: {"lines": 0, "books": 0, "pages": set()}
        for split_name in splits_found
    }
    for book_id, book_info in book_stats.items():
        split_name = book_info["split"]
        split_stats[split_name]["lines"] += book_info["lines"]
        split_stats[split_name]["books"] += 1
        split_stats[split_name]["pages"] |= book_info["pages"]
        book_info["pages"] = len(book_info["pages"])

    for split_name in split_stats:
        split_stats[split_name]["pages"] = len(split_stats[split_name]["pages"])

    return {
        "total_lines": len(all_records),
        "total_books": len(book_stats),
        "splits": split_stats,
        "per_book": book_stats,
    }


def write_dataset_stats(output_dir, stats):
    """Write the aggregate dataset stats JSON."""
    stats_path = os.path.join(output_dir, DATASET_STATS_FILENAME)
    with open(stats_path, "w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2, ensure_ascii=False)
    return stats_path


def print_summary(output_dir, all_records, manifests, stats, splits_found):
    """Print a concise summary of the generated dataset artifacts."""
    print(f"\n{'=' * 60}")
    print(f"  Total line images : {len(all_records)}")
    for split_name in splits_found:
        split_info = stats["splits"][split_name]
        books_in_split = [
            book_id
            for book_id, book_stats in stats["per_book"].items()
            if book_stats["split"] == split_name
        ]
        print(
            f"  {split_name:6s}  : {split_info['lines']:5d} lines  "
            f"{split_info['books']} books ({', '.join(sorted(books_in_split))})"
        )

    print(f"{'=' * 60}")
    print("\nOutputs:")
    print(f"  images/           → {len(all_records)} .png + .gt.txt pairs")
    for split_name, manifest_path in manifests.items():
        print(f"  {split_name}_manifest.txt  → {manifest_path}")
    print("  metadata.csv      → full record for paper/analysis")
    print("  dataset_stats.json→ per-book and per-split counts")
    print("  split_used.json   → exact split for reproducibility")
    print("\nTo fine-tune kraken:")
    print("  ketos train ")
    print("    --load  YOUR_BASE_MODEL.mlmodel ")
    print(f"    -t {manifests.get('train', '')} ")
    print(f"    -e {manifests.get('val', '')}")
    print("\nTo compile to binary first (faster):")
    print(
        f"  ketos compile -f binary -o {output_dir}/train.arrow "
        f"$(cat {manifests.get('train', '')})"
    )
    print(
        f"  ketos compile -f binary -o {output_dir}/val.arrow   "
        f"$(cat {manifests.get('val', '')})"
    )
