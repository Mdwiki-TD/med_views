#!/usr/bin/python3
"""

python3 start_views.py
python3 I:/mdwiki/med_views/start_views.py

tfj run views0 --image python3.9 --command "$HOME/local/bin/python3 pybot/med_views/start_views.py"
tfj run views11 --image python3.9 --command "$HOME/local/bin/python3 pybot/med_views/start_views.py -max:1000"
tfj run views2 --image python3.9 --command "$HOME/local/bin/python3 pybot/med_views/start_views.py -min:1000 -max:5000"
tfj run views3 --image python3.9 --command "$HOME/local/bin/python3 pybot/med_views/start_views.py -min:5000 -max:10000"
tfj run views4 --image python3.9 --command "$HOME/local/bin/python3 pybot/med_views/start_views.py -min:10000 -max:19000"
tfj run views5 --image python3.9 --command "$HOME/local/bin/python3 pybot/med_views/start_views.py -min:19000"

"""
import json
import logging
import sys

import tqdm

from src.dump_utils import load_lang_titles_from_dump, load_languages_counts
from src.helps import get_views_all_file, is_empty_data, json_load
from src.stats_bot import dump_stats
from src.views_utils.views_helps import article_all_views

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def dump_one(file, data) -> None:
    # ---
    if not data:
        return
    # ---
    logger.debug(f"dump_one({file}), {len(data)=}")
    # ---
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


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
    for i in range(0, len(titles), 500):
        # ---
        group = titles[i : i + 500]
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
    for i in range(0, len(titles), 2000):
        # ---
        group = titles[i : i + 2000]
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


def load_one_lang_views_all(langcode, titles, year, max_items=1000, maxv=0):
    # ---
    """
    Load, render, and persist view data for a single language, optionally merging with existing file data.

    Parameters:
        langcode (str): Language code identifying which views file to read and write.
        titles (Sequence[str]): Candidate page titles for processing; will be filtered against titles already present in the views file.
        year (str): Year identifier used when rendering view data.
        max_items (int): Maximum number of items to include per rendered batch.
        maxv (int): If greater than zero, skip processing when the number of titles exceeds this limit.
    """
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
    data = render_data(titles, langcode, year, json_file, json_file_stats, max_items=max_items)
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


def generate_work_data(filter_by, langs, maxv, minx):
    """
    Builds a per-language work plan mapping each language to its full title list and the subset to process, applying minimum and maximum size filters.

    Parameters:
        filter_by (str): Which list to use when applying min/max limits; expected values include "titles" or "to_work".
        langs (Mapping): Mapping of language codes to metadata (used only for iteration order).
        maxv (int): Maximum allowed size for the chosen filter list; languages with larger lists are skipped.
        minx (int): Minimum required size for the chosen filter list; languages with smaller lists are skipped.

    Returns:
        dict: Mapping from language code to a dict with keys "titles" (list of all titles) and "to_work" (list of titles selected for processing). The returned mapping is sorted in ascending order by the length of the list indicated by `filter_by`.
    """
    work_data = {}
    # ---
    for lang, _ in tqdm.tqdm(langs.items()):
        # ---
        titles = load_lang_titles_from_dump(lang)
        # ---
        to_work = []
        # ---
        to_filter = titles
        # ---
        # to speed loading
        if filter_by != "titles":
            to_work = get_titles_to_work(lang, titles, "all")
        # ---
        if len(to_filter) == 0:
            continue
        # ---
        if minx > 0 and len(to_filter) < minx:
            logger.info(f"<<yellow>> {lang}>> len {filter_by} ({len(to_filter)}) < min {minx}, skipping")
            continue
        # ---
        if len(to_filter) > maxv:
            logger.info(f"<<yellow>> {lang}>> len {filter_by} ({len(to_filter)}) > max {maxv}, skipping")
            continue
        # ---
        # to speed loading
        if not to_work:
            to_work = get_titles_to_work(lang, titles, "all")
        # ---
        work_data[lang] = {"titles": titles, "to_work": to_work}
    # ---
    # sort work_data by len of to_work
    work_data = dict(sorted(work_data.items(), key=lambda item: len(item[1][filter_by]), reverse=False))
    return work_data


def parse_arg_limits():
    """
    Parse command-line limits for maximum and minimum item thresholds from sys.argv.

    Scans sys.argv for tokens of the form "-max:<N>" and "-min:<N>" and extracts their integer values. If a key is missing or its value is not a digit, the function uses the defaults.

    Returns:
        (maxv, minx) (tuple[int, int]): maxv is the parsed maximum value (default 1000000), minx is the parsed minimum value (default 0).
    """
    maxv = 1000000
    minx = 0
    # ---
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        if key == "-max" and val.isdigit():
            maxv = int(val)
        elif key == "-min" and val.isdigit():
            minx = int(val)
    return maxv, minx


def start(lang="", filter_by="titles"):
    # ---
    """
    Orchestrates generation of per-language work data and sequentially processes each language's view data.

    Builds a sorted work plan from available language counts, applies command-line min/max filters, and for each language logs a summary and invokes the per-language loader/updater unless execution is suppressed via command-line flags.

    Parameters:
        lang (str): Optional language code to target a single language. If empty, all eligible languages are considered.
        filter_by (str): Which list to base work sizing on; either "titles" or "to_work". Invalid values default to "titles".
    """
    langs = load_languages_counts()
    # ---
    if not langs:
        logger.error("No languages found, run `python3 start_titles.py` first")
        return
    # ---
    # sort langs by len of titles { "ar": 19972, "bg": 2138, .. }
    langs = dict(sorted(langs.items(), key=lambda item: item[1], reverse=False))
    # ---
    filter_by = filter_by if filter_by in ["titles", "to_work"] else "titles"
    # ---
    maxv, minx = parse_arg_limits()
    # ---
    work_data = generate_work_data(filter_by, langs, maxv, minx)
    # ---
    logger.info(f"<<green>> work_data: {len(work_data)}")
    # ---
    if not work_data:
        logger.info("No work_data found, exiting")
        return
    # ---
    for n, (lang, data) in enumerate(work_data.items(), start=1):
        # ---
        titles = data["titles"]
        # ---
        logger.info(f"<<yellow>> {n}/{len(work_data)} lang:{lang},\ttitles: {len(titles)}")
        # ---
        if "no" not in sys.argv:
            load_one_lang_views_all(lang, titles, "all")


if __name__ == "__main__":
    start()
