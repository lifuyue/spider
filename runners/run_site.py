import argparse

from crawler_core.engine import run


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(args.config, dry_run=args.dry_run)

