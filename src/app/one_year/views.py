#!/usr/bin/python3
"""Single-year view data collection and processing."""

from __future__ import annotations

import logging
import sys

from ..io.dump_utils import DumpManager
from ..views_utils.views_fetcher import ViewsFetcher

logger = logging.getLogger(__name__)


class SingleYearViewsService:
    """Service for collecting and processing single-year view data.

    Handles fetching, merging, and caching of pageview data for a single year.
    """

    def __init__(
        self,
        views_fetcher: ViewsFetcher | None = None,
        dump_manager: DumpManager | None = None,
    ) -> None:
        """Initialize the service."""
        self._fetcher = views_fetcher or ViewsFetcher()
        self.dump_manager = dump_manager or DumpManager()

    @staticmethod
    def calculate_total_views(langcode: str, u_data: dict) -> int:
        """Calculate total views across all articles.

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

    def get_one_lang_views_by_titles(self, langcode: str, titles: list, year: int) -> dict:
        """Fetch views for all titles of one language.

        Parameters:
            langcode: Language code.
            titles: List of article titles.
            year: Year to fetch views for.

        Returns:
            dict: Merged view data for all titles.
        """
        all_data = {}

        for i in range(0, len(titles), 500):
            group = titles[i : i + 500]

            data = self._fetcher.article_views(langcode, group, year)

            all_data = self.update_data(all_data, data)

        return all_data

    def load_one_lang_views(self, langcode: str, titles: list, year: int) -> dict[str, int]:
        """Load view statistics for one language.

        Parameters:
            langcode: Language code.
            titles: List of article titles.
            year: Year to fetch views for.

        Returns:
            dict: View data for the language.
        """
        data = {}

        if "zero" in sys.argv:
            data = dict.fromkeys(titles, 0)
        else:
            data = self.get_one_lang_views_by_titles(langcode, titles, year)

        return data

    def get_one_lang_views(self, langcode: str, titles: list, year: int, json_file, maxv: int = 0) -> dict:
        """Get views for one language with file caching.

        Parameters:
            langcode: Language code.
            titles: List of article titles.
            year: Year to fetch views for.
            json_file: Path to cache file.
            maxv: Maximum number of titles to process (0 for no limit).

        Returns:
            dict: View data for the language.
        """
        u_data = {}
        titles_not_in_file = titles

        if json_file.exists():
            u_data: dict = self.dump_manager.json_load(json_file)  # pyright: ignore[reportAssignmentType]
            titles_not_in_file = [x for x in titles if (x not in u_data)]
            logger.info(f"{langcode}: {len(titles):,} titles, titles_not_in_file: {len(titles_not_in_file):,}")
        else:
            logger.info(f"{json_file} not found.")

        titles_not_in_file.sort()

        if maxv > 0 and len(titles_not_in_file) > maxv:
            logger.info(f"{langcode}: {len(titles):,} titles > max {maxv}, skipping")
        elif "local" in sys.argv:
            logger.info(f"load_one_lang_views(lang:{langcode}) \t titles: {len(titles):,}")
        else:
            views_t = self.load_one_lang_views(langcode, titles_not_in_file, year)
            u_data = self.update_data(u_data, views_t)

        return u_data


__all__ = [
    "SingleYearViewsService",
]
