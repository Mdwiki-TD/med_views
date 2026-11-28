# SQLite Migration: Implementation Status Report

## Executive Summary

Phase A (Research and Design) is **complete** with all corrections applied. Phase B (Implementation) is **partially complete**: database infrastructure is in place, but collector conversion is pending.

**Design Document**: `docs/plans/full-data-storage-design.md`

---

## Phase A: Research and Design ✅ COMPLETE

### Completed Tasks

1. **Inventory**: All data readers/writers identified and documented
2. **Data Flow**: Complete pipeline mapped with verification in code
3. **Schema Design**: Corrected per feedback (single `views` table, composite PKs, denormalized `lang`)
4. **Code Verification**: 
   - Agent type sources verified (`users_agents` comes from external source)
   - Title normalization rule confirmed (underscores → spaces)
   - "All" total rule clarified (excludes 2015)
5. **Design Corrections Applied**:
   - Single `views` table with `agent_type` column
   - No `INSERT OR REPLACE` on FK rows; use SQLite-specific upsert
   - Composite primary keys, `WITHOUT ROWID`
   - Removed `pipeline_metadata`, timestamps, `title_count`
   - `ReportGenerator` marked as read-only (out of scope)
   - Clear title normalization rule
   - Explicit handling of uncovered outputs

### Files Created

- `docs/plans/full-data-storage-design.md` (comprehensive design document)

---

## Phase B: Implementation 🔄 IN PROGRESS

### Completed Infrastructure

#### 1. Configuration ✅
- **File**: `src/app/config.py`
- **Change**: Added `database_path: Path` to `ViewsDataPaths`
- **Status**: Complete, tested

#### 2. Models ✅ (Need Revision)
- **Files**: 
  - `src/app/database/views_db/models/title.py`
  - `src/app/database/views_db/models/view.py`
  - `src/app/database/views_db/models/language_count.py`
  - `src/app/database/views_db/models/statistic.py`
- **Status**: Created but need revision to match corrected design
- **Issues**:
  - Currently uses surrogate IDs; should use composite PKs
  - `views` split into two tables; should be single table with `agent_type`
  - Has `updated_at` columns; should be removed

#### 3. DatabaseService ✅
- **File**: `src/app/database/views_db/services/database_service.py`
- **Status**: Complete with pragma setup
- **Features**: Singleton pattern, session management, table creation

#### 4. Services ✅ (Need Revision)
- **Files**:
  - `src/app/database/views_db/services/title_service.py`
  - `src/app/database/views_db/services/view_service.py`
  - `src/app/database/views_db/services/aggregation_service.py`
- **Status**: Created but need revision
- **Issues**:
  - Uses old two-table model for views
  - Needs SQLite-specific upsert implementation
  - Needs to remove `updated_at` handling

#### 5. Import Tool ✅ (Need Revision)
- **File**: `src/import_json_to_db.py`
- **Status**: Created but needs revision
- **Issues**:
  - Imports to two view tables; should import to single table with `agent_type`
  - Needs to handle external `users_agents` data source

#### 6. Tests ✅ (Need Revision)
- **File**: `tests/unit/database/views_db/services/test_services.py`
- **Status**: 23 tests passing
- **Issues**: Tests use old schema; need update after model revision

### Pending Implementation

#### 1. Model Revision ⏳
**Priority**: High (blocking)

**Tasks**:
- Update `Title` model: Remove surrogate ID, use composite PK `(lang, title)`, add `WITHOUT ROWID`
- Update `View` model: Merge into single table with `agent_type` column, composite PK `(title_id, year, agent_type)`, add denormalized `lang`, add `WITHOUT ROWID`
- Update `LanguageCount` model: Remove surrogate ID, remove `updated_at`, use composite PK `(lang, year, agent_type)`
- Update `Statistic` model: Remove surrogate ID, remove `updated_at`, use composite PK `(lang, year)`

**Files to Update**:
- `src/app/database/views_db/models/title.py`
- `src/app/database/views_db/models/view.py`
- `src/app/database/views_db/models/language_count.py`
- `src/app/database/views_db/models/statistic.py`

#### 2. Service Revision ⏳
**Priority**: High (blocking)

**Tasks**:
- Update `ViewService`: Merge `all_agents` and `users_agents` methods into single methods with `agent_type` parameter
- Implement SQLite-specific upsert using `sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_update(...)`
- Remove `updated_at` handling
- Update bulk insert to use executemany form

**Files to Update**:
- `src/app/database/views_db/services/view_service.py`
- `src/app/database/views_db/services/aggregation_service.py`

#### 3. Collector Conversion ⏳
**Priority**: High

**Tasks**:
- Convert `TitlesLoader` to write titles to database
- Convert `MultiYearViewsPipeline` to write views to database
- Convert `after1.py` to filter and write to database
- Convert `after2.py` to aggregate and write to database

**Files to Update**:
- `src/app/titles_loader.py`
- `src/app/all_years/run.py`
- `src/app/all_years/views.py`
- `src/after1.py`
- `src/after2.py`

#### 4. Import Tool Revision ⏳
**Priority**: Medium

**Tasks**:
- Update to import to single `views` table with `agent_type`
- Handle external `users_agents` data (if available)

**Files to Update**:
- `src/import_json_to_db.py`

#### 5. Test Updates ⏳
**Priority**: Medium

**Tasks**:
- Update tests to use new schema
- Add parity tests (JSON vs database)
- Add import verification tests

**Files to Update**:
- `tests/unit/database/views_db/services/test_services.py`

#### 6. Parity Checks ⏳
**Priority**: High (verification)

**Tasks**:
- Run legacy JSON pipeline
- Run new database pipeline
- Compare outputs (counts, sums, random samples)
- Document any differences

#### 7. Documentation ⏳
**Priority**: Low

**Tasks**:
- Update module docstrings
- Update CLAUDE.md with database usage
- Create migration guide

---

## Verification Results

### Unit Tests
- **Config Tests**: 27/27 passing ✅
- **Service Tests**: 23/23 passing ✅ (but use old schema)
- **Other Tests**: Not yet run

### Parity Checks
- **Status**: Not yet performed
- **Reason**: Collector conversion pending

### Import Verification
- **Status**: Not yet performed
- **Reason**: Import tool needs revision

---

## Readers of Old JSON Files Not Converted

### Out of Scope (Read-Only)

| Module | Files Read | Reason |
|--------|-----------|--------|
| `report_generator.py` | `dumps/views_by_year/<year>/<lang>.json` | Read-only module; generates wiki reports; will be updated separately |

### Utility Modules

| Module | Files Read | Decision |
|--------|-----------|----------|
| `dump_utils.py` | Various | Keep `json_load()` and `replace_underscores()`; remove write methods |

---

## Behavior Described but Not Implemented

**Finding**: None identified in code review.

All comments and docstrings accurately describe implemented behavior.

---

## Differences Between Old and New Outputs

**Status**: To be determined after parity checks.

**Expected Differences**: None (design preserves all behavior).

---

## Assumptions Made

1. **`users_agents` Data Source**: Assumed to come from external process (no code found that writes to `views_by_year_users_agents/`)
2. **Real Data Measurements**: Used estimates (no production data available)
3. **SQLite Performance**: Assumed sufficient for ~15M rows (no benchmarking done)
4. **Title Normalization**: Assumed all titles use spaces (verified in code)

---

## Open Questions

1. **`users_agents` Data**: Where does this data come from? Is it imported manually or generated by an external process?
2. **Incremental Updates**: Should we implement incremental title updates (only add new titles)?
3. **Backup Strategy**: How often should the database be backed up?
4. **Performance**: Should we benchmark query performance with real data?

---

## Next Steps

### Immediate (Blocking)

1. **Revise Models**: Update to match corrected schema (composite PKs, single `views` table)
2. **Revise Services**: Implement SQLite-specific upsert, remove `updated_at`
3. **Update Tests**: Ensure tests use new schema

### Short-Term

4. **Convert Collectors**: One at a time, with parity checks after each
5. **Run Full Parity Check**: Compare all outputs
6. **Update Import Tool**: Handle new schema

### Long-Term

7. **Documentation**: Update all docs
8. **Performance Testing**: Benchmark with real data
9. **Production Deployment**: Plan migration strategy

---

## Definition of Done (Revised)

- [ ] Models match corrected schema (composite PKs, single `views` table)
- [ ] Services use SQLite-specific upsert
- [ ] All collectors converted to use database
- [ ] Import tool updated and tested
- [ ] Parity checks pass (no differences found)
- [ ] All unit tests pass
- [ ] Comments and docstrings accurate
- [ ] No display or query-endpoint code added
- [ ] Existing JSON files not deleted
- [ ] Design document matches implementation

---

## Appendix: Files Created/Modified

### Created

- `docs/plans/full-data-storage-design.md`
- `src/app/database/views_db/models/title.py`
- `src/app/database/views_db/models/view.py`
- `src/app/database/views_db/models/language_count.py`
- `src/app/database/views_db/models/statistic.py`
- `src/app/database/views_db/models/metadata.py` (to be removed)
- `src/app/database/views_db/services/database_service.py`
- `src/app/database/views_db/services/title_service.py`
- `src/app/database/views_db/services/view_service.py`
- `src/app/database/views_db/services/aggregation_service.py`
- `src/import_json_to_db.py`
- `tests/unit/database/views_db/services/test_services.py`

### Modified

- `src/app/config.py` (added `database_path`)
- `tests/unit/test_config.py` (updated for `database_path`)

### To Be Modified

- All model files (schema revision)
- All service files (upsert revision)
- `src/app/titles_loader.py` (conversion)
- `src/app/all_years/run.py` (conversion)
- `src/app/all_years/views.py` (conversion)
- `src/after1.py` (conversion)
- `src/after2.py` (conversion)
- `src/import_json_to_db.py` (revision)
- `tests/unit/database/views_db/services/test_services.py` (update)

---

## Conclusion

Phase A is complete with all corrections applied. Phase B is partially complete: infrastructure is in place but needs revision to match the corrected design, and collector conversion is pending.

**Estimated Remaining Work**: 2-3 days for full implementation and verification.

**Recommendation**: Complete model and service revision first, then convert collectors one at a time with parity checks after each.
