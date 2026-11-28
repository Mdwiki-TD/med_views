"""
View model for storing article view counts (revised schema).
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class View(BaseModel):
    """
    View counts for articles with agent type.

    Single table for both 'all_agents' and 'users_agents' data.
    Uses composite primary key (title_id, year, agent_type).

    Denormalized lang column for query performance (avoids joins).
    """

    __tablename__ = "views"

    # Composite primary key
    title_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("titles.rowid", ondelete="CASCADE"),
        primary_key=True,
    )
    lang: Mapped[str] = mapped_column(String(20), primary_key=True)  # Denormalized
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False)

    # Index for paginated queries: WHERE lang=? AND year=? AND agent_type=? ORDER BY views DESC
    __table_args__ = (
        Index("idx_views_lang_year_agent_views", "lang", "year", "agent_type", "views"),
        {"sqlite_without_rowid": True},
    )

    def __repr__(self) -> str:
        return (
            f"<View(title_id={self.title_id}, lang='{self.lang}', "
            f"year={self.year}, agent_type='{self.agent_type}', views={self.views})>"
        )


__all__ = [
    "View",
]
