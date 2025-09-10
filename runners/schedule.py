import argparse
import glob

from crawler_core.engine import run


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True)
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    for path in glob.glob(args.glob):
        run(path)

