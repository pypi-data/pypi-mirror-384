from __future__ import annotations

import logging
import sys
from typing import Optional


def configure_logging(level: int = logging.INFO, logger_name: Optional[str] = None) -> logging.Logger:
    """Configure structured logging for CLI and scripts."""
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
