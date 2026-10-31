# GeoHealth NSW — Revised MVP requirements, October 2026

GeoHealth supports evidence-based NSW mental-health/AOD service planning, comparing service utilisation, geographic jurisdictions, and (when published) funding and resources.

## Confirmed first source and data contract

Source: [HealthStats NSW, mental-health-related ED presentations](https://www.healthstats.nsw.gov.au/r/135943), updated June 2026. Supplied original export 18 Oct 2026.

- 588 source observations, 42 quarterly periods (2015-Q4–2026-Q1), 13 separately reported LHDs and published All LHDs aggregate (not an additional polygon).
- Age 12+, persons, total mental-health presentations.
- Crude rates per 100,000 and lower/upper published 95% confidence bounds; **not counts**.
- Far West and Western NSW suppressed. No imputation or reverse-engineering suppressed values.
- LHD is the patient's residence; Murrumbidgee omits Albury Hospital presentations.
- HIE/EDWARD reporting change starting FY2021–22 means forecast stationarity needs monitoring.

## Accepted MVP requirements

| ID | Requirement | Test |
| --- | --- | --- |
| FR-001 | Official data only | No synthetic dashboard records |
| FR-002 | Source-specific ETL | Parse original source title, strata, footer, quarterly periods |
| FR-003 | Geographic integrity | Preserve suppressed areas; show All LHDs as separate benchmark |
| FR-004 | Provenance | Raw SHA-256, retrieved date, release date, citation link |
| FR-005 | Original observation intervals | Keep source LL/UL 95% CI; never call them forecast bounds |
| FR-006 | Quarterly-rate forecasting | >=24 contiguous quarters, backtested against seasonal naive |
| FR-007 | Transparent uncertainty | Label forecast-error bands as uncalibrated |
| FR-008 | Jurisdiction comparison | Comparison plot of selected published LHDs |
| FR-009 | Interactive map | Use only real official polygon geometry; no synthetic boundaries |
| FR-010 | No database dependency | `streamlit run app.py` starts without PostgreSQL |
| FR-011 | Reliable error state | Clearly require source CSV if missing |
| FR-012 | No public data release by default | Raw/processed observations remain .gitignored |

## Forecast semantics

The observed quarterly *rate* is the target, not treatment counts or disease prevalence. Use four-quarter seasonal-naïve and seasonal-trend candidates with rolling-origin MAE; forecast 1/2/4/8 quarters, reject gaps, missing or invalid values. These are exploratory extrapolations with no causal interpretation or guaranteed prediction-interval coverage. Retain separate monthly count forecaster for future genuine monthly-count sources.

## Deferred

AOD data adapters, postcode/LGA disaggregation, PHN concordances, funding attribution, source licence approval, user auth, Postgres/PostGIS, cloud deployment. Do not allocate larger-geography funding or infer suppressed outcomes for the first MVP.

## Acceptance workflow

Copy unchanged attached CSV to `data/raw/NSW_HealthStats_LHD.csv` → `python -m etl.build` → validate 588 observations and 14 labels, observed CI, no duplicate quarters → `streamlit run app.py` → select Sydney LHD and compare with All LHDs → view quarterly-rate forecast → optionally download real LHD polygons for map. Dataset itself is not committed publicly.
