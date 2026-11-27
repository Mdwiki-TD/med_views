"""Tests for refactored classes in src/app."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


from src.app.api_sql.wiki_sql import WikiDatabaseMapper, WikiSQLClient
from src.app.dump_utils import DumpManager
from src.app.helps import JsonHelper
from src.app.services.mysql_client import MySQLClient
from src.app.texts_utils import WikiTextBuilder


class TestMySQLClient:
    """Tests for the MySQLClient class."""

    def test_decode_value_bytes(self):
        """Test decoding bytes to string."""
        result = MySQLClient.decode_value(b"hello")
        assert result == "hello"

    def test_decode_value_non_bytes(self):
        """Test decoding non-bytes value."""
        result = MySQLClient.decode_value(123)
        assert result == "123"

    def test_decode_bytes_in_list(self):
        """Test decoding bytes in list of dicts."""
        rows = [{"name": b"test", "count": 5}]
        result = MySQLClient.decode_bytes_in_list(rows)
        assert result == [{"name": "test", "count": 5}]

    def test_execute_empty_query(self):
        """Test executing empty query returns empty list."""
        client = MySQLClient()
        result = client.execute("")
        assert result == []


class TestWikiDatabaseMapper:
    """Tests for the WikiDatabaseMapper class."""

    def test_map_wiki_to_database_simple(self):
        """Test mapping simple wiki name."""
        mapper = WikiDatabaseMapper()
        host, db = mapper.map_wiki_to_database("enwiki")
        assert host == "enwiki.analytics.db.svc.wikimedia.cloud"
        assert db == "enwiki_p"

    def test_map_wiki_to_database_with_hyphen(self):
        """Test mapping wiki name with hyphen."""
        mapper = WikiDatabaseMapper()
        host, db = mapper.map_wiki_to_database("be-tarask")
        assert host == "be_x_oldwiki.analytics.db.svc.wikimedia.cloud"
        assert db == "be_x_oldwiki_p"

    def test_map_wiki_to_database_wikidata(self):
        """Test mapping wikidata."""
        mapper = WikiDatabaseMapper()
        host, db = mapper.map_wiki_to_database("wikidatawiki")
        assert host == "wikidatawiki.analytics.db.svc.wikimedia.cloud"
        assert db == "wikidatawiki_p"


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


class TestDumpManager:
    """Tests for the DumpManager class."""

    def test_replace_underscores_dict(self):
        """Test replacing underscores in dict keys."""
        data = {"hello_world": 1, "test_case": 2}
        result = DumpManager.replace_underscores(data)
        assert result == {"hello world": 1, "test case": 2}

    def test_replace_underscores_list(self):
        """Test replacing underscores in list."""
        data = ["hello_world", "test_case"]
        result = DumpManager.replace_underscores(data)
        assert result == ["hello world", "test case"]

    def test_load_lang_titles_from_dump_missing_file(self):
        """Test loading from non-existent file returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.app.config import Config

            config = Config()
            config.json_titles_path = Path(tmpdir)
            manager = DumpManager(config=config)
            result = manager.load_lang_titles_from_dump("nonexistent")
            assert result == []

    def test_dump_one_empty_data(self):
        """Test dumping empty data does nothing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.app.config import Config

            config = Config()
            manager = DumpManager(config=config)
            file = Path(tmpdir) / "test.json"
            manager.dump_one(file, [])
            assert not file.exists()


class TestJsonHelper:
    """Tests for the JsonHelper class."""

    def test_is_empty_data_none(self):
        """Test None data is empty."""
        assert JsonHelper.is_empty_data(None) is True

    def test_is_empty_data_empty_dict(self):
        """Test empty dict is empty."""
        assert JsonHelper.is_empty_data({}) is True

    def test_is_empty_data_zero_all(self):
        """Test dict with all=0 is empty."""
        assert JsonHelper.is_empty_data({"all": 0}) is True

    def test_is_empty_data_single_key(self):
        """Test dict with single key is empty."""
        assert JsonHelper.is_empty_data({"key": "value"}) is True

    def test_is_empty_data_not_empty(self):
        """Test non-empty dict."""
        assert JsonHelper.is_empty_data({"all": 100, "2024": 100}) is False

    def test_json_load_with_underscores(self):
        """Test loading JSON normalizes underscores."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"hello_world": 1, "test_case": 2}, f)
            temp_path = f.name

        result = JsonHelper.json_load(temp_path)
        assert result == {"hello world": 1, "test case": 2}

        Path(temp_path).unlink()

    def test_json_load_missing_file(self):
        """Test loading missing file returns None."""
        result = JsonHelper.json_load("/nonexistent/file.json")
        assert result is None


class TestWikiTextBuilder:
    """Tests for the WikiTextBuilder class."""

    def test_build_wiki_text_basic(self):
        """Test building basic wiki text."""
        builder = WikiTextBuilder()
        languages = {"en": 100, "ar": 50}
        views = {"en": 10000, "ar": 5000}

        result = builder.build_wiki_text(languages, views)

        assert "Total views for medical content = 15,000" in result
        assert "Total articles= 150" in result
        assert "en" in result
        assert "ar" in result

    def test_build_wiki_text_empty(self):
        """Test building wiki text with empty data."""
        builder = WikiTextBuilder()
        result = builder.build_wiki_text({}, {})

        assert "Total views for medical content = 0" in result
        assert "Total articles= 0" in result


class TestLegacyCompatibility:
    """Tests for legacy function compatibility."""

    def test_mysql_client_make_sql_connect(self):
        """Test legacy make_sql_connect function."""
        from src.app.services.mysql_client import make_sql_connect

        result = make_sql_connect("")
        assert result == []

    def test_wiki_sql_retrieve_sql_results(self):
        """Test legacy retrieve_sql_results function."""
        from src.app.api_sql.wiki_sql import retrieve_sql_results

        with patch("src.app.api_sql.wiki_sql.get_sql", return_value=False):
            result = retrieve_sql_results("SELECT 1", "enwiki")
            assert result == []

    def test_dump_utils_functions(self):
        """Test legacy dump_utils functions."""
        from src.app.dump_utils import replace_underscores

        result = replace_underscores({"a_b": 1})
        assert result == {"a b": 1}

    def test_helps_functions(self):
        """Test legacy helps functions."""
        from src.app.helps import is_empty_data

        assert is_empty_data(None) is True
        assert is_empty_data({"all": 100, "2024": 100}) is False

    def test_texts_utils_functions(self):
        """Test legacy texts_utils functions."""
        from src.app.texts_utils import build_wiki_text

        result = build_wiki_text({"en": 100}, {"en": 1000})
        assert "Total views" in result
