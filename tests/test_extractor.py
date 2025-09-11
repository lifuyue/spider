from crawler_core.extractor import Extractor
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

