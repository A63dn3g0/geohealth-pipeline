# Migration from the old GeoHealth repository

This branch replaces an overbuilt synthetic/PostGIS stack with a minimal Python/Streamlit data product. The original code remains in Git history and on `main` until this branch is approved and merged.

## Retired
Old `geohealth_pipeline_Project.py`, demo LGA/sample datasets, placeholder ETL, API, Postgres config, PostGIS SQL, redundant Python package manifests, Docker/nginx production scaffolding, Sphinx deployment pages, binary output artifacts and obsolete demo tests.

## New minimal execution
1. Install Python 3.11+ and `pip install -r requirements-dev.txt`.
2. `pytest -q` (unit tests use tiny artificial fixtures; no mock data appears in dashboard).
3. `streamlit run app.py`: a working empty-data onboarding view (no DB needed).
4. Obtain genuine HealthStats monthly LHD CSV using the source link.
5. `python -m etl.build --inspect data/raw/FILE.csv`.
6. Set true column names/strata in `config/sources.json`.
7. `python -m etl.build`; reload dashboard.
8. Optionally `python -m etl.download --boundaries`.

## Status
Refactored code and tests are committed to the feature branch. End-to-end validation using a real monthly government CSV and a Streamlit browser smoke test is a distinct outstanding milestone. Do not claim a working public-health forecast until data has been validated.
