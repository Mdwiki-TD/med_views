"""
Pipeline metadata model for tracking pipeline state.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import BaseModel


class PipelineMetadata(BaseModel):
    """
    Pipeline metadata for tracking state and progress.

    Stores key-value pairs for tracking pipeline state, such as last run times,
    versions, and progress indicators for resumable operations.
    """

    __tablename__ = "pipeline_metadata"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="ISO 8601 timestamp of last update",
    )

    def __repr__(self) -> str:
        return f"<PipelineMetadata(key='{self.key}', value='{self.value[:30]}...')>"


__all__ = [
    "PipelineMetadata",
]
