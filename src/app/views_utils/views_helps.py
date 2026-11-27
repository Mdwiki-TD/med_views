#!/usr/bin/python3
"""Utilities for fetching article view data from Wikimedia API."""

from __future__ import annotations

import logging
from pathlib import Path

from ..config import Config, get_config
from ..services.mw_views import PageviewsClient

logger = logging.getLogger(__name__)


class ViewsFetcher:
    """Fetcher for article view data from Wikimedia API.

    Handles fetching pageview data for articles across different time periods
    and languages.
    """

    def __init__(
        self,
        pageviews_client: PageviewsClient | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize the ViewsFetcher.

        Parameters:
            pageviews_client: Optional PageviewsClient for API calls.
                Defaults to a new client with config parallelism.
            config: Optional configuration object. Defaults to get_config().
        """
        self._config = config or get_config()
        self._client = pageviews_client or PageviewsClient(parallelism=self._config.parallelism)

    def article_views(self, site: str, articles: list, year: int = 2024) -> dict:
        """Get article views for a specific site and year.

        Parameters:
            site: Language code for the Wikipedia site.
            articles: List of article titles to fetch views for.
            year: Year to fetch views for.

        Returns:
            dict: Mapping from article title to view count for the year.
        """
        site = "be-tarask" if site == "be-x-old" else site

        data = self._client.article_views_new(
            f"{site}.wikipedia",
            articles,
            granularity="monthly",
            start=f"{year}0101",
            end=f"{year}1231",
        )

        new_data = {}

        for title, views in data.items():
            title = title.replace("_", " ")

            new_data[title] = views.get(year) or views.get(str(year)) or views.get("all", 0)

        return new_data

    def article_views_all_years(self, site: str, articles: list) -> dict:
        """Get article views for all years (2015-2025).

        Parameters:
            site: Language code for the Wikipedia site.
            articles: List of article titles to fetch views for.

        Returns:
            dict: Mapping from article title to dict of yearly view counts.
        """
        site = "be-tarask" if site == "be-x-old" else site

        data = self._client.article_views_new(
            f"{site}.wikipedia",
            articles,
            granularity="monthly",
            agent="user",
            start="20150101",
            end="20251231",
        )

        new_data = {}

        for title, views in data.items():
            title = title.replace("_", " ")

            new_data[title] = views

        return new_data

    def get_view_file(self, lang: str, year: int) -> Path:
        """Compute the filesystem path for the language's views JSON file.

        Parameters:
            lang: Language code (used as the JSON filename without extension).
            year: Year used to select or create the yearly subdirectory.

        Returns:
            pathlib.Path: Path to the "{lang}.json" file inside the year directory.
        """
        dir_v = self._config.views_by_year_path / str(year)

        if not dir_v.exists():
            dir_v.mkdir(parents=True)

        file = dir_v / f"{lang}.json"

        return file


# Legacy compatibility layer
_default_fetcher: ViewsFetcher | None = None


def _get_default_fetcher() -> ViewsFetcher:
    """Get or create the default ViewsFetcher instance."""
    global _default_fetcher
    if _default_fetcher is None:
        _default_fetcher = ViewsFetcher()
    return _default_fetcher


def article_views(site, articles, year: int = 2024):
    """Legacy entry point. Use ViewsFetcher.article_views instead."""
    return _get_default_fetcher().article_views(site, articles, year)


def article_views_all_years(site, articles):
    """Legacy entry point. Use ViewsFetcher.article_views_all_years instead."""
    return _get_default_fetcher().article_views_all_years(site, articles)


def get_view_file(lang, year):
    """Legacy entry point. Use ViewsFetcher.get_view_file instead."""
    return _get_default_fetcher().get_view_file(lang, year)


__all__ = [
    "ViewsFetcher",
    "article_views",
    "article_views_all_years",
    "get_view_file",
]
