from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import httpx

from .logger import info, warn, error


@dataclass
class FetchRequest:
    url: str
    headers: Optional[Dict[str, str]] = None
    method: str = "GET"
    data: Optional[bytes] = None


class Fetcher:
    """httpx based fetcher with minimal options."""

    client = httpx.Client(follow_redirects=True)

    def __init__(self, cfg: Any) -> None:
        req_cfg = (
            getattr(cfg, "request", {})
            if hasattr(cfg, "request")
            else cfg.get("request", {})
        )
        self.verify = req_cfg.get("verify", True)
        self.timeout = req_cfg.get("timeout_s", 15) or 15
        self.default_headers = {
            "User-Agent": "confdriven-crawler/0.1 (+https://example.local)",
            "Accept": "*/*",
        }

    # --- helpers ---------------------------------------------------------
    def _coerce(self, req: Union[FetchRequest, Dict[str, Any], str]) -> FetchRequest:
        if isinstance(req, FetchRequest):
            return req
        if isinstance(req, dict):
            return FetchRequest(url=req.get("url", ""), headers=req.get("headers"))
        if isinstance(req, str):
            return FetchRequest(url=req)
        if hasattr(req, "url"):
            return FetchRequest(url=getattr(req, "url"))
        return FetchRequest(url=str(req))

    def _file_fetch(self, url: str) -> Dict[str, Any]:
        path = urlparse(url).path
        p = Path(path)
        if not p.exists() and path.startswith("/workspace/spider"):
            root = Path(__file__).resolve().parent.parent
            p = root / Path(path).relative_to("/workspace/spider")
        if not p.exists():
            error("fetch", url=url, err="FILE_NOT_FOUND")
            return {"url": url, "error": "file not found", "status": 0, "headers": {}, "content": b"", "text": "", "elapsed": 0.0}
        start = time.time()
        body = p.read_bytes()
        elapsed = time.time() - start
        info("fetch", url=url, status=200, ms=int(elapsed * 1000))
        return {
            "url": url,
            "status": 200,
            "headers": {},
            "content": body,
            "text": body.decode("utf-8", errors="replace"),
            "elapsed": elapsed,
        }

    # --- public API ------------------------------------------------------
    def get(self, req: Union[FetchRequest, Dict[str, Any], str]):
        fr = self._coerce(req)
        url = fr.url
        if url.startswith("file://"):
            return self._file_fetch(url)

        headers = dict(self.default_headers)
        if fr.headers:
            headers.update(fr.headers)
        start = time.time()
        try:
            resp = self.client.request(
                fr.method,
                url,
                headers=headers,
                content=fr.data,
                timeout=self.timeout,
            )
        except httpx.HTTPError as e:
            if (not self.verify) and "certificate" in str(e).lower():
                warn("fetch", url=url, err="SSL_CERT")
                try:
                    resp = self.client.request(
                        fr.method,
                        url,
                        headers=headers,
                        content=fr.data,
                        timeout=self.timeout,
                        verify=False,
                    )
                except httpx.HTTPError as e2:
                    error("fetch", url=url, err="SSL_CERT")
                    return {
                        "url": url,
                        "error": str(e2),
                        "status": None,
                        "headers": {},
                        "content": b"",
                        "text": "",
                        "elapsed": time.time() - start,
                    }
            else:
                error("fetch", url=url, err=str(e))
                return {
                    "url": url,
                    "error": str(e),
                    "status": None,
                    "headers": {},
                    "content": b"",
                    "text": "",
                    "elapsed": time.time() - start,
                }
        body = resp.content
        elapsed = time.time() - start
        info("fetch", url=url, status=resp.status_code, ms=int(elapsed * 1000))
        return {
            "url": url,
            "status": resp.status_code,
            "headers": dict(resp.headers),
            "content": body,
            "text": body.decode(resp.encoding or "utf-8", errors="replace"),
            "elapsed": elapsed,
        }
