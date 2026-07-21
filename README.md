# AraMS-28k: Historical Arabic Manuscript Line Dataset

AraMS-28k is a line-level dataset of historical Arabic manuscripts produced by the **RefLAM** (Reference-grounded Line Annotation for Manuscripts) pipeline. It comprises **14 books**, **3,043 pages**, and **28,600 line annotations** (27,971 main-text + 629 margin lines) with bounding boxes, layout labels, and insertion anchors.

## Key Features

- **Scripts**: Naskh, Ruq'ah, and Maghrebi
- **Layout annotations**: Explicit main/margin line-type labels and margin anchors recovering non-linear reading order
- **Geometry**: Baseline polylines, boundary polygons, and axis-aligned bounding boxes
- **Ground truth**: Character-level validated transcriptions with diacritic-agnostic alignment confidence scores
- **Reference-grounded**: Every line is traceable to a contiguous span in a clean scholarly transcription

## Dataset Statistics

| Property | Value |
|:---|:---|
| Books | 14 |
| Total pages | 3,043 |
| Fully page-validated | 548 |
| Partially line-validated | 2,495 |
| Main-text lines | 27,971 |
| Margin lines | 629  |
| Scripts | Naskh, Ruq'ah, Maghrebi |
| Avg. words/line | 9.5-17.2 |
| Avg. lines/page (PV) | 20.9 |
| Margin anchor coverage | ~30% |
| Train/val/test split | 9 / 2 / 3 books |
| License | CC BY-NC-SA |

## Splits

Splits are defined at the book level:

| Split | Books | Lines | Notes |
|:---|:---|:---|:---|
| **Train** | 9 | 19,739 | Mix of page-validated and line-validated; all three scripts |
| **Validation** | 2 | 1,486 | Page-validated Naskh only (book_06, book_11) |
| **Test** | 3 | 6,744 | Page-validated: Naskh (book_09), Maghrebi (book_03), Ruq'ah (book_05) |

Each record also carries a `split` field (`train`, `val`, or `test`) for convenience.

See `splits/*.txt` for the exact book IDs in each split.

## Repository Structure

```
AraMS-28k/
├── README.md
├── DATASHEET.md
├── LICENSE
├── images/               # Page images organized by book
│   ├── book_03/
│   │   ├── book_03_page_001.jpg
│   │   └── ...
│   └── book_XX/...
├── annotations/          # Line-level annotations (JSONL)
│   ├── book_03.jsonl
│   └── book_XX.jsonl
├── splits/               # Train/val/test book lists
│   ├── train_books.txt
│   ├── val_books.txt
│   └── test_books.txt
├── schema/
│   └── line_record.schema.json   # Formal JSON Schema
└── scripts/
    ├── validate_dataset.py       # Schema, checksum, and completeness checks
    └── load_dataset.py           # Minimal loader example
```

## Data Format

Each file in `annotations/` is a **JSON Lines** (`.jsonl`) file with one JSON record per line. The formal JSON Schema is available in `schema/line_record.schema.json`.

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

### `margin_anchor` Object (margin lines only; `null` for main lines)

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

Under RefLAM's alignment metric, a confidence score of **100** is a *provable guarantee* of character-for-character normalised-string identity (see Proposition 1 in the RefLAM paper). Lines with `confidence == 100` were verified through rapid human visual confirmation; sub-100 lines received detailed manual review (page-validated books) or were excluded from release (line-validated books).

## Usage

### Quick Start

```python
from scripts.load_dataset import load_book

records = load_book("annotations/book_03.jsonl")
for r in records:
    print(r["line_uid"], r["text"]["gt_raw"])
```

### Validation

```bash
python scripts/validate_dataset.py --root .
```

## License

This dataset is released under the **Creative Commons Attribution-NonCommercial-ShareAlike** (CC BY-NC-SA) license.

## Citation

If you use AraMS-28k or the RefLAM pipeline in your research, please cite:

```bibtex
@article{reflam2025,
  title={RefLAM: A Reference-Grounded Line Annotation Pipeline for Historical Arabic Manuscripts},
  author={[TODO]},
  journal={[TODO]},
  year={2025}
}
```

## References

- **RefLAM Paper**: [TODO: arXiv / conference URL]
- **HATFormer**: [arXiv:2410.02179](https://arxiv.org/abs/2410.02179)
- **Muharaf Dataset**: [NeurIPS 2024 Datasets and Benchmarks Track](https://datasets-benchmarks-proceedings.neurips.cc/)
- **Kraken**: [https://kraken.re](https://kraken.re)
