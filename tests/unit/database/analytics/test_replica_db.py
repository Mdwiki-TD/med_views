"""
Tests for src.app.database.analytics.replica_db module.
"""

from unittest.mock import MagicMock, patch

import pymysql
import pytest

from src.app.database.analytics.replica_db import RowDecoder, WikiReplicaBaseDB


class TestRowDecoder:
    """Tests for the RowDecoder class."""

    def test_decode_value_bytes(self):
        """Test decoding bytes to string."""
        result = RowDecoder.decode_value(b"hello")
        assert result == "hello"

    def test_decode_value_string(self):
        """Test decoding non-bytes falls back to str()."""
        result = RowDecoder.decode_value(123)
        assert result == "123"

    def test_decode_value_undecodable(self):
        """Test decoding undecodable value returns empty string."""

        # Create an object that fails both decode and str
        class BadObject:
            def decode(self, encoding):
                raise Exception("cannot decode")

            def __str__(self):
                raise Exception("cannot convert to str")

        result = RowDecoder.decode_value(BadObject())
        assert result == ""

    def test_resolve_bytes_mixed_rows(self):
        """Test resolve_bytes handles mixed byte and non-byte values."""
        rows = [
            {"name": b"Alice", "age": 30},
            {"name": b"Bob", "city": b"NYC"},
        ]

        result = RowDecoder.resolve_bytes(rows)

        assert result == [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "city": "NYC"},
        ]

    def test_resolve_bytes_empty_rows(self):
        """Test resolve_bytes with empty list."""
        result = RowDecoder.resolve_bytes([])
        assert result == []

    def test_resolve_bytes_no_bytes(self):
        """Test resolve_bytes with no byte values."""
        rows = [{"name": "Alice", "age": 30}]
        result = RowDecoder.resolve_bytes(rows)
        assert result == [{"name": "Alice", "age": 30}]


class TestWikiReplicaBaseDB:
    """Tests for the WikiReplicaBaseDB class."""

    def test_init(self):
        """Test initialization stores attributes."""
        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        )

        assert db.dbname == "testdb"
        assert db.host == "localhost"
        assert db.user == "user"
        assert db.password == "pass"
        assert db.port == 3306
        assert db.connection is None

    def test_init_custom_port(self):
        """Test initialization with custom port."""
        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
            port=3307,
        )

        assert db.port == 3307

    def test_ensure_connection_no_credentials(self):
        """Test _ensure_connection raises without credentials."""
        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="",
            password="",
        )

        with pytest.raises(pymysql.err.OperationalError):
            db._ensure_connection()

    @patch("src.app.database.analytics.replica_db.pymysql.connect")
    def test_ensure_connection_success(self, mock_connect):
        """Test _ensure_connection establishes connection."""
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_connect.return_value = mock_connection

        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        )
        db._ensure_connection()

        mock_connect.assert_called_once()
        assert db.connection == mock_connection

    @patch("src.app.database.analytics.replica_db.pymysql.connect")
    def test_select(self, mock_connect):
        """Test select executes query and returns results."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_connection = MagicMock()
        mock_connection.open = True
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        )
        result = db.select("SELECT * FROM test")

        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch("src.app.database.analytics.replica_db.pymysql.connect")
    def test_select_one(self, mock_connect):
        """Test select_one returns first result."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1}]
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_connection = MagicMock()
        mock_connection.open = True
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        )
        result = db.select_one("SELECT * FROM test")

        assert result == {"id": 1}

    @patch("src.app.database.analytics.replica_db.pymysql.connect")
    def test_select_one_empty(self, mock_connect):
        """Test select_one returns None when no results."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_connection = MagicMock()
        mock_connection.open = True
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        )
        result = db.select_one("SELECT * FROM test WHERE id = 999")

        assert result is None

    @patch("src.app.database.analytics.replica_db.pymysql.connect")
    def test_select_safe_connection_error(self, mock_connect):
        """Test select_safe returns empty list on connection error."""
        mock_connect.side_effect = pymysql.err.OperationalError("Connection failed")

        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        )
        result = db.select_safe("SELECT * FROM test")

        assert result == []

    @patch("src.app.database.analytics.replica_db.pymysql.connect")
    def test_close(self, mock_connect):
        """Test close closes connection."""
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_connect.return_value = mock_connection

        db = WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        )
        db._ensure_connection()
        db.close()

        mock_connection.close.assert_called_once()
        assert db.connection is None

    @patch("src.app.database.analytics.replica_db.pymysql.connect")
    def test_context_manager(self, mock_connect):
        """Test context manager closes connection on exit."""
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_connect.return_value = mock_connection

        with WikiReplicaBaseDB(
            dbname="testdb",
            host="localhost",
            user="user",
            password="pass",
        ) as db:
            pass

        mock_connection.close.assert_called_once()
