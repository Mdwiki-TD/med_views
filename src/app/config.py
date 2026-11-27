from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parents[3] / ".env")


@dataclass
class Config:
    """Configuration manager for the medical pageviews analysis system."""

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
        self.main_dump_path.mkdir(exist_ok=True)
        self.json_titles_path.mkdir(exist_ok=True)
        self.views_by_year_path.mkdir(exist_ok=True)


# Singleton instance
_config_instance: Config | None = None


def get_config() -> Config:
    """
    Get the singleton Config instance.

    Returns:
        Config: The singleton configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


__all__ = [
    "Config",
    "get_config",
]
