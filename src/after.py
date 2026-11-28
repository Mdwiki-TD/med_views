"""
Read raw language JSON files from `update_med_views/views_new/all` and process
already split yearly files from `update_med_views/views_by_year_users_agents`.

1. Raw views pipeline (`update_med_views/views_new/all` -> `update_med_views/views_by_year_all_agents`):
   - Example of `update_med_views/views_new/all/ab.json`:
     {"Аџьар Ҟаԥшь": { "2021": 672, "2022": 1548, "2023": 2365, "2024": 1136, "2025": 549, "all": 6270 }, "Иҳәаадоу аҳақьымцәа": { "2017": 85, "2018": 319, "2019": 680, "2020": 763, "2021": 567, "2022": 838, "2023": 1135, "2024": 1019, "2025": 444, "all": 5850 },}
   - For each year (excluding `"all"`, non-digit keys, and excluded years such as `"2025"`),
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

2. Pre-split yearly views pipeline (`update_med_views/views_by_year_users_agents`):
   - Reads existing `<year>/<lang>.json` files inside each year directory.
   - Sums the view counts per language for each year and writes sorted descending
     summaries to `views_by_year_users_agents/<year>_languages_counts.json`.
"""

from __future__ import annotations

import functools
import json
import logging
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from app.config import Config

logger = logging.getLogger(__name__)

config = Config.get_instance()

# Base directory for views data  (default: ~data/views/update_med_views/)
BASE_PATH = config.paths.update_med_views

# Source and output paths for raw views (all agents)
RAW_SOURCE_PATH = BASE_PATH / "views_new" / "all"

ALL_AGENTS_OUTPUT_PATH = BASE_PATH / "views_by_year_all_agents"

# Pre-split yearly views path (users agents)
USERS_AGENTS_YEAR_PATH = BASE_PATH / "views_by_year_users_agents"


def dump_languages_counts(
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
    """Split raw language JSON files by year and export yearly language view counts."""
    if excluded_years is None:
        excluded_years = {"2025"}

    if not source_dir.exists():
        print(f"Source path {source_dir} does not exist.")
        return

    languages_counts_by_year: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    json_files = list(source_dir.glob("*.json"))

    for file_path in tqdm(json_files, desc="Processing raw language files"):
        lang = file_path.stem

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            continue

        # Map each year to a dict of {title: view_count}
        year_split_data: defaultdict[str, dict[str, int]] = defaultdict(dict)

        for title, views_dict in data.items():
            for year, count in views_dict.items():
                if year == "all" or not year.isdigit() or year in excluded_years:
                    continue

                if count > 0:
                    year_split_data[year][title] = count
                    languages_counts_by_year[lang][year] += count

        # Remove obsolete yearly language files during a refresh.
        # If an existing language/year changes from positive counts to all-zero counts, year_split_data has no entry for that year.
        # This loop leaves the previous language file unchanged. The new summary excludes the language,
        # but its yearly file still reports positive views.
        # Reconcile previously generated language files after successful processing.
        # Remove files that no longer have positive counts, while preserving files generated by the current run.
        for year, titles_data in year_split_data.items():
            year_dir = create_year_folder(output_dir, year)
            output_file = year_dir / f"{lang}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(titles_data, f, ensure_ascii=False, indent=4)

    dump_languages_counts(languages_counts_by_year, output_dir)


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

    dump_languages_counts(languages_counts_by_year, years_root_dir)


def start() -> None:
    """Run both pipelines in sequence."""
    process_raw_views(
        source_dir=RAW_SOURCE_PATH,
        output_dir=ALL_AGENTS_OUTPUT_PATH,
        excluded_years={"2025"},
    )
    process_pre_split_years(
        years_root_dir=USERS_AGENTS_YEAR_PATH,
    )


if __name__ == "__main__":
    start()
