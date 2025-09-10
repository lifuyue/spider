from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from .base import Sink


class CSVSink(Sink):
    def __init__(self, cfg: Dict) -> None:
        self.path = Path(cfg["path"])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = open(self.path, "a", newline="", encoding="utf-8")
        self.writer = None

    def emit(self, item: dict) -> None:
        if self.writer is None:
            self.writer = csv.DictWriter(self.file, fieldnames=list(item.keys()))
            if self.file.tell() == 0:
                self.writer.writeheader()
        self.writer.writerow(item)
        self.file.flush()

