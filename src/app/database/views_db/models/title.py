"""
Title model for storing article titles (revised schema).
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class Title(BaseModel):
    """
    Article title with language code.

    Normalized storage for article titles to avoid duplication across years
    and agent types. Each title is unique per language.

    Uses composite primary key (lang, title) - no surrogate ID.
    """

    __tablename__ = "titles"

    # Composite primary key
    lang: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(Text, primary_key=True)

    def __repr__(self) -> str:
        return f"<Title(lang='{self.lang}', title='{self.title[:30]}...')>"


__all__ = [
    "Title",
]
