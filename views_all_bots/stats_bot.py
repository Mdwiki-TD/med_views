#!/usr/bin/python3
"""


"""
import json
import sys
from pathlib import Path

from .helps import is_empty_data
from .utils import dump_one


def sum_all_views_new(new_data):
    views = {}
    for x in new_data.values():
        for k, v in x.items():
            views[k] = views.get(k, 0) + v

    views = dict(sorted(views.items(), key=lambda item: item[0], reverse=False))

    # remove any key < 2015 and not = "all"
    views = {k: v for k, v in views.items() if (k.isnumeric() and int(k) >= 2015) or k == "all" or v > 0}

    return views


def dump_stats(json_file_stats, new_data):
    # ---
    data_hash = [x for x in new_data if x.find("#") != -1]
    # ---
    data2 = {x: new_data[x] for x in new_data if x not in data_hash}
    # ---
    empty = [x for x in data2.values() if is_empty_data(x)]
    # ---
    views = sum_all_views_new(new_data)
    # ---
    stats = {
        "all": len(data2),
        "empty": len(empty),
        "not_empty": len(data2) - len(empty),
        "hash": len(data_hash),
        "views": views,
    }
    # ---
    # print(stats)
    # ---
    dump_one(json_file_stats, stats)
    # ---
    return stats


def update_all_stats(stats_data):
    # ---
    stats_file = Path(__file__).parent.parent / "views_new/stats.json"
    # ---
    if "update_stats" not in sys.argv:
        print("add 'update_stats' to sys.argv to update stats.json")
        return
    # ---
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, ensure_ascii=False)
    # ---
    print(f"update_all_stats: {len(stats_data)=:,}")
