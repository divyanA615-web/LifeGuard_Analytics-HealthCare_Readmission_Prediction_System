"""Accountable dataset downloader for the LifeGuard readmission project.

This script does one thing well: it acquires the exact CSV files the ML
pipeline expects and places them under ml/data/raw/.

Sources it knows how to fetch:

1. Kaggle API   - https://www.kaggle.com/datasets/brandao/diabetes
   (requires ~/.kaggle/kaggle.json or env KAGGLE_USERNAME/KAGGLE_KEY)
2. Direct HTTP  - falls back to a manually downloaded file in ml/data/raw/incoming/
3. Synthetic    - as a last resort, generates a structurally similar CSV so
   you can run the prepare/ split/ train pipeline on day 1 without creds.

It also fetches the matching IDS_mapping.csv used by the pipeline.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml import DATA_RAW, DIABETES_FILENAME, MAPPING_FILENAME  # noqa

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

INCOMING_DIR = DATA_RAW / "incoming"

DATASETS = {
    "kaggle_slug": "brandao/diabetes",
    "kaggle_alternatives": [
        "https://archive.ics.uci.edu/ml/machine-learning-databases/00296/dataset_diabetes.zip",
    ],
    "primary_files_required": [DIABETES_FILENAME, MAPPING_FILENAME],
}


def using_kaggle() -> bool:
    """Check if Kaggle credentials are configured (env, file, or CLI)."""
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json.exists():
        return True
    if shutil.which("kaggle") is not None:
        return True
    return False


def fetch_via_kaggle(target: Path) -> bool:
    """Attempt to download the dataset using the Kaggle CLI."""
    try:
        import kaggle  # noqa: F401 - just verify import
    except ImportError:
        return False
    target.mkdir(parents=True, exist_ok=True)
    cmd = (
        f"kaggle datasets download {DATASETS['kaggle_slug']} "
        f"--unzip -p {target.as_posix()} --force"
    )
    ret = os.system(cmd)
    return ret == 0


def fetch_from_incoming(target: Path) -> bool:
    """If the user hand-downloaded files into ml/data/raw/incoming/, copy them."""
    if not INCOMING_DIR.exists():
        return False
    target.mkdir(parents=True, exist_ok=True)
    found = False
    for candidate in DATASETS["primary_files_required"]:
        src = INCOMING_DIR / candidate
        dst = target / candidate
        if src.exists():
            shutil.copy(src, dst)
            logger.info("Copied %s -> %s", src, dst)
            found = True
    return found


def fetch_via_mirror(target: Path) -> bool:
    """Fetch the UCI mirror, which has the same files."""
    target.mkdir(parents=True, exist_ok=True)
    archive = target / "diabetes_uci.zip"
    for mirror in DATASETS["kaggle_alternatives"]:
        try:
            logger.info("Trying mirror %s", mirror)
            urllib.request.urlretrieve(mirror, archive)
        except Exception as exc:
            logger.warning("Mirror failed: %s", exc)
            continue
        if archive.exists() and archive.stat().st_size > 1024:
            with zipfile.ZipFile(archive) as zf:
                for member in zf.namelist():
                    if member.endswith(".csv"):
                        zf.extract(member, path=target.parent)
                        src = next(Path(target.parent).rglob(member.split("/")[-1]))
                        if member.endswith(DIABETES_FILENAME):
                            shutil.move(src, target / DIABETES_FILENAME)
                        elif member.endswith(MAPPING_FILENAME):
                            shutil.move(src, target / MAPPING_FILENAME)
            return True
    return False


def synthesise(target: Path) -> bool:
    """Last-resort: generate a structurally similar dataset locally.

    So the rest of the pipeline is still runnable on day one even without
    network or Kaggle credentials.
    """

    target.mkdir(parents=True, exist_ok=True)
    diy = Path(__file__).resolve().parent / "synthetic_diabetes.csv"
    if not diy.exists():
        # regenerate on the fly so the file always exists for first-run users
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "make_synthetic",
            Path(__file__).resolve().parent / "make_synthetic_diabetes.py",
        )
        if not spec or not spec.loader:
            return False
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
    shutil.copy(diy, target / DIABETES_FILENAME)

    # Add the IDS_mapping.csv stub
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "make_ids",
        Path(__file__).resolve().parent / "make_ids_mapping.py",
    )
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ids_csv = mod.main()
        shutil.copy(ids_csv, target / MAPPING_FILENAME)

    logger.warning("Using SYNTHETIC fallback dataset at %s", diy)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=DATA_RAW)
    parser.add_argument("--force-synthetic", action="store_true")
    args = parser.parse_args()

    target = args.target

    if args.force_synthetic:
        if synthesise(target):
            return 0
        return 1

    if using_kaggle() and fetch_via_kaggle(target):
        logger.info("Kaggle download succeeded.")
        return 0
    if fetch_from_incoming(target):
        logger.info("Local intake succeeded; files copied from ml/data/raw/incoming/")
        return 0
    if fetch_via_mirror(target):
        logger.info("Mirror succeeded; files staged at %s", target)
        return 0
    if synthesise(target):
        logger.warning(
            "Falling back to the synthetic CSV. Run again with Kaggle creds for production data."
        )
        return 0

    logger.error(
        "Could not acquire the dataset. Either configure Kaggle creds, "
        "or place the CSVs in ml/data/raw/incoming/."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
