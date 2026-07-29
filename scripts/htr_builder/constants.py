"""Shared constants for the HTR dataset builder."""

DEFAULT_OUTPUT_DIR = "./AraMS-28k-HTR"
IMAGES_DIRNAME = "images"
METADATA_FILENAME = "metadata.csv"
SPLIT_USED_FILENAME = "split_used.json"
DATASET_STATS_FILENAME = "dataset_stats.json"

BBOX_PAD = 2
POLYGON_PAD = 4

SPLIT_CONFIG = {
    "train": [
        "book_27",
        "book_10",
        "book_12",
        "book_16",
        "book_17",
        "book_19",
        "book_20",
        "book_24",
        "book_21",
    ],
    "val": ["book_06", "book_11"],
    "test": ["book_09", "book_03", "book_05"],
}
