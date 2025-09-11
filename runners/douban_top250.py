import os
import pathlib
from crawler_core.engine import run

if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parents[1]
    cfg = root / "configs" / "douban_top250.yml"
    assert cfg.exists(), f"config not found: {cfg}"
    # 允许从环境变量控制 dry-run（默认 False）
    dry = os.getenv("DRY_RUN", "false").lower() in ("1","true","yes")
    run(str(cfg), dry_run=dry)

