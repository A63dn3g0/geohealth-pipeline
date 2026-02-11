from docx import Document
from pathlib import Path

# Create Word document
doc = Document()
doc.add_heading("GeoHealth LGA Project – Project Requirements", level=1)

# 1. Project Overview
doc.add_heading("1. Project Overview", level=2)
doc.add_paragraph(
    "The GeoHealth LGA Project is a public health and geospatial analytics platform designed to "
    "integrate mental health and alcohol & other drug (AOD) service funding, outcomes data, and "
    "population metrics across Australian Local Government Areas (LGAs) and Primary Health Networks (PHNs). "
    "The platform supports crosswalk mapping between LGA and PHN boundaries, per-capita metric derivation, "
    "and geographic visualisation for policy and resource allocation."
)

# 2. Objectives
doc.add_heading("2. Objectives", level=2)
doc.add_paragraph("• Aggregate and standardise public datasets from ABS, AIHW, PHNs, and funding agencies.")
doc.add_paragraph("• Build a PostGIS-enabled database as the authoritative geospatial and metrics store.")
doc.add_paragraph("• Create reproducible ETL pipelines for ingestion, transformation, and validation.")
doc.add_paragraph("• Enable per-capita and funding-per-population metric calculations.")
doc.add_paragraph("• Deliver APIs, dashboards, and GIS layers for stakeholders.")
doc.add_paragraph("• Ensure scalability, reproducibility, and secure access control.")

# 3. Scope
doc.add_heading("3. Scope", level=2)
doc.add_paragraph(
    "The project will ingest datasets from public health agencies and funding sources, "
    "create crosswalk mappings between LGAs and PHNs using area-weighted intersections, "
    "store geospatial and tabular data in PostGIS, and expose data products through APIs, dashboards, "
    "and downloadable files. The system will support development (synthetic data), staging (masked data), "
    "and production (real data) environments."
)

# 4. Stakeholders
doc.add_heading("4. Stakeholders", level=2)
doc.add_paragraph("• Government health departments")
doc.add_paragraph("• Primary Health Networks")
doc.add_paragraph("• Public health researchers")
doc.add_paragraph("• NGOs providing health and AOD services")
doc.add_paragraph("• Data analysts and GIS specialists")

# 5. Functional Requirements
doc.add_heading("5. Functional Requirements", level=2)
doc.add_paragraph("• Data ingestion from CSV, Parquet, GeoJSON, and API sources.")
doc.add_paragraph("• LGA↔PHN crosswalk generation with area and population weighting.")
doc.add_paragraph("• Population-normalised metrics (per 1,000 or 100,000).")
doc.add_paragraph("• Geospatial joins, aggregations, and materialised views.")
doc.add_paragraph("• Data validation using Great Expectations.")
doc.add_paragraph("• REST API with filtering, pagination, and GeoJSON output.")
doc.add_paragraph("• Dashboards with interactive maps, charts, and download options.")

# 6. Non-Functional Requirements
doc.add_heading("6. Non-Functional Requirements", level=2)
doc.add_paragraph("• Scalability: deployable from a laptop to cloud infrastructure.")
doc.add_paragraph("• Reproducibility: versioned data with DVC and locked dependencies.")
doc.add_paragraph("• Security: OAuth2/OIDC authentication, role-based access control.")
doc.add_paragraph("• Performance: spatial indexing, materialised views, API caching.")
doc.add_paragraph("• Reliability: automated backups, disaster recovery plan.")
doc.add_paragraph("• Observability: logging, metrics, and tracing.")

# 7. Data Sources
doc.add_heading("7. Data Sources", level=2)
doc.add_paragraph("• ABS – Australian Bureau of Statistics (Population, SEIFA, boundaries)")
doc.add_paragraph("• AIHW – Australian Institute of Health and Welfare (Health outcomes, AOD treatment data)")
doc.add_paragraph("• PHN – Primary Health Networks (Service locations, funding data)")
doc.add_paragraph("• Health Department funding allocations")
doc.add_paragraph("• OpenStreetMap (optional – base maps)")

# 8. Technical Stack
doc.add_heading("8. Technical Stack", level=2)
doc.add_paragraph("• Database: PostgreSQL + PostGIS")
doc.add_paragraph("• ETL: Python (pandas, geopandas, pyogrio, shapely, prefect)")
doc.add_paragraph("• Validation: Great Expectations")
doc.add_paragraph("• API: FastAPI + Uvicorn")
doc.add_paragraph("• Dashboard: Streamlit/Dash, Apache Superset")
doc.add_paragraph("• GIS: QGIS, pg_tileserv/tegola")
doc.add_paragraph("• Orchestration: Prefect/Airflow")
doc.add_paragraph("• Versioning: Git + DVC")
doc.add_paragraph("• Deployment: Docker + docker-compose")

# 9. Deliverables
doc.add_heading("9. Deliverables", level=2)
doc.add_paragraph("• PostGIS database schema and initial dataset load.")
doc.add_paragraph("• ETL scripts with configuration files.")
doc.add_paragraph("• LGA↔PHN crosswalk CSVs.")
doc.add_paragraph("• API endpoints and documentation.")
doc.add_paragraph("• Interactive dashboard and GIS layers.")
doc.add_paragraph("• Technical documentation and operations guide.")

# 10. Milestones
doc.add_heading("10. Milestones", level=2)
doc.add_paragraph("1. Requirements & design sign-off.")
doc.add_paragraph("2. Data source integration and schema setup.")
doc.add_paragraph("3. Pipeline development and crosswalk creation.")
doc.add_paragraph("4. API and dashboard MVP.")
doc.add_paragraph("5. Validation, optimisation, and stakeholder review.")
doc.add_paragraph("6. Production deployment.")

# Save file
requirements_doc_path = Path("/mnt/data/GeoHealth_Project_Requirements.docx")
doc.save(requirements_doc_path)

requirements_doc_path
