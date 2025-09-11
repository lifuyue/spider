from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REQUIRED_FIELDS = ["name", "base_url", "entrypoints", "items", "pipelines"]


class Config(dict):
    """Simple dict-based config object supporting attribute access."""

    __getattr__ = dict.get  # type: ignore


def load_and_validate(path: str) -> Config:
    cfg_path = Path(path)
    raw = cfg_path.read_text()
    data: Dict[str, Any]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: allow YAML in .yml/.yaml files
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(raw)
        except Exception as e:  # pragma: no cover - optional dependency path
            raise ValueError(f"Failed to parse config as JSON or YAML: {e}")
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"missing field: {field}")
    return Config(data)


__all__ = ["Config", "load_and_validate"]
