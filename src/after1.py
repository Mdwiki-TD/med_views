"""


Read per-year language JSON files from `dumps/views_by_year`

1. Raw views pipeline (`dumps/views_by_year` -> `update_med_views/views_by_year_all_agents`):
   - Example of `dumps/views_by_year/2021/ab.json`:
     {"Аџьар Ҟаԥшь": 672, "Иҳәаадоу аҳақьымцәа": 567}
   - For each year folder (skipping non-digit folders and excluded years such as `"2015"`),
     create a folder in `views_by_year_all_agents/<year>` and write `<lang>.json` containing
     only titles with views > 0 in that year:
     - File: `views_by_year_all_agents/2021/ab.json`
     - Content: `{ "Аџьар Ҟаԥшь": 672, "Иҳәаадоу аҳақьымцәа": 567 }`
   - Write per-year language view totals sorted descending into:
     `views_by_year_all_agents/<year>_languages_counts.json`
     - Example:
       {
           "ab": 1239,
           "en": 9876
       }

"""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path

from tqdm import tqdm

from app.config import Config

logger = logging.getLogger(__name__)

config = Config.get_instance()
"""
$MED_VIEWS_PATH (default: ~data/views/)
    ├── dumps
    │   ├── titles/
    │   │   └─── ar.json, ..., en.json
    │   │
    │   └── views_by_year/
    │       └── 2016, ..., 2025
    │           └── ar.json, ..., en.json
    │
    └── update_med_views
        ├── languages_titles_counts.json
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

# Source and output paths for raw views (all agents)
RAW_SOURCE_PATH = config.paths.dump_dir_path / "views_by_year"

ALL_AGENTS_OUTPUT_PATH = config.paths.update_med_views / "views_by_year_all_agents"


@functools.cache
def create_year_folder(base_output_dir: Path, year: str) -> Path:
    """Create and cache a year directory under the given output path."""
    year_folder = base_output_dir / year
    year_folder.mkdir(parents=True, exist_ok=True)
    return year_folder


def process_raw_views(
    source_dir: Path,
    output_dir: Path,
    excluded_years: set[str] | None = None,
) -> None:
    """Read per-year language JSON files and export only titles with views > 0."""
    if excluded_years is None:
        excluded_years = {"2015"}

    if not source_dir.exists():
        print(f"Source path {source_dir} does not exist.")
        return

    year_dirs = [p for p in source_dir.iterdir() if p.is_dir() and p.name.isdigit() and p.name not in excluded_years]

    for year_dir in tqdm(year_dirs, desc="Processing yearly folders"):
        year = year_dir.name

        for file_path in year_dir.glob("*.json"):
            lang = file_path.stem

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                continue

            # Keep only titles with views > 0: {title: view_count}
            titles_data = {title: count for title, count in data.items() if count > 0}

            if not titles_data:
                continue

            output_year_dir = create_year_folder(output_dir, year)
            output_file = output_year_dir / f"{lang}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(titles_data, f, ensure_ascii=False, indent=4)


def start() -> None:
    """Run both pipelines in sequence."""
    process_raw_views(
        source_dir=RAW_SOURCE_PATH,
        output_dir=ALL_AGENTS_OUTPUT_PATH,
        excluded_years={"2015"},
    )


if __name__ == "__main__":
    start()
