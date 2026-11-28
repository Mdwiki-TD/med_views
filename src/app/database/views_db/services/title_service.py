"""
Title service for CRUD operations on article titles (revised).
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert

from ..models import Title
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class TitleService:
    """
    Service for CRUD operations on article titles.

    Provides methods for inserting, querying, and managing article titles
    in the database.
    """

    def __init__(self, db_service: DatabaseService | None = None) -> None:
        """
        Initialize the title service.

        Parameters:
            db_service: Database service instance. If None, uses singleton.
        """
        self.db_service = db_service or DatabaseService.get_instance()

    def insert_titles(self, lang: str, titles: list[str], chunk_size: int = 1000) -> int:
        """
        Insert titles for a language in bulk.

        Uses SQLite-specific upsert to handle duplicates.

        Parameters:
            lang: Language code.
            titles: List of article titles.
            chunk_size: Number of titles to insert per transaction.

        Returns:
            int: Number of titles inserted/updated.
        """
        if not titles:
            return 0

        inserted_count = 0

        with self.db_service.get_session() as session:
            # Process in chunks to avoid memory issues
            for i in range(0, len(titles), chunk_size):
                chunk = titles[i : i + chunk_size]

                # Normalize titles (replace underscores with spaces)
                data = [{"lang": lang, "title": title.replace("_", " ")} for title in chunk]

                # Use SQLite-specific upsert
                stmt = insert(Title).values(data)
                stmt = stmt.on_conflict_do_nothing(index_elements=["lang", "title"])

                result = session.execute(stmt)
                inserted_count += result.rowcount

                logger.debug("Inserted %d titles for %s", result.rowcount, lang)

        logger.info("Inserted %d titles for %s", inserted_count, lang)
        return inserted_count

    def get_titles_for_language(self, lang: str) -> list[str]:
        """
        Get all titles for a language.

        Parameters:
            lang: Language code.

        Returns:
            list[str]: List of article titles.
        """
        with self.db_service.get_session() as session:
            stmt = select(Title.title).where(Title.lang == lang)
            result = session.execute(stmt).scalars().all()
            return list(result)

    def get_title_count_for_language(self, lang: str) -> int:
        """
        Get the count of titles for a language.

        Parameters:
            lang: Language code.

        Returns:
            int: Number of titles.
        """
        with self.db_service.get_session() as session:
            stmt = select(func.count(Title.title)).where(Title.lang == lang)
            return session.execute(stmt).scalar_one()

    def get_all_language_counts(self) -> dict[str, int]:
        """
        Get title counts for all languages.

        Returns:
            dict[str, int]: Mapping of language code to title count.
        """
        with self.db_service.get_session() as session:
            stmt = select(Title.lang, func.count(Title.title)).group_by(Title.lang)
            results = session.execute(stmt).all()
            return {lang: count for lang, count in results}

    def delete_titles_for_language(self, lang: str) -> int:
        """
        Delete all titles for a language.

        Parameters:
            lang: Language code.

        Returns:
            int: Number of titles deleted.
        """
        with self.db_service.get_session() as session:
            stmt = delete(Title).where(Title.lang == lang)
            result = session.execute(stmt)
            deleted_count = result.rowcount
            logger.info("Deleted %d titles for %s", deleted_count, lang)
            return deleted_count

    def title_exists(self, lang: str, title: str) -> bool:
        """
        Check if a title exists for a language.

        Parameters:
            lang: Language code.
            title: Article title.

        Returns:
            bool: True if title exists, False otherwise.
        """
        normalized_title = title.replace("_", " ")
        with self.db_service.get_session() as session:
            stmt = select(Title).where(Title.lang == lang, Title.title == normalized_title)
            result = session.execute(stmt).scalar_one_or_none()
            return result is not None


__all__ = [
    "TitleService",
]
