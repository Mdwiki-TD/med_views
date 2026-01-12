#!/usr/bin/python3
"""

"""
import sys

from .dump_utils import load_lang_titles_from_dump
from .sql_utils import one_lang_titles


def load_lang_titles(lang):
    # ---
    data = load_lang_titles_from_dump(lang)
    # ---
    if data:
        return data
    # ---
    if "local" in sys.argv:
        return []
    # ---
    data = one_lang_titles(lang)
    # ---
    data = [x.replace("_", " ") for x in data]
    # ---
    return data
