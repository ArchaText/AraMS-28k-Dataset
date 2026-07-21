# AraMS-28k Datasheet

This datasheet follows the framework proposed by Gebru et al., "Datasheets for Datasets" (2021), to document the composition, collection process, and intended use of AraMS-28k.

---

## 1. Motivation

### For what purpose was the dataset created?
AraMS-28k was created to provide line-level training and evaluation data for handwritten text recognition (HTR) models targeting historical Arabic manuscripts. Existing public corpora for this domain were either too small (RASM2018, ~120 pages), lacked layout annotations (Muharaf), or consisted of modern rather than historical material (KHATT). AraMS-28k fills the gap by offering the first publicly released large-scale line-level dataset of genuine historical Arabic manuscripts with explicit main/margin layout labels and insertion anchors.

### Who created the dataset and on whose behalf?
[TODO: Author names and affiliations]. The dataset was created as part of the RefLAM (Reference-grounded Line Annotation for Manuscripts) research project.

### Who funded the creation of the dataset?
[TODO: Funding sources, if any.]

### Any other comments?
No.

---

## 2. Composition

### What do the instances that comprise the dataset represent?
Each instance is a single text line extracted from a digitised historical Arabic manuscript page. An instance includes:
- A bounding geometry (axis-aligned rectangle or polygon) locating the line on the page image.
- A validated ground-truth transcription (`gt_raw`), typically from a fully diacritised scholarly edition.
- A raw MLLM OCR hypothesis (`gemini_raw`).
- Layout metadata: line type (`main` or `margin`), insertion anchor, coarse rotation.
- Alignment metadata: confidence score, reference span indices, page anchor offset.

### How many instances are there in total?
28,100 line annotations across 3,043 pages from 14 books.
- 27,969 main-text lines
- 131 margin lines (129 with rectangular boxes, 2 with polygonal boxes)

### Does the dataset contain all possible instances or is it a sample?
The dataset contains all lines from the selected pages of each book. Books were chosen to maximise diversity across script style (Naskh, Ruq'ah, Maghrebi), diacritisation level, scan quality, and layout complexity. It is not a random sample of all Arabic manuscripts.

### What data does each instance consist of?
Each instance is a JSON record. See `schema/line_record.schema.json` for the formal schema. Key fields include:
- `book_id`, `page_id`, `line_id`, `line_idx`
- `line_type`: `"main"` or `"margin"`
- `insertion_anchor`: integer or `null`
- `rotation`: coarse orientation class
- `box`: bounding geometry (bbox or polygon)
- `gt_raw`, `gemini_raw`, `norm_gt`, `norm_ocr`
- `confidence`: integer in [0, 100]
- `span_start`, `span_end`, `page_anchor_offset`
- `review_status`, `reviewer_notes`
- `image_path`, `page_image_path`

### Is there a label or target associated with each instance?
Yes. The primary label is `gt_raw`, the clean reference transcription. Secondary labels include `line_type`, `insertion_anchor`, and `rotation`.

### Is any information missing from individual instances?
- `insertion_anchor` is `null` for approximately 30% of margin lines where assignment was editorially ambiguous (ownership stamps, later commentaries, etc.).
- `rotation` is a coarse 8-directional estimate; continuous angle is not provided.
- `reviewer_notes` may be empty.

### Are relationships between individual instances made explicit?
Yes. Within a page, `line_idx` gives the top-to-bottom reading order. For margin lines, `insertion_anchor` explicitly links the margin line to the main-text line after which it logically inserts, recovering non-linear reading order.

### Are there recommended data splits?
Yes. The dataset is split at the book level:
- **Train**: 9 books (19,739 lines)
- **Validation**: 2 books (1,486 lines)
- **Test**: 3 books (6,744 lines)

See `splits/*.txt` for exact book assignments.

### Are there any errors, sources of noise, or redundancies in the dataset?
- **OCR noise**: `gemini_raw` is an unvalidated MLLM hypothesis and may contain hallucinations, omissions, or merged lines. It is provided for research purposes, not as ground truth.
- **Segmentation noise**: Approximately 2% of lines required manual correction of predicted bounding boxes.
- **Normalisation**: `norm_gt` and `norm_ocr` strip diacritics, kashida, and certain letter variants, which may obscure subtle orthographic distinctions.
- **Line-validated books**: For 7 books, only confidence-100 lines were retained; sub-100 lines were excluded rather than manually corrected.

### Is the dataset self-contained, or does it link to or otherwise rely on external resources?
The dataset is self-contained. Page images are included. However, the reference transcriptions (`gt_raw`) originate from external scholarly digital text repositories; the dataset includes only the matched spans, not the full books.

### Does the dataset contain data that might be considered confidential?
No. All source manuscripts are historical (centuries old) and publicly digitised.

### Does the dataset contain data that, if viewed directly, might be offensive, insulting, threatening, or might otherwise cause anxiety?
No. The content consists of classical Arabic scholarly texts (medicine, jurisprudence, philosophy, theology).

### Does the dataset relate to people?
No. The dataset contains text from historical manuscripts, not personal data about individuals.

### Any other comments?
No.

---

## 3. Collection Process

### How was the data associated with each instance acquired?
Data was acquired through the RefLAM pipeline:
1. **Page images** were obtained from publicly available manuscript digitisation projects.
2. **Line segmentation** was initialised using a Kraken model trained on Muharaf, then manually verified/corrected.
3. **MLLM OCR** was generated by Google Gemini (gemini-3-flash-preview) via zero-shot full-page calls.
4. **Page anchoring** located each page within a book-level clean transcription via fuzzy 5-line window search.
5. **Line-level fuzzy alignment** matched each OCR line to a contiguous span in the reference text, producing a confidence score.
6. **Human review** confirmed, corrected, or excluded every line.

### What mechanisms or procedures were used to collect the data?
See the RefLAM paper (Section 3) for full algorithmic details. The pipeline is released alongside the dataset.

### If the dataset is a sample from a larger set, what was the sampling strategy?
Books were purposively selected to span three scripts (Naskh, Ruq'ah, Maghrebi), varying scan quality, and diverse layout complexity. Pages within each book were processed exhaustively.

### Who was involved in the data collection process?
[TODO: Annotator names/roles if disclosable.]

### Over what timeframe was the data collected?
[TODO: Collection period.]

### Were any ethical review processes conducted?
[TODO: If applicable.]

### Did you collect the data from the individuals in question directly, or obtain it via third parties or other sources?
Page images were obtained from third-party digitisation archives. Clean transcriptions were obtained from digital Arabic text repositories or produced by OCR over scanned printed editions.

### Was the data validated?
Yes. Two validation phases were conducted:
- **Page-validated (PV)**: 7 books, 548 pages, 11,436 lines — every line inspected by two independent reviewers.
- **Line-validated (LV)**: 7 books, 2,495 pages, 16,533 lines — only confidence-100 lines retained; all sub-100 lines excluded.

### Any other comments?
No.

---

## 4. Preprocessing / Cleaning / Labelling

### Was any preprocessing/cleaning/labeling of the data done?
Yes:
- **Polygon-to-rectangle conversion**: Kraken polygonal outputs were converted to axis-aligned bounding boxes for ~2% of lines where polygon correction was impractical.
- **Diacritic-agnostic normalisation**: Both OCR and reference text were normalised by stripping harakat, kashida, alef variants, etc. (Definition 1 in the RefLAM paper).
- **Fuzzy alignment**: Greedy line-to-reference matching with confidence scoring.
- **Human review**: Bounding box adjustment, transcription correction, and layout tag verification.

### Was the "raw" data saved in addition to the preprocessed/cleaned/labeled data?
Yes. `gt_raw` and `gemini_raw` preserve the original transcriptions before normalisation.

### Is the software used to preprocess/clean/label the instances available?
Yes. The RefLAM pipeline and browser-based review tool are released alongside the dataset. See the repository for `scripts/validate_dataset.py` and `scripts/load_dataset.py`.

### Any other comments?
No.

---

## 5. Uses

### Has the dataset been used for any tasks already?
Yes. The dataset was used to finetune and evaluate two HTR baselines:
- **Kraken** (CNN-BLSTM-CTC): 13.08% CER overall
- **HATFormer** (Transformer-based): 26.74% CER overall

### Is there a repository that links to any or all papers or systems that use the dataset?
[TODO: Link to benchmark leaderboard or paper list if created.]

### What (other) tasks could the dataset be used for?
- Historical Arabic handwritten text recognition (HTR) training and benchmarking
- Layout analysis (main/margin detection, insertion anchor prediction)
- Diacritisation restoration (comparing `gt_raw` with `norm_gt`)
- OCR error analysis and post-correction
- Script style classification (Naskh vs. Ruq'ah vs. Maghrebi)
- Margin annotation and non-linear reading order recovery
- Weak/distant supervision research (reference-grounded alignment)

### Is there anything about the composition of the dataset or the way it was collected and preprocessed/cleaned/labeled that might impact future uses?
- The confidence-100 filtering on line-validated books means those subsets contain only "easy" lines; they are not representative of the full difficulty distribution.
- The dataset is not balanced across scripts or books.
- Margin lines are extremely rare (131 / 28,100); tasks requiring large margin samples will be challenging.
- The dataset requires a clean reference transcription to exist; this limits applicability to manuscripts without such editions.

### Are there tasks for which the dataset should not be used?
- The dataset should not be used for modern Arabic handwriting (use KHATT instead).
- It should not be used as a general-purpose Arabic language corpus without acknowledging the historical, scholarly, and diacritised nature of the text.
- Commercial use is prohibited under the CC BY-NC-SA license.

### Any other comments?
No.

---

## 6. Distribution

### Will the dataset be distributed to third parties outside of the entity on behalf of which the dataset was created?
Yes. The dataset is publicly released.

### How will the dataset be distributed?
Via [TODO: Zenodo / HuggingFace Datasets URL and DOI].

### When will the dataset be distributed?
[TODO: Release date.]

### Will the dataset be distributed under a copyright or other intellectual property (IP) license, and/or under applicable terms of use (ToU)?
Yes. The dataset is released under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International** (CC BY-NC-SA 4.0) license. See `LICENSE`.

### Have any third parties imposed IP-based or other restrictions on the data associated with the instances?
[TODO: If source archives or transcription repositories imposed restrictions.]

### Do any export controls or other regulatory restrictions apply to the dataset or to individual instances?
No.

### Any other comments?
No.

---

## 7. Maintenance

### Who will be supporting/hosting/maintaining the dataset?
[TODO: Responsible lab/institution.]

### How can the owner/curator/manager of the dataset be contacted?
[TODO: Contact email or issue tracker URL.]

### Is there an erratum?
Not yet. Errata will be published in the repository's issue tracker or a dedicated `ERRATA.md` file.

### Will the dataset be updated?
Future releases may include:
- Additional books or scripts
- Per-line cropped images (currently only full-page images are guaranteed)
- Continuous rotation angles instead of coarse classes
- Semi-automated margin anchor assignment for the remaining ~30% of unanchored margin lines

### If others want to extend/augment/build on/contribute to the dataset, is there a mechanism for them to do so?
Contributions are welcome via the GitHub repository. Proposed additions must pass the validation script (`scripts/validate_dataset.py`) and adhere to the JSON Schema.

### Any other comments?
No.
