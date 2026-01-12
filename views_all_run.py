#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/views_all_run

tfj run views0 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start"
tfj run views --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -max:1000"
tfj run views1 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:1000 -max:5000"
tfj run views2 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:5000 -max:10000"
tfj run views3 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:10000 -max:19000"
tfj run views4 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:19000"

"""
import logging
import sys
from pathlib import Path

import tqdm

from med_views.views_all_bots.helps import get_views_all_file, json_load
from med_views.views_all_bots.stats_bot import update_all_stats
from views_all_bots.utils import load_lang_titles_from_dump, load_languages_counts
from views_all_bots.views_all import article_all_views, dump_stats, get_titles_to_work, load_one_lang_views_all

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def start(lang="", filter_by="titles"):
    # python3 core8/pwb.py med_views/views_all_run start2
    langs = load_languages_counts()
    # ---
    filter_by = filter_by if filter_by in ["titles", "to_work"] else "titles"
    # ---
    maxv = 1000000
    minx = 0
    # ---
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        if key == "-max" and val.isdigit():
            maxv = int(val)
        elif key == "-min" and val.isdigit():
            minx = int(val)
    # ---
    # sort langs by len of titles { "ar": 19972, "bg": 2138, .. }
    langs = dict(sorted(langs.items(), key=lambda item: item[1], reverse=False))
    # ---
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
    # ---
    logger.info(f"<<green>> work_data: {len(work_data)}")
    # ---
    for n, (lang, data) in enumerate(work_data.items(), start=1):
        # ---
        titles = data["titles"]
        to_work = data["to_work"]
        # ---
        logger.info(f"<<yellow>> {n}/{len(work_data)} lang:{lang},\ttitles: {len(titles)}, to_work: {len(to_work)}")
        # ---
        if "no" not in sys.argv:
            load_one_lang_views_all(lang, titles, "all")


def start2(lang=""):
    # python3 core8/pwb.py med_views/views_all_run start
    return start(filter_by="to_work")


def test2(lang=""):
    # python3 core8/pwb.py med_views/views_all_run test2
    titles = ["Yemen", "COVID-19", "Iran–Israel war", "wj2340-0"]
    # ---
    ux = article_all_views("en", titles, 2024)
    # ---
    for t, tt in ux.items():
        print(t, tt)
    # ---
    print(f"{len(ux)=:,}")


def hash_it(lang=""):
    # python3 core8/pwb.py med_views/views_all_run hash_it -lang:nup
    # ---
    langs = load_languages_counts()
    # ---
    if lang:
        if lang in langs:
            langs = {lang: langs[lang]}
        else:
            logger.info(f"hash_it: lang {lang} not found")
            return
    # ---
    stats_file = Path(__file__).parent / "views_new/stats.json"
    # ---
    with open(stats_file, "r", encoding="utf-8") as f:
        stats_data = {}
    # ---
    for langcode, _ in langs.items():
        json_file = get_views_all_file(langcode)
        json_file_stats = get_views_all_file(langcode, "stats")
        # ---
        if not json_file.exists():
            continue
        # ---
        new_data = json_load(json_file)
        # ---
        if new_data:
            stats_data[langcode] = dump_stats(json_file_stats, new_data)
    # ---
    update_all_stats(stats_data)


def test(lang=""):
    # ---
    lang = lang or "pa"
    # ---
    # python3 core8/pwb.py med_views/views_all_run test
    titles = load_lang_titles_from_dump(lang)
    # ---
    print("load_one_lang_views_all:")
    load_one_lang_views_all(lang, titles, "all")


if __name__ == "__main__":
    # ---
    defs = {
        "start": start,
        "start2": start2,
        "test2": test2,
        "test": test,
        "hash_it": hash_it,
    }
    # ---
    lang = ""
    # ---
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        # ---
        if key == "-lang":
            lang = val
    # ---
    for arg in sys.argv:
        key, _, val = arg.partition(":")
        # ---
        if arg in defs:
            defs[arg](lang=lang)
    # ---
    # python3 core8/pwb.py med_views/views_all_run test -lang:ha
    # python3 core8/pwb.py med_views/views_all_run test -lang:kn
    # python3 core8/pwb.py med_views/views_all_run test -lang:be-x-old
