from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def _db_path() -> Path:
    work_dir = Path(os.environ.get("WORK_DIR", "build")).resolve()
    return work_dir / "db" / "sap2000_mcp.db"


def test_rowid_parity_and_counts():
    db = _db_path()
    if not db.exists():
        raise RuntimeError(f"Database not found: {db}")
    conn = sqlite3.connect(str(db))
    try:
        cur = conn.execute("SELECT COUNT(*) FROM functions")
        n = cur.fetchone()[0]
        assert n > 0
        assert conn.execute("SELECT COUNT(*) FROM fts").fetchone()[0] == n
        assert conn.execute("SELECT COUNT(*) FROM fts_gram").fetchone()[0] == n
        assert conn.execute(
            "SELECT COUNT(*) FROM fts WHERE rowid NOT IN (SELECT id FROM functions)"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM fts_gram WHERE rowid NOT IN (SELECT id FROM functions)"
        ).fetchone()[0] == 0
    finally:
        conn.close()

