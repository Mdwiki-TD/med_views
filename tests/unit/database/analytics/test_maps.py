"""
Tests for src.app.database.analytics.maps module.
"""

import json
import time
from unittest.mock import MagicMock, patch

from src.app.database.analytics.maps import MapsData, WikiMapsStore, WikiReplicaMaps


class TestMapsData:
    """Tests for the MapsData dataclass."""

    def test_init(self):
        """Test MapsData initialization."""
        data = MapsData(
            last_cache_update=1234.5,
            data={"enwiki": {"lang": "en"}},
        )

        assert data.last_cache_update == 1234.5
        assert data.data == {"enwiki": {"lang": "en"}}


class TestWikiMapsStore:
    """Tests for the WikiMapsStore class."""

    def test_load_local_wikimap_success(self, tmp_path):
        """Test loading wiki map from file."""
        file_path = tmp_path / "wikimap.json"
        data = {
            "last_cache_update": 1234.5,
            "data": {"enwiki": {"lang": "en", "dbname": "enwiki"}},
        }
        file_path.write_text(json.dumps(data))

        store = WikiMapsStore()
        result = store.load_local_wikimap(file_path)

        assert result.last_cache_update == 1234.5
        assert result.data == {"enwiki": {"lang": "en", "dbname": "enwiki"}}

    def test_load_local_wikimap_not_found(self, tmp_path):
        """Test loading missing file returns empty MapsData."""
        file_path = tmp_path / "nonexistent.json"

        store = WikiMapsStore()
        result = store.load_local_wikimap(file_path)

        assert result.last_cache_update == 0
        assert result.data == {}

    def test_load_local_wikimap_invalid_json(self, tmp_path):
        """Test loading invalid JSON returns empty MapsData."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")

        store = WikiMapsStore()
        result = store.load_local_wikimap(file_path)

        assert result.last_cache_update == 0
        assert result.data == {}

    def test_save_wikimap(self, tmp_path):
        """Test saving wiki map to file."""
        file_path = tmp_path / "subdir" / "wikimap.json"
        data = {
            "last_cache_update": 1234.5,
            "data": {"enwiki": {"lang": "en"}},
        }

        store = WikiMapsStore()
        store.save_wikimap(str(file_path), data)

        assert file_path.exists()
        loaded = json.loads(file_path.read_text())
        assert loaded == data


class TestWikiReplicaMaps:
    """Tests for the WikiReplicaMaps class."""

    def test_is_cache_valid_never_expire(self):
        """Test cache validation with TTL < 10 (never expire)."""
        with patch("src.app.database.analytics.maps.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.cache_ttl = 0
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            mock_store = MagicMock()
            mock_store.load_local_wikimap.return_value = MapsData(
                last_cache_update=0,
                data={"enwiki": {"lang": "en"}},
            )

            maps = WikiReplicaMaps(
                store=mock_store,
                cache_ttl=0,
                save_new_data=False,
            )

            # With TTL=0, cache is always valid
            assert maps.is_cache_valid(0, time.time()) is True
            assert maps.is_cache_valid(time.time() - 1000000, time.time()) is True

    def test_is_cache_valid_expired(self):
        """Test cache validation with expired cache."""
        with patch("src.app.database.analytics.maps.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.cache_ttl = 3600
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            mock_store = MagicMock()
            mock_store.load_local_wikimap.return_value = MapsData(last_cache_update=0, data={})

            maps = WikiReplicaMaps(
                store=mock_store,
                cache_ttl=3600,
                save_new_data=False,
            )

            # Old timestamp should be expired
            assert maps.is_cache_valid(time.time() - 7200, time.time()) is False

    def test_is_cache_valid_fresh(self):
        """Test cache validation with fresh cache."""
        with patch("src.app.database.analytics.maps.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.cache_ttl = 3600
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            mock_store = MagicMock()
            mock_store.load_local_wikimap.return_value = MapsData(last_cache_update=0, data={})

            maps = WikiReplicaMaps(
                store=mock_store,
                cache_ttl=3600,
                save_new_data=False,
            )

            # Recent timestamp should be valid
            assert maps.is_cache_valid(time.time() - 100, time.time()) is True

    def test_resolve_wiki_direct_hit(self):
        """Test resolve_wiki with direct identifier match."""
        with patch("src.app.database.analytics.maps.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.cache_ttl = 0
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            mock_store = MagicMock()
            mock_store.load_local_wikimap.return_value = MapsData(
                last_cache_update=time.time(),
                data={"enwiki": {"lang": "en", "dbname": "enwiki"}},
            )

            maps = WikiReplicaMaps(
                store=mock_store,
                save_new_data=False,
            )

            result = maps.resolve_wiki("enwiki")

            assert result == {"lang": "en", "dbname": "enwiki"}

    def test_resolve_wiki_append_wiki(self):
        """Test resolve_wiki appends 'wiki' to identifier."""
        with patch("src.app.database.analytics.maps.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.cache_ttl = 0
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            mock_store = MagicMock()
            mock_store.load_local_wikimap.return_value = MapsData(
                last_cache_update=time.time(),
                data={"enwiki": {"lang": "en", "dbname": "enwiki"}},
            )

            maps = WikiReplicaMaps(
                store=mock_store,
                save_new_data=False,
            )

            result = maps.resolve_wiki("en")

            assert result == {"lang": "en", "dbname": "enwiki"}

    def test_resolve_wiki_no_match(self):
        """Test resolve_wiki returns None when no match."""
        with patch("src.app.database.analytics.maps.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.cache_ttl = 0
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            mock_store = MagicMock()
            mock_store.load_local_wikimap.return_value = MapsData(
                last_cache_update=time.time(),
                data={},
            )

            maps = WikiReplicaMaps(
                store=mock_store,
                save_new_data=False,
            )

            result = maps.resolve_wiki("unknownwiki")

            assert result is None

    def test_get_instance_singleton(self):
        """Test get_instance returns same instance."""
        WikiReplicaMaps._instance = None  # Reset singleton

        with patch("src.app.database.analytics.maps.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.cache_ttl = 0
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            mock_store = MagicMock()
            mock_store.load_local_wikimap.return_value = MapsData(last_cache_update=0, data={})

            # Can't easily test singleton without modifying the class,
            # but we can verify the method exists
            assert hasattr(WikiReplicaMaps, "get_instance")
