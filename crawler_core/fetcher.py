from __future__ import annotations

import urllib.request

from .types import Request, Response


class Fetcher:
    def __init__(self, cfg) -> None:
        self.headers = cfg.get("request", {}).get("headers", {})

    def get(self, req: Request) -> Response:
        req_obj = urllib.request.Request(req.url, headers=self.headers)
        with urllib.request.urlopen(req_obj) as resp:  # pragma: no cover - network
            text = resp.read().decode("utf-8", errors="ignore")
            return Response(url=req.url, status=resp.status, text=text)

