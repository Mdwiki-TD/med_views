#!/usr/bin/python3
"""
python3 start_views_all_years.py
Collects and stores article views for all years (2015-2025)
"""
import json
import logging
import sys

from src.config import main_dump_path
from src.views_all_years import get_one_lang_views
from src.dump_utils import count_languages_in_json, load_languages_counts
from src.sql_utils import get_language_article_counts_sql
from src.titles_utils import load_lang_titles
from src.views_utils.views_helps import (
    get_view_file,
)
from src.stats_bot_all_years import dump_stats, dump_stats_all

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

empty_data_all = {}


def dump_empty_data_all() -> None:
    # ---
    file = main_dump_path / "empty_views_all_years.json"
    logger.debug(f"dump_empty_data_all({file}), {len(empty_data_all)=}")
    # ---
    # sort empty_data_all by len of values desc
    empty_data_all_sorted = dict(
        sorted(empty_data_all.items(), key=lambda item: len(item[1]), reverse=True)
    )
    # ---
    with open(file, "w", encoding="utf-8") as f:
        json.dump(empty_data_all_sorted, f, ensure_ascii=False, indent=4)


def dump_one_lang_files(titles, data, lang) -> None:
    # ---
    if not data:
        return
    # ---
    titles = [x.replace("_", " ") for x in titles]
    # ---
    logger.debug(f"dump_one_lang_files for {lang}, {len(data)=}")
    # ---
    if isinstance(data, dict):
        data = {x.replace("_", " "): v for x, v in data.items()}
    # ---
    if isinstance(data, list):
        data = [x.replace("_", " ") if isinstance(x, str) else x for x in data]
    # ---
    dump_stats(titles, data, lang)
    # ---
    # Separate data by year and save to corresponding year folders
    # First, organize data by year
    years_data = {}
    
    for title, views in data.items():
        if isinstance(views, dict):
            # views is a dictionary of {year: count}
            for year, count in views.items():
                if year not in years_data:
                    years_data[year] = {}
                years_data[year][title] = count
        elif isinstance(views, int):
            # Single value, might be from "all" or a specific year
            # We'll skip this for now or handle as needed
            pass
    
    # Save each year's data to its corresponding folder
    for year, year_data in years_data.items():
        file = get_view_file(lang, year)
        # Filter out zero values
        not_empty_data = {k: v for k, v in year_data.items() if v != 0}
        
        if not_empty_data:
            with open(file, "w", encoding="utf-8") as f:
                json.dump(not_empty_data, f, ensure_ascii=False)
    
    # Track empty data across all years
    empty_data = []
    for k in titles:
        val = data.get(k, 0)
        if val == 0:
            empty_data.append(k)
        elif isinstance(val, dict):
            # Check if all year values are 0
            if all(v == 0 for v in val.values()):
                empty_data.append(k)
    
    if empty_data:
        empty_data_all[lang] = empty_data


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


def make_views(languages, limit, maxv=0) -> dict[str, dict]:
    # ---
    views = {}
    # ---
    for n, (lang, _) in enumerate(languages.items(), start=1):
        # ---
        if limit > 0 and n > limit:
            logger.info(f"limit {limit} reached, break")
            break
        # ---
        data = process_language_views(lang, maxv)
        # ---
        views[lang] = data
    # ---
    dump_stats_all()
    dump_empty_data_all()
    # ---
    return views


def process_language_views(lang, maxv=0) -> dict[str, dict]:
    # ---
    titles = load_lang_titles(lang)
    # ---
    # For all years, we'll check an existing file from the current year to see what titles we already have
    # Use the current year or latest available year as reference
    import datetime
    current_year = datetime.datetime.now().year
    # Ensure we don't go beyond 2025
    reference_year = min(current_year, 2025)
    json_file = get_view_file(lang, reference_year)
    # ---
    data = get_one_lang_views(lang, titles, json_file, maxv=maxv)
    # ---
    dump_one_lang_files(titles, data, lang)
    # ---
    return data


def start(limit, maxv):
    # ---
    """
    Orchestrates collection of per-language pageview totals for all years (2015-2025).

    Retrieves stored language article counts, computes pageviews (respecting `limit` and `maxv`), 
    and saves the data for each year in separate folders within views_by_year_path.

    Parameters:
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
    make_views(languages, limit, maxv)


def parse_args():
    limit = 0
    maxv = 0
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        if key in ["limit", "-limit"] and val.isdigit():
            limit = int(val)
        elif key in ["max", "-max"] and val.isdigit():
            maxv = int(val)
    return limit, maxv


if __name__ == "__main__":
    limit, maxv = parse_args()
    start(limit, maxv)
