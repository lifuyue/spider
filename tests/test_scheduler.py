from crawler_core.scheduler import Scheduler


def test_scheduler_prevents_duplicate_enqueue():
    sched = Scheduler({})
    sched.seed([{"url": "http://a"}])
    sched.enqueue(["http://a", "http://b", "http://b"])
    assert [r.url for r in sched.queue] == ["http://a", "http://b"]
    first = sched.next()
    assert first.url == "http://a"
    sched.enqueue(["http://a"])
    assert [r.url for r in sched.queue] == ["http://b"]
