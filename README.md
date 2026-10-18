# GeoHealth NSW — real-data public-health dashboard MVP

**NSW-first, source-backed, no PostgreSQL, no synthetic analytical data.**

GeoHealth now supports the actual **HealthStats NSW mental-health-related ED presentations — LHD quarterly crude-rate export** provided on 18 October 2026. The source title contains “monthly”, but LHD observations are **quarterly rates per 100,000**, not monthly counts. The current export contains 13 individually reported LHDs plus a separately published “All LHDs” benchmark, covering 2015-Q4 through 2026-Q1.

## Quick start (Python 3.11+)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

**Put the exact, unmodified HealthStats CSV you supplied** in:

```
data/raw/NSW_HealthStats_LHD.csv
```

The file is already configured in `config/sources.json`. It is **not committed to this public repository**, pending review of the source reuse and commercial redistribution licence.

```bash
python -m etl.build --inspect data/raw/NSW_HealthStats_LHD.csv
python -m etl.build
streamlit run app.py
```

The builder saves **observations.csv** and **provenance.json** to `data/processed/`. The provenance records the raw SHA-256, source update, agency, citation URL, and retrieval date. The original CSV stays unchanged.

Optional official NSW Local Health District map:

```bash
python -m etl.download --boundaries
```

No database, GIS library, API server, Docker, or synthetic dataset is required to view actual LHD time series and forecasts. Mapping requires downloading the official government GeoJSON boundaries.

## What the dashboard shows

- Quarterly crude-rate time series, by selected LHD, including **source-published 95% confidence intervals**
- Comparisons between up to five LHDs and the independent **All LHDs** published benchmark
- Available LHD choropleth polygons (excludes All LHDs aggregate and suppressed LHDs)
- Forecasts 1, 2, 4, or 8 quarters ahead where there are at least **24 uninterrupted quarterly rate observations**
- Seasonal-naïve vs seasonal-linear-trend models selected by rolling-origin MAE, with **uncalibrated empirical forecast-error bands**, not confused with observed-rate CIs
- Source provenance and CSV export

**Health interpretation:** ED presentation rates measure recorded service utilisation, not illness prevalence, treatment access, or distinct people. Crude rates are not age-standardised. Far West and Western NSW are suppressed; Murrumbidgee data omit Albury presentations; source systems changed from HIE to EDWARD commencing FY2021–22. Never fabricate missing LHD values or redistribute NSW totals into LGA/postcode results.

## Tests

```bash
python -m pytest -q
```

Fixtures use tiny invented values in tests only; no synthetic values are used for application reporting.

## Next milestones

1. Run the real-file acceptance test in your local checkout and confirm the dashboard/map render.
2. Verify boundary-name matching and any geo-source revisions.
3. Obtain a suitable AOD source and implement its dedicated adapter.
4. Add official population denominators and only appropriately attributable funding data.
5. Review commercial redistribution rights before putting raw or cleaned government observations in this public repository.

See `docs/PRODUCT_REQUIREMENTS.md` and `docs/SOURCE_ACQUISITION.md`. Draft PR #1 remains separate from `main`.
