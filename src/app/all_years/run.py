#!/usr/bin/python3
"""
Collects and stores article views for single year or all years (2015-2025)
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any

from ..config import Config
from ..io.dump_utils import DumpManager
from ..sql_loader import MedicalTitlesRepository
from ..titles_utils import TitlesLoader
from ..views_utils.views_fetcher import ViewsFetcher
from .stats import MultiYearStatsService
from .views import MultiYearViewsService

logger = logging.getLogger(__name__)


class MultiYearViewsPipeline:
    """Orchestrates single-year/multi-year view collection pipeline."""

    def __init__(
        self,
        views_fetcher: ViewsFetcher | None = None,
        dump_manager: DumpManager | None = None,
        local: bool = False,
        dump_dir_path: Path | None = None,
    ) -> None:
        # TODO: Forward the dump-directory override to the statistics service.
        self.dump_dir_path = dump_dir_path or Config.get_instance().paths.dump_dir_path

        self.dump_manager = dump_manager or DumpManager()
        self.titles_loader = TitlesLoader()
        self.views_service = MultiYearViewsService()
        self.stats_service = MultiYearStatsService()
        self.views_fetcher = views_fetcher or ViewsFetcher()
        self.empty_data_all: dict[str, list[str]] = {}
        self.local = local

    def dump_empty_data_all(
        self,
        year: int | None = None,
    ) -> None:
        file = f"empty_views_{year}.json" if year else "empty_views_all_years.json"
        file_path = self.dump_dir_path / file
        logger.debug(f"dump_empty_data_all({file_path}), {len(self.empty_data_all)=}")

        # sort empty_data_all by len of values desc
        empty_data_all_sorted = dict(sorted(self.empty_data_all.items(), key=lambda item: len(item[1]), reverse=True))

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(empty_data_all_sorted, f, ensure_ascii=False, indent=4)

    def dump_one_lang_files(
        self,
        titles: list[str],
        data: dict[str, Any],
        lang: str,
        year: int | None = None,
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

        if year:
            years_data[year] = data
        else:
            for title, views in data.items():
                if isinstance(views, dict):
                    # views is a dictionary of {year: count}
                    for y, count in views.items():
                        if y not in years_data:
                            years_data[y] = {}
                        years_data[y][title] = count
                elif isinstance(views, int):
                    # Single value, might be from "all" or a specific year
                    # We'll skip this for now or handle as needed
                    pass

        # Save each year's data to its corresponding folder
        for y, year_data in years_data.items():
            file = self.views_fetcher.get_view_file(lang, y)
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

    def get_languages_articles_counts(self) -> dict[str, int]:
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

    def make_views(
        self,
        languages: dict[str, int],
        limit: int,
        year: int | None = None,
        maxv: int = 0,
    ) -> dict[str, Any]:
        views = {}

        for n, (lang, _) in enumerate(languages.items(), start=1):
            if limit > 0 and n > limit:
                logger.info(f"limit {limit} reached, break")
                break

            data = self.process_language_views(
                lang,
                maxv,
                year=year,
            )

            views[lang] = data

        self.stats_service.dump_stats_all(
            data=self.stats_service.stats_all_data,
            year=year,
        )
        self.dump_empty_data_all(year)

        return views

    def process_language_views(
        self,
        lang: str,
        maxv: int = 0,
        year: int | None = None,
    ) -> dict[str, Any]:
        titles = self.titles_loader.load_lang_titles(lang)
        if year is None:
            # For all years, we'll check an existing file from the current year to see what titles we already have
            # Use the current year or latest available year as reference
            current_year = datetime.datetime.now().year
            # Ensure we don't go beyond 2025
            # TODO: Preserve None for all-years collection.
            year = min(current_year, 2025)

        json_file = self.views_fetcher.get_view_file(
            lang=lang,
            year=year,
        )

        data = self.views_service.get_one_lang_views(
            lang,
            titles,
            json_file,
            maxv=maxv,
            year=year,
        )

        self.dump_one_lang_files(
            titles,
            data,
            lang,
            year=year,
        )

        return data

    def start(
        self,
        limit: int,
        maxv: int,
        year: int | None = None,
    ) -> None:
        """
        Orchestrates collection of per-language pageview totals for a given year or all years (2015-2025).
        """
        languages = self.get_languages_articles_counts()

        logger.info(f"get_languages_articles_counts local: {len(languages)}")

        if not languages or list(set(languages.values())) == [0]:
            logger.error("No languages found, run `python3 start_titles.py` first")
            return

        # sort languages ASC
        languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=False))

        self.make_views(
            languages=languages,
            limit=limit,
            maxv=maxv,
            year=year,
        )


__all__ = [
    "MultiYearViewsPipeline",
]
