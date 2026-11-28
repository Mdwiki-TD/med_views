"""
Read raw language JSON files from `update_med_views/views_new/all` and process
already split yearly files from `update_med_views/views_by_year_users_agents`.

2. Pre-split yearly views pipeline (`update_med_views/views_by_year_users_agents`):
   - Reads existing `<year>/<lang>.json` files inside each year directory.
   - Sums the view counts per language for each year and writes sorted descending
     summaries to `views_by_year_users_agents/<year>_languages_counts.json`.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from app.config import Config

logger = logging.getLogger(__name__)

config = Config.get_instance()
"""
$MED_VIEWS_PATH (default: ~data/views/)
    └── update_med_views
        │
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
# Base directory for views data  (default: ~data/views/update_med_views/)
BASE_PATH = config.paths.update_med_views

ALL_AGENTS_OUTPUT_PATH = BASE_PATH / "views_by_year_all_agents"

# Pre-split yearly views path (users agents)
USERS_AGENTS_YEAR_PATH = BASE_PATH / "views_by_year_users_agents"


def dump_languages_views_counts(
    languages_counts_by_year: defaultdict[str, defaultdict[str, int]],
    output_dir: Path,
) -> None:
    """Aggregate counts by year, sort descending by view count, and write JSON summaries."""
    output_dir.mkdir(parents=True, exist_ok=True)
    years_data: dict[str, dict[str, int]] = {}

    for lang, years in languages_counts_by_year.items():
        for year, count in years.items():
            years_data.setdefault(year, {})[lang] = count

    for year, lang_counts in years_data.items():
        sorted_counts = dict(sorted(lang_counts.items(), key=lambda item: item[1], reverse=True))
        year_file = output_dir / f"{year}_languages_counts.json"
        with open(year_file, "w", encoding="utf-8") as f:
            json.dump(sorted_counts, f, ensure_ascii=False, indent=4)
        print(f"Dumped year data to {year_file}")


def process_pre_split_years(years_root_dir: Path) -> None:
    """Aggregate view counts from already split <year>/<lang>.json directories."""
    if not years_root_dir.exists():
        print(f"Pre-split path {years_root_dir} does not exist.")
        return

    languages_counts_by_year: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    years_paths = [p for p in years_root_dir.glob("*/") if p.is_dir()]

    for year_path in tqdm(years_paths, desc="Processing pre-split years"):
        year = year_path.name

        for file_path in year_path.glob("*.json"):
            lang = file_path.stem

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                continue

            languages_counts_by_year[lang][year] = sum(data.values())

    dump_languages_views_counts(languages_counts_by_year, years_root_dir)


def start() -> None:
    """Run both pipelines in sequence."""
    process_pre_split_years(
        years_root_dir=ALL_AGENTS_OUTPUT_PATH,
    )

    process_pre_split_years(
        years_root_dir=USERS_AGENTS_YEAR_PATH,
    )


if __name__ == "__main__":
    start()
