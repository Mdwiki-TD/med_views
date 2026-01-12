#!/usr/bin/python3
"""

"""
import logging
import sys

from src.dump_utils import load_languages_counts, dump_all, count_languages_in_json
from src.sql_utils import get_language_article_counts_sql
from src.mdwiki_page import page
from src.texts_utils import make_text

from src.titles_utils import load_lang_titles
from src.views import get_one_lang_views

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_languages_articles_counts():
    # ---
    all_infos = load_languages_counts()
    # ---
    if not all_infos and ("local" not in sys.argv):
        data = get_language_article_counts_sql()
        dump_all(data)
        return data
    # ---
    if all_infos:
        return all_infos
    # ---
    result = count_languages_in_json()
    # ---
    print(f"get_languages_articles_counts local: {len(result)}")
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
    title = f"WikiProjectMed:WikiProject Medicine/Stats/Total pageviews by language {year}"
    # ---
    languages = get_languages_articles_counts()
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
