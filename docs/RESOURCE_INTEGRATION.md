# GeoHealth NSW | LHD Population and Resource Evidence Layer

## Purpose

Integrates the six user-supplied NSW LHD research extract CSVs dated 29 October 2026. This feature is separate from HealthStats NSW MH/AOD time-series reporting and ABS LGA SEIFA ingestion, and runs with **no PostgreSQL, spatial crosswalk, fabricated figures or inference of missing values**.

## Source files and local placement

Place original research-extract CSVs **unchanged** in `data/raw/`, using these names:

| File name | Input rows | Meaning |
| --- | ---: | --- |
| `nsw_lhd_population_demographics.csv` | 15 | Population and demographics by LHD |
| `nsw_lhd_socioeconomic_2021.csv` | 15 | Sparse source-verified Census socioeconomic measures |
| `nsw_lhd_mh_aod_budgets_2025_26.csv` | 31 | FY2025–26 LHD initial MH, AOD and combined operating allocation classifications |
| `nsw_lhd_aod_ngo_grants_2023_2024_awards.csv` | 9 | Four-year AOD NGO grant awards, assigned by recipient locality |
| `nsw_lhd_geodata_joined_2025_26.csv` | 15 | Published joined reference for cross-checking—not an independent second allocation |
| `nsw_lhd_source_register.csv` | 12 | Official source references |

Uploads labelled `(1).csv` in ChatGPT must be copied to the filenames above (remove the parenthetical suffix); the original CSV **contents** should remain unchanged.

Run:

```bash
python -m pip install -r requirements-dev.txt
python -m etl.resources
streamlit run app.py
```

The application loads resources even when HealthStats files are absent, and adds an optional `Population & resources` tab alongside existing outcomes when both layers are available.

## Produced files (gitignored, not committed)

`data/processed/resources/`:

- `lhd_profiles.csv`: 15 profiles, demographic fields and explicit socioeconomic missingness
- `funding_allocations.csv`: 31 original classification-preserving budget records (10 disclosed amounts; **21 undisclosed**)
- `ngo_grant_awards.csv`: 9 grants with scope and attribution labels, explicitly *not additive* to district operating allocations
- `lhd_resource_coverage.csv`: 15-LHD summary with separate full MH, full AOD, partial MH, combined unsplit MH+AOD, grant award association, and missingness classifications
- `source_register.csv`: 12 references
- `resource_provenance.json`: SHA-256 of all six source files, record counts, restrictions and build timestamp

All outputs may be exported as CSV from the resource dashboard. Geography matching is by stable `lhd_id` rather than inferred names.

## Exact scope of identifiable FY2025–26 budget amounts

- **4 LHDs with separate MH and AOD service operating amounts:** Illawarra Shoalhaven, Mid North Coast, South Western Sydney, Sydney (**8 amounts**).
- **Central Coast:** one MH ABF purchased-service component (**partial**, not a full district MH budget).
- **Murrumbidgee:** one **combined MH+AOD** allocation, with **no validated MH/AOD split**.
- Remaining 21 MH or AOD funding rows have no numeric amount. **Undisclosed is not zero.**
- The government extracts represent *initial operating budgets*, not actual expenditure or spending resident-by-resident.
- Missing budgets, specialist program funding and Commonwealth PHN commissioning are not fully represented.

## Grant treatment

Nine AOD hub awards totalling **AUD 23,545,000** are **four-year programme award totals**, not annualised or FY2025–26 expenditures. An LHD association reflects a recipient locality; it **does not establish the service catchment**. Recipients may be funded from or overlap other budget channels. Never add the awards to LHD operating budgets without a reconciliation.

## Population and socioeconomic limitations

The supplied population figures are **mixed-vintage**: 14 districts are sourced from a 2022–23 NSW Health annual report with underlying population reference dates not conclusively established; Central Coast is a rounded 2025 local projection (357,300). Accordingly, FY2025–26 per-resident funding and ranking are **deliberately withheld**.

The 2021 socioeconomic file has directly verified numerical Census fields for **Central Coast only**; the other 14 districts are unpopulated in those fields, and all 15 weighted IRSD values are blank. ABS LGA SEIFA does **not** translate to LHD directly. An SA1-level data pipeline and population-weighted LHD crosswalk are a distinct future development milestone.

Demographic indicators are not themselves measures of socioeconomic disadvantage. Do not substitute ancestry, birthplace or language shares for IRSD.

## Validation and release status

The ETL rejects unknown/mismatched districts, invalid budget scopes, missing grant amounts, wrong periods, invalid numeric values, fabricated LHD IRSD values, duplicate funding stream assignments, budget/reference pivot disagreements and annualised grant claims. Missing source files fail explicitly without manufacturing placeholders.

Tests use *synthetic fixtures strictly within the test suite*. Source data are **not** committed to the public GitHub repository. Local source reuse and commercial redistribution rights must be verified independently; HealthStats commercial use restrictions remain a separate unresolved release gate.

**Next acceptance:** Execute the complete pipeline using all six original user-supplied CSVs in the target environment, verify 15 LHD profiles, 31 budget rows, 9 awards and 12 source references, visually inspect the Streamlit dashboard and confirm full/partial/unsplit funding displays. This feature branch does not merge automatically.

## Full real-data acceptance command

Once all **nine** original local source CSVs are present (three existing health/SEIFA files plus the six resource extracts), run:

```bash
python -m etl.acceptance
```

This processes original MH (588), AOD (368), and ABS LGA SEIFA (2,176) observations and cross-checks all five resource tables. It verifies LHD names, rates and published confidence bounds, the number of funding records, NGO award totals, source provenance, and the absence of invented LHD IRSD or approved per-resident funding.

A successful run writes `data/processed/real_data_acceptance.json` with `"result": "PASS"`. The report is **gitignored** and must be checked before accepting the actual source files. It is an ETL/data-contract gate, **not** a substitute for the Streamlit browser inspection or legal data licensing decision.

