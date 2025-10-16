from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from .logging_utils import configure_logging


def decompile_chm(chm_path: Path, output_dir: Path, overwrite: bool = False) -> None:
    """Invoke Microsoft's HTML Help compiler to extract CHM contents."""
    logger = configure_logging(level=logging.INFO, logger_name=__name__)
    chm_path = chm_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    if not chm_path.exists():
        raise FileNotFoundError(f"CHM file not found: {chm_path}")

    if overwrite and output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Decompiling CHM %s -> %s", chm_path, output_dir)
    subprocess.run(
        ["hh.exe", "-decompile", str(output_dir), str(chm_path)],
        check=True,
        capture_output=False,
    )
    logger.info("CHM decompilation complete.")
