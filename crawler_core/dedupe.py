from __future__ import annotations

from typing import Any, Dict, Tuple


class Dedupe:
    _seen: set[Tuple[Any, ...]] = set()

    @classmethod
    def seen(cls, item: Dict[str, Any], items_cfg: Dict[str, Any]) -> bool:
        icfg = next(iter(items_cfg.values()))
        keys = icfg.get("dedupe_keys", [])
        key = tuple(item.get(k) for k in keys)
        if key in cls._seen:
            return True
        cls._seen.add(key)
        return False

