"""
View service for CRUD operations on article views (corrected).
"""

from __future__ import annotations

import logging
from typing import Literal

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert

from ..models import View
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

AgentType = Literal["all_agents", "users_agents"]


class ViewService:
    """
    Service for CRUD operations on article views.

    Provides methods for inserting, querying, and managing view counts
    for both agent types using a single View table.
    """

    def __init__(self, db_service: DatabaseService | None = None) -> None:
        """
        Initialize the view service.

        Parameters:
            db_service: Database service instance. If None, uses singleton.
        """
        self.db_service = db_service or DatabaseService.get_instance()

    def insert_views(
        self,
        lang: str,
        year: int,
        views_data: dict[str, int],
        agent_type: AgentType,
        chunk_size: int = 1000,
    ) -> int:
        """
        Insert view counts for a language and year in bulk.

        Uses SQLite-specific upsert to handle duplicates.

        Parameters:
            lang: Language code.
            year: Year.
            views_data: Mapping of title to view count.
            agent_type: Type of agent data ('all_agents' or 'users_agents').
            chunk_size: Number of records to insert per chunk.

        Returns:
            int: Number of views inserted/updated.
        """
        if not views_data:
            return 0

        inserted_count = 0

        with self.db_service.get_session() as session:
            # Process in chunks
            items = list(views_data.items())
            for i in range(0, len(items), chunk_size):
                chunk = items[i : i + chunk_size]

                # Prepare data for bulk insert (normalize titles)
                data = [
                    {
                        "lang": lang,
                        "title": title.replace("_", " "),
                        "year": year,
                        "agent_type": agent_type,
                        "views": views,
                    }
                    for title, views in chunk
                ]

                # Use SQLite-specific upsert
                stmt = insert(View).values(data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["lang", "title", "year", "agent_type"],
                    set_={"views": stmt.excluded.views},
                )

                result = session.execute(stmt)
                inserted_count += result.rowcount

                logger.debug(f"Inserted {result.rowcount} views for {lang}/{year}")

        logger.info(f"Inserted {inserted_count} views for {lang}/{year} ({agent_type})")
        return inserted_count

    def get_views_for_language_year(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
    ) -> dict[str, int]:
        """
        Get view counts for a language and year.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.

        Returns:
            dict[str, int]: Mapping of title to view count.
        """
        with self.db_service.get_session() as session:
            stmt = (
                select(View.title, View.views)
                .where(View.lang == lang, View.year == year, View.agent_type == agent_type)
            )
            results = session.execute(stmt).all()
            return {title: views for title, views in results}

    def get_total_views_for_language_year(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
    ) -> int:
        """
        Get total view count for a language and year.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.

        Returns:
            int: Total view count.
        """
        with self.db_service.get_session() as session:
            stmt = (
                select(func.sum(View.views))
                .where(View.lang == lang, View.year == year, View.agent_type == agent_type)
            )
            result = session.execute(stmt).scalar_one_or_none()
            return result or 0

    def get_title_count_for_language_year(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
        min_views: int = 0,
    ) -> int:
        """
        Get count of titles with views for a language and year.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.
            min_views: Minimum view count filter.

        Returns:
            int: Number of titles.
        """
        with self.db_service.get_session() as session:
            stmt = (
                select(func.count(View.title))
                .where(
                    View.lang == lang,
                    View.year == year,
                    View.agent_type == agent_type,
                    View.views > min_views,
                )
            )
            result = session.execute(stmt).scalar_one()
            return result

    def delete_views_for_language_year(
        self,
        lang: str,
        year: int,
        agent_type: AgentType,
    ) -> int:
        """
        Delete all views for a language and year.

        Parameters:
            lang: Language code.
            year: Year.
            agent_type: Type of agent data.

        Returns:
            int: Number of records deleted.
        """
        with self.db_service.get_session() as session:
            stmt = delete(View).where(
                View.lang == lang,
                View.year == year,
                View.agent_type == agent_type,
            )
            result = session.execute(stmt)
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} views for {lang}/{year} ({agent_type})")
            return deleted_count


__all__ = [
    "ViewService",
    "AgentType",
]
