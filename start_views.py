#!/usr/bin/python3
"""
python3 I:/mdwiki/med_views/start_views2.py
"""
import json
import logging
import sys

from src.config import main_dump_path
from src.views import get_one_lang_views
from src.dump_utils import count_languages_in_json, load_languages_counts
from src.sql_utils import get_language_article_counts_sql
from src.titles_utils import load_lang_titles
from src.views_utils.views_helps import (
    get_view_file,
)
from src.stats_bot import dump_stats, dump_stats_all

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

empty_data_all = {}


def dump_empty_data_all(year) -> None:
    # ---
    file = main_dump_path / f"empty_views_{year}.json"
    logger.debug(f"dump_empty_data_all({file}), {len(empty_data_all)=}")
    # ---
    # sort empty_data_all by len of values desc
    empty_data_all_sorted = dict(
        sorted(empty_data_all.items(), key=lambda item: len(item[1]), reverse=True)
    )
    # ---
    with open(file, "w", encoding="utf-8") as f:
        json.dump(empty_data_all_sorted, f, ensure_ascii=False, indent=4)


def dump_one_lang_files(titles, data, lang, year) -> None:
    # ---
    file = get_view_file(lang, year)
    # ---
    if not data:
        return
    # ---
    titles = [x.replace("_", " ") for x in titles]
    # ---
    logger.debug(f"dump_one({file}), {len(data)=}")
    # ---
    if isinstance(data, dict):
        data = {x.replace("_", " "): v for x, v in data.items()}
    # ---
    if isinstance(data, list):
        data = [x.replace("_", " ") if isinstance(x, str) else x for x in data]
    # ---
    dump_stats(titles, data, lang)
    # ---
    empty_data = [k for k in titles if data.get(k, 0) == 0]
    # ---
    not_empty_data = {k: v for k, v in data.items() if v != 0}
    # ---
    if empty_data:
        empty_data_all[lang] = empty_data
    # ---
    with open(file, "w", encoding="utf-8") as f:
        json.dump(not_empty_data, f, ensure_ascii=False)


def get_languages_articles_counts():
    # ---
    all_infos = load_languages_counts()
    # ---
    if not all_infos and ("local" not in sys.argv):
        data = get_language_article_counts_sql()
        return data
    # ---
    if all_infos:
        return all_infos
    # ---
    result = count_languages_in_json()
    # ---
    logger.debug(f"get_languages_articles_counts local: {len(result)}")
    # ---
    return result


def make_views(languages, year, limit, maxv=0) -> dict[str, int]:
    # ---
    views = {}
    # ---
    for n, (lang, _) in enumerate(languages.items(), start=1):
        # ---
        if limit > 0 and n > limit:
            logger.info(f"limit {limit} reached, break")
            break
        # ---
        data = process_language_views(year, lang, maxv)
        # ---
        views[lang] = data
    # ---
    dump_stats_all(year)
    dump_empty_data_all(year)
    # ---
    return views


def process_language_views(year, lang, maxv=0) -> dict[str, int]:
    # ---
    titles = load_lang_titles(lang)
    # ---
    json_file = get_view_file(lang, year)
    # ---
    data = get_one_lang_views(lang, titles, year, json_file, maxv=maxv)
    # ---
    dump_one_lang_files(titles, data, lang, year)
    # ---
    return data


def start(year, limit, maxv):
    # ---
    """
    Orchestrates collection of per-language pageview totals for a given year and updates the corresponding wiki stats page.

    Retrieves stored language article counts, computes pageviews (respecting `limit` and `maxv`), generates page text, and saves the page if content changed. The function logs progress and exits early without modifying the wiki when no language data or no non-zero views are available.

    Parameters:
        year (int): Year used in view calculations and included in the target wiki page title.
        limit (int): Maximum number of languages to process (0 means no limit).
        maxv (int): Upper bound applied to per-language view calculations (0 means no cap).
    """
    # ---
    languages = get_languages_articles_counts()
    # ---
    logger.info(f"get_languages_articles_counts local: {len(languages)}")
    # ---
    if not languages or list(set(languages.values())) == [0]:
        logger.error("No languages found, run `python3 start_titles.py` first")
        return
    # ---
    # sort languages ASC
    languages = {k: v for k, v in sorted(languages.items(), key=lambda item: item[1], reverse=False)}
    # ---
    make_views(languages, year, limit, maxv)


def parse_args():
    year = 2025
    limit = 0
    maxv = 0
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        if key in ["limit", "-limit"] and val.isdigit():
            limit = int(val)
        elif key in ["year", "-year"] and val.isdigit():
            year = int(val)
        elif key in ["max", "-max"] and val.isdigit():
            maxv = int(val)
    return year, limit, maxv


if __name__ == "__main__":
    year, limit, maxv = parse_args()
    start(year, limit, maxv)
