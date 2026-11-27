#!/usr/bin/python3
"""
Multi-year Wikipedia article view data collection and processing.

This module handles collecting and processing Wikipedia article views
for all years from 2015 to 2025, as opposed to single-year collection.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from ..helps import JsonHelper
from ..views_utils.views_helps import ViewsFetcher

logger = logging.getLogger(__name__)


class MultiYearViewsService:
    """Service for collecting and processing multi-year view data.

    Handles fetching, merging, and caching of pageview data across
    multiple years (2015-2025).
    """

    def __init__(
        self,
        views_fetcher: ViewsFetcher | None = None,
        json_helper: type | None = None,
    ) -> None:
        """Initialize the service.

        Parameters:
            views_fetcher: Optional ViewsFetcher for API calls.
                Defaults to ViewsFetcher.
            json_helper: Optional JsonHelper class for JSON operations.
                Defaults to JsonHelper.
        """
        self._fetcher = views_fetcher or ViewsFetcher()
        self._json_helper = json_helper or JsonHelper

    @staticmethod
    def calculate_total_views(langcode: str, u_data: dict) -> int:
        """Calculate total views across all articles and years.

        Parameters:
            langcode: Language code for logging.
            u_data: Mapping from article title to view data dict.

        Returns:
            int: Total view count across all years.
        """
        total = 0

        for _, views in u_data.items():
            if isinstance(views, dict):
                views = views.get("all", 0)
            total += views

        if total == 0:
            logger.info(f"<<yellow>> No views for {langcode}")
        return total

    @staticmethod
    def update_data(all_data: dict, data: dict) -> dict:
        """Merge new data into existing data, normalizing underscores.

        Parameters:
            all_data: Existing data to update.
            data: New data to merge in.

        Returns:
            dict: Merged data with normalized keys.
        """
        data = {x.replace("_", " "): v for x, v in data.items()}
        all_data = {x.replace("_", " "): v for x, v in all_data.items()}

        all_data.update({x: v for x, v in data.items() if (x not in all_data or all_data[x] == 0)})

        return all_data

    def get_one_lang_views_by_titles(self, langcode: str, titles: list) -> dict:
        """Fetch views for all titles of one language across all years.

        Parameters:
            langcode: Language code.
            titles: List of article titles.

        Returns:
            dict: Merged view data for all titles.
        """
        all_data = {}

        for i in range(0, len(titles), 500):
            group = titles[i : i + 500]

            data = self._fetcher.article_views_all_years(langcode, group)

            all_data = self.update_data(all_data, data)

        return all_data

    def load_one_lang_views(self, langcode: str, titles: list) -> dict[str, Any]:
        """Load view statistics for one language across all years.

        Parameters:
            langcode: Language code.
            titles: List of article titles.

        Returns:
            dict: View data for the language.
        """
        data = {}

        if "zero" in sys.argv:
            data = dict.fromkeys(titles, 0)
        else:
            data = self.get_one_lang_views_by_titles(langcode, titles)

        return data

    def get_one_lang_views(self, langcode: str, titles: list, json_file, maxv: int = 0) -> dict:
        """Get views for one language with file caching across all years.

        Parameters:
            langcode: Language code.
            titles: List of article titles.
            json_file: Path to cache file.
            maxv: Maximum number of titles to process (0 for no limit).

        Returns:
            dict: View data for the language.
        """
        u_data = {}
        titles_not_in_file = titles

        if json_file.exists():
            u_data: dict = self._json_helper.json_load(json_file)  # pyright: ignore[reportAssignmentType]
            titles_not_in_file = [
                x
                for x in titles
                if (
                    x
                    not in u_data
                    # or u_data[x] == 0
                )
            ]
            logger.info(
                f"<<yellow>> {langcode}: {len(titles):,} titles, titles_not_in_file: {len(titles_not_in_file):,}"
            )
        else:
            logger.info(f"<<yellow>> {json_file} not found.")

        titles_not_in_file.sort()

        if maxv > 0 and len(titles_not_in_file) > maxv:
            logger.info(f"<<yellow>> {langcode}: {len(titles):,} titles > max {maxv}, skipping")
        elif "local" in sys.argv:
            logger.info(f"<<green>> load_one_lang_views(lang:{langcode}) \t titles: {len(titles):,}")
        else:
            views_t = self.load_one_lang_views(langcode, titles_not_in_file)
            u_data = self.update_data(u_data, views_t)

        return u_data


__all__ = [
    "MultiYearViewsService",
]
