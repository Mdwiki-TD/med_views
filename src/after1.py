"""
Filter per-year language view files, keeping only titles with views > 0.

Pipeline (`dumps/views_by_year` -> `update_med_views/views_by_year_all_agents`):
   - Input: `dumps/views_by_year/<year>/<lang>.json`, a flat `{title: views}` mapping.
     Example of `dumps/views_by_year/2021/ab.json`:
     {"Аџьар Ҟаԥшь": 672, "Иҳәаадоу аҳақьымцәа": 567, "Example": 0}
   - Folders whose name is not a number, and excluded years such as `"2015"`, are skipped.
   - For every other year, `views_by_year_all_agents/<year>/<lang>.json` is written
     with only the titles that have views > 0:
     - File: `views_by_year_all_agents/2021/ab.json`
     - Content: `{ "Аџьар Ҟаԥшь": 672, "Иҳәаадоу аҳақьымцәа": 567 }`
   - Languages with no title above 0 in a year get no output file for that year.
   - Unreadable (invalid JSON) input files are skipped.
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
Directory layout used by this script ($MED_VIEWS_PATH, default: ~data/views/):

$MED_VIEWS_PATH
    ├── dumps
    │   └── views_by_year/                  <- input
    │       └── 2016, ..., 2025
    │           └── ar.json, ..., en.json
    │
    └── update_med_views
        └── views_by_year_all_agents/       <- output
            └── 2016, ..., 2025
                └── ar.json, ..., en.json
"""

# Input: per-year language files (`<year>/<lang>.json`)
RAW_SOURCE_PATH = config.paths.dump_dir_path / "views_by_year"

# Output: per-year language files containing only titles with views > 0
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
    """Copy each `<year>/<lang>.json` to the output, keeping only titles with views > 0."""
    if excluded_years is None:
        excluded_years = {"2015"}

    if not source_dir.exists():
        print(f"Source path {source_dir} does not exist.")
        return

    # Year folders only: numeric names that are not excluded
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

            # {title: view_count} restricted to titles with views > 0
            titles_data = {title: count for title, count in data.items() if count > 0}

            # Nothing positive for this language/year: no file is written
            if not titles_data:
                continue

            output_year_dir = create_year_folder(output_dir, year)
            output_file = output_year_dir / f"{lang}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(titles_data, f, ensure_ascii=False, indent=4)


def start() -> None:
    """Run the pipeline."""
    process_raw_views(
        source_dir=RAW_SOURCE_PATH,
        output_dir=ALL_AGENTS_OUTPUT_PATH,
        excluded_years={"2015"},
    )


if __name__ == "__main__":
    start()
