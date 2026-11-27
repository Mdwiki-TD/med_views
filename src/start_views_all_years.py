#!/usr/bin/python3
"""
python src/start_views_all_years.py

Collects and stores article views for all years (2015-2025)
"""

from __future__ import annotations

import logging
import sys

from src.app.all_years.run import MultiYearViewsPipeline

logger = logging.getLogger(__name__)


def parse_args():
    limit = 0
    maxv = 0
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        if key in ["limit", "-limit"] and val.isdigit():
            limit = int(val)
        elif key in ["max", "-max"] and val.isdigit():
            maxv = int(val)
    return limit, maxv


if __name__ == "__main__":
    limit, maxv = parse_args()
    pipeline = MultiYearViewsPipeline(
        local="local" in sys.argv,
    )
    pipeline.start(limit, maxv)
