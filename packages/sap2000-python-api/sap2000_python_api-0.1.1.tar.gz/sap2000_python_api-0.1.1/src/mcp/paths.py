from __future__ import annotations

from pathlib import Path

from .config import DEFAULT_ENV, EnvironmentConfig


def ensure_work_directories(env: EnvironmentConfig = DEFAULT_ENV) -> None:
    """Ensure that the expected directory structure exists."""
    env.work_dir.mkdir(parents=True, exist_ok=True)
    (env.work_dir / "html").mkdir(parents=True, exist_ok=True)
    (env.work_dir / "cards").mkdir(parents=True, exist_ok=True)
    (env.work_dir / "db").mkdir(parents=True, exist_ok=True)


def resolve_relative(path: str | Path, base: Path | None = None) -> Path:
    """Resolve a path relative to the work directory."""
    base_dir = base or DEFAULT_ENV.work_dir
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve()
