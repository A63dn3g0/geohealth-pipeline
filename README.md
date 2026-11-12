## New: 15-LHD population, socioeconomic and resource layer

The resource layer is built independently of the HealthStats MH/AOD and ABS SEIFA ingestion flows. Copy the six supplied NSW LHD research extract CSVs (population, socioeconomic, funding, NGO awards, joined-reference and source register) to `data/raw/`, using **original file content** and the exact filenames in [docs/RESOURCE_INTEGRATION.md](docs/RESOURCE_INTEGRATION.md).

```bash
python -m etl.resources
streamlit run app.py
```

The resulting `data/processed/resources/` directory contains LHD profiles, scope-labelled initial budgets, separately attributable multi-year NGO grant awards, 15-district coverage/missingness summaries, source register and SHA-256 provenance. All five tables can be downloaded from the dashboard.

**Do not misinterpret these extracts:**
- Budgets are FY2025–26 **initial operating allocations**, not actual spending; 21/31 funding entries lack separately verified amounts.
- Central Coast's purchased-service mental-health component is **partial**; Murrumbidgee's combined MH+AOD allocation is **unsplit**; grant award decisions are **multi-year recipient-location associations** and cannot be added to operating allocations.
- Population denominators are **mixed or uncertain in reference year**. The MVP intentionally **does not generate funding-per-resident or funding-gap rankings** from them.
- Only Central Coast has verified numeric LHD Census socioeconomic indicators; **no LHD IRSD** is currently sourced. The ABS 2021 LGA index requires an SA1-based crosswalk before being reported at LHD level.

The new resource layer can be viewed independently if the three original health/SEIFA CSVs are not locally present; their absence must not be disguised by dummy data.

---

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

Both government source CSVs are already configured in `config/sources.json`. It is **not committed to this public repository**, pending review of the source reuse and commercial redistribution licence.

```bash
python -m etl.build --inspect data/raw/NSW_HealthStats_LHD.csv
python -m etl.build
streamlit run app.py
```

Also place the original AOD export at `data/raw/Alcohol and other drug hospitalisations_LHD.csv`. It contains annual financial-year **age-standardised AOD-related hospitalisation rates** for all 15 LHDs, 2001–02 to 2023–24, with 95% confidence intervals. This is a different indicator and frequency from the mental-health ED quarterly crude rate; GeoHealth never sums the two. See `docs/AOD_INTEGRATION.md`.

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
- Mental-health quarterly forecasts 1, 2, 4, or 8 quarters ahead where there are at least **24 uninterrupted quarterly rate observations**
- Seasonal-naïve vs seasonal-linear-trend models selected by rolling-origin MAE, with **uncalibrated empirical forecast-error bands**, not confused with observed-rate CIs
- Source provenance and CSV export

**Health interpretation:** ED presentation rates measure recorded service utilisation, not illness prevalence, treatment access, or distinct people. Crude rates are not age-standardised. Far West and Western NSW are suppressed; Murrumbidgee data omit Albury presentations; source systems changed from HIE to EDWARD commencing FY2021–22. Never fabricate missing LHD values or redistribute NSW totals into LGA/postcode results.

## Tests

```bash
python -m pytest -q
```

Fixtures use tiny invented values in tests only; no synthetic values are used for application reporting.

## ABS SEIFA 2021 socioeconomic layer (LGA, not LHD)

The official ABS SEIFA 2021 LGA workbook can now be loaded as a **separate 2021 LGA geography** using the provided NSW-only CSV extraction. Copy `geohealth_abs_nsw_lga_seifa_2021.csv` into `data/raw/`; it is enabled in `config/sources.json`. The source includes **128 named NSW LGAs** and four ABS socioeconomic indexes (IRSD, IRSAD, IER, IEO), plus 2021 Census usual-resident population and published ranking/decile fields. No raw Census data is committed to the public repo.

This does NOT create LHD-specific SEIFA scores or a direct LGA-to-LHD overlay; an official 2021 SA1-to-LHD correspondence and appropriately weighted SA1 socioeconomic measures are still necessary for defensible LHD-level socioeconomic comparisons. The dashboard intentionally does not map these LGA values using LHD polygons or forecast one-time Census indexes. See `docs/ABS_SEIFA_LGA_2021.md`.

## Map verification status

The official ArcGIS layer metadata was independently checked: it exposes `lhd_name` and `lhd_code`, uses polygon geometry, and advertises GeoJSON query support. The live polygon download and geographic join/visual rendering are **not yet certified**; this environment cannot retrieve the service's live geometry. The app's audit refuses missing polygons and invalid joins. Download polygons locally with `python -m etl.download --boundaries` and check `docs/GEOGRAPHY_ACCEPTANCE.md`. The boundary dataset's licence also needs a separate review.

## Next milestones

1. Run the real-file acceptance test in your local checkout and confirm the dashboard/map render.
2. Verify boundary-name matching and any geo-source revisions.
3. AOD source adapter is implemented; add a separately backtested annual-rate forecast only after a defensible model is validated.
4. Add official population denominators and only appropriately attributable funding data.
5. Review commercial redistribution rights before putting raw or cleaned government observations in this public repository.

See `docs/PRODUCT_REQUIREMENTS.md` and `docs/SOURCE_ACQUISITION.md`. Draft PR #1 remains separate from `main`.
