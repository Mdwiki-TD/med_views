#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/titles


"""

import logging

from src.config import json_titles_path
from src.dump_utils import (
    dump_all,
    dump_one,
)
from src.sql_utils import (
    retrieve_medicine_titles,
)

logger = logging.getLogger(__name__)


def dump_data(all_data):
    # ---
    for n, (lang, titles) in enumerate(all_data.items(), start=1):
        # ---
        logger.debug(f"dump_data(): lang:{n}/{len(all_data)} \t {lang} {len(titles)}")
        # ---
        file = json_titles_path / f"{lang}.json"
        # ---
        dump_one(file, titles)
    # ---
    logger.debug(f"dump_data: all langs: {len(all_data)}")


def start():
    # ---
    all_links = retrieve_medicine_titles()
    # ---
    dump_all({x: len(y) for x, y in all_links.items()})
    # ---
    dump_data(all_links)


if __name__ == "__main__":
    start()
