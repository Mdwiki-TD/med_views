#!/usr/bin/python3
"""

"""
import logging

from .dump_utils import dump_one
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


def dump_it(json_file, data):
    # ---
    new_data = {}
    # ---
    # sort all sub data inside data
    for k, v in data.items():
        new_data[k] = {k2: v2 for k2, v2 in sorted(v.items(), key=lambda item: item[0], reverse=False)}
    # ---
    dump_one(json_file, new_data)
    # ---
    return new_data


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
