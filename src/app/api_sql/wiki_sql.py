#!/usr/bin/python3
"""Wiki SQL client for querying Wikimedia analytics databases."""

from __future__ import annotations

import functools
import logging
import os
import time
from collections.abc import Callable

from ..services.mysql_client import MySQLClient

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_sql() -> bool:
    """Check if running on Toolforge infrastructure where SQL is available.

    Returns:
        bool: True if SQL queries can be executed, False otherwise.
    """
    dir1 = "/mnt/nfs/labstore-secondary-tools-project/"
    dir2 = "/data/project/"

    if not os.path.isdir(dir1) and not os.path.isdir(dir2) or os.path.isdir("I:/core/bots"):
        return False

    return True


class WikiDatabaseMapper:
    """Maps wiki names to database hosts and names.

    Handles the naming conventions used by Wikimedia analytics databases.
    """

    # Known database name mappings
    DATABASE_MAP = {
        "wikidata": "wikidatawiki",
        "be-x-old": "be_x_old",
        "be_tarask": "be_x_old",
        "be-tarask": "be_x_old",
    }

    VALID_ENDS = ["wiktionary"]

    def map_wiki_to_database(self, wiki: str) -> tuple[str, str]:
        """Generate host and database name for a given wiki.

        This method takes a wiki name as input, processes it to conform to
        specific naming conventions, and generates the corresponding host and
        database name. It handles certain predefined wiki names by mapping them
        to standardized formats.

        Parameters:
            wiki: The name of the wiki, which may include a suffix or hyphens.

        Returns:
            tuple: A tuple containing (host, database_name).
        """
        wiki = wiki.removesuffix("wiki")
        wiki = wiki.replace("-", "_")

        wiki = self.DATABASE_MAP.get(wiki) or wiki

        if not (any((wiki.endswith(x)) for x in self.VALID_ENDS)) and wiki.find("wiki") == -1:
            wiki = f"{wiki}wiki"

        host = f"{wiki}.analytics.db.svc.wikimedia.cloud"
        dbs_p = f"{wiki}_p"

        return host, dbs_p


class WikiSQLClient:
    """Client for executing SQL queries against Wikimedia analytics databases.

    This class coordinates wiki-to-database mapping and SQL execution,
    with proper dependency injection for testing.
    """

    def __init__(
        self,
        database_mapper: WikiDatabaseMapper | None = None,
        sql_client: MySQLClient | None = None,
        sql_checker: Callable | None = None,
    ) -> None:
        """Initialize the WikiSQL client.

        Parameters:
            database_mapper: Optional mapper for wiki names to database hosts.
                Defaults to WikiDatabaseMapper.
            sql_client: Optional MySQL client for executing queries.
                Defaults to MySQLClient.
            sql_checker: Optional callable that returns whether SQL is available.
                Defaults to get_sql.
        """
        self._mapper = database_mapper or WikiDatabaseMapper()
        self._sql_client = sql_client or MySQLClient()
        self._sql_checker = sql_checker or get_sql

    def retrieve_sql_results(self, queries, wiki: str = "", values=None) -> list:
        """Retrieve SQL query results for a specified wiki's analytics database.

        Parameters:
            queries: SQL query string or list of query strings to execute.
            wiki: Wiki identifier used to derive the analytics host and database.
            values: Optional parameter values for a parameterized query.

        Returns:
            List of rows returned by the database, or empty list if SQL
            execution is skipped.
        """
        logger.debug(f"wiki_sql.py retrieve_sql_results wiki '{wiki}'")

        host, dbs_p = self._mapper.map_wiki_to_database(wiki)

        logger.debug(queries)

        if not self._sql_checker():
            logger.info("no get_sql()")
            return []

        start = time.perf_counter()

        rows = self._sql_client.execute(queries, db=dbs_p, host=host, values=values)

        delta = time.perf_counter() - start

        logger.debug(f'wiki_sql.py retrieve_sql_results len(encats) = "{len(rows)}", in {delta:.2f} seconds')

        return rows


__all__ = [
    "WikiDatabaseMapper",
    "WikiSQLClient",
]
