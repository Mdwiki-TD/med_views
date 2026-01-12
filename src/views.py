#!/usr/bin/python3
"""

"""
import logging
import sys

from .dump_utils import dump_one
from .helps import json_load
from .views_utils.views_helps import (
    get_file_views_new,
    article_views,
    get_view_file,
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


def retrieve_view_statistics(data, langcode, in_file):
    # ---
    data = {x.replace("_", " "): v for x, v in data.items()}
    # ---
    if len(in_file) > 0:
        # ---
        logger.info(f"<<yellow>>(lang:{langcode}) new data: {len(data)}, in_file: {len(in_file)}")
        # ---
        in_file = update_data(in_file, data)
        # ---
        data = in_file
    else:
        # ---
        logger.info(f"<<green>>(lang:{langcode}) new data: {len(data)}")
    # ---
    return data


def load_one_lang_views(langcode, titles, year, max_items=1000):
    # ---
    json_file = get_view_file(langcode, year)
    # ---
    if "zero" in sys.argv:
        data = {x: 0 for x in titles}
    elif len(titles) > max_items:
        data = get_one_lang_views_by_titles_plus_1k(langcode, titles, year, json_file, max_items=max_items)
    else:
        data = get_one_lang_views_by_titles(langcode, titles, year)
    # ---
    return data


same_titles = 0
diff_titles = 0


def print_title_stats():
    global same_titles, diff_titles
    logger.info("----"*20)
    logger.info("----"*20)
    logger.info(f"<<blue>> Titles with same views file status: {same_titles}")
    logger.info(f"<<blue>> Titles with different views file status: {diff_titles}")
    logger.info("----"*20)
    logger.info("----"*20)


def get_one_lang_views(langcode, titles, year, maxv=0):
    global same_titles, diff_titles
    # ---
    json_file_all = get_file_views_new(langcode)
    json_file = get_view_file(langcode, year)
    # ---
    titles_not_in_file_all = titles
    # ---
    u_data_all = {}
    u_data = {}
    titles_not_in_file = titles
    # ---
    if json_file_all.exists():
        u_data_all = json_load(json_file_all)
        titles_not_in_file_all = [x for x in titles if (x not in u_data_all or u_data_all[x].get(str(year), 0) == 0)]
    else:
        logger.info(f"<<yellow>> No all views file for lang:{langcode}")
    # ---
    if json_file.exists():
        u_data = json_load(json_file)
        titles_not_in_file = [x for x in titles if (x not in u_data or u_data[x] == 0)]
    # ---
    titles_not_in_file_all.sort()
    titles_not_in_file.sort()
    # ---
    if titles_not_in_file == titles_not_in_file_all:
        print("same")
        same_titles += 1
    else:
        print("diff")
        print("Titles not in file all:", len(titles_not_in_file_all))
        print("Titles not in file year:", len(titles_not_in_file))
        diff_titles += 1
    # ---
    if maxv > 0 and len(titles_not_in_file) > maxv:
        logger.info(f"<<yellow>> {langcode}: {len(titles)} titles > max {maxv}, skipping")
    elif "local" in sys.argv:
        logger.info(f"<<green>> load_one_lang_views(lang:{langcode}) \t titles: {len(titles):,}")
    else:
        views_t = load_one_lang_views(langcode, titles_not_in_file, year)
        u_data = update_data(u_data, views_t)
        dump_one(json_file, u_data)
    # ---
    if not u_data:
        return 0
    # ---
    total = calculate_total_views(langcode, u_data)
    # ---
    return total
