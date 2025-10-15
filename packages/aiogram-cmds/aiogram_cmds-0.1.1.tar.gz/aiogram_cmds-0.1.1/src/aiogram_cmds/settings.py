"""
Standalone settings for aiogram_cmds package.

This module provides settings dataclass and configuration loading
from pyproject.toml, making the library configurable without hardcoded values.
"""

from __future__ import annotations

import logging
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 compatibility

from pydantic import BaseModel, ConfigDict, field_validator


class CmdsSettings(BaseModel):
    """Configuration settings for command management."""

    model_config = ConfigDict(extra="ignore", frozen=True)
    languages: tuple[str, ...] = ("en",)
    fallback_language: str = "en"
    i18n_key_prefix: str = "cmd"
    profile: str = "default"
    menu_button: str = "commands"  # "commands" | "default"

    @field_validator("languages", mode="before")
    @classmethod
    def _ensure_nonempty(cls, v):
        if v is None:
            return ("en",)
        if isinstance(v, str):
            return (v,)
        if isinstance(v, (list, tuple)):
            return tuple(v) if v else ("en",)
        return ("en",)


def load_settings(pyproject_path: Path | None = None) -> CmdsSettings:
    """
    Load settings from [tool.aiogram_cmds] in pyproject.toml (if present).
    """
    p = pyproject_path or Path("pyproject.toml")
    if not p.exists():
        return CmdsSettings()
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        cfg = (data.get("tool") or {}).get("aiogram_cmds") or {}
        return CmdsSettings.model_validate(cfg)
    except Exception as ex:  # pragma: no cover
        logging.getLogger(__name__).warning(
            "aiogram_cmds: failed to load settings: %s", ex
        )
        return CmdsSettings()
