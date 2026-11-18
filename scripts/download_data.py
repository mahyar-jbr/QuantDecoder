"""Download Google's surface code dataset (Zenodo record 6804040) into data/ and unpack it.

Run from the repository root: uv run python scripts/download_data.py
A second run does nothing once the data is in place. Delete data/ to start over.
"""

import argparse
import logging
from pathlib import Path

from qec.download import GOOGLE_QEC3V5, ensure_dataset

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and unpack the Zenodo 6804040 dataset.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="folder for the zip and the unpacked files (default: data/ in the repository)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    target = ensure_dataset(GOOGLE_QEC3V5, args.data_dir)
    print(f"Dataset ready in {target}")


if __name__ == "__main__":
    main()
