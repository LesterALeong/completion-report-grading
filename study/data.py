"""Small file readers shared by offline validation and the call runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases(split: str) -> list[dict[str, Any]]:
    if split not in {"development", "holdout"}:
        raise ValueError(f"unknown split: {split}")
    return read_json(ROOT / "cases" / f"{split}.json")


def load_protocol() -> dict[str, Any]:
    return read_json(ROOT / "protocol.json")
