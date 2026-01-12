#!/usr/bin/python3
"""

python3 start_views.py
python3 I:/mdwiki/med_views/start_views.py

tfj run views0 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start"
tfj run views --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -max:1000"
tfj run views1 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:1000 -max:5000"
tfj run views2 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:5000 -max:10000"
tfj run views3 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:10000 -max:19000"
tfj run views4 --image python3.9 --command "$HOME/local/bin/python3 core8/pwb.py med_views/views_all_run start -min:19000"

"""
import logging
import sys

import tqdm

from src.dump_utils import load_lang_titles_from_dump, load_languages_counts
from src.helps import get_views_all_file
from src.views_utils.views_all import dump_it, get_titles_and_in_file, get_titles_to_work, render_data, update_data_new

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_one_lang_views_all(langcode, titles, year, max_items=1000, maxv=0):
    # ---
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
        to_work = data["to_work"]
        # ---
        logger.info(f"<<yellow>> {n}/{len(work_data)} lang:{lang},\ttitles: {len(titles)}, to_work: {len(to_work)}")
        # ---
        if "no" not in sys.argv:
            load_one_lang_views_all(lang, titles, "all")


if __name__ == "__main__":
    start()
