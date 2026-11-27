#!/usr/bin/python3
"""
python src/start_titles.py
"""

from __future__ import annotations

import json
import logging
import sys

from app.config import get_config
from src.app.api_sql.sql_utils import MedicalTitlesRepository
from src.app.io.dump_utils import DumpManager

logger = logging.getLogger(__name__)


def start():
    config = get_config()
    dump_manager = DumpManager(config=config)
    titles_repo = MedicalTitlesRepository()

    file = config.main_dump_path / "all_languages_titles.json"

    if "local" in sys.argv:
        logger.info("dump_data: loading from local files")
        all_links = {}
        with open(file, encoding="utf-8") as f:
            all_links = json.load(f)
    else:
        all_links = titles_repo.retrieve_medicine_titles()

    logger.info(f"dump_data: retrieved langs: {len(all_links)}")

    if not all_links or len(all_links) == 0:
        logger.warning("No links retrieved from database, aborting.")
        return

    dump_manager.dump_one(file, all_links)

    dump_manager.dump_languages_counts({x: len(y) for x, y in all_links.items()})

    for n, (lang, titles) in enumerate(all_links.items(), start=1):
        logger.debug(f"dump_data(): lang:{n}/{len(all_links)} \t {lang} {len(titles)}")

        file = config.json_titles_path / f"{lang}.json"

        dump_manager.dump_list(file, titles)

    logger.debug(f"dump_data: all langs: {len(all_links)}")


if __name__ == "__main__":
    start()
