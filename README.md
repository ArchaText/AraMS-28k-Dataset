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
This repository holds the **code** used to build and reproduce AraMS-28k
(annotation schema, split definitions, the AraMS-28k-HTR build script,
and documentation). **Data is not stored in this repository** — download
it from Hugging Face  
[**AraMS-28k**](https://huggingface.co/datasets/Archatext/AraMS-28k)
[**AraMS-28k-HTR**](https://huggingface.co/datasets/Archatext/AraMS-28k-HTR)

---

## Overview

AraMS-28k comprises 14 books, 3,043 pages, and 28,600 annotated text
lines (27,971 main-text, 629 margin) spanning three hand-copied script
traditions — Naskh, Ruq'ah, and Maghrebi — plus one lithographed printed
edition. Every line is labelled as main-text or margin, and margin
lines with an unambiguous attachment point are further annotated with
an **insertion anchor**, recovering the manuscript's non-linear reading
order at line-level granularity — to our knowledge the first such
annotation released for a historical Arabic manuscript corpus.

## Dataset Statistics

| Property | Value |
|---|---|
| Books | 14 |
| Pages | 3,043 |
| Main lines | 27,971 |
| Margin lines | 629 |
| Confidently anchored margin lines | 189 / 629 (~30%) |
| Scripts | Naskh, Ruq'ah, Maghrebi (+1 lithographed volume) |
| Train / val / test split | 9 / 2 / 3 books |
| License | CC BY-NC-SA 4.0 |

Full per-book statistics: paper Appendix A.

## Download

Two release formats, matching the paper's Appendix C:

| Release | What | Where |
|---|---|---|
| **AraMS-28k** | full annotation release (images + geometry + raw/normalized text + anchors + review metadata) |  [**AraMS-28k**](https://huggingface.co/datasets/Archatext/AraMS-28k)
 |
| **AraMS-28k-HTR** | recognition-ready release (cropped line images + `.gt.txt`, ready for Kraken/HTR pipelines) | [**AraMS-28k-HTR**](https://huggingface.co/datasets/Archatext/AraMS-28k-HTR) |


### Checksums

```
376c1e19bf04d678f1052505e45e805dd2753ea182cb146614a546027925fa55  AraMS-28k.zip
8c4acccefae78f3940deb26af91a72d6aad80f67de175a287669dd9e297b2091  AraMS-28k-HTR.zip
```

Verify any download:
```bash
sha256sum -c SHA256SUMS.txt

python scripts/verify_checksums.py
```

## Repository Structure

```
schema/       — JSON Schema for the per-line annotation record
splits/       — book-level train/val/test assignment
scripts/      — build_data.py (AraMS-28k → AraMS-28k-HTR) and dependencies
docs/         — annotation guidelines, FAQ
examples/     — notebook: load a record, draw its polygon/bbox on the page image
```

## Line Record Schema

```json
{
  "line_uid": "book_03_page_001_L000",
  "line_type": "main",
  "text": {
      "gt_raw": "...",
      "gt_normalized": "...",
      "gemini_raw": "...",
      "confidence": 100
  },
  "layout": {"insertion_anchor": null, "rotation": "horizontal"},
  "split": "train"
}
```

`gt_normalized` (diacritic-stripped, matched to what's visually present
in the hand) is the **recommended training target** for HTR models;
`gt_raw` is the fully vocalized reference. See `schema/line_record.schema.json`
and paper Sec. 4 for the full field list.

## Building AraMS-28k-HTR from AraMS-28k

```bash
pip install -r requirements.txt

python scripts/build_data.py \
    --input_dir ./annotations \
    --images_root . \
    --output_dir ./AraMS-28k-HTR \
    --split_cfg splits/split.json
```

Produces cropped `.png` line images + `.gt.txt` targets + a manifest,
for both main and margin lines. See `docs/faq.md` for path-resolution
notes if you hit missing-image warnings.

## Citation

```bibtex
@article{arams28k,
  title   = {AraMS-28k: The Largest Publicly Released Line-Level Dataset of Historical Arabic Manuscripts, with Margin and Insertion-Anchor Annotations},
  author  = {TBD},
  year    = {2026}
}
```

## License

Released under **CC BY-NC-SA 4.0**. Reference transcriptions may carry
independent copyright where derived from a modern critical edition —
see `DATASHEET.md`.

