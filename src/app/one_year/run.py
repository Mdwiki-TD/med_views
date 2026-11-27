#!/usr/bin/python3
"""
Collects and stores article views for single year.
"""

from __future__ import annotations

import json
import logging

from ..api_sql.sql_utils import MedicalTitlesRepository
from ..config import get_config
from ..io.dump_utils import DumpManager
from ..titles_utils import TitlesLoader
from ..views_utils.views_helps import ViewsFetcher
from .stats import SingleYearStatsService
from .views import SingleYearViewsService

logger = logging.getLogger(__name__)


class SingleYearViewsPipeline:
    """Orchestrates single-year view collection pipeline."""

    def __init__(self, local: bool = False) -> None:
        self.config = get_config()
        self.dump_manager = DumpManager(config=self.config)
        self.titles_loader = TitlesLoader()
        self.views_service = SingleYearViewsService()
        self.stats_service = SingleYearStatsService(config=self.config)
        self.views_fetcher = ViewsFetcher()
        self.empty_data_all: dict = {}
        self.local = local

    def dump_empty_data_all(self, year: int) -> None:
        file = self.config.main_dump_path / f"empty_views_{year}.json"
        logger.debug(f"dump_empty_data_all({file}), {len(self.empty_data_all)=}")

        # sort empty_data_all by len of values desc
        empty_data_all_sorted = dict(sorted(self.empty_data_all.items(), key=lambda item: len(item[1]), reverse=True))

        with open(file, "w", encoding="utf-8") as f:
            json.dump(empty_data_all_sorted, f, ensure_ascii=False, indent=4)

    def dump_one_lang_files(
        self,
        titles: list[str],
        data: dict,
        lang: str,
        year: int,
    ) -> None:
        file = self.views_fetcher.get_view_file(lang, year)

        if not data:
            return

        titles = [x.replace("_", " ") for x in titles]

        logger.debug(f"{file=}, {len(data)=}")

        empty_data = []
        not_empty_data = {}

        data = {x.replace("_", " "): v for x, v in data.items()}
        empty_data = [k for k in titles if data.get(k, 0) == 0]
        not_empty_data = {k: v for k, v in data.items() if v != 0}

        self.stats_service.dump_stats(titles, data, lang)

        if empty_data:
            self.empty_data_all[lang] = empty_data

        with open(file, "w", encoding="utf-8") as f:
            json.dump(not_empty_data, f, ensure_ascii=False)

    def get_languages_articles_counts(self) -> dict:
        all_infos = self.dump_manager.load_languages_counts()

        if not all_infos and not self.local:
            titles_repo = MedicalTitlesRepository()
            data = titles_repo.get_language_article_counts_sql()
            return data

        if all_infos:
            return all_infos

        result = self.dump_manager.count_languages_in_json()

        logger.debug(f"get_languages_articles_counts local: {len(result)}")

        return result

    def make_views(self, languages, year, limit, maxv=0) -> dict[str, int]:
        views = {}

        for n, (lang, _) in enumerate(languages.items(), start=1):
            if limit > 0 and n > limit:
                logger.info(f"limit {limit} reached, break")
                break

            data = self.process_language_views(year, lang, maxv)

            views[lang] = data

        self.stats_service.dump_stats_all(year, self.stats_service.stats_all_data)
        self.dump_empty_data_all(year)

        return views

    def process_language_views(self, year: int, lang: str, maxv: int = 0) -> dict[str, int]:
        titles = self.titles_loader.load_lang_titles(lang)

        json_file = self.views_fetcher.get_view_file(lang, year)

        data = self.views_service.get_one_lang_views(lang, titles, year, json_file, maxv=maxv)

        self.dump_one_lang_files(titles, data, lang, year)

        return data

    def start(self, year, limit, maxv):
        """
        Orchestrates collection of per-language pageview totals for a given year.

        Parameters:
            year (int): Year used in view calculations.
            limit (int): Maximum number of languages to process (0 means no limit).
            maxv (int): Upper bound applied to per-language view calculations (0 means no cap).
        """
        languages = self.get_languages_articles_counts()

        logger.info(f"get_languages_articles_counts local: {len(languages)}")

        if not languages or list(set(languages.values())) == [0]:
            logger.error("No languages found, run `python3 start_titles.py` first")
            return

        # sort languages ASC
        languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=False))

        self.make_views(languages, year, limit, maxv)


__all__ = [
    "SingleYearViewsPipeline",
]
