"""
Aggregation service for computing and caching derived data.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..models import LanguageCount, Statistic, Title, ViewAllAgents, ViewUsersAgents
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
            dict: Aggregated counts including total_views and title_count.
        """
        view_model = ViewAllAgents if agent_type == "all_agents" else ViewUsersAgents

        with self.db_service.get_session() as session:
            # Compute total views and title count
            stmt = (
                select(
                    func.sum(view_model.views).label("total_views"),
                    func.count(view_model.id).label("title_count"),
                )
                .join(Title, Title.id == view_model.title_id)
                .where(Title.lang == lang, view_model.year == year)
            )
            result = session.execute(stmt).one()

            return {
                "total_views": result.total_views or 0,
                "title_count": result.title_count or 0,
            }

    def cache_language_counts(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
        total_views: int,
        title_count: int,
    ) -> None:
        """
        Cache language counts in the database.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.
            total_views: Total view count.
            title_count: Number of titles.
        """
        with self.db_service.get_session() as session:
            # Check if record exists
            stmt = select(LanguageCount).where(
                LanguageCount.lang == lang,
                LanguageCount.year == year,
                LanguageCount.agent_type == agent_type,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                # Update existing record
                existing.total_views = total_views
                existing.title_count = title_count
                existing.updated_at = datetime.utcnow().isoformat()
            else:
                # Create new record
                record = LanguageCount(
                    lang=lang,
                    year=year,
                    agent_type=agent_type,
                    total_views=total_views,
                    title_count=title_count,
                    updated_at=datetime.utcnow().isoformat(),
                )
                session.add(record)

        logger.debug(f"Cached language counts for {lang}/{year} ({agent_type})")

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
                "title_count": result.title_count,
                "updated_at": result.updated_at,
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

    def compute_statistics(
        self,
        lang: str,
        year: int | None,
        articles: int,
        empty_views: int,
        not_empty_views: int,
        hash_count: int,
        total_views: int,
    ) -> dict[str, Any]:
        """
        Compute statistics for a language and year.

        Parameters:
            lang: Language code.
            year: Year (None for all-years summary).
            articles: Total number of articles.
            empty_views: Number of articles with zero views.
            not_empty_views: Number of articles with non-zero views.
            hash_count: Number of articles with special characters.
            total_views: Total view count.

        Returns:
            dict: Computed statistics.
        """
        return {
            "articles": articles,
            "empty_views": empty_views,
            "not_empty_views": not_empty_views,
            "hash_count": hash_count,
            "total_views": total_views,
        }

    def cache_statistics(
        self,
        lang: str,
        year: int | None,
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
            year: Year (None for all-years summary).
            articles: Total number of articles.
            empty_views: Number of articles with zero views.
            not_empty_views: Number of articles with non-zero views.
            hash_count: Number of articles with special characters.
            total_views: Total view count.
        """
        with self.db_service.get_session() as session:
            # Check if record exists
            stmt = select(Statistic).where(Statistic.lang == lang, Statistic.year == year)
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                # Update existing record
                existing.articles = articles
                existing.empty_views = empty_views
                existing.not_empty_views = not_empty_views
                existing.hash_count = hash_count
                existing.total_views = total_views
                existing.updated_at = datetime.utcnow().isoformat()
            else:
                # Create new record
                record = Statistic(
                    lang=lang,
                    year=year,
                    articles=articles,
                    empty_views=empty_views,
                    not_empty_views=not_empty_views,
                    hash_count=hash_count,
                    total_views=total_views,
                    updated_at=datetime.utcnow().isoformat(),
                )
                session.add(record)

        logger.debug(f"Cached statistics for {lang}/{year}")

    def get_cached_statistics(
        self,
        lang: str,
        year: int | None,
    ) -> dict[str, Any] | None:
        """
        Get cached statistics from the database.

        Parameters:
            lang: Language code.
            year: Year (None for all-years summary).

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
                "updated_at": result.updated_at,
            }

    def get_all_statistics_for_year(
        self,
        year: int | None,
    ) -> dict[str, dict[str, int]]:
        """
        Get cached statistics for all languages in a year.

        Parameters:
            year: Year (None for all-years summary).

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
