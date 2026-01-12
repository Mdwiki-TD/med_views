#!/usr/bin/python3
"""

"""
import sys

from .dump_utils import load_lang_titles_from_dump
from .sql_utils import one_lang_titles


def load_lang_titles(lang):
    # ---
    """
    Retrieve page titles for the given language, preferring a dump-derived source and falling back to a SQL source.
    
    If titles are available from the dump, those are returned. If not and the process was started with "local" in sys.argv, an empty list is returned. Otherwise titles are fetched from the SQL source and any underscores in each title are replaced with spaces.
    
    Parameters:
        lang (str): Language code or identifier to load titles for.
    
    Returns:
        list[str]: A list of page title strings for the language.
    """
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