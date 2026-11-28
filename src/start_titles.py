#!/usr/bin/python3
"""
python src/start_titles.py
"""

from __future__ import annotations

import logging
import sys

from src.app.titles_loader import TitlesLoader

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    loader = TitlesLoader(
        local="local" in sys.argv,
    )

    loader.start()
