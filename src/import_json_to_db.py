#!/usr/bin/env python3
"""
Import existing JSON files into the SQLite database.

This script migrates data from JSON files under $MED_VIEWS_PATH into the
SQLite database. It is idempotent and resumable.

Usage:
    python3 src/import_json_to_db.py [--titles] [--views] [--all]

Options:
    --titles    Import titles only
    --views     Import views only
    --all       Import both titles and views (default)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Config
from app.database.views_db.services import (
    AggregationService,
    DatabaseService,
    TitleService,
    ViewService,
)

logger = logging.getLogger(__name__)


class JsonImporter:
    """
    Import JSON files into the SQLite database.

    Provides methods for importing titles and views from existing JSON files
    into the database.
    """

    def __init__(self) -> None:
        """Initialize the importer."""
        self.config = Config.get_instance()
        self.db_service = DatabaseService.get_instance(self.config.paths.database_path)
        self.db_service.initialize()

        self.title_service = TitleService(self.db_service)
        self.view_service = ViewService(self.db_service)
        self.aggregation_service = AggregationService(self.db_service)

    def import_titles(self) -> None:
        """
        Import titles from dumps/titles/<lang>.json files.

        Reads each language file and inserts titles into the database.
        """
        titles_dir = self.config.paths.dump_dir_titles_path

        if not titles_dir.exists():
            logger.warning("Titles directory does not exist: %s", titles_dir)
            return

        json_files = list(titles_dir.glob("*.json"))
        logger.info("Found %d title files to import", len(json_files))

        for json_file in tqdm(json_files, desc="Importing titles"):
            lang = json_file.stem

            try:
                with open(json_file, encoding="utf-8") as f:
                    titles = json.load(f)

                if not isinstance(titles, list):
                    logger.warning("Invalid title data in %s", json_file)
                    continue

                # Normalize titles (replace underscores with spaces)
                titles = [t.replace("_", " ") for t in titles]

                count = self.title_service.insert_titles(lang, titles)
                logger.debug("Imported %d titles for %s", count, lang)

            except (json.JSONDecodeError, IOError) as e:
                logger.error("Error importing %s: %s", json_file, e)
                continue

        logger.info("Title import completed")

    def import_views_by_year(self, agent_type: str = "all_agents") -> None:
        """
        Import views from the appropriate directory based on agent_type.

        - all_agents: reads from dumps/views_by_year/<year>/<lang>.json
        - users_agents: reads from update_med_views/views_by_year_users_agents/<year>/<lang>.json

        Parameters:
            agent_type: Type of agent data ('all_agents' or 'users_agents').
        """
        if agent_type == "users_agents":
            views_dir = self.config.paths.update_med_views / "views_by_year_users_agents"
        else:
            views_dir = self.config.paths.dump_dir_views_by_year_path

        if not views_dir.exists():
            logger.warning("Views directory does not exist: %s", views_dir)
            return

        # Process each year directory
        year_dirs = [d for d in views_dir.iterdir() if d.is_dir() and d.name.isdigit()]
        logger.info("Found %d year directories to import", len(year_dirs))

        for year_dir in tqdm(year_dirs, desc="Importing years"):
            year = int(year_dir.name)

            # Skip excluded years
            if year == 2015:
                logger.debug("Skipping excluded year %d", year)
                continue

            # Process each language file
            json_files = list(year_dir.glob("*.json"))

            for json_file in json_files:
                lang = json_file.stem

                try:
                    with open(json_file, encoding="utf-8") as f:
                        views_data = json.load(f)

                    if not isinstance(views_data, dict):
                        logger.warning("Invalid view data in %s", json_file)
                        continue

                    # Handle nested year data (for all-years collection)
                    # If values are dicts, we need to extract the specific year
                    processed_data = {}
                    for title, value in views_data.items():
                        if isinstance(value, dict):
                            # Extract the specific year's views
                            year_views = value.get(str(year), 0)
                            if year_views > 0:
                                processed_data[title.replace("_", " ")] = year_views
                        elif isinstance(value, int):
                            if value > 0:
                                processed_data[title.replace("_", " ")] = value

                    if not processed_data:
                        continue

                    count = self.view_service.insert_views(
                        lang=lang,
                        year=year,
                        views_data=processed_data,
                        agent_type=agent_type,
                    )
                    logger.debug("Imported %d views for %s/%s", count, lang, year)

                except (json.JSONDecodeError, IOError) as e:
                    logger.error("Error importing %s: %s", json_file, e)
                    continue

        logger.info("View import completed for %s", agent_type)

    def import_all(self) -> None:
        """Import all data (titles and views)."""
        logger.info("Starting full import")

        # Import titles first
        self.import_titles()

        # Import views for all_agents
        self.import_views_by_year(agent_type="all_agents")

        # Import views for users_agents (filtered)
        self.import_views_by_year(agent_type="users_agents")

        logger.info("Full import completed")

    def verify_import(self) -> None:
        """
        Verify the import by comparing database counts with file counts.

        Logs warnings if counts don't match. Normalizes titles (underscores
        to spaces) and deduplicates before counting, matching the import logic.
        """
        logger.info("Verifying import...")

        # Check title counts
        titles_dir = self.config.paths.dump_dir_titles_path
        if titles_dir.exists():
            for json_file in titles_dir.glob("*.json"):
                lang = json_file.stem

                with open(json_file, encoding="utf-8") as f:
                    raw_titles = json.load(f)

                # Normalize and deduplicate, matching import logic
                normalized = {t.replace("_", " ") for t in raw_titles}
                file_count = len(normalized)

                db_count = self.title_service.get_title_count_for_language(lang)

                if file_count != db_count:
                    logger.warning(
                        "Title count mismatch for %s: file=%d, db=%d",
                        lang,
                        file_count,
                        db_count,
                    )
                else:
                    logger.debug("Title count verified for %s: %d", lang, db_count)

        logger.info("Verification completed")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Import JSON files into SQLite database")
    parser.add_argument("--titles", action="store_true", help="Import titles only")
    parser.add_argument("--views", action="store_true", help="Import views only")
    parser.add_argument("--all", action="store_true", help="Import all data (default)")
    parser.add_argument("--verify", action="store_true", help="Verify import after completion")

    args = parser.parse_args()

    # Default to --all if no specific option given
    if not (args.titles or args.views or args.all):
        args.all = True

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        importer = JsonImporter()

        if args.titles or args.all:
            importer.import_titles()

        if args.views or args.all:
            importer.import_views_by_year(agent_type="all_agents")
            importer.import_views_by_year(agent_type="users_agents")

        if args.verify:
            importer.verify_import()

        logger.info("Import completed successfully")

    except Exception as e:
        logger.exception("Import failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
