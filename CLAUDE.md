# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

```bash
# Testing
python -m pytest                    # All tests (excludes network)
python -m pytest -m network         # Network tests only
python -m pytest tests/test_config.py  # Single test file

# Linting
black src/ tests/ && isort src/ tests/
ruff check src/ tests/

# Workflow execution (in order)
python3 start_titles.py             # 1. Collect titles from DB
python3 start_views.py              # 2. Fetch pageviews (single year)
python3 start_views_all_years.py    # 2. Fetch pageviews (2015-2025)
python3 save_reports.py             # 3. Generate/upload reports
```

## Architecture

### Three-Phase Pipeline

```
DB Query → Titles JSON → API Fetch → Views JSON → Aggregation → Wiki Report
```

1. **start_titles.py**: Queries Wikimedia Labs DB for medical articles across all language editions
2. **start_views.py / start_views_all_years.py**: Fetches pageview data via Wikimedia API
3. **save_reports.py**: Aggregates statistics and generates MediaWiki tables for MDWiki

### Dual-System Design

Two parallel implementations exist:

- **Single-year** (`one_year/views.py`, `one_year/stats.py`): Processes one year
- **Multi-year** (`all_years/views.py`, `all_years/stats.py`): Processes 2015-2025 simultaneously

Both share utilities in `src/app/views_utils/`.

### Entry Points

Entry point scripts exist in both root and `src/` directories. Both work identically.

### Key Modules

- `src/app/services/mw_views.py`: Pageviews API client with ThreadPoolExecutor parallelism
- `src/app/api_sql/wiki_sql.py`: SQL executor with wiki name mapping
- `src/app/sql_utils.py`: SQL queries for medical article retrieval
- `src/app/texts_utils.py`: MediaWiki table generation
- `src/app/services/mdwiki_page_mwclient.py`: MDWiki upload via mwclient
- `src/app/config.py`: Centralized config with env vars

## Command-Line Arguments

Runtime arguments passed via sys.argv with `key:value` format:

- `-max:N` - Max titles per language
- `-min:N` - Min titles to process language
- `-para:N` - Parallel thread count (default: 10)
- `year:YYYY` - Year for stats (default: 2024)
- `limit:N` - Limit languages processed
- `save` - Actually upload to MDWiki (otherwise local only)
- `local` - Load from files instead of DB (start_titles.py only)

## Environment Variables

```bash
MDWIKI_USERNAME=your_username      # MDWiki login
MDWIKI_HIMO_PASSWORD=your_password # MDWiki password
VIEWS_DUMP_PATH=/path/to/output    # Output directory (default: ~data/views_dumps/)
```

## Data Structure

```
~data/views_dumps/
├── titles/*.json              # Per-language article lists
├── views_by_year/YYYY/*.json  # Yearly view data per language
├── all_languages_titles.json  # Title count summary
└── YYYY_summary.json          # Annual statistics
```

## Key Patterns

- **Config dataclass**: `src/app/config.py` uses a `@dataclass` with singleton access via `get_config()`. The dataclass handles env var loading and path computation in `__post_init__`. Use `config = get_config()` to get the singleton instance.
- **Batch processing**: 500 articles per API call
- **Incremental updates**: Checks existing files before re-fetching
- **Title normalization**: Automatic underscore↔space conversion for wiki compatibility
- **Graceful degradation**: Works without DB when `get_sql()` returns false
- **Parallel fetching**: ThreadPoolExecutor with configurable workers

## Testing

Test markers defined in `pytest.ini`:

- `unit`: Unit tests (no external dependencies)
- `network`: Tests requiring actual API access (excluded by default)

Tests mirror source structure in `tests/` directory.
