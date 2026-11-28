"""
Tests for src.app.database.analytics.client module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.app.database.analytics.client import WikiReplicaDB


class TestWikiReplicaDB:
    """Tests for the WikiReplicaDB class."""

    def test_init_unknown_wiki_raises(self):
        """Test initialization raises ValueError for unknown wiki."""
        with patch("src.app.database.analytics.client.WikiReplicaMaps") as mock_maps_class:
            mock_maps = MagicMock()
            mock_maps.resolve_wiki.return_value = None
            mock_maps_class.get_instance.return_value = mock_maps

            with pytest.raises(ValueError, match="Unknown wiki"):
                WikiReplicaDB(wiki_identifier="unknownwiki", safe_load=False)

    def test_init_unknown_wiki_safe_load(self):
        """Test initialization with safe_load=True returns without error."""
        with patch("src.app.database.analytics.client.WikiReplicaMaps") as mock_maps_class:
            mock_maps = MagicMock()
            mock_maps.resolve_wiki.return_value = None
            mock_maps_class.get_instance.return_value = mock_maps

            # Should not raise
            db = WikiReplicaDB(wiki_identifier="unknownwiki", safe_load=True)
            # Object is created but not fully initialized
            assert db.maps == mock_maps

    def test_init_resolves_wiki(self):
        """Test initialization resolves wiki and sets attributes."""
        with patch("src.app.database.analytics.client.WikiReplicaMaps") as mock_maps_class:
            with patch("src.app.database.analytics.client.Config") as mock_config:
                mock_maps = MagicMock()
                mock_maps.resolve_wiki.return_value = {
                    "dbname": "enwiki",
                    "slice": "s1",
                }
                mock_maps_class.get_instance.return_value = mock_maps

                mock_config.get_instance.return_value.analytics_database.user = "user"
                mock_config.get_instance.return_value.analytics_database.password = "pass"

                db = WikiReplicaDB(wiki_identifier="enwiki")

                assert db.dbname == "enwiki_p"
                assert "s1" in db.host

    def test_init_default_slice(self):
        """Test initialization uses default slice if not in info."""
        with patch("src.app.database.analytics.client.WikiReplicaMaps") as mock_maps_class:
            with patch("src.app.database.analytics.client.Config") as mock_config:
                mock_maps = MagicMock()
                mock_maps.resolve_wiki.return_value = {
                    "dbname": "enwiki",
                    # No slice key
                }
                mock_maps_class.get_instance.return_value = mock_maps

                mock_config.get_instance.return_value.analytics_database.user = "user"
                mock_config.get_instance.return_value.analytics_database.password = "pass"

                db = WikiReplicaDB(wiki_identifier="enwiki")

                assert "s1" in db.host  # Default slice

    def test_can_use_sql_true(self):
        """Test can_use_sql returns True when configured."""
        with patch("src.app.database.analytics.client.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.use_sql = True
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = True

            result = WikiReplicaDB.can_use_sql()

            assert result is True

    def test_can_use_sql_false(self):
        """Test can_use_sql returns False when not configured."""
        with patch("src.app.database.analytics.client.Config") as mock_config:
            mock_config.get_instance.return_value.analytics_database.use_sql = False
            mock_config.get_instance.return_value.analytics_database.can_use_sql.return_value = False

            result = WikiReplicaDB.can_use_sql()

            assert result is False

    def test_load_classmethod(self):
        """Test load classmethod creates instance."""
        with patch("src.app.database.analytics.client.WikiReplicaMaps") as mock_maps_class:
            with patch("src.app.database.analytics.client.Config") as mock_config:
                mock_maps = MagicMock()
                mock_maps.resolve_wiki.return_value = {
                    "dbname": "enwiki",
                    "slice": "s1",
                }
                mock_maps_class.get_instance.return_value = mock_maps

                mock_config.get_instance.return_value.analytics_database.user = "user"
                mock_config.get_instance.return_value.analytics_database.password = "pass"

                db = WikiReplicaDB.load("enwiki")

                assert isinstance(db, WikiReplicaDB)
