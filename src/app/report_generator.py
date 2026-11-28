#!/usr/bin/python3
""" """

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import Config
from app.services import MwclientPage
from src.app.io.dump_utils import DumpManager
from src.app.views_utils.views_fetcher import ViewsFetcher
from src.app.wikitext.texts_utils import WikiTextBuilder

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates and uploads wiki reports for medical pageview statistics."""

    def __init__(
        self,
        dump_manager: DumpManager | None = None,
        wiki_builder: WikiTextBuilder | None = None,
        views_fetcher: ViewsFetcher | None = None,
        dump_dir_path: Path | None = None,
        save: bool = True,
    ) -> None:
        self.dump_manager = dump_manager or DumpManager()
        self.wiki_builder = wiki_builder or WikiTextBuilder()
        self.views_fetcher = views_fetcher or ViewsFetcher()

        self.dump_dir_path = dump_dir_path or Config.get_instance().paths.dump_dir_path
        self.save = save

    def get_languages_articles_counts(self) -> dict[str, int]:
        all_infos = self.dump_manager.load_languages_counts()

        if all_infos:
            return all_infos

        result = self.dump_manager.count_languages_in_json()

        logger.debug(f"get_languages_articles_counts local: {len(result)}")

        return result

    def calculate_total_views(self, langcode: str, u_data: dict[str, Any] | None) -> int:
        if u_data is None:
            return 0

        total = 0

        for _, views in u_data.items():
            if isinstance(views, dict):
                views = views.get("all", 0)
            total += views

        if total == 0:
            logger.info(f"No views for {langcode}")
        return total

    def fetch_language_statistics(self, year: int, langcode: str) -> int:
        json_file = self.views_fetcher.get_view_file(langcode, year)
        year_data = self.dump_manager.json_load(json_file)

        # Handle case where json_load returns a list or None
        if not isinstance(year_data, dict):
            return 0

        return self.calculate_total_views(langcode, year_data)

    def make_views_local(self, languages: dict[str, int], year: int, limit: int) -> dict[str, int]:
        views = {}

        for n, (lang, _) in enumerate(languages.items(), start=1):
            if limit > 0 and n > limit:
                logger.info(f"limit {limit} reached, break")
                break

            views[lang] = self.fetch_language_statistics(year, lang)

        return views

    def make_page_text(self, year: int, limit: int) -> str | None:
        """
        Orchestrates collection of per-language pageview totals for a given year.

        Parameters:
            year (int): Year used in view calculations and included in the target wiki page title.
            limit (int): Maximum number of languages to process (0 means no limit).

        Returns:
            str | None: Generated wiki text, or None if no data available.
        """
        languages = self.get_languages_articles_counts()

        logger.info(f"get_languages_articles_counts local: {len(languages)}")

        if not languages or list(set(languages.values())) == [0]:
            logger.error("No languages found, run `python3 start_titles.py` first")
            return None

        # sort languages ASC
        languages = dict(sorted(languages.items(), key=lambda item: item[1], reverse=False))

        views = self.make_views_local(languages, year, limit)

        views_not_0 = len([x for x in views.values() if x > 0])

        logger.info(f"Total views not 0: {views_not_0:,}")

        if not views_not_0:
            logger.info("No views found, run `python3 start_views.py` first")
            return None

        # sort views by value DESC
        views = dict(sorted(views.items(), key=lambda item: item[1], reverse=True))

        # dump views
        with open(self.dump_dir_path / f"{year}_views_by_lang.json", "w", encoding="utf-8") as f:
            json.dump(views, f, ensure_ascii=False, indent=4)

        newtext = self.wiki_builder.build_wiki_text(languages, views)

        with open(self.dump_dir_path / f"{year}_text.txt", "w", encoding="utf-8") as f:
            f.write(newtext)

        return newtext

    def start(self, year: int, limit: int) -> None:
        newtext = self.make_page_text(year, limit)

        if not self.save:
            logger.info("Dry run mode, not saving changes.")
            return

        title = f"WikiProjectMed:WikiProject Medicine/Stats/Total pageviews by language {year}"
        target_page = MwclientPage(title)

        text = target_page.get_text()

        if not newtext:
            logger.info("no text")
            return

        if text == newtext:
            logger.info("no change")
            return

        if target_page.exists():
            target_page.save(newtext=newtext, summary="update")
        else:
            target_page.create(newtext, summary="update")
