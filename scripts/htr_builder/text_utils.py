"""Text normalization helpers for HTR targets."""

import re

# Tashkil (harakat + shadda + tanwin + tatweel).
_TASHKIL = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]"
)
# Keep only Arabic letters (0621-063A, 0641-064A) and spaces.
_KEEP = re.compile(r"[^\u0621-\u063A\u0641-\u064A ]")


def clean_gt(text):
    """Normalize the training target text."""
    text = _TASHKIL.sub("", text)
    text = _KEEP.sub("", text)
    text = re.sub(r" +", " ", text).strip()
    return text
