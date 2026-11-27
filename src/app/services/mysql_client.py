#!/usr/bin/python3
"""MySQL client for executing SQL queries on Wikimedia analytics databases."""

from __future__ import annotations

from collections.abc import Callable
import functools
import logging
from pathlib import Path
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def load_db_config(db: str, host: str) -> dict[str, Any]:
    """
    Constructs a PyMySQL connection configuration dictionary for the specified database and host, using ~/replica.my.cnf as the read-default file.

    Parameters:
        db (str): Name of the target MySQL database.
        host (str): Hostname or IP address of the MySQL server.

    Returns:
        dict[str, Any]: Connection parameters for PyMySQL including:
            - host: provided host
            - database: provided db
            - read_default_file: path to ~/replica.my.cnf
            - charset: "utf8mb4"
            - use_unicode: True
            - autocommit: True
            - cursorclass: DictCursor
    """
    replica_cnf_path = Path.home() / "replica.my.cnf"
    return {
        "host": host,
        "database": db,
        "read_default_file": str(replica_cnf_path),
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": True,
        "cursorclass": DictCursor,
    }


class MySQLClient:
    """Client for executing SQL queries on MySQL databases.

    This class encapsulates database connection and query execution logic,
    with proper dependency injection for testing and configuration.
    """

    def __init__(
        self,
        db_config_loader: Callable | None = None,
    ) -> None:
        """Initialize the MySQL client.

        Parameters:
            db_config_loader: Optional callable that returns a dict of connection
                parameters. Defaults to load_db_config.
        """
        self._db_config_loader = db_config_loader or load_db_config

    def _sql_connect_pymysql(self, query: str, db: str = "", host: str = "", values: tuple = None) -> list:
        """Execute a SQL query and return results.

        Parameters:
            query: SQL query string to execute.
            db: Database name.
            host: Database host.
            values: Optional parameter values for parameterized queries.

        Returns:
            List of result rows as dictionaries, or empty list on error.
        """
        logger.debug("start _sql_connect_pymysql:")

        params = None

        if values:
            params = values

        # connect to the database server without error
        db_config = self._db_config_loader(db, host)

        try:
            connection = pymysql.connect(**db_config)
        except pymysql.Error as e:
            logger.exception(e)
            return []

        with connection as conn, conn.cursor() as cursor:
            # skip sql errors
            try:
                cursor.execute(query, params)

            except Exception as e:
                logger.exception(e)
                return []

            results = []

            try:
                results = cursor.fetchall()

            except Exception as e:
                logger.exception(e)
                return []

            return results

    @staticmethod
    def decode_value(value: bytes | Any) -> str:
        """Decode a bytes value to string.

        Parameters:
            value: Value to decode (bytes or other type).

        Returns:
            Decoded string, or string representation, or empty string on failure.
        """
        try:
            value = value.decode("utf-8")  # Assuming UTF-8 encoding
        except Exception:
            try:
                value = str(value)
            except Exception:
                return ""
        return value

    @classmethod
    def decode_bytes_in_list(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Decode all bytes values in a list of dictionaries.

        Parameters:
            rows: List of dictionaries potentially containing bytes values.

        Returns:
            List of dictionaries with bytes decoded to strings.
        """
        decoded_rows = []

        for row in rows:
            decoded_row = {}
            for key, value in row.items():
                if isinstance(value, bytes):
                    value = cls.decode_value(value)
                decoded_row[key] = value
            decoded_rows.append(decoded_row)

        return decoded_rows

    def execute(self, query: str, db: str = "", host: str = "", values=None) -> list:
        """Execute a SQL query and return decoded results.

        This is the main entry point for executing queries.

        Parameters:
            query: SQL query string to execute.
            db: Database name.
            host: Database host.
            values: Optional parameter values for parameterized queries.

        Returns:
            List of result rows as dictionaries with decoded values.
        """
        if not query:
            logger.debug("query == ''")
            return []

        logger.debug("<<lightyellow>> newsql::")

        rows = self._sql_connect_pymysql(query, db=db, host=host, values=values)
        rows = self.decode_bytes_in_list(rows)

        return rows


# Legacy compatibility layer
_default_client: MySQLClient | None = None


def _get_default_client() -> MySQLClient:
    """Get or create the default MySQL client instance."""
    global _default_client
    if _default_client is None:
        _default_client = MySQLClient()
    return _default_client


def make_sql_connect(query: str, db: str = "", host: str = "", values=None):
    """Legacy entry point. Use MySQLClient.execute instead.

    Parameters:
        query: SQL query string to execute.
        db: Database name.
        host: Database host.
        values: Optional parameter values for parameterized queries.

    Returns:
        List of result rows as dictionaries with decoded values.
    """
    return _get_default_client().execute(query, db=db, host=host, values=values)


def decode_value(value: bytes | Any) -> str:
    """Legacy entry point. Use MySQLClient.decode_value instead."""
    return MySQLClient.decode_value(value)


def decode_bytes_in_list(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Legacy entry point. Use MySQLClient.decode_bytes_in_list instead."""
    return MySQLClient.decode_bytes_in_list(rows)


__all__ = [
    "MySQLClient",
    "make_sql_connect",
    "decode_value",
    "decode_bytes_in_list",
]
