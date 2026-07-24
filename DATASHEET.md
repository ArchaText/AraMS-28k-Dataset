# AraMS-28k Datasheet

This datasheet follows the framework proposed by Gebru et al., "Datasheets for Datasets" (2021), to document the composition, collection process, and intended use of AraMS-28k.

---

## 1. Motivation

### For what purpose was the dataset created?
AraMS-28k was created to provide line-level training and evaluation data for handwritten text recognition (HTR) models targeting historical Arabic manuscripts. Existing public corpora for this domain were either too small (RASM2018, ~120 pages), lacked layout annotations (Muharaf), or consisted of modern rather than historical material (KHATT). AraMS-28k fills the gap by offering the first publicly released large-scale line-level dataset of genuine historical Arabic manuscripts with explicit main/margin layout labels and insertion anchors.

### Who created the dataset and on whose behalf?
[TODO: Author names and affiliations]. The dataset was created as part of the RefLAM (Reference-grounded Line Annotation for Manuscripts) research project.

### Who funded the creation of the dataset?

### Any other comments?
No.

---

## 2. Composition

### What do the instances that comprise the dataset represent?
Each instance is a single text line extracted from a digitised historical Arabic manuscript page. An instance includes:
- A bounding geometry (baseline, boundary polygon, or axis-aligned bounding box) locating the line on the page image.
- A validated ground-truth transcription (`gt_raw`), drawn from a fully diacritised scholarly edition, plus a diacritic-normalised counterpart (`gt_normalized`).
- A raw MLLM OCR hypothesis (`gemini_raw`), retained for reference but never used as ground truth.
- Layout metadata: line type (`main` or `margin`) and, for margin lines, insertion-anchor metadata (`margin_anchor`) recording where the line inserts into the main-text reading order.
- Review metadata recording whether the line was edited, validated, deleted, or part of a fully reviewed page.

### How many instances are there in total?
**28,600 line annotations** across 3,043 pages from 14 books:
- 27,971 main-text lines
- 629 margin lines

### Does the dataset contain all possible instances or is it a sample?
The dataset contains all lines from the selected pages of each book. Books were chosen to maximise diversity across script style (Naskh, Ruq'ah, Maghrebi, plus one lithographed printed edition), diacritisation level, scan quality, and layout complexity. It is not a random sample of all Arabic manuscripts.

### What data does each instance consist of?
Each instance is a JSON record. See `schema/line_record.schema.json` for the formal schema. Key fields include:
- `line_uid`, `book_id`, `page_id`, `page_image`, `line_idx`
- `line_type`: `"main"` or `"margin"`
- `split`: `"train"`, `"val"`, or `"test"`
- `text`: `{gt_raw, gemini_raw, gt_normalized, confidence}`
- `geometry`: `{baseline, boundary_polygon, bounding_box}` (null where not applicable)
- `margin_anchor`: `{before, after, line, rotation}` — populated only for margin lines; `null` for main lines
- `review`: `{edited, validated, deleted, page_reviewed}`

### Is there a label or target associated with each instance?
Yes. The primary label is `gt_raw` (or its normalised counterpart `gt_normalized`, the recommended training target — see Section 4). Secondary labels include `line_type` and, for margin lines, `margin_anchor.line`.

### Is any information missing from individual instances?
- `margin_anchor` fields are `null` for approximately 70% of margin lines (440 of 629), where assignment was editorially ambiguous (ownership stamps, later commentaries, or placements with no unambiguous attachment point). A confident anchor is assigned for the remaining ≈30% (189 of 629 margin lines).
- `geometry.baseline` / `boundary_polygon` are null for the small subset of lines (~2% of main lines, concentrated in book_27) stored only as axis-aligned bounding boxes.

### Are relationships between individual instances made explicit?
Yes. Within a page, `line_idx` gives the top-to-bottom reading order for main-text lines. For margin lines with a confident anchor, `margin_anchor.line` explicitly links the margin line to the main-text line after which it logically inserts, recovering non-linear reading order.

### Are there recommended data splits?
Yes. The dataset is split at the book level:
- **Train**: 9 books (19,739 lines)
- **Validation**: 2 books (1,486 lines)
- **Test**: 3 books (6,744 lines)

Together these account for 27,969 of the corpus's 27,971 main-text lines; the remaining two lines were held out of all splits during final quality control and are documented in the release changelog. See `splits/*.txt` for exact book assignments.

### Are there any errors, sources of noise, or redundancies in the dataset?
- **OCR noise**: `gemini_raw` is an unvalidated MLLM hypothesis and may contain hallucinations, omissions, or merged lines. It is provided for research purposes, not as ground truth.
- **Segmentation noise**: a small fraction of lines required manual correction of predicted geometry.
- **Normalisation**: `gt_normalized` strips diacritics, kashida, and certain letter variants, which may obscure subtle orthographic distinctions; `gt_raw` is preserved for tasks that need the fully vocalised form.
- **Line-validated (LV) books**: for 7 of the 14 books (2,495 pages, 16,533 lines), only lines achieving a perfect alignment score against the reference were retained; lower-confidence lines were excluded rather than manually corrected. This subset is plausibly biased toward cleaner scans and more regular hands — see Section 5 for usage implications.

### Is the dataset self-contained, or does it link to or otherwise rely on external resources?
The dataset is self-contained. Page images are included. However, the reference transcriptions (`gt_raw`) originate from external scholarly digital text repositories or OCR over scanned printed editions; the dataset includes only the matched line-level spans, not the full source books.

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
3. **MLLM OCR** was generated by Google Gemini via zero-shot full-page calls, separating main-text from marginal content.
4. **Page anchoring** located each page within a book-level clean transcription via fuzzy 5-line window search.
5. **Line-level fuzzy alignment** matched each OCR line to a contiguous span in the reference text, producing a confidence score.
6. **Human review** confirmed, corrected, or excluded every line before release.

### What mechanisms or procedures were used to collect the data?
See the RefLAM paper (Section 3) for full algorithmic details, including the alignment metric and the Confidence-100 correctness guarantee. The pipeline is released alongside the dataset.

### If the dataset is a sample from a larger set, what was the sampling strategy?
Books were purposively selected to span three hand-copied script traditions (Naskh, Ruq'ah, Maghrebi) plus one lithographed printed edition, with varying scan quality and layout complexity. Pages within each selected book were processed exhaustively.

### Who was involved in the data collection process?
[TODO: Annotator names/roles if disclosable.]

### Over what timeframe was the data collected?
The full corpus (14 books, 3,043 pages, 28,600 lines) was constructed in approximately one month. [TODO: exact calendar dates, if disclosable.]

### Were any ethical review processes conducted?
[TODO: If applicable.]

### Did you collect the data from the individuals in question directly, or obtain it via third parties or other sources?
Page images were obtained from third-party digitisation archives. Clean transcriptions were obtained from digital Arabic text repositories or produced by OCR over scanned printed editions.

### Was the data validated?
Yes. Two validation phases were conducted:
- **Page-validated (PV)**: 7 books, 548 pages, 11,438 main lines — every line on every page inspected by two independent reviewers, providing full manual verification of segmentation and transcription.
- **Line-validated (LV)**: 7 books, 2,495 pages, 16,533 lines — the automatic reference-alignment score is used as a formal acceptance filter; only main-text lines achieving a perfect alignment score are retained, and lines falling short are discarded rather than corrected.

### Any other comments?
No.

---

## 4. Preprocessing / Cleaning / Labelling

### Was any preprocessing/cleaning/labeling of the data done?
Yes:
- **Polygon-to-rectangle conversion**: for a small subset of lines (concentrated in book_27, where a rule-based segmentation method produced predominantly rectangular output), boundary polygons were replaced with axis-aligned bounding boxes.
- **Diacritic-agnostic normalisation**: both OCR and reference text were normalised by stripping harakat, kashida, alef variants, etc., yielding `gt_normalized` from `gt_raw`.
- **Fuzzy alignment**: greedy line-to-reference matching with a character-level confidence score in [0, 100].
- **Human review**: geometry adjustment, transcription correction, and layout/anchor tag verification.

### Was the "raw" data saved in addition to the preprocessed/cleaned/labeled data?
Yes. `gt_raw` (fully diacritised reference) and `gemini_raw` (raw MLLM OCR hypothesis) are preserved alongside `gt_normalized`.

### Is the software used to preprocess/clean/label the instances available?
Yes. The RefLAM pipeline and browser-based review tool are released alongside the dataset. See the repository for `scripts/build_htr_data.py` and dataset-loading utilities.

### Any other comments?
No.

---

## 5. Uses

### Has the dataset been used for any tasks already?
Yes. The dataset was used to finetune and evaluate two Muharaf-pretrained HTR baselines on the held-out test split (3 books, 6,744 lines):
- **Kraken** (CNN-BLSTM-CTC): 23.31% CER overall (11.65%–32.71% per test book)
- **HATFormer** (Transformer-based): 26.74% CER overall (13.26%–37.88% per test book)

### Is there a repository that links to any or all papers or systems that use the dataset?
[TODO: Link to benchmark leaderboard or paper list if created.]

### What (other) tasks could the dataset be used for?
- Historical Arabic handwritten text recognition (HTR) training and benchmarking
- Layout analysis (main/margin detection, insertion-anchor prediction)
- Diacritisation restoration (comparing `gt_raw` with `gt_normalized`)
- OCR error analysis and post-correction
- Script style classification (Naskh vs. Ruq'ah vs. Maghrebi)
- Margin annotation and non-linear reading-order recovery
- Weak/distant supervision research (reference-grounded alignment)

### Is there anything about the composition of the dataset or the way it was collected and preprocessed/cleaned/labeled that might impact future uses?
- The line-validated (LV) subset is conditioned on perfect automatic alignment, which plausibly biases it toward cleaner scans and more regular hands; PV and LV statistics should be considered separately rather than merged.
- The dataset is not balanced across scripts or books.
- Margin lines are a small fraction of the corpus (629 of 28,600, ≈2.2%); tasks requiring balanced main/margin examples (e.g., margin-detection training) should account for this imbalance, for instance via resampling or class weighting.
- Roughly 70% of margin lines lack a confident insertion anchor, by design; a null anchor should be treated as "no confident attachment point exists," not as a missing/incomplete label.
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
- Continuous rotation angles instead of coarse classes
- Semi-automated margin-anchor assignment for the remaining ~70% of unanchored margin lines

No further manuscript books are currently planned for addition; extensions to new scripts or languages, if undertaken, will be released as a distinct dataset.

### If others want to extend/augment/build on/contribute to the dataset, is there a mechanism for them to do so?
Contributions are welcome via the GitHub repository. Proposed additions must pass the validation script and adhere to the JSON Schema (`schema/line_record.schema.json`).

### Any other comments?
No.
