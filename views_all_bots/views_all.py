#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/views_all

"""
import logging
import sys

from apis.mw_views import PageviewsClient

from med_views.views_all_bots.helps import get_views_all_file, is_empty_data, json_load, update_data_new
from med_views.views_all_bots.stats_bot import dump_stats
from views_all_bots.utils import dump_one

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


parallelism = 2

for arg in sys.argv:
    key, _, val = arg.partition(":")
    if key == "-para":
        parallelism = int(val) or parallelism

view_bot = PageviewsClient(parallelism=parallelism)


def dump_it(json_file, data, json_file_stats):
    # ---
    new_data = {}
    # ---
    # sort all sub data inside data
    for k, v in data.items():
        new_data[k] = {k2: v2 for k2, v2 in sorted(v.items(), key=lambda item: item[0], reverse=False)}
    # ---
    dump_one(json_file, new_data)
    # ---
    dump_stats(json_file_stats, new_data)


def article_all_views(site, articles, year=2024):
    # ---
    site = "be-tarask" if site == "be-x-old" else site
    # ---
    data = view_bot.article_views_new(
        f"{site}.wikipedia", articles, granularity="monthly", start="20100101", end="20250627"
    )
    # ---
    # print(data)
    # ---
    return data


def get_one_lang_views_all_by_titles(langcode, titles, year):
    # ---
    all_data = {}
    # ---
    for i in range(0, len(titles), 20):
        # ---
        group = titles[i : i + 20]
        # ---
        data = article_all_views(langcode, group, year)
        # ---
        all_data = update_data_new(all_data, data)
    # ---
    return all_data


def get_one_lang_views_all_by_titles_plus_1k(langcode, titles, year, json_file, json_file_stats, max_items=1000):
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
        data = article_all_views(langcode, group, year)
        # ---
        all_data = update_data_new(all_data, data)
        # ---
        in_file = update_data_new(in_file, data)
        # ---
        dump_it(json_file, in_file, json_file_stats)
    # ---
    return all_data


def render_data(titles, langcode, year, json_file, json_file_stats, max_items=1000):
    data = {}
    # ---
    if "zero" in sys.argv:
        data = {x: {"all": 0} for x in titles}
    elif len(titles) > max_items:
        data = get_one_lang_views_all_by_titles_plus_1k(
            langcode, titles, year, json_file, json_file_stats, max_items=max_items
        )
    else:
        data = get_one_lang_views_all_by_titles(langcode, titles, year)
    # ---
    data = {x.replace("_", " "): v for x, v in data.items()}
    # ---
    return data


def get_titles_and_in_file(json_file, titles):
    # ---
    if not json_file.exists():
        name = json_file.name
        print(f"json_file does not exist: {name}")
        return titles, {}
    # ---
    u_data = json_load(json_file)
    # ---
    if u_data is False:
        # TODO: error when loading the json data
        return [], {}
    # ---
    titles_not_in_file = [x for x in titles if is_empty_data(u_data.get(x, {})) and x.find("#") == -1]
    # ---
    if not (len(u_data) != len(titles) or len(titles_not_in_file) > 0):
        logger.info(f"<<green>> load_one_lang_views_all(lang:{json_file}) \t titles: {len(titles):,}")
        print("nothing to do")
        return [], {}
    # ---
    logger.info(
        f"<<red>>(lang:{json_file.name}) titles: {len(titles):,}, titles in file: {len(u_data):,}, missing: {len(titles_not_in_file):,}"
    )
    # ---
    in_file = u_data
    # ---
    titles = titles_not_in_file
    # ---
    return titles, in_file


def get_titles_to_work(langcode, titles, year):
    # ---
    json_file = get_views_all_file(langcode)
    # ---
    titles_to_work, _ = get_titles_and_in_file(json_file, titles)
    # ---
    if titles_to_work == titles:
        return []
    # ---
    return titles_to_work


def load_one_lang_views_all(langcode, titles, year, max_items=1000, maxv=0):
    # ---
    json_file = get_views_all_file(langcode)
    json_file_stats = get_views_all_file(langcode, "stats")
    # ---
    titles, in_file = get_titles_and_in_file(json_file, titles)
    # # ---
    if len(titles) == 0:
        return
    # ---
    if maxv > 0 and len(titles) > maxv:
        logger.info(f"<<yellow>> {langcode}: {len(titles)} titles > max {maxv}, skipping")
        return
    # ---
    if "local" in sys.argv:
        return
    # ---
    data = render_data(titles, langcode, year, json_file, json_file_stats, max_items=1000)
    # ---
    if len(in_file) > 0:
        # ---
        logger.info(f"<<yellow>>(lang:{langcode}) new data: {len(data)}, in_file: {len(in_file)}")
        # ---
        data = update_data_new(in_file, data)
    else:
        logger.info(f"<<green>>(lang:{langcode}) new data: {len(data)}")
    # ---
    dump_it(json_file, data, json_file_stats)
