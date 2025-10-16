from __future__ import annotations

import os
from pathlib import Path

from mcp.api import find_functions, FindFunctionsRequest


def _db_exists() -> bool:
    work_dir = Path(os.environ.get("WORK_DIR", "build")).resolve()
    return (work_dir / "db" / "sap2000_mcp.db").exists()


def test_find_functions_smoke():
    assert _db_exists(), "DB not found; build the database before tests"
    data = find_functions(FindFunctionsRequest(q="point coord cartesian", top_k=3)).model_dump()
    assert "results" in data
    assert len(data["results"]) >= 1
    # Ensure scoring field present
    r0 = data["results"][0]
    assert isinstance(r0.get("score"), int)
