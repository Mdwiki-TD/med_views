#!/usr/bin/python3
"""


"""
import logging
import json

from .config import main_dump_path

logger = logging.getLogger(__name__)

stats_all_data = {}


def dump_stats(articles, new_data: dict[str, dict | int], lang: str) -> dict[str, int | dict[str, int]]:
    # ---
    data_hash = [x for x in new_data if x.find("#") != -1]
    data_hash.extend([x for x in articles if x.find("#") != -1])
    # ---
    data_hash = set(data_hash)
    # ---
    data2 = {x: new_data[x] for x in new_data if x not in data_hash}
    # ---
    # Calculate empty entries - entries where all years have 0 views or entry is 0
    empty = []
    for k in articles:
        val = new_data.get(k, 0)
        if val == 0:
            empty.append(k)
        elif isinstance(val, dict):
            # Check if all year values are 0
            if all(v == 0 for v in val.values()):
                empty.append(k)
    # ---
    # Calculate total views across all years
    views = 0
    for v in data2.values():
        if isinstance(v, int):
            views += v
        elif isinstance(v, dict):
            # Sum all year views
            views += sum(year_view for year_view in v.values() if isinstance(year_view, int))
    # ---
    stats = {
        "articles": len(articles),
        "empty": len(empty),
        "not_empty": len(data2) - len(empty),
        "hash": len(data_hash),
        "views": views,
    }
    # ---
    stats_all_data[lang] = stats
    # ---
    return stats


def dump_stats_all() -> None:
    # ---
    all_hash = sum(v["hash"] for v in stats_all_data.values())
    all_not_empty = sum(v["not_empty"] for v in stats_all_data.values())
    all_empty = sum(v["empty"] for v in stats_all_data.values())
    all_views = sum(v["views"] for v in stats_all_data.values())
    all_articles = sum(v["articles"] for v in stats_all_data.values())
    # ---
    summary = {
        "articles": all_articles,
        "empty_views": all_empty,
        "not_empty_views": all_not_empty,
        "hash": all_hash,
        "total_views": all_views,
    }
    # ---
    with open(main_dump_path / "all_years_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)
    # ---
    # sort stats_all_data by "views" descending
    stats_all_data_sorted = dict(sorted(stats_all_data.items(), key=lambda item: item[1].get("views", 0), reverse=True))
    # ---
    with open(main_dump_path / "all_years_stats_all.json", "w", encoding="utf-8") as f:
        json.dump(stats_all_data_sorted, f, ensure_ascii=False, indent=4)
