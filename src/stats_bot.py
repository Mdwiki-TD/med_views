#!/usr/bin/python3
"""


"""
import logging
import json

from .config import main_dump_path

logger = logging.getLogger(__name__)

stats_all_data = {}


def dump_stats(articles, new_data: dict[str, int], lang: str) -> dict[str, int | dict[str, int]]:
    # ---
    data_hash = [x for x in new_data if x.find("#") != -1]
    data_hash.extend([x for x in articles if x.find("#") != -1])
    # ---
    data_hash = set(data_hash)
    # ---
    data2 = {x: new_data[x] for x in new_data if x not in data_hash}
    # ---
    empty = [k for k in articles if new_data.get(k, 0) == 0]
    # ---
    views = sum(v for v in data2.values() if isinstance(v, int))
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


def dump_stats_all(year) -> None:
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
    with open(main_dump_path / f"{year}_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)
    # ---
    # sort stats_all_data by "views" descending
    stats_all_data_sorted = dict(sorted(stats_all_data.items(), key=lambda item: item[1].get("views", 0), reverse=True))
    # ---
    with open(main_dump_path / f"{year}_stats_all.json", "w", encoding="utf-8") as f:
        json.dump(stats_all_data_sorted, f, ensure_ascii=False, indent=4)
