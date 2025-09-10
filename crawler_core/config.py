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
    data: Dict[str, Any] = json.loads(cfg_path.read_text())
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"missing field: {field}")
    return Config(data)


__all__ = ["Config", "load_and_validate"]
