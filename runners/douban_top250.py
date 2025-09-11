import os
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from crawler_core.engine import run

if __name__ == "__main__":
    cfg = root / "configs" / "douban_top250.yml"
    assert cfg.exists(), f"config not found: {cfg}"
    # 允许从环境变量控制 dry-run（默认 False）
    dry = os.getenv("DRY_RUN", "false").lower() in ("1","true","yes")
    run(str(cfg), dry_run=dry)

