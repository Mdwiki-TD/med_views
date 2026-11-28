"""
View model for storing article view counts (corrected).
"""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class View(BaseModel):
    """
    View counts for articles with agent type.

    Single table for both 'all_agents' and 'users_agents' data.
    Uses composite primary key (lang, title, year, agent_type).
    """

    __tablename__ = "views"

    # Composite primary key
    lang: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(Text, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False)

    # Index for paginated queries: WHERE lang=? AND year=? AND agent_type=? ORDER BY views DESC
    __table_args__ = (
        Index("idx_views_lang_year_agent_views", "lang", "year", "agent_type", "views"),
    )

    def __repr__(self) -> str:
        return (
            f"<View(lang='{self.lang}', title='{self.title[:30]}...', "
            f"year={self.year}, agent_type='{self.agent_type}', views={self.views})>"
        )


__all__ = [
    "View",
]
