# Capital Bikeshare Data Pipeline

An ELT pipeline that loads public Capital Bikeshare (Washington, DC) trip data into BigQuery and models it with dbt into a star schema for analysis.

**Stack:** Python, BigQuery, dbt, SQL, GitHub Actions *(CI/CD coming soon)*

## Architecture

```
Capital Bikeshare monthly trip files (CSV in ZIP)
        │
        ▼  Python (ingestion/load_trips.py)
BigQuery  raw.trips            ← untouched copy of the source, all strings
        │
        ▼  dbt staging
BigQuery  stg_trips            ← typed, trimmed, deduplicated (view)
        │
        ▼  dbt marts
BigQuery  fct_trips            ← partitioned by day, clustered by start station
          dim_stations
          dim_date
```

## Data

Trip data comes from [Capital Bikeshare's system data page](https://capitalbikeshare.com/system-data) and is subject to their Data License Agreement. Raw files are not stored in this repo.

This project loads **October 2025 through September 2026** (roughly 8 million trips).

## Project structure

```
ingestion/   Python scripts that download and load raw data into BigQuery
dbt/         dbt project (models, tests, profiles)
```

## Setup

1. Clone the repo and create a virtual environment:
```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
```
2. Create a GCP project, enable BigQuery, and create a service account with the **BigQuery Data Editor** and **BigQuery Job User** roles. Download its JSON key and keep it outside version control.
3. Create BigQuery datasets `raw` and `dbt_dev` in the `US` location.
4. Copy `.env.example` to `.env` and fill in your project ID and the absolute path to your key file.

## Running the pipeline

Load raw data (re-runnable; reloading a month replaces its rows instead of duplicating them):
```
python ingestion/load_trips.py --start 202510 --end 202609
```

Build and test the dbt models:
```
set -a; source .env; set +a
cd dbt
dbt build --profiles-dir .
```

## Design decisions

- **Raw layer is all strings.** Typing and cleaning happen in dbt, so a bad value can never fail a load, and raw stays a faithful copy of the source.
- **Idempotent loads.** Each month loads into a temp table, then that file's rows are deleted and re-inserted in the target, tagged with `_source_file` and `_loaded_at`.
- **Deduplication in staging.** *(Fill in what you found: how many duplicate ride IDs, and which row you keep.)*
- **Bad timestamps are excluded from the fact table.** Trips that end before they start are filtered out of `fct_trips` and flagged by a warning-level dbt test.
- **Null station IDs are kept.** Many e-bike trips have no station, so they stay in the fact table with null keys instead of being dropped.
- **Cost controls.** Queries are capped with `maximum_bytes_billed`, and `fct_trips` is partitioned and clustered to limit bytes scanned.

## Testing

dbt tests cover uniqueness and not-null checks on trip IDs, accepted values for rider and bike types, referential integrity between the fact and dimension tables, and a custom check for trips that end before they start.

## Roadmap

- [ ] GitHub Actions CI: lint and `dbt build` on every pull request
- [ ] Scheduled monthly ingestion and production run
- [ ] dbt docs and lineage graph
- [ ] Analytics mart and dashboard