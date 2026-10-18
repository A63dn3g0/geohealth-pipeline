# HealthStats NSW source register

## Verified initial attachment

- Export: `NSW HealthStats LHD.csv` (copy unchanged to `data/raw/NSW_HealthStats_LHD.csv`).
- Citation: https://www.healthstats.nsw.gov.au/r/135943
- HealthStats indicator: “Mental health related emergency department visits (monthly)” **but LHD and PHN results are quarterly** per exported notes.
- Source release updated June 2026; exported/downloaded 18 October 2026.
- SHA-256 of supplied attachment: `080e5904833c120dedd8309383fac8e8e6444c8f8e2b67cda918ae640b40055d`.
- Observations: 588 for 14 LHD labels (13 individual plus published All LHDs), 42 quarters each (2015-Q4–2026-Q1).
- Measure: crude rate per 100,000, with source-supplied 95% CIs.
- LHD based on patient residence; Far West and Western NSW suppressed; All LHDs includes missing/not stated.
- Coding source changed from HIE to EDWARD beginning FY2021–22; source excludes Albury ED presentations.

## Reproducibility

1. Preserve unchanged source as `data/raw/NSW_HealthStats_LHD.csv`.
2. Run `python -m etl.build`.
3. Inspect `data/processed/observations.csv` and `provenance.json`.
4. Government original files and transformed records are excluded from Git. Reuse/licensing review is **not complete**.
5. Optionally `python -m etl.download --boundaries` to download real LHD geometry from https://portal.data.nsw.gov.au/arcgis/rest/services/Hosted/SAPHARI_Version_LHD_Areas_2/FeatureServer/0.

## Other potential sources

- [Bureau of Health Information](https://www.bhi.nsw.gov.au/downloadable-data) — quarterly hospital/ED activity.
- [ABS regional population](https://www.abs.gov.au/statistics/people/population/regional-population/latest-release).
- [AIHW AODTS PHN data](https://www.aihw.gov.au/reports/alcohol-other-drug-treatment-services/alcohol-other-drug-treatment-services-australia/contents/data-primary-health-network).
- [PHN concordances](https://www.health.gov.au/resources/collections/primary-health-networks-phns-collection-of-concordance-files).

Never conflate service presentations with distinct people, illness incidence or service access, and never redistribute aggregate funds without a defensible recorded allocation method.
