"""Pipeline runner.

Execute the entire ML pipeline end-to-end with a single command:

    python ml/data/download_dataset.py [--force-synthetic]
    python ml/data/prepare_diabetes.py
    python ml/data/split.py
    python ml/data/features.py
    python ml/models/train.py
    python ml/models/evaluate.py

or use this runner:

    python ml/run_all.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STEPS: list[tuple[str, list[str]]] = [
    ("download", ["python", "ml/data/download_dataset.py", "--force-synthetic"]),
    ("prepare", ["python", "ml/data/prepare_diabetes.py"]),
    ("split", ["python", "ml/data/split.py"]),
    ("features", ["python", "ml/data/features.py"]),
    ("train", ["python", "ml/models/train.py"]),
    ("evaluate", ["python", "ml/models/evaluate.py"]),
]


def run_all(skip: set[str] | None = None) -> int:
    skip = skip or set()
    for name, cmd in STEPS:
        if name in skip:
            print(f"== skipping {name} ==")
            continue
        print(f"\n== running {name} ==\n")
        ret = subprocess.call(cmd, cwd=PROJECT_ROOT)
        if ret != 0:
            print(f"!! {name} failed with code {ret}")
            return ret
    print("\n== ALL OK ==")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        help="Pipeline steps to skip (download, prepare, split, features, train, evaluate)",
    )
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Use Kaggle (creds required) instead of synthetic data",
    )
    args = parser.parse_args()

    skip = set(args.skip)
    if args.no_synthetic and "download" not in skip:
        STEPS[0] = ("download", ["python", "ml/data/download_dataset.py"])
    return run_all(skip)


if __name__ == "__main__":
    raise SystemExit(main())
