"""
Tests for src.api_sql.wiki_sql
"""
from unittest.mock import patch
import pytest

from src.api_sql.wiki_sql import (
    GET_SQL,
    make_labsdb_dbs_p,
    retrieve_sql_results,
)


def test_GET_SQL():
    # Clear cache before test
    GET_SQL.cache_clear()
    with patch("os.path.isdir") as mock_isdir:
        # Case 1: On labs
        # Logic: if not isdir(dir1) and not isdir(dir2) or isdir("I:/core/bots"): return False
        # If isdir(dir2) is True, then (False and False) is False.
        # If isdir("I:/core/bots") is False, then (False or False) is False.
        # So it does not return False. It returns True.
        mock_isdir.side_effect = lambda path: path == "/data/project/"
        assert GET_SQL() is True

        # Case 2: Not on labs
        GET_SQL.cache_clear()
        mock_isdir.side_effect = lambda path: False
        assert GET_SQL() is False


def test_make_labsdb_dbs_p():
    host, db = make_labsdb_dbs_p("enwiki")
    assert host == "enwiki.analytics.db.svc.wikimedia.cloud"
    assert db == "enwiki_p"

    host, db = make_labsdb_dbs_p("wikidata")
    assert host == "wikidatawiki.analytics.db.svc.wikimedia.cloud"
    assert db == "wikidatawiki_p"

    # be-tarask maps to be_x_old, which doesn't have "wiki", so "wiki" is appended
    host, db = make_labsdb_dbs_p("be-tarask")
    assert host == "be_x_oldwiki.analytics.db.svc.wikimedia.cloud"
    assert db == "be_x_oldwiki_p"


@patch("src.api_sql.wiki_sql.GET_SQL")
@patch("src.api_sql.wiki_sql.mysql_client.make_sql_connect")
def test_retrieve_sql_results(mock_make_sql, mock_get_sql):
    mock_get_sql.return_value = True
    mock_make_sql.return_value = [{"col": "val"}]

    results = retrieve_sql_results("SELECT 1", wiki="enwiki")

    assert results == [{"col": "val"}]
    mock_make_sql.assert_called_once()

    # Case when GET_SQL is False
    mock_get_sql.return_value = False
    assert retrieve_sql_results("SELECT 1") == []
