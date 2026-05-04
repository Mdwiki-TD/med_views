# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Medical Wikipedia Pageviews Analysis System that collects and analyzes pageview data for medical articles across multiple Wikipedia language editions, then generates reports and uploads them to MDWiki (WikiProject Medicine).

## Common Commands

### Installation
```bash
pip install -r requirements.txt
```

### Testing
```bash
# Run all tests (excludes network tests by default)
python -m pytest

# Run specific test markers
python -m pytest -m unit       # Unit tests only
python -m pytest -m network    # Network tests only

# Run specific test file
python -m pytest tests/test_config.py
```

### Linting/Formatting
```bash
black src/ tests/
isort src/ tests/
```
Configuration: 120 character line length, Python 3.11 target (see pyproject.toml).

### Workflow Execution
```bash
# 1. Collect article titles from Wikimedia DB
python3 start_titles.py

# 2. Collect pageview data
python3 start_views.py           # Single year
python3 start_views_all_years.py # Multi-year (2015-2025)

# 3. Generate reports and upload to MDWiki
python3 start.py                 # Add "save" argument to upload
```

## Architecture

### Three-Phase Data Pipeline
1. **Title Collection** (`start_titles.py`): Queries Wikimedia Labs DB for medical articles, saves per-language JSON files
2. **View Collection** (`start_views.py`/`start_views_all_years.py`): Fetches pageview data from Wikimedia Pageviews API, stores yearly JSON
3. **Report Generation** (`start.py`): Aggregates views by language, generates MediaWiki tables, uploads to MDWiki

### Data Flow
```
Wikimedia Labs DB → Titles (JSON) → Pageviews API → Views (JSON) → Statistics → Wiki Report
```

### Key Modules
- `src/services/mw_views.py`: Pageviews API client with parallel fetching
- `src/api_sql/wiki_sql.py`: SQL query executor with wiki name mapping
- `src/sql_utils.py`: SQL queries for medical article retrieval
- `src/texts_utils.py`: MediaWiki table generation
- `src/wiki/mdwiki_page_mwclient.py`: MDWiki operations via mwclient
- `src/config.py`: Centralized configuration with environment variables

### Dual-System Design
- **Single-year**: `views.py`, `stats_bot.py` - processes one year at a time
- **Multi-year**: `views_all_years.py`, `stats_bot_all_years.py` - processes 2015-2025 simultaneously
- Both share utilities in `src/views_utils/`

## Environment Variables

Required (see `example.env`):
- `MDWIKI_USERNAME`: MDWiki login for report uploads
- `MDWIKI_PASSWORD`: MDWiki password
- `MAIN_PATH`: Output directory for JSON dumps

## Key Patterns

- **Title normalization**: Convert between underscores and spaces for wiki compatibility
- **Parallel processing**: Configurable thread count for API calls
- **Batch processing**: 500 articles per API call
- **Incremental updates**: Check existing files before re-fetching
- **Graceful SQL degradation**: System works without DB when `GET_SQL()` returns false

## Data Output Structure

- `dumps_all_agents/titles/*.json`: Per-language article titles
- `dumps_all_agents/views_by_year/YYYY/*.json`: Yearly view data
- `dumps_all_agents/YYYY_summary.json`: Annual statistics
- `dumps_all_agents/YYYY_stats_all.json`: Per-language statistics
