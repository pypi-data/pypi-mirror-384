from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvironmentConfig:
    """Holds critical environment configuration for the build pipeline."""

    chm_path: Path
    work_dir: Path
    dll_path: Path

    @staticmethod
    def from_env() -> "EnvironmentConfig":
        """Create configuration by reading expected environment variables."""

        def _require(name: str) -> Path:
            value = os.environ.get(name)
            if not value:
                raise EnvironmentError(f"Environment variable {name} is required")
            return Path(value).expanduser().resolve()

        return EnvironmentConfig(
            chm_path=_require("CHM_PATH"),
            work_dir=_require("WORK_DIR"),
            dll_path=_require("SAP2000_API_DLL"),
        )


DEFAULT_ENV = EnvironmentConfig(
    chm_path=Path(os.environ.get("CHM_PATH", "CSI_OAPI_Documentation.chm")).resolve(),
    work_dir=Path(os.environ.get("WORK_DIR", "build")).resolve(),
    dll_path=Path(os.environ.get("SAP2000_API_DLL", "SAP2000v1.dll")).resolve(),
)
