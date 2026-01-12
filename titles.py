#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/titles

from med_views.titles import load_lang_titles

"""
import sys

from views_all_bots.utils import (
    dump_one,
    langs_titles,
    load_lang_titles_from_dump,
    one_lang_titles,
    t_dump_dir,
)


def dump_data(all_data):
    # ---
    for n, (lang, titles) in enumerate(all_data.items(), start=1):
        # ---
        print(f"dump_data(): lang:{n}/{len(all_data)} \t {lang} {len(titles)}")
        # ---
        file = t_dump_dir / f"{lang}.json"
        # ---
        dump_one(file, titles)
    # ---
    print(f"dump_data: all langs: {len(all_data)}")


def load_lang_titles(lang):
    # ---
    data = load_lang_titles_from_dump(lang)
    # ---
    data = [x.replace("_", " ") for x in data]
    # ---
    if data:
        return data
    # ---
    if "local" in sys.argv:
        return {}
    # ---
    data = one_lang_titles(lang)
    # ---
    data = [x.replace("_", " ") for x in data]
    # ---
    return data


def start():
    # ---
    # languages = count_all_langs()
    # ---
    all_links = langs_titles()
    # ---
    dump_data(all_links)


if __name__ == "__main__":
    start()
