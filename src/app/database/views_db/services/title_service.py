"""
Title service for CRUD operations on article titles.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

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

        Parameters:
            lang: Language code.
            titles: List of article titles.
            chunk_size: Number of titles to insert per transaction.

        Returns:
            int: Number of titles inserted.
        """
        if not titles:
            return 0

        inserted_count = 0

        with self.db_service.get_session() as session:
            # Process in chunks to avoid memory issues
            for i in range(0, len(titles), chunk_size):
                chunk = titles[i : i + chunk_size]

                # Prepare data for bulk insert
                data = [{"lang": lang, "title": title.replace("_", " ")} for title in chunk]

                try:
                    # Use INSERT OR IGNORE to skip duplicates
                    for item in data:
                        title = Title(**item)
                        session.add(title)

                    session.flush()
                    inserted_count += len(chunk)
                    logger.debug(f"Inserted {len(chunk)} titles for {lang}")

                except IntegrityError:
                    # Some titles already exist, skip them
                    session.rollback()
                    logger.debug(f"Some titles already exist for {lang}, skipping duplicates")

                    # Insert one by one to handle duplicates
                    for item in data:
                        try:
                            title = Title(**item)
                            session.add(title)
                            session.flush()
                            inserted_count += 1
                        except IntegrityError:
                            session.rollback()
                            continue

        logger.info(f"Inserted {inserted_count} titles for {lang}")
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
            stmt = select(Title).where(Title.lang == lang)
            return len(session.execute(stmt).scalars().all())

    def get_all_language_counts(self) -> dict[str, int]:
        """
        Get title counts for all languages.

        Returns:
            dict[str, int]: Mapping of language code to title count.
        """
        with self.db_service.get_session() as session:
            stmt = select(Title.lang, Title.title)
            results = session.execute(stmt).all()

            counts: dict[str, int] = {}
            for lang, _ in results:
                counts[lang] = counts.get(lang, 0) + 1

            return counts

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
            logger.info(f"Deleted {deleted_count} titles for {lang}")
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
        with self.db_service.get_session() as session:
            stmt = select(Title).where(Title.lang == lang, Title.title == title)
            result = session.execute(stmt).scalar_one_or_none()
            return result is not None

    def get_title_id(self, lang: str, title: str) -> int | None:
        """
        Get the ID of a title.

        Parameters:
            lang: Language code.
            title: Article title.

        Returns:
            int | None: Title ID if found, None otherwise.
        """
        with self.db_service.get_session() as session:
            stmt = select(Title.id).where(Title.lang == lang, Title.title == title)
            result = session.execute(stmt).scalar_one_or_none()
            return result


__all__ = [
    "TitleService",
]
