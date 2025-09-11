from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo


class Normalizer:
    @staticmethod
    def run(item: Dict[str, Any], item_cfg: Dict[str, Any]) -> Dict[str, Any]:
        # Apply normalize ops based on any matching field spec across items
        for _iname, icfg in item_cfg.items():
            for name, field_cfg in icfg.get("fields", {}).items():
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
        if op == "to_int":
            try:
                if isinstance(value, str):
                    return int(value)
                return int(value)
            except Exception:
                m = re.search(r"[-+]?\d+", str(value))
                return int(m.group(0)) if m else value
        if op == "to_float":
            try:
                if isinstance(value, str):
                    return float(value)
                return float(value)
            except Exception:
                m = re.search(r"[-+]?\d+(?:\.\d+)?", str(value))
                return float(m.group(0)) if m else value
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
        if op.startswith("join:"):
            sep = op.split(":", 1)[1]
            # best-effort to unescape common escapes like \n, \t
            sep = sep.encode("utf-8").decode("unicode_escape")
            if isinstance(value, list):
                return sep.join(str(v) for v in value)
            return value
        if op.startswith("regex_extract:"):
            pattern = op.split(":", 1)[1]
            m = re.search(pattern, str(value))
            if m:
                return m.group(1) if m.groups() else m.group(0)
            return value
        return value
