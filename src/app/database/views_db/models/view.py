"""
View models for storing article view counts.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import BaseModel


class ViewAllAgents(BaseModel):
    """
    View counts for all agents (raw data from API).

    Stores the number of views for each article per year, including all
    user agents (bots, spiders, etc.).
    """

    __tablename__ = "views_all_agents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_id: Mapped[int] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Relationship to Title
    title: Mapped["Title"] = relationship("Title", backref="views_all_agents")

    # Unique constraint on (title_id, year) to prevent duplicates
    __table_args__ = (
        UniqueConstraint("title_id", "year", name="uq_views_all_agents_title_year"),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<ViewAllAgents(id={self.id}, title_id={self.title_id}, year={self.year}, views={self.views})>"


class ViewUsersAgents(BaseModel):
    """
    View counts for users agents only (filtered views > 0).

    Stores the number of views for each article per year, filtered to only
    include human users (excluding bots and spiders), and only where views > 0.
    """

    __tablename__ = "views_users_agents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_id: Mapped[int] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Relationship to Title
    title: Mapped["Title"] = relationship("Title", backref="views_users_agents")

    # Unique constraint on (title_id, year) to prevent duplicates
    __table_args__ = (
        UniqueConstraint("title_id", "year", name="uq_views_users_agents_title_year"),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<ViewUsersAgents(id={self.id}, title_id={self.title_id}, year={self.year}, views={self.views})>"


# Import Title for type hints (avoid circular import)
from .title import Title  # noqa: E402


__all__ = [
    "ViewAllAgents",
    "ViewUsersAgents",
]
