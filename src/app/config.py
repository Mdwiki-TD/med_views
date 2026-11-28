from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parents[3] / ".env")


def _safe_int(value: str | None, default: int) -> int:
    """Safely convert string to int, returning default on failure."""
    if not value:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


@dataclass
class DatabaseConfig:
    """
    Configuration for database connections.
    """

    user: str = ""
    password: str = ""
    host: str | None = None
    port: int = 3306
    cache_ttl: int = 60 * 60 * 24 * 7  # 1 week
    use_sql: bool = True

    @classmethod
    def load(cls) -> DatabaseConfig:
        """
        Load Database configuration from environment variables."""
        return cls(
            host=os.getenv("DATABASE_HOST") or "",
            port=_safe_int(os.getenv("DATABASE_PORT"), 3306),
            user=os.getenv("TOOL_REPLICA_USER") or "",
            password=os.getenv("TOOL_REPLICA_PASSWORD") or "",
            cache_ttl=_safe_int(os.getenv("TOOL_REPLICA_CACHE_TTL"), 60 * 60 * 24 * 7),
        )

    def can_use_sql(self) -> bool:
        return bool(self.user and self.password)


@dataclass
class ViewsDataPaths:
    """
    Paths for dump files.
    $MED_VIEWS_PATH (default: ~data/views/)
        ├── dumps
        │   ├── titles/
        │   │   └─── ar.json, ..., en.json
        │   │
        │   └── views_by_year/
        │       └── 2016, ..., 2025
        │           └── ar.json, ..., en.json
        │
        └── update_med_views (Used by frontend API)
            ├── languages_titles_counts.json               #
            ├── views_by_year_all_agents
            │   ├── 2016, ..., 2025
            │   │   └── ar.json, ..., en.json
            │   │
            │   ├── 2016_languages_counts.json
            │   └── 2025_languages_counts.json
            │
            └── views_by_year_users_agents
                ├── 2016, ..., 2025
                │   └── ar.json, ..., en.json
                │
                ├── 2016_languages_counts.json
                └── 2025_languages_counts.json
    """

    views_data_path: Path
    dump_dir_path: Path
    dump_dir_titles_path: Path
    dump_dir_views_by_year_path: Path

    update_med_views: Path

    @classmethod
    def load(cls) -> ViewsDataPaths:
        """Initialize paths and create directories after dataclass init."""
        _views_data_path = os.getenv("MED_VIEWS_PATH", "")
        views_data_path = Path(_views_data_path).expanduser() if _views_data_path else Path.home() / "data/views"

        # --------------------------
        # update_med_views paths
        update_med_views = views_data_path / "update_med_views"
        views_by_year_all_agents = update_med_views / "views_by_year_all_agents"
        views_by_year_users_agents = update_med_views / "views_by_year_users_agents"

        # --------------------------
        # dumps paths
        dump_dir_path = views_data_path / "dumps"

        dump_dir_titles_path = dump_dir_path / "titles"
        dump_dir_views_by_year_path = dump_dir_path / "views_by_year"

        # Create directories
        dump_dir_titles_path.mkdir(parents=True, exist_ok=True)
        dump_dir_views_by_year_path.mkdir(parents=True, exist_ok=True)

        views_by_year_all_agents.mkdir(parents=True, exist_ok=True)
        views_by_year_users_agents.mkdir(parents=True, exist_ok=True)

        return cls(
            views_data_path=views_data_path,
            dump_dir_path=dump_dir_path,
            dump_dir_titles_path=dump_dir_titles_path,
            dump_dir_views_by_year_path=dump_dir_views_by_year_path,
            update_med_views=update_med_views,
        )


@dataclass
class Config:
    """Configuration manager for the medical pageviews analysis system."""

    _instance = None

    analytics_database: DatabaseConfig = field(default_factory=DatabaseConfig.load)
    paths: ViewsDataPaths = field(default_factory=ViewsDataPaths.load)

    # Core settings
    my_username: str = field(default_factory=lambda: os.getenv("MDWIKI_USERNAME", "Mr. Ibrahem"))
    mdwiki_pass: str = field(default_factory=lambda: os.getenv("MDWIKI_HIMO_PASSWORD", ""))

    # Processing settings
    parallelism: int = 10

    @classmethod
    def get_instance(cls) -> Config:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


__all__ = [
    "Config",
]
