#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/bot -year:2025 ask

python3 core8/pwb.py med_views/bot -max:50 ask

python3 core8/pwb.py med_views/bot -limit:50
python3 core8/pwb.py med_views/bot local ask

tfj run umv --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/bot -max:1000"

tfj run umvsh --image tf-python39 --command "$HOME/pybot/md_core/med_views/run.sh"

"""
import logging
import sys

from newapi.mdwiki_page import md_MainPage

from med_views.titles import load_lang_titles
from views_all_bots.utils import count_all_langs
from views_all_bots.views import load_one_lang_views

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_one_lang_views(langcode, titles, year, maxv=0):
    # ---
    views_t = load_one_lang_views(langcode, titles, year, maxv=maxv)
    # ---
    # print(views_t)
    # ---
    total = 0
    # ---
    for _, views in views_t.items():
        if isinstance(views, dict):
            views = views.get("all", 0)
        # ---
        total += views
    # ---
    if total == 0:
        logger.info(f"<<yellow>> No views for {langcode}")
        # logger.info("views_t" + str(views_t))
        # logger.info("titles" + str(titles))
    # ---
    return total


def make_text(languages, views):
    # ---
    total_views = sum(views.values())
    total_articles = sum(languages.values())
    # ---
    text = "{{WPM:WikiProject Medicine/Total medical views by language}}\n"
    # ---
    text += f"* Total views for medical content = {total_views:,}\n"
    text += f"* Total articles= {total_articles:,}\n"
    # ---
    text += "\n"
    # ---
    text += """{| class="wikitable sortable"\n!Rank\n!Lang\n!# of articles\n!Total views\n!Ave. views\n|----"""
    # ---
    # sort languages by count
    languages = {k: v for k, v in sorted(languages.items(), key=lambda item: item[1], reverse=True)}
    # ---
    for n, (lang, articles) in enumerate(languages.items(), start=1):
        # ---
        lang_views = views.get(lang, 0)
        # ---
        Average_views = lang_views // articles if articles and lang_views else 0
        # ---
        text += (
            f"\n|{n}"
            f"\n|[//{lang}.wikipedia.org {lang}]"
            f"\n|{articles:,}"
            f"\n|{lang_views:,}"
            f"\n|{Average_views:,}"
            "\n|-"
        )
    # ---
    text += "\n|}"
    # ---
    return text


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
    languages = count_all_langs()
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
    page = md_MainPage(title, "www", family="mdwiki")
    # ---
    text = page.get_text()
    # ---
    if text == newtext:
        logger.info("No change")
        return
    # ---
    logger.info(f"Total views not 0: {views_not_0:,}")
    # ---
    if page.exists():
        page.save(newtext=newtext, summary="update", nocreate=0, minor="")
    else:
        page.Create(newtext, summary="update")


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
