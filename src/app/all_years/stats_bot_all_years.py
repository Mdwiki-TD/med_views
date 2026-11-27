#!/usr/bin/python3
"""
Statistics calculation and dumping for multi-year view data.

This module calculates and stores statistics for Wikipedia article views
across multiple years (2015-2025), handling dictionary-based year data.
"""

from __future__ import annotations

import json
import logging

from ..config import Config, get_config

logger = logging.getLogger(__name__)


class MultiYearStatsService:
    """Service for calculating and dumping multi-year statistics.

    Handles computation of view statistics across multiple years and
    writing summary files.
    """

    def __init__(
        self,
        config: Config = None,
    ) -> None:
        """Initialize the service.

        Parameters:
            config: Optional configuration object. Defaults to get_config().
        """
        self._config = config or get_config()
        self._stats_all_data: dict = {}

    @property
    def stats_all_data(self) -> dict:
        """Get the accumulated statistics data."""
        return self._stats_all_data

    def dump_stats(self, articles: list, new_data: dict[str, dict | int], lang: str) -> dict[str, int | dict[str, int]]:
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
        for v in data2.values():
            if isinstance(v, int):
                views += v
            elif isinstance(v, dict):
                # Sum all year views
                views += sum(year_view for year_view in v.values() if isinstance(year_view, int))

        stats = {
            "articles": len(articles),
            "empty": len(empty),
            "not_empty": len(data2) - len(empty),
            "hash": len(data_hash),
            "views": views,
        }

        self._stats_all_data[lang] = stats

        return stats

    def dump_stats_all(self) -> None:
        """Write all statistics to summary files for all years."""
        all_hash = sum(v["hash"] for v in self._stats_all_data.values())
        all_not_empty = sum(v["not_empty"] for v in self._stats_all_data.values())
        all_empty = sum(v["empty"] for v in self._stats_all_data.values())
        all_views = sum(v["views"] for v in self._stats_all_data.values())
        all_articles = sum(v["articles"] for v in self._stats_all_data.values())

        summary = {
            "articles": all_articles,
            "empty_views": all_empty,
            "not_empty_views": all_not_empty,
            "hash": all_hash,
            "total_views": all_views,
        }

        with open(self._config.main_dump_path / "all_years_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        # sort stats_all_data by "views" descending
        stats_all_data_sorted = dict(
            sorted(self._stats_all_data.items(), key=lambda item: item[1].get("views", 0), reverse=True)
        )

        with open(self._config.main_dump_path / "all_years_stats_all.json", "w", encoding="utf-8") as f:
            json.dump(stats_all_data_sorted, f, ensure_ascii=False, indent=4)


# Legacy compatibility layer
_default_service: MultiYearStatsService | None = None
stats_all_data: dict = {}


def _get_default_service() -> MultiYearStatsService:
    """Get or create the default MultiYearStatsService instance."""
    global _default_service
    if _default_service is None:
        _default_service = MultiYearStatsService()
    return _default_service


def dump_stats(articles, new_data: dict[str, dict | int], lang: str) -> dict[str, int | dict[str, int]]:
    """Legacy entry point. Use MultiYearStatsService.dump_stats instead."""
    global stats_all_data
    service = _get_default_service()
    result = service.dump_stats(articles, new_data, lang)
    # Sync the module-level variable for legacy callers
    stats_all_data = service.stats_all_data
    return result


def dump_stats_all() -> None:
    """Legacy entry point. Use MultiYearStatsService.dump_stats_all instead."""
    _get_default_service().dump_stats_all()


__all__ = [
    "MultiYearStatsService",
    "dump_stats",
    "dump_stats_all",
    "stats_all_data",
]
