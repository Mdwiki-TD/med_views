#!/usr/bin/python3
"""
python src/save_reports.py
"""

from __future__ import annotations

import logging
import sys

from app.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


def parse_args() -> tuple[int, int]:
    year = 2025
    limit = 0
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        if key in ["limit", "-limit"] and val.isdigit():
            limit = int(val)
        elif key in ["year", "-year"] and val.isdigit():
            year = int(val)

    return year, limit


if __name__ == "__main__":
    year, limit = parse_args()
    generator = ReportGenerator(
        save="save" in sys.argv,
    )
    generator.start(year, limit)
