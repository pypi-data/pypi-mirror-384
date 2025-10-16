from __future__ import annotations

import json
import unicodedata
from typing import Any

JSON_SEPARATORS = (",", ":")


def dumps_sorted(value: Any) -> str:
    """Serialize value to JSON with deterministic ordering and NFC normalization."""
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=JSON_SEPARATORS)
    return unicodedata.normalize("NFC", text)
