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
    # Clear cache before test if needed, but since it's the first time it should be fine.
    # We can use GET_SQL.cache_clear()
    GET_SQL.cache_clear()
    with patch("os.path.isdir") as mock_isdir:
        # Case 1: On labs
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

    host, db = make_labsdb_dbs_p("be-tarask")
    assert host == "be_x_old.analytics.db.svc.wikimedia.cloud"
    assert db == "be_x_old_p"


@patch("src.api_sql.wiki_sql.GET_SQL")
@patch("src.services.mysql_client.make_sql_connect")
def test_retrieve_sql_results(mock_make_sql, mock_get_sql):
    mock_get_sql.return_value = True
    mock_make_sql.return_value = [{"col": "val"}]

    results = retrieve_sql_results("SELECT 1", wiki="enwiki")

    assert results == [{"col": "val"}]
    mock_make_sql.assert_called_once()

    # Case when GET_SQL is False
    mock_get_sql.return_value = False
    assert retrieve_sql_results("SELECT 1") == []
