# AraMS-28k: Historical Arabic Manuscript Line Dataset

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Pages](https://img.shields.io/badge/pages-3%2C043-brightgreen.svg)]()
[![Lines](https://img.shields.io/badge/lines-28%2C600-brightgreen.svg)]()

AraMS-28k is a line-level dataset of historical Arabic manuscripts produced by the
**RefLAM** (Reference-grounded Line Annotation for Manuscripts) pipeline. It comprises
**14 books**, **3,043 pages**, and **28,600 line annotations** (27,971 main-text + 629
margin lines) with bounding boxes, layout labels, and insertion anchors.

---

## Table of Contents

- [Key Features](#key-features)
- [Dataset Statistics](#dataset-statistics)
- [Splits](#splits)
- [Repository Structure](#repository-structure)
- [Data Format](#data-format)
- [Usage](#usage)
- [License](#license)
- [Citation](#citation)
- [References](#references)

---

## Key Features

| | |
|---|---|
| 🖋️ **Scripts** | Naskh, Ruqʿah, and Maghrebi |
| 🗂️ **Layout annotations** | Explicit main/margin line-type labels and margin anchors recovering non-linear reading order |
| 📐 **Geometry** | Baseline polylines, boundary polygons, and axis-aligned bounding boxes |
| ✅ **Ground truth** | Character-level validated transcriptions with diacritic-agnostic alignment confidence scores |
| 🔗 **Reference-grounded** | Every line is traceable to a contiguous span in a clean scholarly transcription |

---

## Dataset Statistics

| Property | Value |
|:---|:---|
| Books | 14 |
| Total pages | 3,043 |
| Fully page-validated | 548 |
| Partially line-validated | 2,495 |
| Main-text lines | 27,971 |
| Margin lines | 629 |
| Scripts | Naskh, Ruqʿah, Maghrebi |
| Avg. words/line | 9.5–17.2 |
| Avg. lines/page (PV) | 20.9 |
| Margin anchor coverage | ~30% |
| Train / val / test split | 9 / 2 / 3 books |
| License | CC BY-NC-SA |

---

## Splits

Splits are defined **at the book level**:

| Split | Books | Lines | Notes |
|:---|:---:|:---:|:---|
| **Train** | 9 | 19,739 | Mix of page-validated and line-validated; all three scripts |
| **Validation** | 2 | 1,486 | Page-validated Naskh only (`book_06`, `book_11`) |
| **Test** | 3 | 6,744 | Page-validated: Naskh (`book_09`), Maghrebi (`book_03`), Ruqʿah (`book_05`) |

Each record also carries a `split` field (`train`, `val`, or `test`) for convenience.
See [`splits/`](splits/) for the exact book IDs in each split.

---

## Repository Structure

```
AraMS-28k/
├── README.md
├── DATASHEET.md
├── LICENSE
├── images/                       # Page images organized by book
│   ├── book_03/
│   │   ├── book_03_page_001.jpg
│   │   └── ...
│   └── book_XX/...
├── annotations/                  # Line-level annotations (JSONL)
│   ├── book_03.jsonl
│   └── book_XX.jsonl
├── splits/                       # Train/val/test book lists
│   ├── train_books.txt
│   ├── val_books.txt
│   └── test_books.txt
├── schema/
│   └── line_record.schema.json   # Formal JSON Schema
└── scripts/
    ├── validate_dataset.py       # Schema, checksum, and completeness checks
    └── load_dataset.py           # Minimal loader example
```

---

## Data Format

Each file in `annotations/` is a **JSON Lines** (`.jsonl`) file with one JSON record per
line. The formal JSON Schema is available in [`schema/line_record.schema.json`](schema/line_record.schema.json).

### Top-Level Fields

| Field | Type | Description |
|:---|:---|:---|
| `line_uid` | string | Globally unique line identifier, e.g. `book_03_page_076_L0000` |
| `book_id` | string | Book identifier, e.g. `book_03` |
| `page_id` | string | Page identifier, e.g. `book_03_page_076` |
| `page_image` | string | Relative path to the full page image |
| `line_idx` | integer | Zero-based line index on the page, top-to-bottom |
| `line_type` | string | `"main"` or `"margin"` |
| `split` | string | `"train"`, `"val"`, or `"test"` |
| `text` | object | Transcriptions and alignment confidence (see below) |
| `geometry` | object | Spatial geometry: baseline, boundary polygon, bounding box (see below) |
| `margin_anchor` | object / null | For margin lines: anchor info linking to main text; `null` for main lines |
| `review` | object | Human review flags (see below) |

### `text` Object

| Field | Type | Description |
|:---|:---|:---|
| `gt_raw` | string | Clean reference transcription from scholarly edition (may include diacritics) |
| `gemini_raw` | string | Raw MLLM OCR hypothesis before correction |
| `confidence` | number | Fuzzy alignment confidence in `[0, 100]`. A value of `100` guarantees character-for-character normalised-string identity (Confidence-100 rule). |

### `geometry` Object

| Field | Type | Description |
|:---|:---|:---|
| `baseline` | array / null | Ordered polyline of `[x, y]` points tracing the text baseline; `null` if unavailable |
| `boundary_polygon` | array / null | Ordered polygon vertices `[[x, y], ...]` faithfully following the text line contour; `null` if unavailable |
| `bounding_box` | object / null | Axis-aligned bounding box `{x, y, w, h}`; `null` if unavailable |

### `margin_anchor` Object

*Margin lines only — `null` for main lines.*

| Field | Type | Description |
|:---|:---|:---|
| `before` | string | Text of the main line immediately before the insertion point |
| `after` | string | Text of the main line immediately after the insertion point |
| `line` | integer | Index of the main line after which this margin line logically inserts |
| `rotation` | string / null | Coarse orientation of the margin text, e.g. `"horizontal"`, or `null` |

### `review` Object

| Field | Type | Description |
|:---|:---|:---|
| `edited` | boolean | Whether the transcription was manually edited during review |
| `validated` | boolean | Whether the line has passed human validation |
| `deleted` | boolean | Whether the line was marked for deletion |
| `page_reviewed` | boolean | Whether the entire containing page was reviewed |

### The Confidence-100 Rule

> Under RefLAM's alignment metric, a confidence score of **100** is a *provable guarantee*
> of character-for-character normalised-string identity (see Proposition 1 in the RefLAM
> paper). Lines with `confidence == 100` were verified through rapid human visual
> confirmation; sub-100 lines received detailed manual review (page-validated books) or
> were excluded from release (line-validated books).

---

## Usage

### Prerequisites

- Python 3.8 or higher
- Install required packages:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Downloading the Image Files and Building the Data

The dataset annotations are included in this repository, but the page images are stored
separately.

1. Download the image archive from the
   [AraMS-28k dataset page](https://huggingface.co/datasets/mguechaoui/AraMS-28k/tree/main)
   and extract it so that the folder structure matches the paths used in the annotation
   files.

   For example, if the annotations reference `images/book_03/book_03_page_001.jpg`, your
   extracted folder should contain:

   ```
   images/
   ├── book_03/
   │   ├── book_03_page_001.jpg
   │   └── ...
   ├── book_05/
   │   └── ...
   └── ...
   ```

   Place the `images/` folder at the repository root: `AraMS-28k-Dataset/images`.

2. Run `scripts/build_data.py`. It reads the unified JSON annotation files
   (`*_unified.json`) and produces:

   - Cropped line images (`.png`)
   - Corresponding ground-truth text files (`.gt.txt`)
   - Split manifests (training, validation, test)
   - Metadata and statistics

   ```bash
   python scripts/build_data.py \
       --input_dir ./unified_books \
       --images_root . \
       --output_dir ./arman_kraken_dataset \
       --split_cfg splits/split.json
   ```

   **Arguments:**

   | Flag | Description |
   |:---|:---|
   | `--input_dir` | Directory containing the `*_unified.json` files |
   | `--images_root` | Root folder where the `images/` directory is located |
   | `--output_dir` | Where the output dataset will be written |
   | `--split_cfg` | *(optional)* JSON file defining train/val/test splits |
   | `--exclude_margins` | *(optional)* Flag to skip margin lines |

---

## License

This dataset is released under the **Creative Commons Attribution-NonCommercial-ShareAlike**
(CC BY-NC-SA) license.

## Citation

If you use AraMS-28k or the RefLAM pipeline in your research, please cite:

```bibtex
@article{reflam2025,
  title   = {RefLAM: A Reference-Grounded Line Annotation Pipeline for Historical Arabic Manuscripts},
  author  = {[TODO]},
  journal = {[TODO]},
  year    = {2025}
}
```

## References

- **RefLAM Paper** — [TODO: arXiv / conference URL]
- **HATFormer** — [arXiv:2410.02179](https://arxiv.org/abs/2410.02179)
- **Muharaf Dataset** — [NeurIPS 2024 Datasets and Benchmarks Track](https://datasets-benchmarks-proceedings.neurips.cc/)
- **Kraken** — [https://kraken.re](https://kraken.re)
