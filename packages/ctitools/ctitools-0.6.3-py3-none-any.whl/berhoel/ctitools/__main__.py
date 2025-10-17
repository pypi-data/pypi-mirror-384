"""Main code for module."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import CTI


def main() -> None:
    """Execute reading of CTI file."""
    parser = argparse.ArgumentParser("Read cti file.")
    parser.add_argument("cti", type=Path, help="input file (required)")
    args = parser.parse_args()

    CTI(args.cti)


if __name__ == "__main__":
    main()
