"""
Aggregation service for computing and caching derived data (corrected).
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert

from ..models import LanguageCount, Statistic, View
from .database_service import DatabaseService
from .view_service import AgentType

logger = logging.getLogger(__name__)


class AggregationService:
    """
    Service for computing and caching aggregated data.

    Provides methods for computing language counts and statistics,
    and caching them in the database.
    """

    def __init__(self, db_service: DatabaseService | None = None) -> None:
        """
        Initialize the aggregation service.

        Parameters:
            db_service: Database service instance. If None, uses singleton.
        """
        self.db_service = db_service or DatabaseService.get_instance()

    def compute_language_counts(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
    ) -> dict[str, Any]:
        """
        Compute aggregated counts for a language and year.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.

        Returns:
            dict: Aggregated counts including total_views.
        """
        with self.db_service.get_session() as session:
            # Compute total views
            stmt = select(func.sum(View.views).label("total_views")).where(
                View.lang == lang, View.year == year, View.agent_type == agent_type
            )
            result = session.execute(stmt).one()

            return {
                "total_views": result.total_views or 0,
            }

    def cache_language_counts(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
        total_views: int,
    ) -> None:
        """
        Cache language counts in the database.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.
            total_views: Total view count.
        """
        with self.db_service.get_session() as session:
            # Use SQLite-specific upsert
            data = {
                "lang": lang,
                "year": year,
                "agent_type": agent_type,
                "total_views": total_views,
            }
            stmt = insert(LanguageCount).values(data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["lang", "year", "agent_type"],
                set_={"total_views": stmt.excluded.total_views},
            )
            session.execute(stmt)

        logger.debug("Cached language counts for %s/%s (%s)", lang, year, agent_type)

    def get_cached_language_counts(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
    ) -> dict[str, Any] | None:
        """
        Get cached language counts from the database.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.

        Returns:
            dict | None: Cached counts or None if not found.
        """
        with self.db_service.get_session() as session:
            stmt = select(LanguageCount).where(
                LanguageCount.lang == lang,
                LanguageCount.year == year,
                LanguageCount.agent_type == agent_type,
            )
            result = session.execute(stmt).scalar_one_or_none()

            if result is None:
                return None

            return {
                "total_views": result.total_views,
            }

    def get_all_language_counts_for_year(
        self,
        year: int,
        agent_type: AgentType,
    ) -> dict[str, int]:
        """
        Get cached language counts for all languages in a year.

        Parameters:
            year: Year.
            agent_type: Type of agent data.

        Returns:
            dict[str, int]: Mapping of language code to total views, sorted descending.
        """
        with self.db_service.get_session() as session:
            stmt = (
                select(LanguageCount.lang, LanguageCount.total_views)
                .where(LanguageCount.year == year, LanguageCount.agent_type == agent_type)
                .order_by(LanguageCount.total_views.desc())
            )
            results = session.execute(stmt).all()
            return {lang: total_views for lang, total_views in results}

    def cache_statistics(
        self,
        lang: str,
        year: int,
        articles: int,
        empty_views: int,
        not_empty_views: int,
        hash_count: int,
        total_views: int,
    ) -> None:
        """
        Cache statistics in the database.

        Parameters:
            lang: Language code.
            year: Year (0 for all-years summary).
            articles: Total number of articles.
            empty_views: Number of articles with zero views.
            not_empty_views: Number of articles with non-zero views.
            hash_count: Number of articles with special characters.
            total_views: Total view count.
        """
        with self.db_service.get_session() as session:
            # Use SQLite-specific upsert
            data = {
                "lang": lang,
                "year": year,
                "articles": articles,
                "empty_views": empty_views,
                "not_empty_views": not_empty_views,
                "hash_count": hash_count,
                "total_views": total_views,
            }
            stmt = insert(Statistic).values(data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["lang", "year"],
                set_={
                    "articles": stmt.excluded.articles,
                    "empty_views": stmt.excluded.empty_views,
                    "not_empty_views": stmt.excluded.not_empty_views,
                    "hash_count": stmt.excluded.hash_count,
                    "total_views": stmt.excluded.total_views,
                },
            )
            session.execute(stmt)

        logger.debug("Cached statistics for %s/%s", lang, year)

    def get_cached_statistics(
        self,
        lang: str,
        year: int,
    ) -> dict[str, Any] | None:
        """
        Get cached statistics from the database.

        Parameters:
            lang: Language code.
            year: Year (0 for all-years summary).

        Returns:
            dict | None: Cached statistics or None if not found.
        """
        with self.db_service.get_session() as session:
            stmt = select(Statistic).where(Statistic.lang == lang, Statistic.year == year)
            result = session.execute(stmt).scalar_one_or_none()

            if result is None:
                return None

            return {
                "articles": result.articles,
                "empty_views": result.empty_views,
                "not_empty_views": result.not_empty_views,
                "hash_count": result.hash_count,
                "total_views": result.total_views,
            }

    def get_all_statistics_for_year(
        self,
        year: int,
    ) -> dict[str, dict[str, int]]:
        """
        Get cached statistics for all languages in a year.

        Parameters:
            year: Year (0 for all-years summary).

        Returns:
            dict[str, dict[str, int]]: Mapping of language code to statistics, sorted by total_views descending.
        """
        with self.db_service.get_session() as session:
            stmt = select(Statistic).where(Statistic.year == year).order_by(Statistic.total_views.desc())
            results = session.execute(stmt).scalars().all()

            return {
                stat.lang: {
                    "articles": stat.articles,
                    "empty_views": stat.empty_views,
                    "not_empty_views": stat.not_empty_views,
                    "hash_count": stat.hash_count,
                    "total_views": stat.total_views,
                }
                for stat in results
            }


__all__ = [
    "AggregationService",
]
