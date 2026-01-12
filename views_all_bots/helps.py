#!/usr/bin/python3
"""

from med_views.views_all_bots.helps import json_load, get_views_all_file, update_data_new, is_empty_data

"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def is_empty_data(data):
    # ---
    # print(data)
    # ---
    if not data:
        return True
    # ---
    if data.get("all", 0) == 0:
        return True
    # ---
    if len(data) == 1:
        return True
    # ---
    # if any of values is 0
    # if any([x == 0 for x in data.values()]): return True
    # ---
    return False


def json_load(json_file):
    # ---
    u_data = False
    # ---
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            u_data = json.load(f)
    except Exception as e:
        logger.info(f"<<red>> json_load({json_file}) {e}")
    # ---
    if isinstance(u_data, dict):
        u_data = {x.replace("_", " "): v for x, v in u_data.items()}
    elif isinstance(u_data, list):
        u_data = [x.replace("_", " ") for x in u_data]
    # ---
    return u_data


def get_views_all_file(lang, subdir="all"):
    # ---
    dir_v = Path(__file__).parent.parent / "views_new" / subdir
    # ---
    if not dir_v.exists():
        dir_v.mkdir(parents=True)
    # ---
    file = dir_v / f"{lang}.json"
    # ---
    return file


def update_data_new(all_data, data):
    # ---
    for title, counts in data.items():
        all_data.setdefault(title, {})
        # ---
        all_data[title].update(
            {x: v for x, v in counts.items() if (x not in all_data[title] or all_data[title][x] == 0)}
        )
    # ---
    return all_data
