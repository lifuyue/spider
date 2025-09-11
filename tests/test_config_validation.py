import json
import pathlib

import pytest

from crawler_core.config import load_and_validate


def test_valid_config():
    cfg = load_and_validate("configs/site_demo.yml")
    assert cfg.name == "quotes_demo"


def test_invalid_config(tmp_path: pathlib.Path):
    bad = tmp_path / "bad.yml"
    bad.write_text("base_url: 'https://x.com'")
    with pytest.raises(Exception):
        load_and_validate(str(bad))

