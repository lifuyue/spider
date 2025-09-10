from __future__ import annotations

from typing import Iterable, List

from .types import Request


class Scheduler:
    """Very small in-memory FIFO scheduler."""

    def __init__(self, cfg) -> None:
        self.queue: List[Request] = []

    def seed(self, entrypoints: Iterable[dict]) -> None:
        for ep in entrypoints:
            if "url" in ep:
                self.queue.append(Request(ep["url"]))
            elif "url_template" in ep and "range" in ep:
                r = ep["range"]
                start, stop, step = r["start"], r["stop"], r.get("step", 1)
                for page in range(start, stop, step):
                    url = ep["url_template"].replace("{{page}}", str(page))
                    self.queue.append(Request(url))

    def has_next(self) -> bool:
        return bool(self.queue)

    def next(self) -> Request:
        return self.queue.pop(0)

    def enqueue(self, links: Iterable[str]) -> None:
        for url in links:
            self.queue.append(Request(url))

    def defer(self, req: Request, _err: Exception) -> None:
        self.queue.append(req)

