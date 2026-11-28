"""
Statistics model for storing summary statistics per language.
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class Statistic(BaseModel):
    """
    Summary statistics per language per year.

    Cached derived data that stores computed statistics for each language
    in a given year, including article counts, view counts, and empty entries.
    """

    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lang: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Year (NULL for all-years summary)",
    )
    articles: Mapped[int] = mapped_column(Integer, nullable=False)
    empty_views: Mapped[int] = mapped_column(Integer, nullable=False)
    not_empty_views: Mapped[int] = mapped_column(Integer, nullable=False)
    hash_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_views: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="ISO 8601 timestamp of last update",
    )

    # Unique constraint on (lang, year) to prevent duplicates
    __table_args__ = (
        UniqueConstraint("lang", "year", name="uq_statistics_lang_year"),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return (
            f"<Statistic(id={self.id}, lang='{self.lang}', year={self.year}, "
            f"articles={self.articles}, total_views={self.total_views})>"
        )


__all__ = [
    "Statistic",
]
