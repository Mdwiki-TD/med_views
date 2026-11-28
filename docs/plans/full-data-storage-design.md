# Full Data Storage Design: SQLite Migration (Revised)

## Executive Summary

This document designs the migration of all file-based data storage under `$MED_VIEWS_PATH` (default `~/data/views/`) to SQLite via SQLAlchemy 2.0. The goal is to replace JSON file I/O with a relational database while preserving all existing behavior and enabling future read-side optimizations.

**Key Corrections Applied**:
- Single `views` table with `agent_type` column (not two separate tables)
- No `INSERT OR REPLACE` on FK-referenced rows; use SQLite-specific upsert
- Composite primary keys, denormalized `lang` in views
- Removed `pipeline_metadata`, timestamps, and `title_count` (not produced by current collectors)
- `ReportGenerator` is read-only and out of scope for conversion
- Clear title normalization rule: always replace underscores with spaces

---

## Phase A: Research and Design (Corrected)

### A1. Inventory (Verified in Code)

#### Code Verification Results

**Agent Type Data Sources**:
- `after1.py`: Reads `dumps/views_by_year/<year>/<lang>.json`, writes to `update_med_views/views_by_year_all_agents/<year>/<lang>.json` (filters views > 0)
- `after2.py`: Reads from **both** `views_by_year_all_agents/` and `views_by_year_users_agents/`, writes `<year>_languages_counts.json`
- **Finding**: No code writes to `views_by_year_users_agents/`. This directory is created by config but populated externally (manual import or separate process).

**Title Normalization**:
- `titles_loader.py`: Calls `replace_underscores()` on load from dump
- `dump_utils.py`: `replace_underscores()` replaces `_` with ` ` in keys and list items
- `views_fetcher.py`: `title.replace("_", " ")` after API fetch
- **Rule**: All titles stored with spaces, never underscores. Normalization happens at load/write time.

**"All" Total Rule**:
- `views_fetcher.py:62,90`: API returns `{"2020": 100, "2021": 200, ..., "all": 300}`
- The `"all"` value is the sum across all years **including 2015**
- `after1.py` excludes 2015 from filtering
- **Rule**: Stored `SUM(views)` excludes 2015; the `"all"` value from API includes 2015. They may differ.

#### Modules and Their Data Access Patterns

| Module | Purpose | Input | Output | Data Shape | Collector? |
|--------|---------|-------|--------|------------|------------|
| `titles_loader.py` | Load/save article titles | SQL DB | `dumps/titles/<lang>.json`, `dumps/all_languages_titles.json`, `dumps/languages_titles_counts.json` | `{lang: [titles]}`, `{lang: count}` | Yes |
| `all_years/run.py` | Orchestrate view collection | Titles, existing views | `dumps/views_by_year/<year>/<lang>.json`, `dumps/empty_views_*.json` | `{title: views}` | Yes |
| `all_years/views.py` | Fetch and cache views | API, cached files | Updates cache | `{title: {year: views}}` | Yes |
| `all_years/stats.py` | Compute statistics | View data | `dumps/<year>_summary.json`, `dumps/<year>_stats_all.json` | Aggregate stats | Yes |
| `after1.py` | Filter views > 0 | `dumps/views_by_year/...` | `update_med_views/views_by_year_all_agents/...` | `{title: views}` (filtered) | Yes |
| `after2.py` | Aggregate language counts | `update_med_views/views_by_year_*/...` | `update_med_views/views_by_year_*/<year>_languages_counts.json` | `{lang: total_views}` | Yes |
| `report_generator.py` | Generate wiki reports | `dumps/views_by_year/...` | `dumps/<year>_views_by_lang.json`, `dumps/<year>_text.txt` | Aggregated views | **No (read-only)** |
| `io/dump_utils.py` | JSON I/O utilities | Various | Various | Generic | Utility |

#### Data Flow Diagram (Corrected)

```
Phase 1: Title Collection
┌─────────────────────────────────────────────────────────────────────────────┐
│ SQL Database → TitlesLoader.start()                                         │
│   → dumps/titles/<lang>.json (underscores → spaces)                         │
│   → dumps/all_languages_titles.json                                         │
│   → dumps/languages_titles_counts.json                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
Phase 2: View Collection
┌─────────────────────────────────────────────────────────────────────────────┐
│ MultiYearViewsPipeline.start()                                              │
│   → dumps/views_by_year/<year>/<lang>.json (spaces, not underscores)        │
│   → dumps/<year>_summary.json (stats per lang)                              │
│   → dumps/<year>_stats_all.json (all langs stats)                           │
│   → dumps/empty_views_*.json (titles with 0 views)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
Phase 3: View Filtering (after1.py)
┌─────────────────────────────────────────────────────────────────────────────┐
│ process_raw_views()                                                         │
│   - Input: dumps/views_by_year/<year>/<lang>.json                           │
│   - Filter: views > 0 only                                                  │
│   - Skip: 2015, non-numeric folders, invalid JSON                           │
│   → update_med_views/views_by_year_all_agents/<year>/<lang>.json            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
Phase 4: Aggregation (after2.py)
┌─────────────────────────────────────────────────────────────────────────────┐
│ process_pre_split_years()                                                   │
│   - Input: views_by_year_all_agents/<year>/<lang>.json                      │
│   - Input: views_by_year_users_agents/<year>/<lang>.json (external source)  │
│   → views_by_year_all_agents/<year>_languages_counts.json                   │
│   → views_by_year_users_agents/<year>_languages_counts.json                 │
└─────────────────────────────────────────────────────────────────────────────┘

Read-Only (Out of Scope):
┌─────────────────────────────────────────────────────────────────────────────┐
│ ReportGenerator.start()                                                     │
│   - Reads: dumps/views_by_year/<year>/<lang>.json                           │
│   - Writes: dumps/<year>_views_by_lang.json, dumps/<year>_text.txt          │
│   - Uploads to MDWiki                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Data Measurements (Verified by Owner)

- **Total titles**: 385,436
- **Languages**: 337
- **Years**: 10 (year range: 2016-2026; 2015 excluded, maximum 10 years)
- **Maximum view rows**: ~3,850,000 (385,436 titles × 10 years; fewer after dropping zero-view rows)
- **File count**: ~3,370 files (337 languages × 10 years)
- **Data size**: ~500 MB uncompressed (estimated from row count)

**Note**: Actual data is much smaller than initial estimates. This simplifies implementation.

### A2. Design Decisions (Corrected)

#### 1. What Gets Stored

**Tables**:
- `titles`: All article titles (normalized to spaces)
- `views`: View counts with `agent_type` column (not two separate tables)
- `language_counts`: Aggregated counts per language/year/agent_type (what `after2.py` writes)
- `statistics`: Summary statistics per language/year (what `stats.py` writes)

**Removed**:
- `pipeline_metadata`: Resumability via idempotent per-language/year transactions
- `created_at`/`updated_at`: Not produced by current collectors
- `title_count` in `language_counts`: Not produced by `after2.py`

**Rationale**:
- Single `views` table with `agent_type` is simpler and matches the actual data flow
- `after1.py` filters views > 0; this is a query-time filter, not a separate storage
- `language_counts` stores only what `after2.py` writes: `{lang: total_views}` per year/agent_type
- `statistics` stores what `stats.py` writes: articles, empty_views, not_empty_views, hash, total_views

#### 2. Schema (Corrected)

```sql
-- Article titles (normalized to spaces)
CREATE TABLE titles (
    lang TEXT NOT NULL,
    title TEXT NOT NULL,
    PRIMARY KEY (lang, title)
) WITHOUT ROWID;

-- View counts (single table with agent_type)
CREATE TABLE views (
    title_id INTEGER NOT NULL,
    lang TEXT NOT NULL,  -- Denormalized for query performance
    year INTEGER NOT NULL,
    agent_type TEXT NOT NULL,  -- 'all_agents' or 'users_agents'
    views INTEGER NOT NULL,
    PRIMARY KEY (title_id, year, agent_type),
    FOREIGN KEY (title_id) REFERENCES titles(rowid) ON DELETE CASCADE
) WITHOUT ROWID;

-- Index for paginated queries: WHERE lang=? AND year=? AND agent_type=? ORDER BY views DESC
CREATE INDEX idx_views_lang_year_agent_views ON views(lang, year, agent_type, views DESC);

-- Aggregated language counts (what after2.py writes)
CREATE TABLE language_counts (
    lang TEXT NOT NULL,
    year INTEGER NOT NULL,
    agent_type TEXT NOT NULL,
    total_views INTEGER NOT NULL,
    PRIMARY KEY (lang, year, agent_type)
) WITHOUT ROWID;

-- Summary statistics (what stats.py writes)
CREATE TABLE statistics (
    lang TEXT NOT NULL,
    year INTEGER,  -- NULL for all-years summary
    articles INTEGER NOT NULL,
    empty_views INTEGER NOT NULL,
    not_empty_views INTEGER NOT NULL,
    hash_count INTEGER NOT NULL,
    total_views INTEGER NOT NULL,
    PRIMARY KEY (lang, year)
) WITHOUT ROWID;
```

**Design Rationale**:
- **Composite primary keys**: No surrogate IDs; natural keys are sufficient
- **WITHOUT ROWID**: Saves space for tables with composite PKs
- **Denormalized `lang` in `views`**: Enables index-based queries without joins
- **Removed redundant indexes**: `UNIQUE(lang, title)` covers lang lookups; no standalone `views(views)` index
- **Index on `(lang, year, agent_type, views DESC)`**: Supports paginated read-side queries

**Future Read-Side Support**:
- Paginated query: `WHERE lang=? AND year=? AND agent_type=? ORDER BY views DESC LIMIT 50 OFFSET ?`
- Index `idx_views_lang_year_agent_views` supports this directly (no join needed)
- Total views: `SELECT SUM(views) FROM views WHERE lang=? AND year=? AND agent_type=?`

**"All" Total Rule**:
- The `"all"` value from the API includes 2015
- Stored `SUM(views)` excludes 2015 (per `after1.py` filtering)
- These may differ; the database stores the filtered sum, not the API's `"all"` value

#### 3. Database Layout

**Decision**: Single SQLite database at `$MED_VIEWS_PATH/med_views.db`.

**Rationale**: Same as before (simplicity, size, backup).

**Concurrency**:
- SQLite WAL mode for concurrent reads during writes
- Pragmas set via `connect` event (not one-time):

```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

#### 4. Write Strategy (Simplified for ~3.85M rows)

**Upsert Strategy**:
- **Do not use `INSERT OR REPLACE`** on rows with FK references (cascades deletes)
- Use SQLAlchemy SQLite-specific upsert:

```python
from sqlalchemy.dialects.sqlite import insert

stmt = insert(View).values([...])
stmt = stmt.on_conflict_do_update(
    index_elements=['title_id', 'year', 'agent_type'],
    set_={'views': stmt.excluded.views}
)
session.execute(stmt)
```

**Re-run Handling**:
- For a language/year re-run: delete existing rows, then bulk insert, in **one transaction**
- Commit once per language/year (337 × 10 = 3,370 transactions max, all fast)

**Bulk Insert**:
- Use executemany form: `conn.execute(insert(Model), list_of_dicts)`
- Chunk size: 1,000 rows per `executemany` call (simple, sufficient for this size)

**Empty Language/Year**:
- Keep current rule: if no positive titles, write nothing (no rows inserted)

**Performance**:
- ~3.85M rows is small; no special optimization needed
- Simple per-language/year transactions are fast and easy to reason about

#### 5. Configuration

**Decision**: Add `database_path` to `ViewsDataPaths` (already done in code).

**Database URL**: `sqlite:///{database_path}`

#### 6. Architecture

**Directory Structure**:
```
src/app/database/views_db/
├── models/
│   ├── title.py           # Title model (composite PK)
│   ├── view.py            # View model (single table, agent_type column)
│   ├── language_count.py  # LanguageCount model
│   └── statistic.py       # Statistic model
├── services/
│   ├── database_service.py   # Init, pragmas, session
│   ├── title_service.py      # Title CRUD
│   ├── view_service.py       # View CRUD (both agent types)
│   └── aggregation_service.py # Compute/cache derived data
└── db.py                  # Existing infrastructure
```

**Legacy Layer**:
- Keep existing public functions working
- Thin wrapper calling new services
- Dual-write mode (JSON + database) allowed for parity comparison, controlled by config flag
- **No fallback to JSON on database failure**; failures are raised

#### 7. Migration of Existing Data

**Import Tool**: `src/import_json_to_db.py`

**Import Order** (Corrected):
1. Import titles from `dumps/titles/<lang>.json`
2. Import views from `dumps/views_by_year/<year>/<lang>.json` as `agent_type='all_agents'`
3. Compute and cache `language_counts` and `statistics`
4. **Note**: `views_by_year_users_agents/` data comes from external source; not imported automatically

**Idempotency**:
- Per-language/year transactions
- Upsert on conflict
- Re-running is safe

**Verification**:
- After import, compare counts and sums
- Per-language/year: `COUNT(*)` and `SUM(views)` must match

#### 8. Rollout and Rollback

**Rollout Order**:
1. Database infrastructure (models, services)
2. `TitlesLoader` (Phase 1)
3. `MultiYearViewsPipeline` (Phase 2)
4. `after1.py` (Phase 3)
5. `after2.py` (Phase 4)
6. Import tool
7. Tests

**Dual-Write Mode**:
- Temporary mode for parity comparison
- Controlled by config flag (e.g., `DUAL_WRITE=true`)
- Writes to both JSON and database
- Compare outputs to verify correctness

**Rollback**:
- Each module can be rolled back independently
- Keep JSON writing during transition
- After verification, disable JSON writing

#### 9. Risks and Open Questions

**Risks**:
- **Collation**: SQLite default collation may not sort non-Latin text correctly (minor)
- **Backup**: Single file is single point of failure; keep JSON archives during transition

**Notes**:
- Database size (~3.85M rows, ~500 MB) is small; no `VACUUM` or performance concerns
- Chunk size: 1,000 rows per `executemany` call is sufficient
- Transaction strategy: One transaction per language/year (337 × 10 = 3,370 transactions max)

**Open Questions**:
- Should we partition by year? **Decision**: No, single table is simpler
- Store `"all"` total explicitly? **Decision**: No, compute on demand; note it excludes 2015

### A3. Title Normalization Rule

**Rule**: Always replace underscores with spaces when storing or loading titles.

**Implementation**:
- `titles_loader.py`: Calls `replace_underscores()` on load
- `views_fetcher.py`: `title.replace("_", " ")` after API fetch
- `dump_utils.py`: `replace_underscores()` utility

**Database**: All titles stored with spaces, never underscores.

### A4. Uncovered Outputs

| Output | Module | Decision |
|--------|--------|----------|
| `empty_views_*.json` | `run.py` | **Derived**: Titles with 0 views. Can be queried: `SELECT title FROM titles WHERE (lang, title) NOT IN (SELECT lang, title FROM views WHERE year=?)` |
| `all_languages_titles.json` | `titles_loader.py` | **Derived**: Aggregate of all titles. Query: `SELECT lang, GROUP_CONCAT(title) FROM titles GROUP BY lang` |
| `<year>_views_by_lang.json` | `report_generator.py` | **Out of scope**: Read-only, generated by `ReportGenerator` |
| `<year>_stats_all.json` | `stats.py` | **Stored**: In `statistics` table |

### A5. Incremental Logic

**Current Behavior** (`all_years/views.py`):
- Checks if `<year>/<lang>.json` exists before fetching
- If exists, loads and merges with new data
- Batch size: 500 titles per API call

**Database Implementation**:
- Query: `SELECT title FROM views WHERE lang=? AND year=? AND agent_type=?`
- If titles exist, skip fetching for those titles
- Batch size remains 500

### A6. `dump_utils.py` Fate

| Helper | Decision | Reason |
|--------|----------|--------|
| `replace_underscores()` | **Keep** | Used by multiple modules for normalization |
| `json_load()` | **Keep** | Used by `report_generator.py` (read-only) |
| `dump_one()`, `dump_list()` | **Remove** | Replaced by database writes |
| `dump_languages_titles_counts()` | **Remove** | Replaced by `language_counts` table |
| `load_languages_counts()` | **Replace** | Query from `language_counts` table |
| `count_languages_in_json()` | **Remove** | Replaced by database query |
| `load_lang_titles_from_dump()` | **Replace** | Query from `titles` table |

### A7. Final Report Additions

**(a) Behavior Described but Not Implemented**:
- None found in current code review

**(b) Readers of Old JSON Files Not Converted**:
- `report_generator.py`: Reads `dumps/views_by_year/<year>/<lang>.json` (out of scope, read-only)

**(c) Differences Found by Parity Checks**:
- To be determined after implementation

---

## Phase B: Implementation (To Be Completed)

### Implementation Status

**Completed**:
- ✅ Updated `Config` to include `database_path`
- ✅ Created models (title, view, language_count, statistic)
- ✅ Created `DatabaseService` with pragma setup
- ✅ Created service classes (title, view, aggregation)
- ✅ Created import tool
- ✅ Created unit tests

**TODO**:
- ⏳ Convert `TitlesLoader` to use database
- ⏳ Convert `MultiYearViewsPipeline` to use database
- ⏳ Convert `after1.py` to use database
- ⏳ Convert `after2.py` to use database
- ⏳ Update tests for converted modules
- ⏳ Run parity checks
- ⏳ Update documentation

### Verification Checklist

- [ ] All unit tests pass
- [ ] Parity tests pass (JSON vs database outputs match)
- [ ] Import tool successfully imports existing data
- [ ] Re-running import is idempotent
- [ ] Comments and docstrings accurately describe code
- [ ] No display or query-endpoint code added
- [ ] Existing JSON files not deleted

---

## Appendix: Code Verification Results

### Agent Type Sources

**Code Search**:
```bash
grep -r "views_by_year_users_agents" src/
```

**Findings**:
- `config.py`: Creates directory
- `after2.py`: Reads from directory
- **No writer found**: Data comes from external source

**Conclusion**: `users_agents` data is imported externally, not generated by the pipeline.

### Title Normalization

**Code Search**:
```bash
grep -n "replace.*_.*\|_.*replace" src/app/*.py
```

**Findings**:
- `titles_loader.py:52`: `data = [x.replace("_", " ") for x in data]`
- `views_fetcher.py:60,90`: `title = title.replace("_", " ")`
- `dump_utils.py:68,84,87`: `replace_underscores()` utility

**Conclusion**: All titles normalized to spaces at load/write time.

### "All" Total Rule

**Code Search**:
```bash
grep -n "all" src/app/views_utils/views_fetcher.py
```

**Findings**:
- Line 62: `new_data[title] = views.get(str(year)) or views.get("all", 0)`
- Line 90: `new_data[title] = views` (includes "all" key)

**Conclusion**: API returns `"all"` value including 2015. Database `SUM(views)` excludes 2015.

---

## Conclusion

The corrected design addresses all issues raised:
- Single `views` table with `agent_type` column
- Proper upsert strategy without FK cascade issues
- Composite primary keys, denormalized `lang`
- Clear title normalization rule
- Explicit handling of uncovered outputs
- Removed unnecessary tables and columns

Phase B implementation is in progress. The database infrastructure is complete; collector conversion remains.
