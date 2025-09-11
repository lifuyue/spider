from __future__ import annotations

from .config import load_and_validate
from .scheduler import Scheduler
from .fetcher import Fetcher
from .extractor import Extractor
from .normalizer import Normalizer
from .dedupe import Dedupe
from .pipelines.base import build_sinks
from .telemetry import Telemetry


def run(config_path: str, dry_run: bool = False) -> None:
    cfg = load_and_validate(config_path)
    telem = Telemetry()
    sched = Scheduler(cfg)
    fetch = Fetcher(cfg)
    sinks = [] if dry_run else build_sinks(cfg["pipelines"])

    sched.seed(cfg["entrypoints"])
    total_items = 0
    while sched.has_next():
        req = sched.next()
        try:
            resp = fetch.get(req)
            links, items = Extractor.parse(resp, cfg)
            for it in items:
                it = Normalizer.run(it, cfg["items"])
                if not Dedupe.seen(it, cfg["items"]):
                    for s in sinks:
                        s.emit(it)
            total_items += len(items)
            sched.enqueue(links)
            telem.mark_success()
        except Exception as e:  # pragma: no cover - simplified error path
            telem.mark_error(e)
            sched.defer(req, e)
    print(f"parsed {total_items} items, successes={telem.success}, errors={telem.errors}")

