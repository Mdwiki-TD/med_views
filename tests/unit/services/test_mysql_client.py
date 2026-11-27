"""
Tests for src.app.services.mysql_client
"""

from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.app.services.mysql_client import (
    MySQLClient,
    load_db_config,
)


def test_load_db_config():
    config = load_db_config("test_db", "test_host")
    assert config["host"] == "test_host"
    assert config["database"] == "test_db"
    assert "replica.my.cnf" in config["read_default_file"]


def test__sql_connect_pymysql(monkeypatch: MonkeyPatch) -> None:
    mock_connect = MagicMock()
    monkeypatch.setattr("src.app.services.mysql_client.pymysql.connect", mock_connect)

    # Setup mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Configure mock_connect
    mock_connect.return_value = mock_conn

    # Configure context managers
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor

    # Setup return value for fetchall
    expected_results = [{"col": "val"}]
    mock_cursor.fetchall.return_value = expected_results

    results = MySQLClient()._sql_connect_pymysql("SELECT 1", db="test_db", host="test_host")

    assert results == expected_results
    mock_connect.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT 1", None)


def test_decode_value():
    assert MySQLClient.decode_value(b"hello") == "hello"
    assert MySQLClient.decode_value("already_str") == "already_str"
    # str(b"\xff") in Python 3 is "b'\xff'"
    assert MySQLClient.decode_value(b"\xff") == "b'\\xff'"


def test_decode_bytes_in_list():
    rows = [{"a": b"val1", "b": 2}, {"a": "val2", "b": b"val3"}]
    expected = [{"a": "val1", "b": 2}, {"a": "val2", "b": "val3"}]
    assert MySQLClient.decode_bytes_in_list(rows) == expected


def test_execute(monkeypatch: MonkeyPatch) -> None:
    mock_sql = MagicMock(return_value=[{"col": b"val"}])
    monkeypatch.setattr("src.app.services.mysql_client.MySQLClient._sql_connect_pymysql", mock_sql)

    client = MySQLClient()
    results = client.execute("SELECT 1")
    # execute calls decode_bytes_in_list on the results
    assert results == [{"col": "val"}]
    mock_sql.assert_called_once()
