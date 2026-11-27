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
class Config:
    """Configuration manager for the medical pageviews analysis system."""

    _instance = None

    analytics_database: DatabaseConfig = field(default_factory=DatabaseConfig.load)

    # Core settings
    my_username: str = field(default_factory=lambda: os.getenv("MDWIKI_USERNAME", "Mr. Ibrahem"))
    mdwiki_pass: str = field(default_factory=lambda: os.getenv("MDWIKI_HIMO_PASSWORD", ""))

    # Processing settings
    parallelism: int = 10

    # Paths (computed in __post_init__)
    main_dump_path: Path = field(init=False)
    json_titles_path: Path = field(init=False)
    views_by_year_path: Path = field(init=False)

    def __post_init__(self):
        """Initialize paths and create directories after dataclass init."""
        # Compute paths
        views_dump_path = os.getenv("VIEWS_DUMP_PATH", "")
        self.main_dump_path = Path(views_dump_path) if views_dump_path else Path.home() / "data/views_dumps"
        self.json_titles_path = self.main_dump_path / "titles"
        self.views_by_year_path = self.main_dump_path / "views_by_year"

        # Create directories
        self.main_dump_path.mkdir(parents=True, exist_ok=True)
        self.json_titles_path.mkdir(parents=True, exist_ok=True)
        self.views_by_year_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> Config:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


__all__ = [
    "Config",
]
