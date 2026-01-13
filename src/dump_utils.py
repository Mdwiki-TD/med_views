#!/usr/bin/python3
"""

"""
import json
import logging

from .config import json_titles_path, main_dump_path

logger = logging.getLogger(__name__)


def count_languages_in_json():
    """
    Count items in each language JSON file in json_titles_path.

    Scans json_titles_path for files with a .json extension, uses each file's stem as the language key, and records the number of top-level items in that file.

    Returns:
        dict: Mapping from language code (file stem) to the count of top-level JSON items.
    """
    result = {}
    # ---
    for json_file in json_titles_path.glob("*.json"):
        lang = json_file.stem
        # ---
        with open(json_file, "r", encoding="utf-8") as f:
            result[lang] = len(json.load(f))
    return result


def load_lang_titles_from_dump(lang):
    # ---
    """
    Load title strings for the given language from the JSON dump, replacing underscores with spaces.

    Parameters:
        lang (str): Language identifier used as the JSON filename (e.g., 'en' for en.json).

    Returns:
        list[str]: A list of title strings with underscores replaced by spaces; returns an empty list if the language file does not exist.
    """
    json_file = json_titles_path / f"{lang}.json"
    # ---
    if json_file.exists():
        # ---
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # ---
        data = [x.replace("_", " ") for x in data]
        return data
    # ---
    return []


def dump_one(file, data) -> None:
    # ---
    if not data:
        return
    # ---
    logger.debug(f"dump_one({file}), {len(data)=}")
    # ---
    if isinstance(data, dict):
        data = {x.replace("_", " "): v for x, v in data.items()}

    if isinstance(data, list):
        data = [x.replace("_", " ") if isinstance(x, str) else x for x in data]

    # ---
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def dump_languages_counts(data: dict[str, int]) -> None:
    """
    Write language count data to the main dump file when there are more than 200 entries.

    The input mapping is sorted by count in descending order and written to
    main_dump_path/languages_counts.json as JSON. If `data` is empty or has
    200 or fewer entries, no file is written.

    Parameters:
        data (dict): Mapping of language identifiers to integer counts.
    """
    file = main_dump_path / "languages_counts.json"
    # ---
    # sort data
    data = {k: v for k, v in sorted(data.items(), key=lambda item: item[1], reverse=True)}
    # ---
    if data and len(data) > 200:
        dump_one(file, data)


def load_languages_counts() -> dict:
    """
    Load the saved mapping of language codes to article counts from the main dump file.

    Returns:
        dict: A mapping from language code (str) to count (int) loaded from "languages_counts.json",
        or an empty dict if the file does not exist.
    """
    file = main_dump_path / "languages_counts.json"
    # ---
    data = {}
    # ---
    if file.exists():
        # ---
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    # ---
    logger.debug(f"load_languages_counts({file}), {len(data)=}")
    # ---
    return data
