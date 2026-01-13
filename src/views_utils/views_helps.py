#!/usr/bin/python3
"""

"""
import logging

from ..config import parallelism, views_by_year_path
from ..services.mw_views import PageviewsClient

logger = logging.getLogger(__name__)

view_bot = PageviewsClient(parallelism=parallelism)


def article_views(site, articles, year=2024):
    # ---
    site = "be-tarask" if site == "be-x-old" else site
    # ---
    data = view_bot.article_views_new(
        f"{site}.wikipedia",
        articles,
        granularity="monthly",
        start=f"{year}0101",
        end=f"{year}1231",
    )
    # ---
    new_data = {}
    # ---
    for title, views in data.items():
        # ---
        title = title.replace("_", " ")
        # ---
        new_data[title] = views.get(year) or views.get(str(year)) or views.get("all", 0)
    # ---
    return new_data


def article_views_all_years(site, articles):
    # ---
    site = "be-tarask" if site == "be-x-old" else site
    # ---
    data = view_bot.article_views_new(
        f"{site}.wikipedia",
        articles,
        granularity="monthly",
        start="20150101",
        end="20251231",
    )
    # ---
    new_data = {}
    # ---
    for title, views in data.items():
        # ---
        title = title.replace("_", " ")
        # ---
        new_data[title] = views
    # ---
    return new_data


def get_view_file(lang, year):
    # ---
    """
    Compute the filesystem path for the language's views JSON file for a given year, creating the year directory if it does not exist.

    Parameters:
        lang (str): Language code (used as the JSON filename without extension).
        year (int | str): Year used to select or create the yearly subdirectory.

    Returns:
        pathlib.Path: Path to the "{lang}.json" file inside the year directory.
    """
    dir_v = views_by_year_path / str(year)
    # ---
    if not dir_v.exists():
        dir_v.mkdir(parents=True)
    # ---
    file = dir_v / f"{lang}.json"
    # ---
    return file


__all__ = [
    "article_views",
    "article_views_all_years",
    "get_view_file",
]
