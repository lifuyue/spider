from __future__ import annotations

from .config import load_and_validate
from .scheduler import Scheduler
from .fetcher import Fetcher
from .extractor import Extractor
from .normalizer import Normalizer
from .dedupe import Dedupe
from .pipelines.base import build_sinks
from .telemetry import Telemetry
from .types import Response


def run(config_path: str, dry_run: bool = False) -> None:
    cfg = load_and_validate(config_path)
    entrypoints = (
        getattr(cfg, "entrypoints", [])
        if hasattr(cfg, "entrypoints")
        else (cfg.get("entrypoints", []) if isinstance(cfg, dict) else [])
    )
    if dry_run:
        print(
            f"[dry-run] config OK. entrypoints={len(entrypoints)}. skipping network fetch."
        )
        return

    telem = Telemetry()
    sched = Scheduler(cfg)
    fetch = Fetcher(cfg)
    sinks = build_sinks(cfg["pipelines"])

    sched.seed(entrypoints)
    total_items = 0
    while sched.has_next():
        req = sched.next()
        try:
            resp_dict = fetch.get(req)
            if resp_dict.get("error"):
                telem.mark_error(Exception(resp_dict.get("error")))
                sched.defer(req, Exception(resp_dict.get("error")))
                continue
            resp = Response(
                url=resp_dict.get("url", ""),
                status=resp_dict.get("status", 0),
                text=resp_dict.get("text", ""),
            )
            links, items = Extractor.parse(resp, cfg)
            for it in items:
                it = Normalizer.run(it, cfg["items"])
                if not Dedupe.seen(it, cfg["items"]):
                    it.pop("__type__", None)
                    for s in sinks:
                        s.emit(it)
                    telem.mark_emit()
            total_items += len(items)
            sched.enqueue(links)
            telem.mark_success()
        except Exception as e:  # pragma: no cover - simplified error path
            telem.mark_error(e)
            sched.defer(req, e)
    print(
        f"summary: success={telem.success} errors={telem.errors} emitted={telem.emitted}"
    )

