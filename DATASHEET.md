{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/TODO/AraMS-28k/schema/line_record.schema.json",
  "title": "AraMS-28k Line Record",
  "description": "Schema for a single line annotation in the AraMS-28k historical Arabic manuscript dataset.",
  "type": "object",
  "required": [
    "book_id",
    "page_id",
    "line_id",
    "line_type",
    "box",
    "gt_raw",
    "gemini_raw",
    "norm_gt",
    "norm_ocr",
    "confidence",
    "review_status",
    "image_path"
  ],
  "properties": {
    "book_id": {
      "type": "string",
      "description": "Book identifier, e.g., book_03",
      "pattern": "^book_[0-9]+$"
    },
    "page_id": {
      "type": "string",
      "description": "Page identifier, e.g., book_03_page_001",
      "pattern": "^book_[0-9]+_page_[0-9]+$"
    },
    "line_id": {
      "type": "string",
      "description": "Globally unique line identifier, e.g., book_03_page_001_line_01"
    },
    "line_idx": {
      "type": "integer",
      "description": "Zero-based line index on the page, top-to-bottom reading order",
      "minimum": 0
    },
    "line_type": {
      "type": "string",
      "description": "Layout classification of the line",
      "enum": [
        "main",
        "margin"
      ]
    },
    "insertion_anchor": {
      "oneOf": [
        {
          "type": "integer",
          "description": "Index of the main-text line after which this margin line logically inserts",
          "minimum": 0
        },
        {
          "type": "null",
          "description": "No anchor assigned (editorially ambiguous, ownership stamp, later commentary, etc.)"
        }
      ]
    },
    "rotation": {
      "type": "string",
      "description": "Coarse text orientation class",
      "enum": [
        "horizontal",
        "N",
        "NE",
        "E",
        "SE",
        "S",
        "SW",
        "W",
        "NW"
      ]
    },
    "box": {
      "oneOf": [
        {
          "type": "object",
          "description": "Axis-aligned bounding box",
          "required": [
            "type",
            "x",
            "y",
            "w",
            "h"
          ],
          "properties": {
            "type": {
              "const": "bbox"
            },
            "x": {
              "type": "number",
              "minimum": 0
            },
            "y": {
              "type": "number",
              "minimum": 0
            },
            "w": {
              "type": "number",
              "minimum": 0
            },
            "h": {
              "type": "number",
              "minimum": 0
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "description": "Polygonal contour faithfully following the text line shape",
          "required": [
            "type",
            "vertices"
          ],
          "properties": {
            "type": {
              "const": "polygon"
            },
            "vertices": {
              "type": "array",
              "description": "Ordered sequence of [x, y] vertex pairs",
              "items": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "items": {
                  "type": "number",
                  "minimum": 0
                }
              },
              "minItems": 3
            }
          },
          "additionalProperties": false
        }
      ]
    },
    "gt_raw": {
      "type": "string",
      "description": "Clean reference transcription, typically from a scholarly edition (may include diacritics)"
    },
    "gemini_raw": {
      "type": "string",
      "description": "Raw MLLM OCR hypothesis before any correction"
    },
    "norm_gt": {
      "type": "string",
      "description": "Diacritic-agnostic normalised ground truth used for alignment"
    },
    "norm_ocr": {
      "type": "string",
      "description": "Diacritic-agnostic normalised OCR used for alignment"
    },
    "confidence": {
      "type": "integer",
      "description": "Fuzzy alignment confidence score in [0, 100]. A value of 100 guarantees character-for-character normalised-string identity (Confidence-100 rule).",
      "minimum": 0,
      "maximum": 100
    },
    "span_start": {
      "type": "integer",
      "description": "Inclusive start index in the flat reference word array for this book",
      "minimum": 0
    },
    "span_end": {
      "type": "integer",
      "description": "Exclusive end index in the flat reference word array for this book",
      "minimum": 0
    },
    "page_anchor_offset": {
      "type": "integer",
      "description": "Line offset in the reference text where the page anchor was detected",
      "minimum": 0
    },
    "review_status": {
      "type": "string",
      "description": "Human review outcome",
      "enum": [
        "confirmed",
        "corrected",
        "excluded",
        "pending"
      ]
    },
    "reviewer_notes": {
      "type": "string",
      "description": "Optional free-text notes from the human reviewer"
    },
    "image_path": {
      "type": "string",
      "description": "Relative path to the cropped line image, or the full page image if no per-line crop exists"
    },
    "page_image_path": {
      "type": "string",
      "description": "Relative path to the full page image"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of record creation"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of last modification"
    }
  },
  "additionalProperties": false
}