"""
Language count model for storing aggregated view counts per language.
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class LanguageCount(BaseModel):
    """
    Aggregated view counts per language per year.

    Cached derived data that stores the total views and title count for each
    language in a given year. This avoids recomputing expensive aggregations.
    """

    __tablename__ = "language_counts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lang: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Agent type: 'all_agents' or 'users_agents'",
    )
    total_views: Mapped[int] = mapped_column(Integer, nullable=False)
    title_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="ISO 8601 timestamp of last update",
    )

    # Unique constraint on (lang, year, agent_type) to prevent duplicates
    __table_args__ = (
        UniqueConstraint(
            "lang", "year", "agent_type", name="uq_language_counts_lang_year_agent"
        ),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return (
            f"<LanguageCount(id={self.id}, lang='{self.lang}', year={self.year}, "
            f"agent_type='{self.agent_type}', total_views={self.total_views})>"
        )


__all__ = [
    "LanguageCount",
]
