#!/usr/bin/python3
"""

"""
import logging
import sys

from .helps import json_load
from .views_utils.views_helps import (
    article_views,
)

logger = logging.getLogger(__name__)


def calculate_total_views(langcode, u_data):
    total = 0
    # ---
    for _, views in u_data.items():
        if isinstance(views, dict):
            views = views.get("all", 0)
        total += views
    # ---
    if total == 0:
        logger.info(f"<<yellow>> No views for {langcode}")
    return total


def update_data(all_data, data) -> dict:
    # ---
    data = {x.replace("_", " "): v for x, v in data.items()}
    all_data = {x.replace("_", " "): v for x, v in all_data.items()}
    # ---
    all_data.update({x: v for x, v in data.items() if (x not in all_data or all_data[x] == 0)})
    # ---
    return all_data


def get_one_lang_views_by_titles(langcode, titles, year):
    # ---
    all_data = {}
    # ---
    for i in range(0, len(titles), 500):
        # ---
        group = titles[i : i + 500]
        # ---
        data = article_views(langcode, group, year)
        # ---
        all_data = update_data(all_data, data)
    # ---
    return all_data


def load_one_lang_views(langcode, titles, year) -> dict[str, int]:
    """
    Load view statistics for one language and a list of titles.
    """
    # ---
    data = {}
    # ---
    if "zero" in sys.argv:
        data = {x: 0 for x in titles}
    else:
        data = get_one_lang_views_by_titles(langcode, titles, year)
    # ---
    return data


def get_one_lang_views(langcode, titles, year, json_file, maxv=0) -> dict:
    # ---
    u_data = {}
    titles_not_in_file = titles
    # ---
    if json_file.exists():
        u_data = json_load(json_file)
        titles_not_in_file = [
            x for x in titles if (
                x not in u_data
                # or u_data[x] == 0
            )]
        logger.info(f"<<yellow>> {langcode}: {len(titles):,} titles, titles_not_in_file: {len(titles_not_in_file):,}")
    else:
        logger.info(f"<<yellow>> {json_file} not found.")
    # ---
    titles_not_in_file.sort()
    # ---
    if maxv > 0 and len(titles_not_in_file) > maxv:
        logger.info(f"<<yellow>> {langcode}: {len(titles):,} titles > max {maxv}, skipping")
    elif "local" in sys.argv:
        logger.info(f"<<green>> load_one_lang_views(lang:{langcode}) \t titles: {len(titles):,}")
    else:
        views_t = load_one_lang_views(langcode, titles_not_in_file, year)
        u_data = update_data(u_data, views_t)
    # ---
    return u_data
