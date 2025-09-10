from datetime import datetime

from crawler_core.normalizer import Normalizer


def test_datetime_and_tz():
    dt = Normalizer.apply("2023-01-02 03:04", "to_datetime:%Y-%m-%d %H:%M")
    dt = Normalizer.apply(dt, "to_tz:Asia/Shanghai")
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_trim_lower():
    val = Normalizer.apply("  HeLLo ", "trim")
    val = Normalizer.apply(val, "lower")
    assert val == "hello"


def test_sanitize_html():
    html = Normalizer.apply("<article><script>x</script><p>hi</p></article>", "sanitize_html")
    assert "script" not in html

