"""
Unit tests for src/app/config.py module.

Classes to test: DatabaseConfig, ViewsDataPaths, Config
"""

import os
from pathlib import Path
from unittest.mock import patch

from src.app.config import (
    Config,
    DatabaseConfig,
    ViewsDataPaths,
    _safe_int,
)


class TestSafeInt:
    """Tests for the _safe_int helper function."""

    def test_valid_integer_string(self):
        """Test conversion of valid integer string."""
        assert _safe_int("42", 0) == 42

    def test_negative_integer_string(self):
        """Test conversion of negative integer string."""
        assert _safe_int("-10", 0) == -10

    def test_zero_string(self):
        """Test conversion of zero string."""
        assert _safe_int("0", 99) == 0

    def test_none_returns_default(self):
        """Test None returns default value."""
        assert _safe_int(None, 100) == 100

    def test_empty_string_returns_default(self):
        """Test empty string returns default value."""
        assert _safe_int("", 100) == 100

    def test_invalid_string_returns_default(self):
        """Test invalid string returns default value."""
        assert _safe_int("not_a_number", 50) == 50

    def test_float_string_returns_default(self):
        """Test float string returns default value."""
        assert _safe_int("3.14", 25) == 25


class TestDatabaseConfig:
    """Tests for the DatabaseConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = DatabaseConfig()

        assert config.user == ""
        assert config.password == ""
        assert config.host is None
        assert config.port == 3306
        assert config.cache_ttl == 60 * 60 * 24 * 7  # 1 week
        assert config.use_sql is True

    def test_custom_values(self):
        """Test initialization with custom values."""
        config = DatabaseConfig(
            user="testuser",
            password="testpass",
            host="localhost",
            port=3307,
            cache_ttl=3600,
            use_sql=False,
        )

        assert config.user == "testuser"
        assert config.password == "testpass"
        assert config.host == "localhost"
        assert config.port == 3307
        assert config.cache_ttl == 3600
        assert config.use_sql is False

    def test_can_use_sql_with_credentials(self):
        """Test can_use_sql returns True when credentials are set."""
        config = DatabaseConfig(user="user", password="pass")
        assert config.can_use_sql() is True

    def test_can_use_sql_without_user(self):
        """Test can_use_sql returns False when user is empty."""
        config = DatabaseConfig(user="", password="pass")
        assert config.can_use_sql() is False

    def test_can_use_sql_without_password(self):
        """Test can_use_sql returns False when password is empty."""
        config = DatabaseConfig(user="user", password="")
        assert config.can_use_sql() is False

    def test_can_use_sql_without_both(self):
        """Test can_use_sql returns False when both are empty."""
        config = DatabaseConfig(user="", password="")
        assert config.can_use_sql() is False

    def test_load_from_env(self):
        """Test load() reads from environment variables."""
        env_vars = {
            "DATABASE_HOST": "db.example.com",
            "DATABASE_PORT": "5432",
            "TOOL_REPLICA_USER": "replica_user",
            "TOOL_REPLICA_PASSWORD": "replica_pass",
            "TOOL_REPLICA_CACHE_TTL": "7200",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = DatabaseConfig.load()

            assert config.host == "db.example.com"
            assert config.port == 5432
            assert config.user == "replica_user"
            assert config.password == "replica_pass"
            assert config.cache_ttl == 7200

    def test_load_with_missing_env_vars(self):
        """Test load() uses defaults for missing env vars."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove specific vars
            for var in ["DATABASE_HOST", "DATABASE_PORT", "TOOL_REPLICA_USER",
                        "TOOL_REPLICA_PASSWORD", "TOOL_REPLICA_CACHE_TTL"]:
                os.environ.pop(var, None)

            config = DatabaseConfig.load()

            assert config.host == ""
            assert config.port == 3306
            assert config.user == ""
            assert config.password == ""
            assert config.cache_ttl == 60 * 60 * 24 * 7

    def test_load_with_invalid_port(self):
        """Test load() uses default port for invalid value."""
        env_vars = {"DATABASE_PORT": "not_a_number"}

        with patch.dict(os.environ, env_vars, clear=False):
            config = DatabaseConfig.load()
            assert config.port == 3306


class TestViewsDataPaths:
    """Tests for the ViewsDataPaths dataclass."""

    def test_custom_values(self):
        """Test initialization with custom values."""
        paths = ViewsDataPaths(
            views_data_path=Path("/data/views"),
            dump_dir_path=Path("/data/views/dumps"),
            dump_dir_titles_path=Path("/data/views/dumps/titles"),
            dump_dir_views_by_year_path=Path("/data/views/dumps/views_by_year"),
            update_med_views=Path("/data/views/update_med_views"),
        )

        assert paths.views_data_path == Path("/data/views")
        assert paths.dump_dir_path == Path("/data/views/dumps")
        assert paths.dump_dir_titles_path == Path("/data/views/dumps/titles")
        assert paths.dump_dir_views_by_year_path == Path("/data/views/dumps/views_by_year")
        assert paths.update_med_views == Path("/data/views/update_med_views")

    def test_load_with_env_var(self, tmp_path):
        """Test load() uses MED_VIEWS_PATH from environment."""
        views_path = tmp_path / "custom_views"

        with patch.dict(os.environ, {"MED_VIEWS_PATH": str(views_path)}, clear=False):
            paths = ViewsDataPaths.load()

            assert paths.views_data_path == views_path
            assert paths.dump_dir_path == views_path / "dumps"
            assert paths.dump_dir_titles_path == views_path / "dumps" / "titles"
            assert paths.dump_dir_views_by_year_path == views_path / "dumps" / "views_by_year"
            assert paths.update_med_views == views_path / "update_med_views"

    def test_load_creates_directories(self, tmp_path):
        """Test load() creates necessary directories."""
        views_path = tmp_path / "new_views"

        with patch.dict(os.environ, {"MED_VIEWS_PATH": str(views_path)}, clear=False):
            ViewsDataPaths.load()

            assert (views_path / "dumps" / "titles").exists()
            assert (views_path / "dumps" / "views_by_year").exists()
            assert (views_path / "update_med_views" / "views_by_year_all_agents").exists()
            assert (views_path / "update_med_views" / "views_by_year_users_agents").exists()

    def test_load_default_path(self):
        """Test load() uses default path when env var is empty."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MED_VIEWS_PATH", None)

            paths = ViewsDataPaths.load()

            expected_base = Path.home() / "data/views"
            assert paths.views_data_path == expected_base


class TestConfig:
    """Tests for the Config singleton dataclass."""

    def setup_method(self):
        """Reset singleton before each test."""
        Config._instance = None

    def teardown_method(self):
        """Reset singleton after each test."""
        Config._instance = None

    def test_get_instance_returns_singleton(self):
        """Test get_instance returns the same instance."""
        instance1 = Config.get_instance()
        instance2 = Config.get_instance()

        assert instance1 is instance2

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()

        assert config.parallelism == 10
        assert isinstance(config.analytics_database, DatabaseConfig)
        assert isinstance(config.paths, ViewsDataPaths)

    def test_custom_username(self):
        """Test custom username from environment."""
        with patch.dict(os.environ, {"MDWIKI_USERNAME": "CustomUser"}, clear=False):
            Config._instance = None  # Reset singleton
            config = Config()
            assert config.my_username == "CustomUser"

    def test_default_username(self):
        """Test default username when env var is not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MDWIKI_USERNAME", None)
            Config._instance = None
            config = Config()
            assert config.my_username == "Mr. Ibrahem"

    def test_password_from_env(self):
        """Test password loaded from environment."""
        with patch.dict(os.environ, {"MDWIKI_HIMO_PASSWORD": "secret123"}, clear=False):
            Config._instance = None
            config = Config()
            assert config.mdwiki_pass == "secret123"

    def test_default_password(self):
        """Test default password when env var is not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MDWIKI_HIMO_PASSWORD", None)
            Config._instance = None
            config = Config()
            assert config.mdwiki_pass == ""

    def test_parallelism_default(self):
        """Test parallelism default value."""
        config = Config()
        assert config.parallelism == 10
