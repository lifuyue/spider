from crawler_core.extractor import Extractor
from crawler_core.types import Response
from crawler_core.config import load_and_validate


HTML = """
<html><body>
<h1 class="title">Hello World</h1>
<time datetime="2023-01-02 03:04"></time>
<article><p>content</p></article>
<div class="tags"><a>t1</a><a>t2</a></div>
</body></html>
"""


def test_extractor_basic():
    cfg = load_and_validate("configs/site_demo.yml")
    resp = Response(url="https://news.example.com/article/1", status=200, text=HTML)
    links, items = Extractor.parse(resp, cfg)
    assert items[0]["title"] == "Hello World"
    assert items[0]["published_at"] == "2023-01-02 03:04"
    assert items[0]["tags"] == ["t1", "t2"]

