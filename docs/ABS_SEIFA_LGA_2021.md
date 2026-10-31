# ABS SEIFA 2021 — NSW Local Government Area integration

The supplied Excel workbook is the ABS **SEIFA 2021 LGA datacube**, not an LHD dataset. The source was released on 27 April 2023 and contains four indices:

- IRSD — Index of Relative Socio-economic Disadvantage (lower scores indicate greater relative disadvantage).
- IRSAD — Index of Relative Socio-economic Advantage and Disadvantage.
- IER — Index of Economic Resources.
- IEO — Index of Education and Occupation.

## Loaded geographic scope

The filtered NSW source contains **128 named 2021 LGAs** and one distinctly flagged `Unincorporated NSW` geographic category (`19399`). The adapter excludes the special category from LGA comparisons, but retains it in the user-provided extract. It emits **2,176 index/population observations** (128 LGAs × 17 measures: four indices × four score/ranking measures, plus 2021 usual-resident population).

Each published source score is assigned to its original 2021 LGA code and name, not to an LHD. This is a one-vintage Census snapshot and is never forecast.

## Getting started

The canonical source is `Local Government Area, Indexes, SEIFA 2021.xlsx`. The cleaned NSW-only CSV generated from its Table 2–5 fields is supplied separately. Place that CSV, without reformatting, at:

`data/raw/geohealth_abs_nsw_lga_seifa_2021.csv`

Then execute `python -m etl.build` to rebuild the processed dataset containing the two HealthStats indicators and the ABS LGA socioeconomic layer. Run `streamlit run app.py`, select `LGA` geography, choose SEIFA index and score/decile/percentile, and view rankings.

**Note:** the builder currently expects every enabled source file to be present. Keep the original mental-health and AOD source CSVs in `data/raw/` as documented.

## LHD crosswalk: do not create false precision

This dataset **cannot simply be joined to the existing LHD health/outcome series** on geographic name or code. Many LGAs cross LHD boundaries. Converting requires either:

1. The **2021 SA1 SEIFA IRSD/IRSAD/IER/IEO values**, 2021 SA1 population weights, and an official or validated SA1↔LHD concordance to recompute weighted LHD socioeconomic distributions; or
2. An approved, documented **LGA↔LHD population-weighted correspondence** with diagnostics, if only approximate LHD proxy values are acceptable.

An arithmetic average of LGA index **deciles/ranks** is invalid and should never be used. Weighted averages of LGA-level index **scores** are approximate and lose within-LGA variation. Prefer SA1-level scores and population weights for policy comparison.

The current LGA map view intentionally refuses to borrow LHD polygons. Loading official 2021 LGA boundaries and checking LGA joins is a separate milestone.

## Caveats

- 2021 LGA Census usual-resident population is not a 2025–26 estimate.
- These scores measure area socioeconomic conditions; they do not attribute disadvantage to every resident or imply causality for mental-health outcomes.
- ABS LGA boundaries (ASGS Non-ABS Structures) should be versioned; 2021 codes should not be silently matched to 2025 codes.
- Even NSW state deciles are ranks **within NSW LGA distributions**, not absolute levels of deprivation.

Source: https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/2021
