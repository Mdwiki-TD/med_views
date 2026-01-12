#!/usr/bin/python3
"""


"""
import json
import logging
import sys

from .config import views_new_path
from .dump_utils import dump_one
from .helps import is_empty_data

logger = logging.getLogger(__name__)


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
    # logger.debug(stats)
    # ---
    dump_one(json_file_stats, stats)
    # ---
    return stats


def update_all_stats(stats_data):
    # ---
    """
    Write provided statistics to views_new_path/stats.json when the process was invoked with the "update_stats" command-line flag.

    If "update_stats" is not present in sys.argv the function returns without writing. When the flag is present, the function serializes stats_data as JSON to the file views_new_path / "stats.json" using UTF-8 encoding and ensure_ascii=False.

    Parameters:
        stats_data (dict): Mapping of statistic keys to values to be written to the stats file.
    """
    stats_file = views_new_path / "stats.json"
    # ---
    if "update_stats" not in sys.argv:
        logger.debug("add 'update_stats' to sys.argv to update stats.json")
        return
    # ---
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, ensure_ascii=False)
    # ---
    logger.debug(f"update_all_stats: {len(stats_data)=:,}")
