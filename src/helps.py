#!/usr/bin/python3
"""


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


def json_load(json_file) -> None | dict | list:
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            u_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load JSON from {json_file}: {e}")
        return None

    if isinstance(u_data, dict):
        return {x.replace("_", " "): v for x, v in u_data.items()}

    if isinstance(u_data, list):
        return [x.replace("_", " ") for x in u_data]

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
