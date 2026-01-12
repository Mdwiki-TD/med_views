"""
Tests for src.services.mysql_client
"""
from unittest.mock import patch, MagicMock
import pytest

from src.services.mysql_client import (
    _sql_connect_pymysql,
    decode_bytes_in_list,
    decode_value,
    load_db_config,
    make_sql_connect,
)


def test_load_db_config():
    config = load_db_config("test_db", "test_host")
    assert config["host"] == "test_host"
    assert config["database"] == "test_db"
    assert "replica.my.cnf" in config["read_default_file"]


@patch("pymysql.connect")
def test__sql_connect_pymysql(mock_connect):
    # Setup mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Setup return value for fetchall
    expected_results = [{"col": "val"}]
    mock_cursor.fetchall.return_value = expected_results

    results = _sql_connect_pymysql("SELECT 1", db="test_db", host="test_host")

    assert results == expected_results
    mock_connect.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT 1", None)


def test_decode_value():
    assert decode_value(b"hello") == "hello"
    assert decode_value("already_str") == "already_str"
    assert decode_value(b"\xff") == "b'\\xff'"  # Fallback to str()


def test_decode_bytes_in_list():
    rows = [{"a": b"val1", "b": 2}, {"a": "val2", "b": b"val3"}]
    expected = [{"a": "val1", "b": 2}, {"a": "val2", "b": "val3"}]
    assert decode_bytes_in_list(rows) == expected


@patch("src.services.mysql_client._sql_connect_pymysql")
def test_make_sql_connect(mock_sql):
    mock_sql.return_value = [{"col": b"val"}]
    results = make_sql_connect("SELECT 1")
    assert results == [{"col": "val"}]
    mock_sql.assert_called_once()
