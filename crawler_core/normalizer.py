from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo


class Normalizer:
    @staticmethod
    def run(item: Dict[str, Any], item_cfg: Dict[str, Any]) -> Dict[str, Any]:
        for name, field_cfg in item_cfg.get("Article", {}).get("fields", {}).items():
            if name in item:
                value = item[name]
                for op in field_cfg.get("normalize", []):
                    value = Normalizer.apply(value, op)
                item[name] = value
        return item

    @staticmethod
    def apply(value: Any, op: str) -> Any:
        if value is None:
            return value
        if op == "trim":
            return value.strip() if isinstance(value, str) else value
        if op == "lower":
            return value.lower() if isinstance(value, str) else value
        if op.startswith("to_datetime:"):
            fmt = op.split(":", 1)[1]
            return datetime.strptime(value, fmt)
        if op.startswith("to_tz:"):
            tz = op.split(":", 1)[1]
            if isinstance(value, datetime):
                return value.replace(tzinfo=ZoneInfo(tz))
            return value
        if op == "sanitize_html":
            return re.sub(r"<script.*?>.*?</script>", "", value, flags=re.S)
        if op == "strip_ads":
            return value
        if op.startswith("split:"):
            sep, idx = op.split(":", 1)[1].split("->")
            parts = value.split(sep)
            return parts[int(idx)] if len(parts) > int(idx) else value
        return value

