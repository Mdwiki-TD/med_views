#!/usr/bin/python3
"""


"""
import logging

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
