#!/usr/bin/python3
"""Utilities for loading and saving JSON dump files."""

from __future__ import annotations

import json
import logging

from .config import Config, get_config

logger = logging.getLogger(__name__)


class DumpManager:
    """Manager for loading and saving JSON dump files.

    Handles all file I/O for dump files including titles, views,
    and language counts.
    """

    def __init__(
        self,
        config: Config | None = None,
    ) -> None:
        """Initialize the DumpManager.

        Parameters:
            config: Optional configuration object. Defaults to get_config().
        """
        self._config = config or get_config()

    def count_languages_in_json(self) -> dict:
        """Count items in each language JSON file in json_titles_path.

        Scans json_titles_path for files with a .json extension, uses each
        file's stem as the language key, and records the number of top-level
        items in that file.

        Returns:
            dict: Mapping from language code (file stem) to the count of
                top-level JSON items.
        """
        result = {}

        for json_file in self._config.json_titles_path.glob("*.json"):
            lang = json_file.stem

            with open(json_file, encoding="utf-8") as f:
                result[lang] = len(json.load(f))
        return result

    def load_lang_titles_from_dump(self, lang: str) -> list:
        """Load title strings for the given language from the JSON dump.

        Parameters:
            lang: Language identifier used as the JSON filename (e.g., 'en').

        Returns:
            list[str]: A list of title strings with underscores replaced by
                spaces; returns an empty list if the language file does not exist.
        """
        json_file = self._config.json_titles_path / f"{lang}.json"

        if json_file.exists():
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            data = [x.replace("_", " ") for x in data]
            return data

        return []

    @staticmethod
    def replace_underscores(data: dict | list):
        """Replace underscores with spaces in data.

        Parameters:
            data: Dictionary or list to process.

        Returns:
            Processed data with underscores replaced by spaces.
        """
        if isinstance(data, dict):
            data = {x.replace("_", " "): v for x, v in data.items()}

        if isinstance(data, list):
            data = [x.replace("_", " ") if isinstance(x, str) else x for x in data]
        return data

    def dump_one(self, file, data) -> None:
        """Write data to a JSON file.

        Parameters:
            file: Path to the output file.
            data: Data to write (dict or list).
        """
        if not data:
            return

        logger.debug(f"dump_one({file}), {len(data)=}")

        data = self.replace_underscores(data)

        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def dump_languages_counts(self, data: dict[str, int]) -> None:
        """Write language count data to the main dump file.

        The input mapping is sorted by count in descending order and written
        to main_dump_path/languages_counts.json as JSON. If data is empty or
        has 200 or fewer entries, no file is written.

        Parameters:
            data: Mapping of language identifiers to integer counts.
        """
        file = self._config.main_dump_path / "languages_counts.json"

        # sort data
        data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))

        if data and len(data) > 200:
            fix_data = self.replace_underscores(data)

            with open(file, "w", encoding="utf-8") as f:
                json.dump(fix_data, f, ensure_ascii=False, indent=4)

    def load_languages_counts(self) -> dict:
        """Load the saved mapping of language codes to article counts.

        Returns:
            dict: A mapping from language code (str) to count (int) loaded
                from "languages_counts.json", or an empty dict if the file
                does not exist.
        """
        file = self._config.main_dump_path / "languages_counts.json"

        data = {}

        if file.exists():
            with open(file, encoding="utf-8") as f:
                data = json.load(f)

        logger.debug(f"load_languages_counts({file}), {len(data)=}")

        return data


__all__ = [
    "DumpManager",
]
