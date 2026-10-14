# GeoHealth NSW — MVP requirements (October 2026)

## Product
GeoHealth is a pre-populated dashboard for public-health resource planning in NSW. It brings together authoritative government data on mental-health and alcohol-and-other-drug (AOD) utilisation, geographical variation, demographics and — where source data permits — funding and service resources.

Primary audiences: Local Health Districts, Primary Health Networks, NSW agencies, NGOs, planners and service commissioners.

## Core MVP acceptance conditions

| ID | Requirement | Acceptance |
| --- | --- | --- |
| FR-001 | Official data only | No demo outcomes, synthetic indicators or made-up funding on dashboard |
| FR-002 | NSW LHD-first | Select a real LHD and display source-observed activity |
| FR-003 | Source provenance | For every imported series, record URL, agency, checksum and import date |
| FR-004 | Reproducibility | Original files unchanged; same config/raw files yield identical observations |
| FR-005 | Validation | Refuse duplicate geography-period-indicator rows, negative counts, invalid dates |
| FR-006 | Suppression safety | Suppressed cells omitted, never read as zero |
| FR-007 | Dashboard | Overview, map, jurisdiction profile, trends, resources and CSV export |
| FR-008 | No invented geography | LHD/PHN/LGA values displayed only at source-supported geography |
| FR-009 | Forecasting | >=36 continuous monthly observed counts, validated against simple baseline |
| FR-010 | Transparency | Backtest model score and non-calibrated uncertainty clearly labelled |
| FR-011 | Graceful onboarding | App opens without DB/source data and explains ingestion |
| FR-012 | No Postgres dependency | Clean local run needs only Python/requirements.txt |

## Initial forecast
Target: monthly mental-health-related ED presentation counts by LHD. Additional substance-related monthly ED indicators may be added after verifying actual source exports. Forecast horizons: 3, 6, 12 months. Models: seasonal naïve, seasonal trend. Select using rolling-origin MAE; display approximate empirical error bands. Withhold forecasts for insufficient, missing, suppressed, or non-count series.

## Not in MVP
Synthetic analytic data; national dashboards; Postgres/PostGIS; FastAPI; Kubernetes/nginx; advanced machine learning; user uploads; generic data scraping; inferred funding redistribution; building custom spatial crosswalks. Funding requires official geography-allocable sources before claims of gaps can be made.

## End-to-end demonstration
Install dependencies → download HealthStats NSW LHD monthly count export → inspect real columns → configure source → run ETL → launch dashboard → compare jurisdictions → view trend/forecast with errors → verify source URL and raw checksum.

## Risks/next prerequisites
1. Actual HealthStats CSV with original source metadata and correct count/age/sex selections.
2. Confirm licensing and allowable reuse, especially for commercial redistribution.
3. Validate that the hospital LHD classification used by each indicator matches mapping geography.
4. Demonstrate model performance against holdout historical data; no accuracy guarantee is implied.
