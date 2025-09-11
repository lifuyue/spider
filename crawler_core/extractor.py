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

        soup = None
        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(text, "html.parser")
        except Exception:
            soup = None

        for name, icfg in cfg.get("items", {}).items():
            match = icfg.get("match_url")
            if match and not re.search(match, path):
                continue

            container_selector = icfg.get("list_selector")
            if not container_selector:
                # backward compatible heuristic for Douban list
                for _field, fcfg in icfg.get("fields", {}).items():
                    for cand in fcfg.get("candidates", []):
                        sel = cand.get("css")
                        if isinstance(sel, str) and "ol.grid_view li" in sel:
                            container_selector = "ol.grid_view li"
                            break
                    if container_selector:
                        break

            if soup is not None and container_selector:
                nodes = soup.select(container_selector)
                for node in nodes:
                    data: Dict[str, Any] = {"__type__": name}
                    for field, fcfg in icfg.get("fields", {}).items():
                        value = None
                        if fcfg.get("from") == "meta.url":
                            value = resp.url
                        else:
                            for cand in fcfg.get("candidates", []):
                                value = Extractor._apply_candidate_bs(node, cand, container_selector)
                                if value not in (None, "", []):
                                    break
                        data[field] = value
                    items.append(data)
            else:
                # Fallback: single-item extraction using simplistic CSS/regex rules
                data: Dict[str, Any] = {"__type__": name}
                for field, fcfg in icfg.get("fields", {}).items():
                    value = None
                    if fcfg.get("from") == "meta.url":
                        value = resp.url
                    else:
                        for cand in fcfg.get("candidates", []):
                            if soup is not None and "css" in cand:
                                value = Extractor._apply_candidate_bs(soup, cand, None)
                            else:
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

    @staticmethod
    def _apply_candidate_bs(root, cand: Dict[str, Any], container_sel: str | None):
        # root can be BeautifulSoup object or a Tag (node)
        if "css" in cand:
            expr = cand["css"]
            as_list = cand.get("as") == "list"
            # handle ::text and ::attr()
            attr_name = None
            if expr.endswith("::text"):
                expr = expr[:-6]
            elif "::attr(" in expr:
                base, _, attr = expr.partition("::attr(")
                expr = base
                attr_name = attr.rstrip(")")
            # make selector relative by removing container prefix if present
            if container_sel and expr.startswith(container_sel + " "):
                expr = expr[len(container_sel) + 1 :]

            try:
                matches = root.select(expr)
            except Exception:
                matches = []

            if not matches:
                return [] if as_list else None

            if attr_name:
                vals = [m.get(attr_name) for m in matches if m and m.get(attr_name) is not None]
                return vals if as_list else (vals[0] if vals else None)

            # text extraction
            if as_list:
                texts: List[str] = []
                for m in matches:
                    # collect stripped strings under each match
                    for s in m.stripped_strings:
                        texts.append(s)
                return texts
            else:
                # First match text
                m = matches[0]
                return m.get_text(strip=True)
        if "regex" in cand:
            text = getattr(root, "text", None)
            if text is None:
                text = str(root)
            m = re.search(cand["regex"], text)
            if m:
                return m.group(1) if m.groups() else m.group(0)
        return None
