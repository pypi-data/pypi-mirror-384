from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from mcp.api import to_python, ToPythonRequest


def _db_path() -> Path:
    work_dir = Path(os.environ.get("WORK_DIR", "build")).resolve()
    return work_dir / "db" / "sap2000_mcp.db"


def _find_function_id_by_name(name: str) -> int | None:
    db = _db_path()
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute("SELECT id FROM functions WHERE name = ? LIMIT 1", (name,)).fetchone()
        return int(row[0]) if row else None
    finally:
        conn.close()


def test_to_python_signature_smoke():
    db = _db_path()
    assert db.exists(), "DB not found; build the database before tests"
    fid = _find_function_id_by_name("GetCoordCartesian") or _find_function_id_by_name("ApplyEditedTables")
    assert fid is not None, "Expected function name not present in DB"

    data = to_python(ToPythonRequest(function_id=fid, binding_mode="direct")).model_dump()
    assert "signature" in data
    assert data["signature"].startswith("ret,") or data["signature"].startswith("ret =") or " = " in data["signature"]
