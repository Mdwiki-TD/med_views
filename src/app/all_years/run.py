#!/usr/bin/python3
"""
Collects and stores article views for all years (2015-2025)
"""

from __future__ import annotations

import datetime
import json
import logging

from ..config import Config
from ..io.dump_utils import DumpManager
from ..sql_loader import MedicalTitlesRepository
from ..titles_utils import TitlesLoader
from ..views_utils.views_fetcher import ViewsFetcher
from .stats import MultiYearStatsService
from .views import MultiYearViewsService

logger = logging.getLogger(__name__)


class MultiYearViewsPipeline:
    """Orchestrates multi-year view collection pipeline."""

    def __init__(self, local: bool = False) -> None:
        self.config = Config.get_instance()
        self.dump_manager = DumpManager(config=self.config)
        self.titles_loader = TitlesLoader()
        self.views_service = MultiYearViewsService()
        self.stats_service = MultiYearStatsService(config=self.config)
        self.views_fetcher = ViewsFetcher()
        self.empty_data_all: dict = {}
        self.local = local

    def dump_empty_data_all(self) -> None:
        file = self.config.main_dump_path / "empty_views_all_years.json"
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
    ) -> None:
        if not data:
            return

        titles = [x.replace("_", " ") for x in titles]

        logger.debug(f"{lang=}, {len(data)=}")

        data = {x.replace("_", " "): v for x, v in data.items()}

        self.stats_service.dump_stats(titles, data, lang)

        # Separate data by year and save to corresponding year folders
        # First, organize data by year
        years_data = {}

        for title, views in data.items():
            if isinstance(views, dict):
                # views is a dictionary of {year: count}
                for year, count in views.items():
                    if year not in years_data:
                        years_data[year] = {}
                    years_data[year][title] = count
            elif isinstance(views, int):
                # Single value, might be from "all" or a specific year
                # We'll skip this for now or handle as needed
                pass

        # Save each year's data to its corresponding folder
        for year, year_data in years_data.items():
            file = self.views_fetcher.get_view_file(lang, year)
            # Filter out zero values
            not_empty_data = {k: v for k, v in year_data.items() if v != 0}

            if not_empty_data:
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(not_empty_data, f, ensure_ascii=False)

        # Track empty data across all years
        empty_data = []
        for k in titles:
            val = data.get(k, 0)
            if val == 0:
                empty_data.append(k)
            elif isinstance(val, dict):
                # Check if all year values are 0
                if all(v == 0 for v in val.values()):
                    empty_data.append(k)

        if empty_data:
            self.empty_data_all[lang] = empty_data

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

    def make_views(self, languages, limit, maxv=0) -> dict[str, dict]:
        views = {}

        for n, (lang, _) in enumerate(languages.items(), start=1):
            if limit > 0 and n > limit:
                logger.info(f"limit {limit} reached, break")
                break

            data = self.process_language_views(lang, maxv)

            views[lang] = data

        self.stats_service.dump_stats_all(self.stats_service.stats_all_data)
        self.dump_empty_data_all()

        return views

    def process_language_views(self, lang, maxv=0) -> dict[str, dict]:
        titles = self.titles_loader.load_lang_titles(lang)

        # For all years, we'll check an existing file from the current year to see what titles we already have
        # Use the current year or latest available year as reference
        current_year = datetime.datetime.now().year
        # Ensure we don't go beyond 2025
        reference_year = min(current_year, 2025)
        json_file = self.views_fetcher.get_view_file(lang, reference_year)

        data = self.views_service.get_one_lang_views(lang, titles, json_file, maxv=maxv)

        self.dump_one_lang_files(titles, data, lang)

        return data

    def start(self, limit, maxv):
        """
        Orchestrates collection of per-language pageview totals for all years (2015-2025).

        Parameters:
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

        self.make_views(languages, limit, maxv)


__all__ = [
    "MultiYearViewsPipeline",
]
