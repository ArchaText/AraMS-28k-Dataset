"""CLI entrypoint for the AraMS HTR dataset builder."""

import argparse

from htr_builder.builder import build
from htr_builder.constants import DEFAULT_OUTPUT_DIR


def parse_args():
    """Parse command line arguments for the HTR dataset builder."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing *_unified.json files",
    )
    parser.add_argument(
        "--images_root",
        required=True,
        help="Root directory for resolving page_image paths",
    )
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--split_cfg",
        default=None,
        help="Optional JSON file to override the default split config",
    )
    parser.add_argument(
        "--exclude_margins",
        action="store_true",
        help="Skip lines with line_type='margin'",
    )
    return parser.parse_args()


def main():
    """Run the build command from parsed CLI arguments."""
    args = parse_args()
    build(
        input_dir=args.input_dir,
        images_root=args.images_root,
        output_dir=args.output_dir,
        split_cfg_path=args.split_cfg,
        exclude_margins=args.exclude_margins,
    )


if __name__ == "__main__":
    main()
