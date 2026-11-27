#!/usr/bin/python3
"""General helper utilities for JSON handling and data validation."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class JsonHelper:
    """Helper class for JSON loading and data validation.

    Provides methods for loading JSON files with normalization and
    checking for empty data.
    """

    @staticmethod
    def is_empty_data(data) -> bool:
        """Check if data is considered empty.

        Parameters:
            data: Data to check (typically a dict).

        Returns:
            bool: True if data is empty, None, has 'all' key with value 0,
                or has only one key.
        """
        if not data:
            return True

        if data.get("all", 0) == 0:
            return True

        if len(data) == 1:
            return True

        return False


__all__ = [
    "JsonHelper",
]
