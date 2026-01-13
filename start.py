#!/usr/bin/python3
"""
python3 I:/mdwiki/med_views/start.py
"""
import logging
import json
import sys

from src.dump_utils import count_languages_in_json, load_languages_counts
from src.texts_utils import make_text
from src.helps import json_load
from src.wiki import page
from src.config import main_dump_path

from src.views_utils.views_helps import (
    get_view_file,
)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def get_languages_articles_counts() -> dict:
    # ---
    all_infos = load_languages_counts()
    # ---
    if all_infos:
        return all_infos
    # ---
    result = count_languages_in_json()
    # ---
    logger.debug(f"get_languages_articles_counts local: {len(result)}")
    # ---
    return result


def calculate_total_views(langcode, u_data):
    # ---
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


def fetch_language_statistics(year, langcode):
    # ---
    json_file = get_view_file(langcode, year)
    year_data = json_load(json_file)
    # ---
    return calculate_total_views(langcode, year_data)


def make_views_local(languages, year, limit):
    # ---
    views = {}
    # ---
    for n, (lang, _) in enumerate(languages.items(), start=1):
        # ---
        if limit > 0 and n > limit:
            logger.info(f"limit {limit} reached, break")
            break
        # ---
        views[lang] = fetch_language_statistics(year, lang)
    # ---
    return views


def start(year, limit):
    # ---
    """
    Orchestrates collection of per-language pageview totals for a given year and updates the corresponding wiki stats page.

    Retrieves stored language article counts, computes pageviews (respecting `limit`), generates page text, and saves the page if content changed. The function logs progress and exits early without modifying the wiki when no language data or no non-zero views are available.

    Parameters:
        year (int): Year used in view calculations and included in the target wiki page title.
        limit (int): Maximum number of languages to process (0 means no limit).
    """
    title = f"WikiProjectMed:WikiProject Medicine/Stats/Total pageviews by language {year}"
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
    views = make_views_local(languages, year, limit)
    # ---
    views_not_0 = len([x for x in views.values() if x > 0])
    # ---
    logger.info(f"<<yellow>> Total views not 0: {views_not_0:,}")
    # ---
    if not views_not_0:
        logger.info("No views found, run `python3 start_views.py` first")
        return
    # ---
    # sort views by value DESC
    views = {k: v for k, v in sorted(views.items(), key=lambda item: item[1], reverse=True)}
    # ---
    # dump views
    with open(main_dump_path / f"views_{year}.json", "w", encoding="utf-8") as f:
        json.dump(views, f, ensure_ascii=False, indent=4)
    # ---
    newtext = make_text(languages, views)
    # ---
    with open(main_dump_path / "text.txt", "w", encoding="utf-8") as f:
        f.write(newtext)
    # ---
    target_page = page(title)
    # ---
    text = target_page.get_text()
    # ---
    if text == newtext:
        logger.info("No change")
        return
    # ---
    logger.info(f"Total views not 0: {views_not_0:,}")
    # ---
    if target_page.exists():
        target_page.save(newtext=newtext, summary="update", nocreate=0, minor="")
    else:
        target_page.Create(newtext, summary="update")


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
