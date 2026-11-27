# Medical Wikipedia Pageviews Analysis System

A comprehensive system that collects and analyzes pageview data for medical articles across multiple Wikipedia language editions, then generates reports and uploads them to MDWiki (WikiProject Medicine).

## Overview

This project implements a three-phase data pipeline:

1. **Title Collection**: Queries Wikimedia Labs DB for medical articles across language editions
2. **View Collection**: Fetches pageview data from Wikimedia Pageviews API for collected titles
3. **Report Generation**: Aggregates statistics and generates MediaWiki tables for MDWiki

## Prerequisites

- Python 3.11+ (configured for 3.13)
- Database access to Wikimedia's labsdb (optional - system works without DB)
- Environment variables configured (see `example.env`)

## Installation

```bash
pip install -r requirements.txt
```

### Required Dependencies

- `tqdm` - Progress bars
- `mwclient` - MediaWiki API client
- `requests` - HTTP requests
- `pymysql` - MySQL database access
- `python-dotenv` - Environment variable management

## Environment Variables

Copy `example.env` to `.env` and configure:

```bash
MDWIKI_USERNAME=your_username
MDWIKI_HIMO_PASSWORD=your_password
MAIN_PATH=/path/to/output/directory
```

- `MDWIKI_USERNAME`: Username for MDWiki uploads
- `MDWIKI_HIMO_PASSWORD`: Password for MDWiki uploads
- `MAIN_PATH`: Output directory for JSON dumps (defaults to `~/data/views_dumps/`)

## Workflow and Execution

The data collection and processing should be performed in the following order:

### 1. Collect Article Titles

Fetch the list of medical article titles for each language from the Wikimedia database.

```bash
python3 start_titles.py
```

**What it does:**

- Retrieves medicine-related titles using SQL queries
- Saves per-language JSON files to `~/data/views_dumps/titles/`
- Creates `all_languages_titles.json` summary

**Options:**

- Add `local` argument to load from existing files instead of querying DB: `python3 start_titles.py local`

### 2. Collect Pageview Data

Fetch historical pageview data for the collected titles.

**Single-year mode:**

```bash
python3 start_views.py
```

**Multi-year mode (2015-2025):**

```bash
python3 start_views_all_years.py
```

**What it does:**

- Iterates through collected titles
- Uses Wikimedia Pageviews API to fetch view counts
- Stores yearly JSON data in `~/data/views_dumps/views_by_year/YYYY/`

**Parameters:**

- `-max:<number>`: Maximum number of titles to process per language
- `-min:<number>`: Minimum number of titles required to process a language
- `-para:<number>`: Number of parallel threads (default: 10)

### 3. Generate Reports and Upload

Aggregate the data and generate a summary report for MDWiki.

```bash
python3 start.py
```

**What it does:**

- Aggregates views by language
- Generates formatted MediaWiki tables
- Uploads summary to MDWiki (with `save` argument)

**Parameters:**

- `year:<year>`: The year for which to generate stats (default: 2024)
- `limit:<number>`: Limit the number of languages processed
- `save`: Actually upload to MDWiki (without this, just generates locally)

## Testing

Run the test suite using pytest:

```bash
# Run all tests (excludes network tests by default)
python -m pytest

# Run only unit tests
python -m pytest -m unit

# Run network tests (requires actual API access)
python -m pytest -m network

# Run specific test file
python -m pytest tests/test_config.py

# Run with verbose output
python -m pytest -v
```

## Code Quality

Format and lint code using the configured tools:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
ruff check src/ tests/
```

Configuration is in `pyproject.toml`:

- Line length: 120 characters
- Target Python: 3.13
- Import sorting: black-compatible profile

## Project Structure

```
med_views/
├── start.py                    # Entry point: report generation
├── start_titles.py             # Entry point: title collection
├── start_views.py              # Entry point: single-year view collection
├── start_views_all_years.py    # Entry point: multi-year view collection
├── src/
│   ├── start.py                # Duplicate entry points (for src layout)
│   ├── start_titles.py
│   ├── start_views.py
│   ├── start_views_all_years.py
│   └── app/
│       ├── config.py           # Centralized configuration
│       ├── services/
│       │   ├── mw_views.py     # Pageviews API client
│       │   └── mysql_client.py # Database client
│       ├── api_sql/
│       │   └── wiki_sql.py     # SQL query executor
│       ├── wiki/
│       │   └── mdwiki_page_mwclient.py  # MDWiki operations
│       ├── views_utils/
│       │   └── views_helps.py  # View processing utilities
│       ├── views.py            # Single-year processing
│       ├── views_all_years.py  # Multi-year processing
│       ├── stats_bot.py        # Single-year statistics
│       ├── stats_bot_all_years.py  # Multi-year statistics
│       ├── sql_utils.py        # SQL query definitions
│       ├── texts_utils.py      # MediaWiki table generation
│       ├── titles_utils.py     # Title processing
│       ├── dump_utils.py       # File I/O utilities
│       └── helps.py            # General utilities
└── tests/                      # Test suite mirroring src structure
```

## Data Output Structure

The system generates JSON files in the following structure:

```
~/data/views_dumps/
├── titles/
│   ├── en.json                 # English medical article titles
│   ├── ar.json                 # Arabic medical article titles
│   └── ...                     # Other languages
├── views_by_year/
│   ├── 2024/
│   │   ├── en.json             # English 2024 view data
│   │   └── ...
│   └── 2025/
│       └── ...
├── all_languages_titles.json   # Summary of all language titles
├── 2024_summary.json           # Annual statistics
└── 2024_stats_all.json         # Per-language statistics
```

## Key Features

- **Parallel Processing**: Configurable thread count for API calls (default: 10)
- **Batch Processing**: 500 articles per API call
- **Incremental Updates**: Checks existing files before re-fetching
- **Graceful SQL Degradation**: Works without database access when `get_sql()` returns false
- **Multi-year Support**: Process data from 2015-2025 simultaneously
- **Title Normalization**: Automatic conversion between underscores and spaces for wiki compatibility

## CI/CD

GitHub Actions workflow runs tests on pull requests:

- Python 3.10 environment
- Runs pytest with default settings
- Excludes network tests

## License

## Contact
