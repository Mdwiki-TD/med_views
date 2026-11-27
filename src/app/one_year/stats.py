#!/usr/bin/python3
"""
Single-year statistics calculation and dumping.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..config import Config, get_config

logger = logging.getLogger(__name__)


class SingleYearStatsService:
    """Service for calculating and dumping single-year statistics.

    Handles computation of view statistics and writing summary files.
    """

    def __init__(
        self,
        config: Config | None = None,
    ) -> None:
        """Initialize the service.

        Parameters:
            config: Optional configuration object. Defaults to get_config().
        """
        _config = config or get_config()
        self.stats_all_data: dict = {}
        self.main_dump_path = _config.main_dump_path

    def dump_stats(
        self,
        articles: list,
        new_data: dict[str, int],
        lang: str,
    ) -> dict[str, int]:
        """Calculate and store statistics for one language.

        Parameters:
            articles: List of article titles.
            new_data: View data mapping article titles to view counts.
            lang: Language code.

        Returns:
            dict: Statistics including article counts, empty counts, and views.
        """
        data_hash = [x for x in new_data if x.find("#") != -1]
        data_hash.extend([x for x in articles if x.find("#") != -1])

        data_hash = set(data_hash)

        data2 = {x: new_data[x] for x in new_data if x not in data_hash}

        empty = [k for k in articles if new_data.get(k, 0) == 0]

        views = sum(v for v in data2.values() if isinstance(v, int))

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
        year: int | str,
        data: dict[str, dict],
    ) -> None:
        """Write all statistics to summary files."""
        self._dump_stats_all(
            self.main_dump_path / f"{year}_summary.json",
            self.main_dump_path / f"{year}_stats_all.json",
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
    "SingleYearStatsService",
]
