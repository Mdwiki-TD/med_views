#!/usr/bin/python3
"""

python3 titles.py


"""

import logging

from src.config import json_titles_path
from src.dump_utils import (
    dump_languages_counts,
    dump_one,
)
from src.sql_utils import (
    retrieve_medicine_titles,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def start():
    # ---
    all_links = retrieve_medicine_titles()
    # ---
    logger.info(f"dump_data: retrieved langs: {len(all_links)}")
    # ---
    if not all_links or len(all_links) == 0:
        logger.warning("No links retrieved from database, aborting.")
        return
    # ---
    dump_languages_counts({x: len(y) for x, y in all_links.items()})
    # ---
    for n, (lang, titles) in enumerate(all_links.items(), start=1):
        # ---
        logger.debug(f"dump_data(): lang:{n}/{len(all_links)} \t {lang} {len(titles)}")
        # ---
        file = json_titles_path / f"{lang}.json"
        # ---
        dump_one(file, titles)
    # ---
    logger.debug(f"dump_data: all langs: {len(all_links)}")


if __name__ == "__main__":
    start()
