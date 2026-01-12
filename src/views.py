#!/usr/bin/python3
"""

"""
import logging
import sys

from .dump_utils import dump_one
from .helps import json_load

from .views_utils.views_helps import (
    article_views,
    get_view_file,
)

logger = logging.getLogger(__name__)


def update_data(all_data, data):
    # ---
    all_data.update({x: v for x, v in data.items() if (x not in all_data or all_data[x] == 0)})
    # ---
    return all_data


def get_one_lang_views_by_titles(langcode, titles, year):
    # ---
    all_data = {}
    # ---
    for i in range(0, len(titles), 20):
        # ---
        group = titles[i : i + 20]
        # ---
        data = article_views(langcode, group, year)
        # ---
        all_data = update_data(all_data, data)
    # ---
    return all_data


def get_one_lang_views_by_titles_plus_1k(langcode, titles, year, json_file, max_items=1000):
    # ---
    in_file = {}
    all_data = {}
    # ---
    if json_file.exists():
        in_file = json_load(json_file)
    # ---
    if in_file is False:
        return False
    # ---
    for i in range(0, len(titles), 200):
        # ---
        group = titles[i : i + 200]
        # ---
        data = article_views(langcode, group, year)
        # ---
        all_data = update_data(all_data, data)
        # ---
        in_file = update_data(in_file, data)
        # ---
        dump_one(json_file, in_file)
    # ---
    return all_data


def retrieve_view_statistics(langcode, titles, year, max_items, json_file, in_file):
    if "zero" in sys.argv:
        data = {x: 0 for x in titles}
    elif len(titles) > max_items:
        data = get_one_lang_views_by_titles_plus_1k(langcode, titles, year, json_file, max_items=max_items)
    else:
        data = get_one_lang_views_by_titles(langcode, titles, year)
    # ---
    data = {x.replace("_", " "): v for x, v in data.items()}
    # ---
    if len(in_file) > 0:
        # ---
        logger.info(f"<<yellow>>(lang:{langcode}) new data: {len(data)}, in_file: {len(in_file)}")
        # ---
        in_file = update_data(in_file, data)
        # ---
        dump_one(json_file, in_file)
        # ---
        data = in_file
    else:
        # ---
        logger.info(f"<<green>>(lang:{langcode}) new data: {len(data)}")
        # ---
        dump_one(json_file, data)
    return data


def load_one_lang_views(langcode, titles, year, max_items=1000, maxv=0):
    # ---
    json_file = get_view_file(langcode, year)
    # ---
    u_data = {}
    in_file = {}
    # ---
    if json_file.exists():
        # ---
        u_data = json_load(json_file)
        # ---
        if u_data is None:
            return False
        # ---
        u_data = {x.replace("_", " "): v for x, v in u_data.items()}
        # ---
        titles_not_in_file = [x for x in titles if (x not in u_data or u_data[x] == 0)]
        # ---
        if len(u_data) != len(titles) or len(titles_not_in_file) > 0:
            logger.info(
                f"<<red>>(lang:{json_file.name}) titles: {len(titles):,}, titles in file: {len(u_data):,}, missing: {len(titles_not_in_file):,}"
            )
            # ---
            in_file = u_data
            # ---
            titles = titles_not_in_file
        else:
            logger.info(f"<<green>> load_one_lang_views(lang:{json_file}) \t titles: {len(titles):,}")
            # ---
            return u_data
    # ---
    if maxv > 0 and len(titles) > maxv:
        logger.info(f"<<yellow>> {langcode}: {len(titles)} titles > max {maxv}, skipping")
        return u_data
    # ---
    if "local" in sys.argv:
        return u_data
    # ---
    data = retrieve_view_statistics(langcode, titles, year, max_items, json_file, in_file)
    # ---
    return data


def get_one_lang_views(langcode, titles, year, maxv=0):
    # ---
    views_t = load_one_lang_views(langcode, titles, year, maxv=maxv)
    # ---
    if not views_t:
        return 0
    # ---
    # logger.debug(views_t)
    # ---
    total = 0
    # ---
    for _, views in views_t.items():
        if isinstance(views, dict):
            views = views.get("all", 0)
        total += views
    # ---
    if total == 0:
        logger.info(f"<<yellow>> No views for {langcode}")
        # logger.info("views_t" + str(views_t))
        # logger.info("titles" + str(titles))
    # ---
    return total
