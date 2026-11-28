#!/usr/bin/python3
"""
Multi-year Wikipedia article view data collection and processing.

This module handles collecting and processing Wikipedia article views
for all years from 2015 to 2025, as opposed to single-year collection.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from ..io.dump_utils import DumpManager
from ..views_utils.views_fetcher import ViewsFetcher

logger = logging.getLogger(__name__)


class MultiYearViewsService:
    """Service for collecting and processing multi-year view data.

    Handles fetching, merging, and caching of pageview data across
    multiple years (2015-2025).
    """

    def __init__(
        self,
        views_fetcher: ViewsFetcher | None = None,
        dump_manager: DumpManager | None = None,
        local: bool = False,
    ) -> None:
        """Initialize the service."""
        self._fetcher = views_fetcher or ViewsFetcher()
        self.dump_manager = dump_manager or DumpManager()

        self.local = local

    @staticmethod
    def calculate_total_views(langcode: str, u_data: dict[str, Any]) -> int:
        """Calculate total views across all articles and years.

        Parameters:
            langcode: Language code for logging.
            u_data: Mapping from article title to view count or dict.

        Returns:
            int: Total view count.
        """
        total = 0

        for _, views in u_data.items():
            if isinstance(views, dict):
                views = views.get("all", 0)
            total += views

        if total == 0:
            logger.info(f"No views for {langcode}")
        return total

    def get_one_lang_views_by_titles(
        self,
        langcode: str,
        titles: list[str],
        year: int | None = None,
    ) -> dict[str, Any]:
        """Fetch views for all titles of one language."""
        all_data = {}

        for i in range(0, len(titles), 500):
            group = titles[i : i + 500]
            if year:
                data = self._fetcher.article_views(langcode, group, year)
            else:
                data = self._fetcher.article_views_all_years(langcode, group)

            all_data.update({x: v for x, v in data.items() if (x not in all_data or all_data[x] == 0)})

        return all_data

    def load_one_lang_views(
        self,
        langcode: str,
        titles: list[str],
        year: int | None = None,
    ) -> dict[str, Any]:
        """Load view statistics for one language."""
        data = {}

        if "zero" in sys.argv:
            data = dict.fromkeys(titles, 0)
        else:
            data = self.get_one_lang_views_by_titles(
                langcode,
                titles,
                year,
            )

        return data

    def get_one_lang_views(
        self,
        langcode: str,
        titles: list[str],
        json_file: Path,
        year: int | None = None,
        maxv: int = 0,
    ) -> dict[str, Any]:
        """Get views for one language with file caching."""
        u_data = {}
        titles = [x.replace("_", " ") for x in titles]

        if json_file.exists():
            u_data: dict = self.dump_manager.json_load(json_file)  # pyright: ignore[reportAssignmentType]
            # TODO: Select the requested year from nested cached values.
            # For year=2024, a cached value of {"2023": 10, "2024": 20, "all": 30} remains unchanged. The title then counts as cached, so no fetch replaces the value. The shared statistics service reports 30 instead of 20, and the yearly writer preserves the nested value.
            # When year is supplied, extract that year's count before checking cache completeness. Fetch entries that lack the requested year. Preserve nested values when year is None.
            u_data = {x.replace("_", " "): v for x, v in u_data.items()}
        else:
            logger.info(f"{json_file} not found.")

        titles_not_in_file = [x for x in titles if (x not in u_data)]
        logger.info(f"{langcode}: {len(titles):,} titles, titles_not_in_file: {len(titles_not_in_file):,}")

        titles_not_in_file.sort()

        if maxv > 0 and len(titles_not_in_file) > maxv:
            logger.info(f"{langcode}: {len(titles):,} titles > max {maxv}, skipping")
        elif self.local:
            logger.info(f"load_one_lang_views(lang:{langcode}) \t titles: {len(titles):,}")
        else:
            views_t = self.load_one_lang_views(
                langcode,
                titles_not_in_file,
                year,
            )

            u_data.update({x: v for x, v in views_t.items() if (x not in u_data or u_data[x] == 0)})

        return u_data


__all__ = [
    "MultiYearViewsService",
]
