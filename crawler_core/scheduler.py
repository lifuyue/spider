from __future__ import annotations

from typing import Iterable, List

from .types import Request


class Scheduler:
    """Very small in-memory FIFO scheduler with dedupe and retry."""

    def __init__(self, cfg) -> None:
        self.queue: List[Request] = []
        self.pending: set[str] = set()
        self.visited: set[str] = set()
        req_cfg = (
            getattr(cfg, "request", {})
            if hasattr(cfg, "request")
            else cfg.get("request", {})
        )
        retry_cfg = req_cfg.get("retry", {})
        self.max_attempts = retry_cfg.get("max_attempts", 3)

    # ------------------------------------------------------------------
    def _maybe_enqueue(self, url: str) -> None:
        if url in self.visited or url in self.pending:
            return
        self.queue.append(Request(url))
        self.pending.add(url)

    def seed(self, entrypoints: Iterable[dict]) -> None:
        for ep in entrypoints:
            if "url" in ep:
                self._maybe_enqueue(ep["url"])
            elif "url_template" in ep and "range" in ep:
                r = ep["range"]
                start, stop, step = r["start"], r["stop"], r.get("step", 1)
                for page in range(start, stop, step):
                    url = ep["url_template"].replace("{{page}}", str(page))
                    self._maybe_enqueue(url)

    def has_next(self) -> bool:
        return bool(self.queue)

    def next(self) -> Request:
        req = self.queue.pop(0)
        self.pending.discard(req.url)
        self.visited.add(req.url)
        return req

    def enqueue(self, links: Iterable[str]) -> None:
        for url in links:
            self._maybe_enqueue(url)

    def defer(self, req: Request, _err: Exception) -> None:
        if req.attempts + 1 >= self.max_attempts:
            return
        req.attempts += 1
        self.queue.append(req)
        self.pending.add(req.url)
