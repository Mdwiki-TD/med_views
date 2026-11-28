#!/usr/bin/python3
"""Utilities for loading article titles from dumps or SQL."""

from __future__ import annotations


from .io.dump_utils import DumpManager
from .sql_loader import MedicalTitlesRepository


class TitlesLoader:
    """Loader for article titles from dump files or SQL database.

    Coordinates loading titles from local dump files first, falling back
    to SQL queries when needed.
    """

    def __init__(
        self,
        dump_manager: DumpManager | None = None,
        titles_repo: MedicalTitlesRepository | None = None,
        local: bool = False,
    ) -> None:
        """Initialize the TitlesLoader.

        Parameters:
            dump_manager: Optional DumpManager for loading from dump files.
                Defaults to DumpManager.
            titles_repo: Optional MedicalTitlesRepository for SQL queries.
                Defaults to MedicalTitlesRepository.
        """
        self._dump_manager = dump_manager or DumpManager()
        self._titles_repo = titles_repo or MedicalTitlesRepository()

        self.local = local

    def load_lang_titles(self, lang: str) -> list[str]:
        """Retrieve page titles for the given language.

        Prefers a dump-derived source and falls back to a SQL source.

        If titles are available from the dump, those are returned. If not and
        the process was started with "local" in sys.argv, an empty list is
        returned. Otherwise titles are fetched from the SQL source and any
        underscores in each title are replaced with spaces.

        Parameters:
            lang: Language code or identifier to load titles for.

        Returns:
            list[str]: A list of page title strings for the language.
        """
        data = self._dump_manager.load_lang_titles_from_dump(lang)

        if data:
            return data

        if self.local:
            return []

        data = self._titles_repo.one_lang_titles(lang)

        data = [x.replace("_", " ") for x in data]

        return data


__all__ = [
    "TitlesLoader",
]
