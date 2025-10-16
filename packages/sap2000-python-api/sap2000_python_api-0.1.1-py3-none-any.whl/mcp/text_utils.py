from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Set

WHITESPACE_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^0-9a-z]+")


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim."""
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_ascii(text: str) -> str:
    """Normalize to NFC then ASCII, lowercased."""
    normalized = unicodedata.normalize("NFC", text).lower()
    return normalized


def normalize_for_index(text: str) -> str:
    """
    Normalize text for FTS indexing.

    - Lowercase
    - Remove non word characters (replace with space)
    - Collapse whitespace
    """
    lowered = normalize_ascii(text)
    stripped = NON_WORD_RE.sub(" ", lowered)
    return normalize_whitespace(stripped)


def generate_char_ngrams(text: str, n: int = 3) -> List[str]:
    """
    Generate sorted unique character n-grams for text.
    Spaces are removed before generating n-grams to
    emphasize contiguous sequences of letters/numbers.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    normalized = normalize_for_index(text).replace(" ", "")
    grams: Set[str] = set()
    for i in range(len(normalized) - n + 1):
        grams.add(normalized[i : i + n])
    return sorted(grams)


def build_fts_document(parts: Iterable[str]) -> str:
    """
    Build a normalized FTS document from string parts.
    """
    combined = " ".join(part for part in parts if part)
    return normalize_for_index(combined)
