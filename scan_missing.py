#!/usr/bin/python3
"""

python3 core8/pwb.py med_views/scan_missing is_zero
python3 core8/pwb.py med_views/scan_missing

"""
import json
import sys
from pathlib import Path

from views_all_bots.views import get_view_file

dump_dir = Path(__file__).parent / "titles"

files = [x for x in dump_dir.glob("*.json")]
# ---
result = {}
# ---
okay = 0
# ---
is_zero = "is_zero" in sys.argv
# ---
for json_file in files:
    # ---
    lang = json_file.stem
    # ---
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    # ---
    len_titles = len(data)
    # ---
    tab = {"titles": len_titles}
    # ---
    views_2023 = get_view_file(lang, 2023, open_it=True)
    views_2024 = get_view_file(lang, 2024, open_it=True)
    # ---
    tab["2023 missing"] = [x for x in data if x not in views_2023 or (views_2023[x] == 0 and is_zero)]
    tab["2024 missing"] = [x for x in data if x not in views_2024 or (views_2024[x] == 0 and is_zero)]
    # ---
    if tab["2023 missing"] or tab["2024 missing"]:
        result[lang] = tab
    else:
        okay += 1

# sort result by missing 2024
result = {k: v for k, v in sorted(result.items(), key=lambda item: len(item[1]["2024 missing"]), reverse=True)}

missing_2024, missing_2023 = {}, {}

for k, v in result.items():
    if v["2024 missing"]:
        missing_2024[k] = len(v["2024 missing"])

    if v["2023 missing"]:
        missing_2023[k] = len(v["2023 missing"])

    print(
        f"{k}: \t\t{str(v['titles']).ljust(12)}\t\t missing: 2024 {len(v['2024 missing'])}\t 2023 {len(v['2023 missing'])}"
    )


with open(Path(__file__).parent / "missing_2023.json", "w", encoding="utf-8") as f:
    json.dump(missing_2023, f, indent=2, ensure_ascii=False)

with open(Path(__file__).parent / "missing_2024.json", "w", encoding="utf-8") as f:
    json.dump(missing_2024, f, indent=2, ensure_ascii=False)

print(f"all files: {len(files)}, okay: {okay}, with: missing: {len(result)}")

print(f"missing_2023: {len(missing_2023)}, missing_2024: {len(missing_2024)}")
