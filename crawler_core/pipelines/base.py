from __future__ import annotations

from typing import List


class Sink:
    def emit(self, item: dict) -> None:  # pragma: no cover - interface
        raise NotImplementedError


def build_sinks(cfg_list) -> List[Sink]:
    sinks: List[Sink] = []
    for cfg in cfg_list:
        if cfg["type"] == "csv":
            from .csv_sink import CSVSink

            sinks.append(CSVSink(cfg))
        elif cfg["type"] in {"db"}:
            from .pg_sink import PgSink

            sinks.append(PgSink(cfg))
    return sinks

