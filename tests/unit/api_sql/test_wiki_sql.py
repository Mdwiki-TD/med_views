"""
Tests for src.app.api_sql.wiki_sql
"""

from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.app.api_sql.wiki_sql import (
    WikiDatabaseMapper,
    WikiSQLClient,
    get_sql,
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


class TestWikiDatabaseMapper:
    """Tests for the WikiDatabaseMapper class."""

    def test_map_wiki_to_database_enwiki(self):
        mapper = WikiDatabaseMapper()
        host, db = mapper.map_wiki_to_database("enwiki")
        assert host == "enwiki.analytics.db.svc.wikimedia.cloud"
        assert db == "enwiki_p"

    def test_map_wiki_to_database_wikidata(self):
        mapper = WikiDatabaseMapper()
        host, db = mapper.map_wiki_to_database("wikidata")
        assert host == "wikidatawiki.analytics.db.svc.wikimedia.cloud"
        assert db == "wikidatawiki_p"

    def test_map_wiki_to_database_be_tarask(self):
        # be-tarask maps to be_x_old, which doesn't have "wiki", so "wiki" is appended
        mapper = WikiDatabaseMapper()
        host, db = mapper.map_wiki_to_database("be-tarask")
        assert host == "be_x_oldwiki.analytics.db.svc.wikimedia.cloud"
        assert db == "be_x_oldwiki_p"


class TestWikiSQLClient:
    """Tests for the WikiSQLClient class."""

    def test_retrieve_sql_results_when_sql_disabled(self):
        """Test that empty list is returned when SQL is disabled."""
        mock_sql_checker = MagicMock(return_value=False)
        client = WikiSQLClient(sql_checker=mock_sql_checker)
        result = client.retrieve_sql_results("SELECT 1", "enwiki")
        assert result == []

    def test_retrieve_sql_results_when_sql_enabled(self):
        """Test that SQL is executed when enabled."""
        mock_sql_client = MagicMock()
        mock_sql_client.execute.return_value = [{"page_title": "Test"}]
        mock_sql_checker = MagicMock(return_value=True)

        client = WikiSQLClient(sql_client=mock_sql_client, sql_checker=mock_sql_checker)
        result = client.retrieve_sql_results("SELECT page_title FROM page", "enwiki")

        assert result == [{"page_title": "Test"}]
        mock_sql_client.execute.assert_called_once()
