from __future__ import annotations

import urllib.request

from .types import Request, Response


class Fetcher:
    def __init__(self, cfg) -> None:
        req = cfg.get("request", {})
        self.headers = dict(req.get("headers", {}))
        ua = self.headers.get("User-Agent")
        if ua and "ua.random" in ua:
            # simple fallback UA if template placeholder is used
            self.headers["User-Agent"] = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )

    def get(self, req: Request) -> Response:
        req_obj = urllib.request.Request(req.url, headers=self.headers)
        with urllib.request.urlopen(req_obj) as resp:  # pragma: no cover - network
            text = resp.read().decode("utf-8", errors="ignore")
            return Response(url=req.url, status=resp.status, text=text)
