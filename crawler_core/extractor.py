from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Any, Dict, List, Tuple

from .types import Response


class Extractor:
    """Very small extractor supporting a subset of CSS and regex."""

    @staticmethod
    def parse(resp: Response, cfg) -> Tuple[List[str], List[Dict[str, Any]]]:
        items: List[Dict[str, Any]] = []
        links: List[str] = []
        text = resp.text
        path = urlparse(resp.url).path
        for name, icfg in cfg.get("items", {}).items():
            match = icfg.get("match_url")
            if match and not re.search(match, path):
                continue
            data: Dict[str, Any] = {}
            for field, fcfg in icfg.get("fields", {}).items():
                value = None
                if fcfg.get("from") == "meta.url":
                    value = resp.url
                else:
                    for cand in fcfg.get("candidates", []):
                        value = Extractor._apply_candidate(text, cand)
                        if value not in (None, ""):
                            break
                data[field] = value
            items.append(data)
        return links, items

    @staticmethod
    def _apply_candidate(text: str, cand: Dict[str, Any]):
        if "css" in cand:
            expr = cand["css"]
            if expr == "article" and cand.get("as") == "html":
                m = re.search(r"<article[^>]*>(.*?)</article>", text, re.S)
                return m.group(0) if m else None
            if expr.endswith("::text"):
                expr = expr[:-6]
                if expr.startswith(".tags a"):
                    block = re.search(r"<div class=\"tags\">(.*?)</div>", text, re.S)
                    if block:
                        return re.findall(r"<a>(.*?)</a>", block.group(1))
                    return []
                tag, _, cls = expr.partition(".")
                if cls:
                    pattern = rf"<{tag}[^>]*class=\"[^\"]*{cls}[^\"]*\"[^>]*>(.*?)</{tag}>"
                else:
                    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
                m = re.search(pattern, text, re.S)
                return m.group(1).strip() if m else None
            if "::attr(" in expr:
                tag, _, attr = expr.partition("::attr(")
                attr = attr.rstrip(")")
                pattern = rf"<{tag}[^>]*{attr}=\"([^\"]+)\""
                m = re.search(pattern, text)
                return m.group(1) if m else None
        if "regex" in cand:
            m = re.search(cand["regex"], text)
            if m:
                return m.group(1) if m.groups() else m.group(0)
        return None

