from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Tuple

from .logger import warn


class Dedupe:
    _seen: dict[str, set[Tuple[Any, ...]]] = defaultdict(set)
    _warned: set[str] = set()

    @classmethod
    def seen(cls, item: Dict[str, Any], items_cfg: Dict[str, Any]) -> bool:
        name = item.get("__type__")
        if not name or name not in items_cfg:
            return False
        icfg = items_cfg[name]
        keys = icfg.get("dedupe_keys", [])
        if not keys:
            if name not in cls._warned:
                warn("dedupe", item=name, err="NO_KEYS")
                cls._warned.add(name)
            return True
        key = tuple(item.get(k) for k in keys)
        if all(v in (None, "") for v in key):
            if name not in cls._warned:
                warn("dedupe", item=name, err="EMPTY_KEY")
                cls._warned.add(name)
            return True
        seen = cls._seen.setdefault(name, set())
        if key in seen:
            return True
        seen.add(key)
        return False
