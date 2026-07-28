"""Split configuration helpers."""

import json
import os

from htr_builder.constants import SPLIT_CONFIG


def load_split_config(split_cfg_path):
    """Load an override split config, or fall back to the default one."""
    split = SPLIT_CONFIG.copy()
    if split_cfg_path and os.path.exists(split_cfg_path):
        with open(split_cfg_path, encoding="utf-8") as handle:
            split = json.load(handle)
        print(f"Loaded split config from {split_cfg_path}")
    return split


def build_book_to_split(split_config):
    """Map each book id to its split name."""
    book_to_split = {}
    for split_name, books in split_config.items():
        for book_id in books:
            book_to_split[book_id] = split_name
    return book_to_split
