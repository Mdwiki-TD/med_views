#!/usr/bin/python3
""" """

from __future__ import annotations

import json
import logging
import sys

from .config import Config
from .io.dump_utils import DumpManager
from .sql_loader import MedicalTitlesRepository

logger = logging.getLogger(__name__)


class TitlesLoader:

    def __init__(
        self,
        dump_manager: DumpManager | None = None,
        titles_repo: MedicalTitlesRepository | None = None,
        local: bool = False,
    ) -> None:
        """Initialize the repository."""
        self.config = Config.get_instance()
        self.dump_manager = dump_manager or DumpManager(config=self.config)
        self.titles_repo = titles_repo or MedicalTitlesRepository()
        self.local = local

    def start(self):
        self.config = Config.get_instance()

        file = self.config.main_dump_path / "all_languages_titles.json"

        if "local" in sys.argv:
            logger.info("dump_data: loading from local files")
            all_links = {}
            with open(file, encoding="utf-8") as f:
                all_links = json.load(f)
        else:
            all_links = self.titles_repo.retrieve_medicine_titles()

        logger.info(f"dump_data: retrieved langs: {len(all_links)}")

        if not all_links or len(all_links) == 0:
            logger.warning("No links retrieved from database, aborting.")
            return

        self.dump_manager.dump_one(file, all_links)

        self.dump_manager.dump_languages_counts({x: len(y) for x, y in all_links.items()})

        for n, (lang, titles) in enumerate(all_links.items(), start=1):
            logger.debug(f"dump_data(): lang:{n}/{len(all_links)} \t {lang} {len(titles)}")

            file = self.config.json_titles_path / f"{lang}.json"

            self.dump_manager.dump_list(file, titles)

        logger.debug(f"dump_data: all langs: {len(all_links)}")
