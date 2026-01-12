#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/views_all

"""
import logging
import sys

from ..dump_utils import dump_one
from ..helps import get_views_all_file, is_empty_data, json_load
from ..stats_bot import dump_stats
from ..views_utils.views_helps import article_all_views

logger = logging.getLogger(__name__)


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


def update_data_new(all_data, data):
    # ---
    for title, counts in data.items():
        all_data.setdefault(title, {})
        # ---
        all_data[title].update(
            {x: v for x, v in counts.items() if (x not in all_data[title] or all_data[title][x] == 0)}
        )
    # ---
    return all_data


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
    """
    Determine which titles still require processing by comparing a list of titles against data stored in a JSON file.

    If the JSON file does not exist, returns the original titles list and an empty in-file mapping. If loading the JSON fails (json_load returns False), returns two empty structures. Otherwise, returns a tuple (titles_to_work, in_file) where titles_to_work is the subset of input titles that either are missing from the file or have empty data (titles containing '#' are excluded), and in_file is the parsed JSON mapping loaded from json_file.

    Parameters:
        json_file (Path): Path to the JSON file containing previously fetched title data.
        titles (list[str]): List of titles to check.

    Returns:
        tuple[list[str], dict]: (titles_to_work, in_file)
            titles_to_work: titles that need processing (excluded: titles containing '#' and titles with non-empty data).
            in_file: the loaded JSON data mapping title -> data (empty if file missing or load failed).
    """
    if not json_file.exists():
        logger.debug(f"json_file does not exist: {json_file.name}")
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
        logger.info(f"<<green>> get_titles_and_in_file(lang:{json_file.name}) \t titles: {len(titles):,}")
        logger.debug("nothing to do")
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
    """
    Determine which of the given titles still require processing for the specified language.

    Loads the language's aggregated views file and compares it to the provided titles. Returns the subset of titles that are missing or have empty data in the file. If no titles need processing or if every requested title is missing from the file, an empty list is returned.

    Parameters:
        langcode (str): Language code identifying the target views file.
        titles (list[str]): Titles to check.
        year (int): Ignored by this function (kept for API compatibility).

    Returns:
        list[str]: Titles that should be processed, or an empty list when none should be processed.
    """
    json_file = get_views_all_file(langcode)
    # ---
    titles_to_work, _ = get_titles_and_in_file(json_file, titles)
    # ---
    if titles_to_work == titles:
        return []
    # ---
    return titles_to_work
