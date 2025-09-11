from crawler_core.extractor import Extractor
from crawler_core.types import Response
from crawler_core.config import load_and_validate

HTML = """
<html><body>
<div class="quote">
  <span class="text">“A witty saying proves nothing.”</span>
  <small class="author">Voltaire</small>
  <div class="tags"><a class="tag">wit</a><a class="tag">philosophy</a></div>
</div>
</body></html>
"""


def test_extractor_basic():
    cfg = load_and_validate("configs/site_demo.yml")
    resp = Response(url="http://quotes.toscrape.com/page/1/", status=200, text=HTML)
    links, items = Extractor.parse(resp, cfg)
    assert items[0]["text"] == "“A witty saying proves nothing.”"
    assert items[0]["author"] == "Voltaire"
    assert items[0]["tags"] == ["wit", "philosophy"]


def test_list_selector_extracts_multiple_items():
    html = "<ul><li><span>A</span></li><li><span>B</span></li></ul>"
    cfg = {
        "items": {
            "Demo": {
                "list_selector": "li",
                "fields": {
                    "title": {"candidates": [{"css": "span::text"}]}
                },
            }
        }
    }
    resp = Response(url="http://x", status=200, text=html)
    _, items = Extractor.parse(resp, cfg)
    assert len(items) == 2
    assert items[0]["title"] == "A"
    assert items[1]["title"] == "B"
