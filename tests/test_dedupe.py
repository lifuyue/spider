from crawler_core.dedupe import Dedupe


def test_dedupe_skips_duplicates():
    Dedupe._seen.clear()
    items_cfg = {"Quote": {"dedupe_keys": ["url"]}}
    item1 = {"__type__": "Quote", "url": "u1"}
    item2 = {"__type__": "Quote", "url": "u1"}
    assert Dedupe.seen(item1, items_cfg) is False
    assert Dedupe.seen(item2, items_cfg) is True
