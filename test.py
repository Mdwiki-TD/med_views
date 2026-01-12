#!/usr/bin/python3
"""
python3 I:/mdwiki/med_views/test.py
"""
import sys

from start import fetch_language_statistics  # (year, maxv, lang)

year = 2025
limit = 0
maxv = 0
lang = "pam"

for arg in sys.argv:
    key, _, val = arg.partition(":")
    if key in ["limit", "-limit"] and val.isdigit():
        limit = int(val)
    elif key in ["year", "-year"] and val.isdigit():
        year = int(val)
    elif key in ["max", "-max"] and val.isdigit():
        maxv = int(val)
    elif key in ["lang", "-lang"] and val.isalpha():
        lang = val

data = fetch_language_statistics(year, maxv, lang)

print(data)
