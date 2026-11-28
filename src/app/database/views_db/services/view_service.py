"""
View service for CRUD operations on article views.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from ..models import Title, ViewAllAgents, ViewUsersAgents
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

AgentType = Literal["all_agents", "users_agents"]


class ViewService:
    """
    Service for CRUD operations on article views.

    Provides methods for inserting, querying, and managing view counts
    for both all_agents and users_agents types.
    """

    def __init__(self, db_service: DatabaseService | None = None) -> None:
        """
        Initialize the view service.

        Parameters:
            db_service: Database service instance. If None, uses singleton.
        """
        self.db_service = db_service or DatabaseService.get_instance()

    def _get_view_model(self, agent_type: AgentType) -> type[ViewAllAgents | ViewUsersAgents]:
        """Get the appropriate view model class for the agent type."""
        if agent_type == "all_agents":
            return ViewAllAgents
        elif agent_type == "users_agents":
            return ViewUsersAgents
        else:
            raise ValueError(f"Invalid agent_type: {agent_type}")

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

        Parameters:
            lang: Language code.
            year: Year.
            views_data: Mapping of title to view count.
            agent_type: Type of agent data ('all_agents' or 'users_agents').
            chunk_size: Number of records to insert per transaction.

        Returns:
            int: Number of views inserted.
        """
        if not views_data:
            return 0

        view_model = self._get_view_model(agent_type)
        inserted_count = 0

        with self.db_service.get_session() as session:
            # First, get or create title IDs
            title_ids = {}
            for title in views_data.keys():
                # Check if title exists
                stmt = select(Title.id).where(Title.lang == lang, Title.title == title)
                title_id = session.execute(stmt).scalar_one_or_none()

                if title_id is None:
                    # Create title
                    new_title = Title(lang=lang, title=title)
                    session.add(new_title)
                    session.flush()
                    title_id = new_title.id

                title_ids[title] = title_id

            # Process in chunks
            items = list(views_data.items())
            for i in range(0, len(items), chunk_size):
                chunk = items[i : i + chunk_size]

                # Prepare data for bulk insert
                data = [
                    {
                        "title_id": title_ids[title],
                        "year": year,
                        "views": views,
                    }
                    for title, views in chunk
                ]

                try:
                    # Insert records
                    for item in data:
                        view_record = view_model(**item)
                        session.add(view_record)

                    session.flush()
                    inserted_count += len(chunk)
                    logger.debug(f"Inserted {len(chunk)} views for {lang}/{year}")

                except IntegrityError:
                    # Some records already exist, update them
                    session.rollback()
                    logger.debug(f"Some views already exist for {lang}/{year}, updating")

                    # Insert/update one by one
                    for item in data:
                        try:
                            view_record = view_model(**item)
                            session.add(view_record)
                            session.flush()
                            inserted_count += 1
                        except IntegrityError:
                            session.rollback()
                            # Update existing record
                            stmt = select(view_model).where(
                                view_model.title_id == item["title_id"],
                                view_model.year == item["year"],
                            )
                            existing = session.execute(stmt).scalar_one_or_none()
                            if existing:
                                existing.views = item["views"]
                                session.flush()
                            continue

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
        view_model = self._get_view_model(agent_type)

        with self.db_service.get_session() as session:
            stmt = (
                select(Title.title, view_model.views)
                .join(view_model, Title.id == view_model.title_id)
                .where(Title.lang == lang, view_model.year == year)
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
        view_model = self._get_view_model(agent_type)

        with self.db_service.get_session() as session:
            stmt = (
                select(func.sum(view_model.views))
                .join(Title, Title.id == view_model.title_id)
                .where(Title.lang == lang, view_model.year == year)
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
        view_model = self._get_view_model(agent_type)

        with self.db_service.get_session() as session:
            stmt = (
                select(func.count(view_model.id))
                .join(Title, Title.id == view_model.title_id)
                .where(Title.lang == lang, view_model.year == year, view_model.views > min_views)
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
        view_model = self._get_view_model(agent_type)

        with self.db_service.get_session() as session:
            # Get title IDs for this language
            stmt = select(Title.id).where(Title.lang == lang)
            title_ids = session.execute(stmt).scalars().all()

            if not title_ids:
                return 0

            # Delete views for these titles and year
            stmt = delete(view_model).where(
                view_model.title_id.in_(title_ids),
                view_model.year == year,
            )
            result = session.execute(stmt)
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} views for {lang}/{year} ({agent_type})")
            return deleted_count

    def filter_views_greater_than_zero(
        self,
        lang: str,
        year: int,
    ) -> dict[str, int]:
        """
        Get views for a language and year, filtered to only include views > 0.

        This is used for the users_agents data.

        Parameters:
            lang: Language code.
            year: Year.

        Returns:
            dict[str, int]: Mapping of title to view count (only where views > 0).
        """
        return self.get_views_for_language_year(lang, year, "all_agents")

        # Filter to views > 0
        # filtered = {title: views for title, views in all_views.items() if views > 0}
        # return filtered


__all__ = [
    "ViewService",
    "AgentType",
]
