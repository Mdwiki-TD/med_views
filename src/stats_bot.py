#!/usr/bin/python3
"""


"""
import logging

from .dump_utils import dump_one

logger = logging.getLogger(__name__)


def dump_stats(json_file_stats, new_data) -> dict[str, int | dict[str, int]]:
    # ---
    data_hash = [x for x in new_data if x.find("#") != -1]
    # ---
    data2 = {x: new_data[x] for x in new_data if x not in data_hash}
    # ---
    empty = [v for v in data2.values() if v == 0]
    # ---
    views = sum(v for v in data2.values() if isinstance(v, int))
    # ---
    stats = {
        "all": len(data2),
        "empty": len(empty),
        "not_empty": len(data2) - len(empty),
        "hash": len(data_hash),
        "views": views,
    }
    # ---
    dump_one(json_file_stats, stats)
    # ---
    return stats
