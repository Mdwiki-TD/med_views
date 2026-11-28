#!/usr/bin/python3
"""
Statistics calculation and dumping for multi-year view data.

This module calculates and stores statistics for Wikipedia article views
across multiple years (2015-2025), handling dictionary-based year data.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..config import Config

logger = logging.getLogger(__name__)


class MultiYearStatsService:
    """Service for calculating and dumping multi-year statistics.

    Handles computation of view statistics across multiple years and writing summary files.
    """

    def __init__(
        self,
        dump_dir_path: Path | None = None,
    ) -> None:
        """Initialize the service."""
        self.stats_all_data: dict = {}
        self.dump_dir_path = dump_dir_path or Config.get_instance().paths.dump_dir_path

    def dump_stats(
        self,
        articles: list[str],
        new_data: dict[str, Any],
        lang: str,
    ) -> dict[str, int]:
        """Calculate and store statistics for one language across all years.

        Parameters:
            articles: List of article titles.
            new_data: View data mapping article titles to yearly view dicts.
            lang: Language code.

        Returns:
            dict: Statistics including article counts, empty counts, and views.
        """
        data_hash = [x for x in new_data if x.find("#") != -1]
        data_hash.extend([x for x in articles if x.find("#") != -1])

        data_hash = set(data_hash)

        data2 = {x: new_data[x] for x in new_data if x not in data_hash}

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

        # Calculate total views across all years
        views = 0
        for k, v in data2.items():
            if k == "all":
                continue

            if isinstance(v, int):
                views += v
            elif isinstance(v, dict):
                # Sum all year views
                views += sum(year_view for x, year_view in v.items() if isinstance(year_view, int) and x != "all")

        stats = {
            "articles": len(articles),
            "empty": len(empty),
            "not_empty": len(data2) - len(empty),
            "hash": len(data_hash),
            "views": views,
        }

        self.stats_all_data[lang] = stats

        return stats

    def dump_stats_all(
        self,
        data: dict[str, dict],
        year: int | str | None = None,
    ) -> None:
        """Write all statistics to summary files."""
        file_name_1 = "all_years_summary.json"
        file_name_2 = "all_years_stats_all.json"
        if year:
            file_name_1 = f"{year}_summary.json"
            file_name_2 = f"{year}_stats_all.json"

        self._dump_stats_all(
            self.dump_dir_path / file_name_1,
            self.dump_dir_path / file_name_2,
            data,
        )

    def _dump_stats_all(
        self,
        file1: Path,
        file2: Path,
        data: dict[str, dict],
    ) -> None:
        """Write all statistics to summary files."""
        all_hash = sum(v["hash"] for v in data.values())
        all_not_empty = sum(v["not_empty"] for v in data.values())
        all_empty = sum(v["empty"] for v in data.values())
        all_views = sum(v["views"] for v in data.values())
        all_articles = sum(v["articles"] for v in data.values())

        summary = {
            "articles": all_articles,
            "empty_views": all_empty,
            "not_empty_views": all_not_empty,
            "hash": all_hash,
            "total_views": all_views,
        }

        with open(file1, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        # sort stats_all_data by "views" descending
        stats_all_data_sorted = dict(sorted(data.items(), key=lambda item: item[1].get("views", 0), reverse=True))

        with open(file2, "w", encoding="utf-8") as f:
            json.dump(stats_all_data_sorted, f, ensure_ascii=False, indent=4)


__all__ = [
    "MultiYearStatsService",
]
