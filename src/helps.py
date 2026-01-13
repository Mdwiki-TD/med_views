#!/usr/bin/python3
"""


"""
import json
import logging

from .config import stats_path

logger = logging.getLogger(__name__)


def is_empty_data(data):
    # ---
    # logger.debug(data)
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
    """
    Load JSON from a file and normalize underscore-separated names to space-separated names.

    Loads and parses the JSON at `json_file`. If the top-level value is a dict, returns a new dict with all keys having underscores replaced by spaces. If the top-level value is a list, returns a new list where string elements have underscores replaced by spaces; non-string list elements are returned unchanged. Returns the parsed value unchanged for other JSON types. If the file is missing or contains invalid JSON, returns `None`.

    Parameters:
        json_file (str | os.PathLike): Path to the JSON file to load.

    Returns:
        None | dict | list: The normalized JSON structure, or `None` if loading/parsing failed.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            u_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load JSON from {json_file}: {e}")
        return None

    if isinstance(u_data, dict):
        return {x.replace("_", " "): v for x, v in u_data.items()}

    if isinstance(u_data, list):
        return [x.replace("_", " ") if isinstance(x, str) else x for x in u_data]

    return u_data


def get_stats_file(lang):
    # ---
    """
    """
    dir_v = stats_path
    # ---
    if not dir_v.exists():
        dir_v.mkdir(parents=True)
    # ---
    file = dir_v / f"{lang}.json"
    # ---
    return file
