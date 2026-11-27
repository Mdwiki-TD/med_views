#!/usr/bin/python3
"""General helper utilities for JSON handling and data validation."""

from __future__ import annotations

import json
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

    @staticmethod
    def json_load(json_file) -> None | dict | list:
        """Load JSON from a file and normalize underscore-separated names.

        Loads and parses the JSON at json_file. If the top-level value is a
        dict, returns a new dict with all keys having underscores replaced by
        spaces. If the top-level value is a list, returns a new list where
        string elements have underscores replaced by spaces. Returns the parsed
        value unchanged for other JSON types. If the file is missing or contains
        invalid JSON, returns None.

        Parameters:
            json_file: Path to the JSON file to load.

        Returns:
            The normalized JSON structure, or None if loading/parsing failed.
        """
        try:
            with open(json_file, encoding="utf-8") as f:
                u_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to load JSON from {json_file}: {e}")
            return None

        if isinstance(u_data, dict):
            return {x.replace("_", " "): v for x, v in u_data.items()}

        if isinstance(u_data, list):
            return [x.replace("_", " ") if isinstance(x, str) else x for x in u_data]

        return u_data


__all__ = [
    "JsonHelper",
]
