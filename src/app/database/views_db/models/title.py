"""
Title model for storing article titles.
"""

from __future__ import annotations

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class Title(BaseModel):
    """
    Article title with language code.

    Normalized storage for article titles to avoid duplication across years
    and agent types. Each title is unique per language.
    """

    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lang: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # Unique constraint on (lang, title) to prevent duplicates
    __table_args__ = (
        UniqueConstraint("lang", "title", name="uq_title_lang_title"),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<Title(id={self.id}, lang='{self.lang}', title='{self.title[:30]}...')>"


__all__ = [
    "Title",
]
