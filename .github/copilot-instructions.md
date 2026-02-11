# Copilot Instructions for GeoHealth Pipeline Project

## Project Overview
- Modular, config-driven pipeline for integrating, transforming, and exporting Australian health and geography data at the LGA level.
- Supports both file-based and PostGIS workflows.
- Key files: `geohealth_pipeline_Project.py`, `geohealth_config.yaml`, `etl/`, `api/`, `dashboard/`, `schemas/`, `outputs/`.

## Architecture & Data Flow
- **Config-driven:** All data sources, joins, and outputs are defined in a YAML config file (`geohealth_config.yaml`).
- **Flexible I/O:** Pipeline reads/writes from CSV, GeoPackage, and PostGIS. Geography and datasets are specified in config.
- **Major Steps:**
  1. Load LGA geography (GeoPackage or shapefile)
  2. Load datasets (CSV or PostGIS)
  3. Join datasets to geography
  4. Compute derived metrics (per-capita rates, z-scores)
  5. Export results (GeoPackage, CSV, PNG quickmap)
- **Demo mode:** Use `--demo` flag to generate synthetic data for testing.
- **Crosswalks:** Area-weighted LGA↔PHN crosswalks are generated if PHN boundaries are provided.

## Developer Workflows
- **Run pipeline:**
  - `python geohealth_pipeline_Project.py --config geohealth_config.yaml`
  - For demo: `python geohealth_pipeline_Project.py --demo`
  - For PostGIS: `python geohealth_pipeline_Project.py --read-postgis --pg-user ... --pg-password ... --pg-db ... --pg-table ...`
- **Export to PostGIS:**
  - `python geohealth_pipeline_Project.py --write-postgis --pg-user ... --pg-password ... --pg-db ... --pg-table ...`
- **Inspect DB schema:**
  - `python geohealth_pipeline_Project.py --show-db-schema --pg-user ... --pg-password ... --pg-db ...`
- **Config conventions:**
  - Use correct field names for each geography/dataset (e.g., `LGA_NAME25`, `LGA_CODE25` for 2025 data)
  - Datasets can be sourced from CSV or PostGIS; update config accordingly

## Patterns & Conventions
- **YAML config controls all pipeline logic.**
- **Field names must match actual data columns.**
- **Outputs are written to `outputs/` directory.**
- **Error handling:** Pipeline will fail with clear error if required files/fields are missing.
- **Quick mapping:** PNG choropleth is generated for fast visual checks.

## Integration Points
- **PostGIS:** Use CLI flags and config to read/write from PostgreSQL/PostGIS.
- **External data:** Place input files in `inputs/` or configure DB access.
- **Schema files:** See `schemas/` for JSON schema examples.

## Examples
- See `README.md` and `geohealth_config.yaml` for annotated config and usage examples.
- Typical run: `python geohealth_pipeline_Project.py --config geohealth_config.yaml`
- Demo run: `python geohealth_pipeline_Project.py --demo`
- PostGIS read: `python geohealth_pipeline_Project.py --read-postgis --pg-user ... --pg-password ... --pg-db ... --pg-table ...`

---

If any section is unclear or missing, please provide feedback to improve these instructions.
