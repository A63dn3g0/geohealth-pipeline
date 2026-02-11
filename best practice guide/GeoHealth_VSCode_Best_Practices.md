# GeoHealth LGA Project – Best Practices Guide

## 1. Architecture at a Glance
**Data Lake:** raw & staged files (CSV/Parquet/GeoJSON) in object storage (local `data/` → S3/MinIO).  
**Core DB:** PostgreSQL + PostGIS (authoritative store; spatial joins, materialized views, vector tile generation).  
**Pipelines:** Python (Pandas/GeoPandas + Pyogrio/Shapely), orchestrated by Prefect (simple) or Airflow (team/scale).  
**APIs:** FastAPI for serving metrics (query by LGA/PHN) and exporting GeoJSON/Parquet/vector tiles.  
**Analytics/Viz:** QGIS for power users; Streamlit/Dash for web; Apache Superset for charts; pg_tileserv/tegola for vector tiles.  
**Ops:** Docker + Compose (local), GitHub Actions (CI/CD), Great Expectations (data validation), DVC (data versioning).

## 2. Data Layer (Robust & Queryable)
- **Formats:** Prefer columnar Parquet for large tabular data; GeoParquet for geospatial; keep original CSVs for audit.
- **Database:**
  - PostGIS with GIST/SP-GIST spatial indexes; numeric b-tree on codes (LGA_CODE_2023, PHN_CODE).
  - Use EPSG:3577 (GDA94 / Australian Albers) for area-weighted operations; store geometry also in EPSG:4326 for web.
  - Create materialized views for common aggregations (e.g., per-capita metrics, funding per LGA).
- **Modeling (star-ish schema):**
  - Dimensions: dim_lga, dim_phn, dim_seifa, dim_time.
  - Facts: fact_outcomes_lga (counts), fact_funding_phn (totals), fact_crosswalk_lga_phn (weights), fact_rates_lga (derived).
- **Versioning:** DVC to track large datasets alongside Git; tag releases for “data snapshots”.

## 3. Ingestion & Transformation
- **ETL/ELT:**
  - Use Pyogrio for fast reads; GeoPandas for spatial ops; Shapely for geometry fixes; DuckDB for quick SQL on Parquet.
  - For bigger-than-memory workloads: Dask (tabular) or GeoPandas + dask-geopandas.
- **Crosswalks:** Build area-weighted (EPSG:3577) LGA↔PHN and optionally population-weighted versions. Store both with weights summing to 1.
- **Validation:** Great Expectations suites: expected columns, value ranges, CRS checks, weight sums, join coverage (≥95%), no divide-by-zero in rates.

## 4. Orchestration, Packaging, and Environments
- **Orchestration:** Prefect for simple flows; Airflow for enterprise scale.
- **Packaging:** uv or poetry for lockfile reproducibility; produce a requirements.txt for CI runners.
- **Containers:** Docker images with GDAL, GEOS, PROJ pinned; multi-stage builds.
- **Environments:** dev (synthetic data) → staging (masked) → prod (controlled). Use Alembic for schema migrations.

## 5. APIs & Serving
- **FastAPI Endpoints:** `/lga/{code}`, `/phn/{code}`, `/tiles/{z}/{x}/{y}`, `/download`.
- **Tiles:** pg_tileserv or tegola; tippecanoe for static MBTiles.
- **Auth:** OAuth2/OIDC with role-based access.

## 6. Frontend, Dashboards & GIS
- **Internal mapping:** QGIS connected to PostGIS.
- **Web UI:** Streamlit or Dash; filters, choropleths, exports.
- **BI:** Apache Superset for dashboards.

## 7. Security, Privacy, and Governance
- Aggregate data only; mask small cells (<5).
- Manage secrets with Vault/Doppler/1Password.
- Log pipeline metadata; track lineage.

## 8. Observability & Reliability
- **Logging:** Structured JSON logs.
- **Tests:** pytest for ETL, joins, API contracts.
- **Load Tests:** k6/Locust for APIs.
- **Backups:** pg_dump + WAL archiving.

## 9. Performance Tips (GIS + Analytics)
- Pre-compute materialized views; spatial partitioning.
- Store large tables as Parquet; COPY for ingestion.
- Use API caching/CDN for public layers.

## 10. Stack Reference
- **Core DB:** PostgreSQL 15+/PostGIS 3+
- **Py stack:** Python 3.11, pandas, geopandas, pyogrio, shapely, numpy, pyyaml, great_expectations, fastapi, uvicorn
- **Orchestration:** Prefect
- **Versioning:** Git + DVC
- **Viz:** QGIS; Streamlit; Superset
- **Tiles:** pg_tileserv (or tegola)
- **Auth:** OAuth2/OIDC
- **Docs:** MkDocs Material + diagrams

## 11. Dev→Prod Workflow
1. **Dev:** Work locally with synthetic data; commit code + DVC samples.
2. **CI:** Run unit tests; build Docker image.
3. **Staging:** Run on masked datasets; stakeholder review.
4. **Prod:** Schedule nightly flows; publish APIs/tiles; snapshot releases.
