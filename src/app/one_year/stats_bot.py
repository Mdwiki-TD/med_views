#!/usr/bin/python3
"""Single-year statistics calculation and dumping."""

from __future__ import annotations

import json
import logging

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
        self._config = config or get_config()
        self._stats_all_data: dict = {}

    @property
    def stats_all_data(self) -> dict:
        """Get the accumulated statistics data."""
        return self._stats_all_data

    def dump_stats(self, articles: list, new_data: dict[str, int], lang: str) -> dict[str, int]:
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

        self._stats_all_data[lang] = stats

        return stats

    def dump_stats_all(self, year) -> None:
        """Write all statistics to summary files.

        Parameters:
            year: Year for the summary file names.
        """
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

        with open(self._config.main_dump_path / f"{year}_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        # sort stats_all_data by "views" descending
        stats_all_data_sorted = dict(
            sorted(self._stats_all_data.items(), key=lambda item: item[1].get("views", 0), reverse=True)
        )

        with open(self._config.main_dump_path / f"{year}_stats_all.json", "w", encoding="utf-8") as f:
            json.dump(stats_all_data_sorted, f, ensure_ascii=False, indent=4)


# Legacy compatibility layer
_default_service: SingleYearStatsService | None = None
stats_all_data: dict = {}


def _get_default_service() -> SingleYearStatsService:
    """Get or create the default SingleYearStatsService instance."""
    global _default_service
    if _default_service is None:
        _default_service = SingleYearStatsService()
    return _default_service


def dump_stats(articles, new_data: dict[str, int], lang: str) -> dict[str, int]:
    """Legacy entry point. Use SingleYearStatsService.dump_stats instead."""
    global stats_all_data
    service = _get_default_service()
    result = service.dump_stats(articles, new_data, lang)
    # Sync the module-level variable for legacy callers
    stats_all_data = service.stats_all_data
    return result


def dump_stats_all(year) -> None:
    """Legacy entry point. Use SingleYearStatsService.dump_stats_all instead."""
    _get_default_service().dump_stats_all(year)


__all__ = [
    "SingleYearStatsService",
    "dump_stats",
    "dump_stats_all",
    "stats_all_data",
]
