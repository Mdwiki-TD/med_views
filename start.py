#!/usr/bin/python3
"""
python3 I:/mdwiki/med_views/start.py
"""
import logging
import sys

from src.dump_utils import count_languages_in_json, dump_languages_counts, load_languages_counts
from src.sql_utils import get_language_article_counts_sql
from src.texts_utils import make_text
from src.titles_utils import load_lang_titles
from src.views import get_one_lang_views
from src.wiki.mdwiki_page import page

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_languages_articles_counts():
    # ---
    all_infos = load_languages_counts()
    # ---
    if not all_infos and ("local" not in sys.argv):
        data = get_language_article_counts_sql()
        dump_languages_counts(data)
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


def make_views(languages, year, limit, maxv):
    # ---
    views = {}
    # ---
    for n, (lang, _) in enumerate(languages.items(), start=1):
        # ---
        if limit > 0 and n > limit:
            logger.info(f"limit {limit} reached, break")
            break
        # ---
        titles = load_lang_titles(lang)
        # ---
        views[lang] = get_one_lang_views(lang, titles, year, maxv=maxv)
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
    views = make_views(languages, year, limit, maxv)
    # ---
    views_not_0 = len([x for x in views.values() if x > 0])
    # ---
    logger.info(f"<<yellow>> Total views not 0: {views_not_0:,}")
    # ---
    if not views_not_0:
        logger.info("No views found, run `python3 start_views.py` first")
        return
    # ---
    newtext = make_text(languages, views)
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
