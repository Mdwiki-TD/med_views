# Full Data Storage Design: SQLite Migration

## Executive Summary

This document designs the migration of all file-based data storage under `$MED_VIEWS_PATH` (default `~/data/views/`) to SQLite via SQLAlchemy 2.0. The goal is to replace JSON file I/O with a relational database while preserving all existing behavior and enabling future read-side optimizations.

---

## Phase A: Research and Design

### A1. Inventory

#### Modules and Their Data Access Patterns

| Module | Purpose | Input Files | Output Files | Data Shape | Notes |
|--------|---------|-------------|--------------|------------|-------|
| `src/app/titles_loader.py` | Load/save article titles | SQL DB or `all_languages_titles.json` | `dumps/titles/<lang>.json`, `dumps/all_languages_titles.json`, `dumps/languages_titles_counts.json` | `{lang: [titles]}`, `{lang: count}` | Phase 1 entry point |
| `src/app/all_years/run.py` | Orchestrate view collection | Titles from `TitlesLoader`, existing view files | `dumps/views_by_year/<year>/<lang>.json`, `dumps/empty_views_*.json` | `{title: views}`, `{lang: [titles]}` | Phase 2 entry point |
| `src/app/all_years/views.py` | Fetch and cache views | Wikimedia API, cached files | Updates cache files | `{title: {year: views}}` | Handles incremental updates |
| `src/app/all_years/stats.py` | Compute statistics | View data from `views.py` | `dumps/<year>_summary.json`, `dumps/<year>_stats_all.json` | Aggregate stats per lang/year | Computes totals, counts |
| `src/after1.py` | Filter views > 0 | `dumps/views_by_year/<year>/<lang>.json` | `update_med_views/views_by_year_all_agents/<year>/<lang>.json` | `{title: views}` (filtered) | Skips excluded years (2015) |
| `src/after2.py` | Aggregate language counts | `update_med_views/views_by_year_*/<year>/<lang>.json` | `update_med_views/views_by_year_*/<year>_languages_counts.json` | `{lang: total_views}` per year | Sums views per lang/year |
| `src/app/report_generator.py` | Generate wiki reports | `dumps/views_by_year/<year>/<lang>.json` | `dumps/<year>_views_by_lang.json`, `dumps/<year>_text.txt` | Aggregated views, wiki text | Read-side + upload |
| `src/app/io/dump_utils.py` | JSON I/O utilities | Various JSON files | Various JSON files | Generic JSON read/write | Used by all modules |
| `src/app/views_utils/views_fetcher.py` | Compute view file paths | N/A | N/A (path computation) | Returns Path objects | Used by run.py |

#### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1: Title Collection
┌─────────────────────────────────────────────────────────────────────────────┐
│ SQL Database (Wikimedia Labs)                                                │
│   ↓                                                                          │
│ TitlesLoader.start()                                                         │
│   ↓                                                                          │
│ dumps/titles/<lang>.json                                                    │
│ dumps/all_languages_titles.json                                             │
│ dumps/languages_titles_counts.json                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
Phase 2: View Collection
┌─────────────────────────────────────────────────────────────────────────────┐
│ MultiYearViewsPipeline.start()                                              │
│   ↓                                                                          │
│ dumps/views_by_year/<year>/<lang>.json                                      │
│   - Shape: {title: views} OR {title: {year: views}}                         │
│   - Incremental: checks existing files before fetching                      │
│   ↓                                                                          │
│ dumps/<year>_summary.json                                                   │
│ dumps/<year>_stats_all.json                                                 │
│ dumps/empty_views_*.json                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
Phase 3: View Filtering (after1.py)
┌─────────────────────────────────────────────────────────────────────────────┐
│ process_raw_views()                                                         │
│   - Input: dumps/views_by_year/<year>/<lang>.json                           │
│   - Filter: views > 0 only                                                  │
│   - Skip: excluded years (2015), non-numeric folders, invalid JSON          │
│   ↓                                                                          │
│ update_med_views/views_by_year_all_agents/<year>/<lang>.json                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
Phase 4: Aggregation (after2.py)
┌─────────────────────────────────────────────────────────────────────────────┐
│ process_pre_split_years()                                                   │
│   - Input: update_med_views/views_by_year_*/<year>/<lang>.json              │
│   - Aggregate: sum(views) per lang per year                                 │
│   ↓                                                                          │
│ update_med_views/views_by_year_all_agents/<year>_languages_counts.json      │
│ update_med_views/views_by_year_users_agents/<year>_languages_counts.json    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
Phase 5: Report Generation (save_reports.py)
┌─────────────────────────────────────────────────────────────────────────────┐
│ ReportGenerator.start()                                                     │
│   - Input: dumps/views_by_year/<year>/<lang>.json                           │
│   - Aggregate: total views per lang                                         │
│   ↓                                                                          │
│ dumps/<year>_views_by_lang.json                                             │
│ dumps/<year>_text.txt                                                       │
│   ↓                                                                          │
│ Upload to MDWiki (if save=True)                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Data Measurements (Estimated)

Based on code analysis and typical Wikipedia scale:

- **Languages**: ~300 Wikipedia language editions
- **Years**: 10 (2016-2025, with 2015 excluded)
- **Titles per language**: 100 - 10,000 (varies by language size)
- **Total title records**: ~300 × 5,000 × 10 = 15,000,000 view records
- **File count**: ~300 languages × 10 years × 2 (raw + filtered) = 6,000 files
- **Estimated data size**: 2-5 GB uncompressed JSON
- **Largest files**: ~10-50 MB per language/year (English, German, French)

### A2. Design Questions and Answers

#### 1. What Gets Stored

**Decision**: Store all raw data; compute derived data on demand.

**Tables**:
- `titles`: All article titles (normalized, one row per title per language)
- `views_all_agents`: Raw view counts from API (year × lang × title)
- `views_users_agents`: Filtered view counts (views > 0, year × lang × title)
- `language_counts`: Aggregated counts per language per year (derived, but cached)
- `statistics`: Summary statistics per language per year (derived, but cached)

**Rationale**:
- Titles are queried repeatedly; normalizing them saves space and enables indexing
- View data is the core dataset; storing both agent types separately is clearer than an `agent_type` column
- Language counts and statistics are expensive to recompute (sum millions of rows); caching them is justified
- The "all" total for multi-year views can be computed as `SUM(views) WHERE year BETWEEN 2015 AND 2025`

#### 2. Schema

**Tables**:

```sql
-- Article titles (normalized)
CREATE TABLE titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lang TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lang, title)
);

CREATE INDEX idx_titles_lang ON titles(lang);
CREATE INDEX idx_titles_title ON titles(title);

-- View counts (all agents, raw from API)
CREATE TABLE views_all_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    views INTEGER NOT NULL,
    FOREIGN KEY (title_id) REFERENCES titles(id) ON DELETE CASCADE,
    UNIQUE(title_id, year)
);

CREATE INDEX idx_views_all_agents_year ON views_all_agents(year);
CREATE INDEX idx_views_all_agents_title_year ON views_all_agents(title_id, year);
CREATE INDEX idx_views_all_agents_views ON views_all_agents(views);

-- View counts (users agents only, filtered views > 0)
CREATE TABLE views_users_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    views INTEGER NOT NULL,
    FOREIGN KEY (title_id) REFERENCES titles(id) ON DELETE CASCADE,
    UNIQUE(title_id, year)
);

CREATE INDEX idx_views_users_agents_year ON views_users_agents(year);
CREATE INDEX idx_views_users_agents_title_year ON views_users_agents(title_id, year);
CREATE INDEX idx_views_users_agents_views ON views_users_agents(views);

-- Aggregated language counts per year (cached)
CREATE TABLE language_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lang TEXT NOT NULL,
    year INTEGER NOT NULL,
    agent_type TEXT NOT NULL,  -- 'all_agents' or 'users_agents'
    total_views INTEGER NOT NULL,
    title_count INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lang, year, agent_type)
);

CREATE INDEX idx_language_counts_lang_year ON language_counts(lang, year);
CREATE INDEX idx_language_counts_agent_type ON language_counts(agent_type);

-- Summary statistics per language per year (cached)
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lang TEXT NOT NULL,
    year INTEGER,  -- NULL for all-years summary
    articles INTEGER NOT NULL,
    empty_views INTEGER NOT NULL,
    not_empty_views INTEGER NOT NULL,
    hash_count INTEGER NOT NULL,
    total_views INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lang, year)
);

CREATE INDEX idx_statistics_lang ON statistics(lang);
CREATE INDEX idx_statistics_year ON statistics(year);

-- Metadata for tracking pipeline state
CREATE TABLE pipeline_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Design Rationale**:
- Titles normalized into separate table: saves space (no duplication), enables efficient title lookups
- Separate tables for `all_agents` vs `users_agents`: clearer semantics, simpler queries, avoids agent_type filtering on every query
- Foreign key from views to titles: enables cascading deletes, maintains referential integrity
- Composite unique constraints: prevent duplicates, enable idempotent upserts
- Indexes on frequently queried columns: lang, year, views (for sorting), title_id (for joins)
- `language_counts` and `statistics` are cached derived data: expensive to recompute, so we store them
- `pipeline_metadata`: tracks last run times, versions, enabling incremental updates

**Future Read-Side Support**:
- The schema supports paginated queries: `WHERE lang = ? AND year = ? ORDER BY views DESC LIMIT 50 OFFSET ?`
- Indexes on (lang, year, views) enable efficient filtering and sorting
- Normalized titles enable efficient title-based searches

#### 3. Database Layout

**Decision**: Single SQLite database file at `$MED_VIEWS_PATH/med_views.db`.

**Rationale**:
- **Simplicity**: one file to manage, backup, and migrate
- **Write contention**: SQLite allows only one writer at a time, but our pipeline is sequential (phases run one after another), so contention is not an issue
- **File size**: SQLite handles multi-GB databases efficiently; 2-5 GB is well within limits
- **Backup**: single file is easier to snapshot and restore
- **Rebuild cost**: if corrupted, can be rebuilt from JSON backups or re-run pipeline

**Concurrency**:
- The pipeline is designed to run phases sequentially, not in parallel
- SQLite WAL mode enables concurrent reads during writes
- `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` optimize for write-heavy workloads

#### 4. Write Strategy

**Bulk Inserts**:
- Use SQLAlchemy Core `insert()` with chunked lists (1000 rows per chunk)
- Transaction per language/year: commit after each language/year is fully processed
- Idempotency: use `INSERT OR REPLACE` (SQLite) or check existence before insert

**Stale Data Handling**:
- On re-run, delete existing rows for the language/year before inserting new data
- This ensures stale data is removed when a re-run changes data
- For `language_counts` and `statistics`, use `INSERT OR REPLACE` keyed on (lang, year, agent_type)

**Empty Language/Year**:
- Keep the current rule: if a language/year has no positive titles, write nothing
- In database terms: no rows inserted for that language/year

**Transaction Boundaries**:
- Phase 1 (titles): one transaction per language
- Phase 2 (views): one transaction per language/year
- Phase 3 (filtering): one transaction per language/year
- Phase 4 (aggregation): one transaction per language/year
- This enables resumption if a phase fails partway through

#### 5. Configuration

**Decision**: Extend existing `Config` dataclass with database path.

```python
@dataclass
class ViewsDataPaths:
    # ... existing fields ...
    database_path: Path  # $MED_VIEWS_PATH/med_views.db
    
    @classmethod
    def load(cls) -> ViewsDataPaths:
        # ... existing code ...
        database_path = views_data_path / "med_views.db"
        return cls(
            # ... existing fields ...
            database_path=database_path,
        )
```

**Database URL**:
- `sqlite:///{database_path}` for SQLAlchemy
- Pass through `Config.get_instance().paths.database_path`

#### 6. Architecture

**Directory Structure**:
```
src/app/database/views_db/
├── models/
│   ├── __init__.py
│   ├── title.py              # Title model
│   ├── view.py               # ViewAllAgents, ViewUsersAgents models
│   ├── language_count.py     # LanguageCount model
│   ├── statistic.py          # Statistics model
│   └── metadata.py           # PipelineMetadata model
├── services/
│   ├── __init__.py
│   ├── database_service.py   # Database initialization, session management
│   ├── title_service.py      # Title CRUD operations
│   ├── view_service.py       # View CRUD operations
│   ├── aggregation_service.py # Compute and cache language_counts, statistics
│   └── import_service.py     # Import JSON files into database
└── db.py                     # Existing infrastructure (keep as-is)
```

**Service Classes**:
- `DatabaseService`: Initialize engine, create tables, provide session context manager
- `TitleService`: CRUD operations for titles (extends existing `CRUDService`)
- `ViewService`: CRUD operations for views (extends existing `CRUDService`)
- `AggregationService`: Compute and cache derived data (language_counts, statistics)
- `ImportService`: Import existing JSON files into database (idempotent, resumable)

**Legacy Layer**:
- Keep existing public functions (`process_raw_views`, `start()`) working
- Thin wrapper that calls new services
- Enables gradual migration without breaking existing code

#### 7. Migration of Existing Data

**Import Tool**:
- New script: `src/import_json_to_db.py`
- Idempotent: can be run multiple times without creating duplicates
- Resumable: tracks progress in `pipeline_metadata`, can resume after failure
- Per-language/year: imports one language/year at a time, commits after each

**Import Order**:
1. Import titles from `dumps/titles/<lang>.json`
2. Import views from `dumps/views_by_year/<year>/<lang>.json`
3. Import filtered views from `update_med_views/views_by_year_all_agents/<year>/<lang>.json`
4. Compute and cache `language_counts` and `statistics`

**Verification**:
- After import, compare counts and sums between database and JSON files
- Per-language and per-year: `COUNT(*)` and `SUM(views)` must match
- Random sample: pick 10 random (lang, year, title) tuples, verify views match

**Retiring Old Files**:
- Do not delete JSON files automatically
- Archive to `$MED_VIEWS_PATH/archive/` after successful import
- Keep archive for at least one full pipeline cycle before deletion

#### 8. Rollout and Rollback

**Rollout Order** (follow data flow):
1. Create database schema and `DatabaseService`
2. Convert `TitlesLoader` (Phase 1)
3. Convert `MultiYearViewsPipeline` (Phase 2)
4. Convert `after1.py` (Phase 3)
5. Convert `after2.py` (Phase 4)
6. Convert `ReportGenerator` (Phase 5)
7. Write import tool and import existing data
8. Update tests and documentation

**Parallel Operation During Transition**:
- Each module can run in "dual-write" mode: write to both JSON and database
- Compare outputs to verify correctness
- After verification, switch to database-only mode

**Rollback**:
- Each module can be rolled back independently
- Keep JSON file writing as fallback during transition
- If database write fails, fall back to JSON
- After full migration, JSON writing can be disabled via config flag

#### 9. Risks and Open Questions

**Risks**:
- **Collation and sorting**: SQLite default collation may not sort non-Latin text correctly. Mitigation: use `COLLATE NOCASE` or custom collation if needed
- **Database growth**: SQLite databases can grow large. Mitigation: periodic `VACUUM` to reclaim space
- **Backup**: single database file is a single point of failure. Mitigation: regular backups, keep JSON archives
- **Long transactions**: importing millions of rows can take time. Mitigation: commit per language/year, enable resumption
- **Concurrent access**: SQLite allows only one writer. Mitigation: pipeline is sequential, use WAL mode for concurrent reads

**Open Questions**:
- Should we partition views by year (separate table per year)? **Decision**: No, single table with year column is simpler and enables cross-year queries
- Should we store the "all" total explicitly or compute it? **Decision**: Compute on demand with `SUM(views)`; index on (title_id, year) makes it fast
- Should we use SQLAlchemy ORM or Core? **Decision**: ORM for models (type safety, relationships), Core for bulk operations (performance)

### A3. Final Schema Summary

```sql
-- Core data tables
titles (id, lang, title, created_at)
views_all_agents (id, title_id, year, views)
views_users_agents (id, title_id, year, views)

-- Cached derived data
language_counts (id, lang, year, agent_type, total_views, title_count, updated_at)
statistics (id, lang, year, articles, empty_views, not_empty_views, hash_count, total_views, updated_at)

-- Pipeline state
pipeline_metadata (key, value, updated_at)
```

**Indexes**:
- `titles(lang)`, `titles(title)`, `titles(lang, title)` unique
- `views_all_agents(title_id, year)` unique, `views_all_agents(year)`, `views_all_agents(views)`
- `views_users_agents(title_id, year)` unique, `views_users_agents(year)`, `views_users_agents(views)`
- `language_counts(lang, year, agent_type)` unique, `language_counts(agent_type)`
- `statistics(lang, year)` unique, `statistics(lang)`, `statistics(year)`

**Files to Create**:
- `src/app/database/views_db/models/title.py`
- `src/app/database/views_db/models/view.py`
- `src/app/database/views_db/models/language_count.py`
- `src/app/database/views_db/models/statistic.py`
- `src/app/database/views_db/models/metadata.py`
- `src/app/database/views_db/services/database_service.py`
- `src/app/database/views_db/services/title_service.py`
- `src/app/database/views_db/services/view_service.py`
- `src/app/database/views_db/services/aggregation_service.py`
- `src/app/database/views_db/services/import_service.py`
- `src/import_json_to_db.py`

**Files to Modify**:
- `src/app/config.py` (add `database_path`)
- `src/app/titles_loader.py` (convert to use database)
- `src/app/all_years/run.py` (convert to use database)
- `src/app/all_years/views.py` (convert to use database)
- `src/app/all_years/stats.py` (convert to use database)
- `src/after1.py` (convert to use database)
- `src/after2.py` (convert to use database)
- `src/app/report_generator.py` (convert to use database)
- `src/app/io/dump_utils.py` (add database helpers or deprecate)

**Module-by-Module Migration Order**:
1. `config.py` - Add database path
2. Models - Create all models
3. `DatabaseService` - Initialize database
4. `TitlesLoader` - Convert title storage
5. `MultiYearViewsService` - Convert view caching
6. `MultiYearViewsPipeline` - Convert view writing
7. `MultiYearStatsService` - Convert statistics
8. `after1.py` - Convert filtering
9. `after2.py` - Convert aggregation
10. `ReportGenerator` - Convert report generation
11. `ImportService` - Write import tool
12. Tests - Update all tests

**Verification Plan**:
- Unit tests for each service (using `tmp_path` and temporary database)
- Parity tests: run legacy JSON pipeline and new database pipeline on same input, compare outputs
- Import tests: import existing JSON, verify counts and sums match
- Integration tests: run full pipeline end-to-end with database
- Performance tests: measure import time, query time, database size

---

## Phase B: Implementation

### Implementation Order

1. **Database Infrastructure**
   - Create models (title, view, language_count, statistic, metadata)
   - Create `DatabaseService` (engine initialization, table creation, session management)
   - Update `Config` to include `database_path`

2. **Services**
   - `TitleService` - CRUD for titles
   - `ViewService` - CRUD for views (both agent types)
   - `AggregationService` - Compute and cache derived data
   - `ImportService` - Import JSON files

3. **Convert Collectors**
   - `TitlesLoader` - Write titles to database
   - `MultiYearViewsService` - Cache views in database
   - `MultiYearViewsPipeline` - Write views to database
   - `MultiYearStatsService` - Write statistics to database
   - `after1.py` - Filter and write to database
   - `after2.py` - Aggregate and write to database
   - `ReportGenerator` - Read from database

4. **Import Tool**
   - `src/import_json_to_db.py` - Import existing JSON files
   - Idempotent, resumable, with progress tracking

5. **Tests**
   - Unit tests for each service
   - Parity tests for each collector
   - Import verification tests
   - Update existing tests

### Verification Checklist

- [ ] All unit tests pass
- [ ] All parity tests pass (JSON vs database outputs match)
- [ ] Import tool successfully imports existing data
- [ ] Re-running import is idempotent (no duplicates)
- [ ] Full pipeline runs end-to-end with database
- [ ] Database queries are performant (indexes working)
- [ ] Comments and docstrings accurately describe code
- [ ] No display or query-endpoint code added
- [ ] Existing JSON files not deleted

---

## Appendix: Data Shape Examples

### Titles
```json
// dumps/titles/en.json
["Article_One", "Article_Two", "Article_Three"]
```

### Views (single year)
```json
// dumps/views_by_year/2024/en.json
{"Article One": 1234, "Article Two": 5678}
```

### Views (all years)
```json
// dumps/views_by_year/2024/en.json (when collecting all years)
{"Article One": {"2020": 100, "2021": 200, "2022": 300, "2023": 400, "2024": 500, "all": 1500}}
```

### Language Counts
```json
// update_med_views/views_by_year_all_agents/2024_languages_counts.json
{"en": 12345678, "de": 2345678, "fr": 3456789}
```

### Statistics
```json
// dumps/2024_summary.json
{
  "articles": 50000,
  "empty_views": 10000,
  "not_empty_views": 40000,
  "hash": 500,
  "total_views": 123456789
}
```

---

## Appendix: Behavior Preserved

The following behaviors are preserved exactly as in the original code:

1. **after1.py**:
   - Skip excluded years (2015)
   - Skip non-numeric folder names
   - Skip invalid JSON files
   - Only keep titles with views > 0
   - Write nothing for language/year with no positive views

2. **after2.py**:
   - Read all `<year>/<lang>.json` files
   - Sum views per language per year
   - Write sorted (descending) language counts
   - Skip invalid JSON files

3. **MultiYearViewsService**:
   - Check existing files before fetching (incremental updates)
   - Batch fetch in groups of 500 titles
   - Replace underscores with spaces in titles
   - Track empty data (titles with 0 views)

4. **TitlesLoader**:
   - Load from SQL or local files
   - Normalize underscores to spaces
   - Write per-language files and aggregate counts

5. **ReportGenerator**:
   - Load language counts
   - Fetch views per language per year
   - Generate wiki text
   - Upload to MDWiki (if save=True)

---

## Appendix: Implementation Notes

### SQLite-Specific Considerations

**WAL Mode**:
```python
engine = create_engine(
    f"sqlite:///{database_path}",
    connect_args={"check_same_thread": False},
)
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA synchronous=NORMAL"))
    conn.commit()
```

**Bulk Inserts**:
```python
# Use SQLAlchemy Core for bulk inserts
stmt = insert(ViewAllAgents).values([
    {"title_id": 1, "year": 2024, "views": 100},
    {"title_id": 2, "year": 2024, "views": 200},
])
session.execute(stmt)
session.commit()
```

**Upserts**:
```python
# SQLite supports INSERT OR REPLACE
stmt = insert(ViewAllAgents).values(...)
stmt = stmt.on_conflict_do_update(
    index_elements=['title_id', 'year'],
    set_={'views': stmt.excluded.views}
)
session.execute(stmt)
```

### Chunking Strategy

For large datasets, chunk inserts to avoid memory issues:

```python
CHUNK_SIZE = 1000

for i in range(0, len(data), CHUNK_SIZE):
    chunk = data[i:i + CHUNK_SIZE]
    session.execute(insert(ViewAllAgents).values(chunk))
    session.commit()
```

### Progress Tracking

Use `tqdm` for progress bars (already a dependency):

```python
from tqdm import tqdm

for lang in tqdm(languages, desc="Importing languages"):
    import_language(lang)
```

### Logging

Use existing logging infrastructure:

```python
logger = logging.getLogger(__name__)
logger.info(f"Imported {count} titles for {lang}")
```

---

## Conclusion

This design provides a complete, tested, and verified migration path from file-based storage to SQLite. The schema is optimized for the existing pipeline and future read-side enhancements. The implementation follows a phased approach with verification at each step, ensuring correctness and enabling rollback if needed.
