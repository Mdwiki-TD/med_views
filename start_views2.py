#!/usr/bin/python3
"""
python3 I:/mdwiki/med_views/start_views2.py
"""
import logging
import sys

from src.views import get_one_lang_views_by_titles, update_data
from src.dump_utils import count_languages_in_json, load_languages_counts
from src.sql_utils import get_language_article_counts_sql
from src.titles_utils import load_lang_titles
from src.dump_utils import dump_one
from src.helps import get_views_all_file, json_load
from src.views_utils.views_helps import (
    get_view_file,
)
from src.stats_bot import dump_stats

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def load_one_lang_views(langcode, titles, year, maxv=0):
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
    # ---
    titles_not_in_file.sort()
    # ---
    if maxv > 0 and len(titles_not_in_file) > maxv:
        logger.info(f"<<yellow>> {langcode}: {len(titles)} titles > max {maxv}, skipping")
    elif "local" in sys.argv:
        logger.info(f"<<green>> load_one_lang_views(lang:{langcode}) \t titles: {len(titles):,}")
    else:
        views_t = load_one_lang_views(langcode, titles_not_in_file, year)
        u_data = update_data(u_data, views_t)
    # ---
    return u_data


def make_views(languages, year, limit, maxv) -> dict:
    # ---
    views = {}
    # ---
    for n, (lang, _) in enumerate(languages.items(), start=1):
        # ---
        if limit > 0 and n > limit:
            logger.info(f"limit {limit} reached, break")
            break
        # ---
        json_file = get_view_file(lang, year)
        json_file_stats = get_views_all_file(lang, "stats")
        # ---
        titles = load_lang_titles(lang)
        # ---
        data = get_one_lang_views(lang, titles, year, json_file, maxv=maxv)
        # ---
        dump_one(json_file, data)
        # ---
        dump_stats(json_file_stats, data)
        # ---
        views[lang] = data
    # ---
    return views


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
    year = 2024
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
