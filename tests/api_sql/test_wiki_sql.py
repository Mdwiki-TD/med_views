"""
Tests for src.app.api_sql.wiki_sql
"""

from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.app.api_sql.wiki_sql import (
    WikiSQLClient,
    get_sql,
    make_labsdb_dbs_p,
    retrieve_sql_results,
)


def test_get_sql(monkeypatch: MonkeyPatch) -> None:
    # Clear cache before test
    get_sql.cache_clear()

    mock_isdir = MagicMock()
    monkeypatch.setattr("os.path.isdir", mock_isdir)

    # Case 1: On labs
    mock_isdir.side_effect = lambda path: path == "/data/project/"
    assert get_sql() is True

    # Case 2: Not on labs
    get_sql.cache_clear()
    mock_isdir.side_effect = lambda path: False
    assert get_sql() is False


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


def test_retrieve_sql_results(monkeypatch: MonkeyPatch) -> None:
    mock_client = MagicMock(spec=WikiSQLClient)
    mock_client.retrieve_sql_results.return_value = [{"col": "val"}]

    monkeypatch.setattr(
        "src.app.api_sql.wiki_sql._get_default_client",
        lambda: mock_client,
    )

    results = retrieve_sql_results("SELECT 1", wiki="enwiki")

    assert results == [{"col": "val"}]
