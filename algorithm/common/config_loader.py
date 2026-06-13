"""Loads conf/application-local.yml. Used by both training and inference."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_PATH = "E:/End-To-End_Recommendation_System_X/conf/application-local.yml"


def load_config(path: str | None = None) -> Dict[str, Any]:
    p = Path(path or os.environ.get("RECSYS_CONFIG", DEFAULT_PATH))
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_CACHED: Dict[str, Any] | None = None


def get_config() -> Dict[str, Any]:
    global _CACHED
    if _CACHED is None:
        _CACHED = load_config()
    return _CACHED
