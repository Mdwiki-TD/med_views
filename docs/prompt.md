# Plan: Move all collected data under `dumps` to SQLite (SQLAlchemy)

## Execution protocol (read first)

You are an implementation agent. Work in two phases and **do not wait for approval between them**:

1. **Phase A, research and design.** Investigate the whole data pipeline, design the complete storage solution, and save the design as `docs/plans/full-data-storage-design.md` (create folders if missing). Save it before writing any implementation code.
2. **Phase B, implementation.** Implement the design you saved, verify it, and report.

Stop and ask only when a blocker cannot be resolved from the code or data (for example, two equally valid options that change a public contract).

## Goal

The project collects data into files under `$MED_VIEWS_PATH` (default `~data/views/`): everything in `dumps/` and the derived outputs in `update_med_views/`. Replace this file-based storage with SQLite accessed through SQLAlchemy 2.0, for the **whole** data set, not for a single module.

Known examples (the list is not complete; finding the rest is part of the task):

```
$MED_VIEWS_PATH
├── dumps
│   ├── titles/<lang>.json
│   ├── views_by_year/<year>/<lang>.json        # {title: views}
│   └── views_new/all/<lang>.json               # {title: {"<year>": views, "all": total}}
└── update_med_views
    ├── languages_titles_counts.json
    ├── views_by_year_all_agents/<year>/<lang>.json
    ├── views_by_year_all_agents/<year>_languages_counts.json
    └── views_by_year_users_agents/ (same shape)
```

Reference module (one collector among many): `views_by_year_all_agents.py` reads `<year>/<lang>.json`, keeps titles with `views > 0`, skips excluded years (`2015`) and non-numeric folders, skips invalid JSON, and writes nothing for a language/year with no positive title.

## Scope

- In scope: every piece of code that **collects, transforms, or writes** data into `dumps/` or `update_med_views/`. These collectors keep their current responsibility, and only their storage changes.
- Out of scope: any display or read-facing layer (web views, DataTables, pagination, API endpoints). The collectors know nothing about display and must not gain such code. A later task will build the read side on top of the database, so the schema should make that easy (see Design questions), but do not build it now.
- Do not add behavior that the current code does not have. If current comments describe behavior that the code does not implement, do not implement it silently. List it in the report instead.

## Phase A: research and design

### A1. Inventory

- Search the whole repository for every reader and writer of the paths above (`dump_dir_path`, `update_med_views`, `MED_VIEWS_PATH`, `*.json` reads and writes, `glob`, `open(`). Include scripts, CLI entry points, scheduled jobs, and tests.
- For each module record: its purpose, input files, output files, data shape, whether it reads outputs of another module, and how it is run.
- Draw the data flow between modules (which output feeds which input).
- Measure the data: number of languages, years, titles, files, total size on disk, and the largest files. If real data is not available, estimate from the code and say so.

### A2. Design questions to answer in the saved design

For each, state the decision and the reason:

1. **What gets stored.** Which datasets become tables (titles, yearly views, derived per-language totals, agent-type variants). Which derived data should be computed by queries instead of stored, and which must remain stored because it is expensive to recompute.
2. **Schema.** Tables, columns, types, primary and foreign keys, uniqueness, and indexes. Consider normalizing titles into their own table, how the "all agents" vs "users agents" variants are represented (an `agent_type` column, separate tables, or separate databases), and the per-year versus the `"all"` total. Keep the schema friendly to a future paginated read side (50 rows per page, filtered by language/year, sorted by views), so index the columns such a query needs, but add no read code.
3. **Database layout.** One database file or several (for example raw dumps vs derived data). Weigh file size, write contention, backup, and rebuild cost. SQLite allows a single writer, so describe how concurrent collectors will not collide.
4. **Write strategy.** Bulk inserts with SQLAlchemy Core in chunks, transaction boundaries (per language/year), idempotency on re-run, and how stale rows are handled when a re-run changes data. Keep the current rule that a language/year with no positive title writes nothing.
5. **Configuration.** How database paths are exposed through `Config`, following the existing conventions.
6. **Architecture.** Layout of `models/` (tables only) and `services/` (logic, no Flask). One class per responsibility, explicit dependencies, and a thin legacy layer so existing public functions such as `process_raw_views` and `start()` keep working during the transition.
7. **Migration of existing data.** How the current JSON files are imported into the database, how correctness is verified, and how the old files are retired (archived, never deleted automatically).
8. **Rollout and rollback.** Order of modules to convert (follow the data flow), what runs in parallel during the transition, and how to revert one module without affecting the others.
9. **Risks and open questions.** Collation and sorting of non-Latin text, database growth, `VACUUM`, backup, long transactions, anything else you find.

### A3. Output of Phase A

Save `docs/plans/full-data-storage-design.md` containing: the inventory table, the data-flow description, the data measurements, the answers to A2, the final schema (with a DDL-style summary), the list of files to create and change, the module-by-module migration order, and the verification plan. Then continue to Phase B.

## Constraints

- SQLAlchemy 2.0 style (`Mapped`, `mapped_column`), SQLite only.
- All code comments and docstrings in English, and they must describe exactly what the code does.
- Models contain tables only. Services contain logic and must not import Flask.
- Bulk writes use SQLAlchemy Core with chunked lists, not ORM object-by-object.
- Follow existing conventions (`Config`, logging, `tqdm` progress, pytest fixtures). Reuse existing DB code if the project already has some.
- Keep each collector's behavior (filtering rules, skipped inputs, excluded years) unchanged unless the design explicitly documents a difference.
- Do not delete existing data files. Do not edit unrelated modules.

## Phase B: implementation

1. Create models and services as designed, with shared database infrastructure first (`DatabaseService` or equivalent: engine, `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, table creation, session/connection context manager).
2. Convert collectors one at a time in the order set by the design. After each conversion run its tests and parity check before starting the next.
3. Write an import tool that loads the existing JSON files into the database (idempotent, resumable per language/year).
4. Update module docstrings and comments of every changed file so they match the new behavior.
5. Leave a working entry point for every converted collector (`start()` or its current equivalent).

## Verification

- Unit tests with `tmp_path` and a temporary SQLite database, per collector: filtering rules, excluded years, non-numeric folders, invalid JSON, empty language/year, and running twice produces identical rows.
- Parity check per collector on real or sample data: run the legacy file pipeline and the new database pipeline on the same source, and assert the sets of records are identical (compare counts, totals, and a random sample).
- Import tool check: after importing the existing JSON files, per-language and per-year counts and sums in the database equal those computed from the files.
- Run the existing test suite and the project's linters. Everything that passed before must still pass.

## Final report

Reply with:

- Path of the saved design file.
- Files created and changed, grouped by module.
- Parity and import verification results, including any difference found.
- Readers of the old files that were not converted, so the later read-side task can handle them.
- Behavior described in comments but not implemented in code (found during inventory).
- Assumptions made and open questions.

## Definition of done

- Every collector under `dumps/` and `update_med_views/` stores its data in SQLite through SQLAlchemy, with unchanged filtering behavior.
- The complete design is saved in `docs/plans/full-data-storage-design.md` and matches what was built.
- Existing JSON data can be imported, and re-running any import is idempotent.
- No display, query-endpoint, or export code was added.
- Tests pass, and comments and docstrings accurately describe the code.
