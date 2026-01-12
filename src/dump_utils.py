#!/usr/bin/python3
"""

"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
t_dump_dir = Path(__file__).parent / "titles"

if not t_dump_dir.exists():
    t_dump_dir.mkdir()


def count_languages_in_json():
    result = {}
    # ---
    for json_file in t_dump_dir.glob("*.json"):
        lang = json_file.stem
        # ---
        with open(json_file, "r", encoding="utf-8") as f:
            result[lang] = len(json.load(f))
    return result


def load_lang_titles_from_dump(lang):
    # ---
    json_file = t_dump_dir / f"{lang}.json"
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


def dump_one(file, data):
    # ---
    if not data:
        return
    # ---
    logger.debug(f"dump_one({file}), {len(data)=}")
    # ---
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        # json.dump(data, f, ensure_ascii=False, indent=2)


def dump_all(data):
    file = Path(__file__).parent / "languages_counts.json"
    # ---
    # sort data
    data = {k: v for k, v in sorted(data.items(), key=lambda item: item[1], reverse=True)}
    # ---
    if data and len(data) > 200:
        dump_one(file, data)


def load_languages_counts():
    file = Path(__file__).parent / "languages_counts.json"
    # ---
    if file.exists():
        # ---
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    # ---
    return {}
