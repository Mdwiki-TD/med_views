"""
Statistics model for storing summary statistics per language (revised schema).
"""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class Statistic(BaseModel):
    """
    Summary statistics per language per year.

    Cached derived data that stores computed statistics for each language
    in a given year (what stats.py writes).

    Uses composite primary key (lang, year) - no surrogate ID.
    Removed updated_at (not produced by collectors).
    """

    __tablename__ = "statistics"

    # Composite primary key
    lang: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int | None] = mapped_column(
        Integer,
        primary_key=True,
        nullable=True,
        comment="Year (NULL for all-years summary)",
    )
    articles: Mapped[int] = mapped_column(Integer, nullable=False)
    empty_views: Mapped[int] = mapped_column(Integer, nullable=False)
    not_empty_views: Mapped[int] = mapped_column(Integer, nullable=False)
    hash_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_views: Mapped[int] = mapped_column(Integer, nullable=False)

    # WITHOUT ROWID for composite PK table
    __table_args__ = (
        {"sqlite_without_rowid": True},
    )

    def __repr__(self) -> str:
        return (
            f"<Statistic(lang='{self.lang}', year={self.year}, "
            f"articles={self.articles}, total_views={self.total_views})>"
        )


__all__ = [
    "Statistic",
]
