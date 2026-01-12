#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/titles


"""

from views_all_bots.dump_utils import (
    dump_one,
    dump_all,
    t_dump_dir,
)
from views_all_bots.sql_utils import (
    retrieve_medicine_titles,
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


def start():
    # ---
    all_links = retrieve_medicine_titles()
    # ---
    dump_all({x: len(y) for x, y in all_links.items()})
    # ---
    dump_data(all_links)


if __name__ == "__main__":
    start()
