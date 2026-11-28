#!/usr/bin/python3
"""
python src/start_views.py
"""

from __future__ import annotations

import logging
import sys

from src.app.one_year.run import SingleYearViewsPipeline

logger = logging.getLogger(__name__)


def parse_args():
    year = 2025
    limit = 0
    maxv = 0
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        if key in ["limit", "-limit"] and val.isdigit():
            limit = int(val)
        elif key in ["year", "-year"] and val.isdigit():
            year = int(val)
        elif key in ["max", "-max"] and val.isdigit():
            maxv = int(val)
    return year, limit, maxv


if __name__ == "__main__":
    year, limit, maxv = parse_args()
    pipeline = SingleYearViewsPipeline(
        local="local" in sys.argv,
    )
    pipeline.start(
        year=year,
        limit=limit,
        maxv=maxv,
    )
