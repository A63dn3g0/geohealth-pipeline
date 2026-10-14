# GeoHealth NSW — real-data dashboard MVP

A deliberately simple, file-backed public-health service-utilisation and forecasting dashboard for NSW. This refactor removes **synthetic analytical data, Postgres, PostGIS, API orchestration and Docker dependencies**.

## Run locally (Python 3.11+)

1. Create and activate a virtual environment.
2. `python -m pip install -r requirements.txt`
3. `streamlit run app.py`

The app launches without sample numbers and gives clear onboarding instructions until **real government observations** are ingested.

## Import monthly mental-health presentations

1. Visit [HealthStats NSW](https://www.healthstats.nsw.gov.au/indicator?name=-men-sui-mth-ed&location=LHD) and select the **number of monthly mental-health ED presentations**, persons / all ages / total category, relevant Local Health Districts. Download data as CSV.
2. Save the original unedited export to `data/raw/healthstats_mental_health_monthly.csv`.
3. Inspect headers: `python -m etl.build --inspect data/raw/healthstats_mental_health_monthly.csv`.
4. Copy the source entry from `config/sources.example.json` into `config/sources.json`, enable it and map the **exact** source column names. Apply explicit filters for sex/age/measure strata.
5. Run `python -m etl.build` to produce `data/processed/observations.csv` and `provenance.json`.
6. Run or refresh `streamlit run app.py`.
7. Download authoritative LHD polygons: `python -m etl.download --boundaries`.

**Do not fabricate columns or convert a rate to a count.** If the source uses a different date convention, inspect the export and implement a source-specific adapter rather than guessing.

## Forecasts

Only complete, **observed monthly counts** with at least 36 successive months qualify. Compare seasonal naïve against interpretable seasonal trend using rolling-origin error. 3/6/12-month projections show **approximate historical error bands**, not calibrated confidence/prediction intervals. Annual PHN AOD treatment datasets remain descriptive until sufficient time history exists.

## Validation and governance

Original government source files remain unchanged and are excluded from Git. The builder rejects negative/duplicate/invalid data and excludes suppressed cells instead of zero-filling them. It records source links and SHA-256 checksums. No data are allocated across jurisdictions without approved geographic correspondence. Check commercial data-redistribution licences before licensing the finished product.

Tests: `python -m pip install -r requirements-dev.txt && pytest -q`.

See `docs/PRODUCT_REQUIREMENTS.md`, `docs/SOURCE_ACQUISITION.md` and `docs/MIGRATION.md`.
