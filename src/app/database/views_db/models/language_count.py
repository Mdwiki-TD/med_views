"""
Language count model for storing aggregated view counts per language (revised schema).
"""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class LanguageCount(BaseModel):
    """
    Aggregated view counts per language per year.

    Cached derived data that stores the total views for each language
    in a given year (what after2.py writes).

    Uses composite primary key (lang, year, agent_type) - no surrogate ID.
    Removed updated_at and title_count (not produced by collectors).
    """

    __tablename__ = "language_counts"

    # Composite primary key
    lang: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    total_views: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<LanguageCount(lang='{self.lang}', year={self.year}, "
            f"agent_type='{self.agent_type}', total_views={self.total_views})>"
        )


__all__ = [
    "LanguageCount",
]
