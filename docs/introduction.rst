.. _introduction:

============
Introduction
============

Overview
========

GeoHealth Pipeline is a modular, config-driven data integration system for Australian health and geography data at the Local Government Area (LGA) level.

**Key Features:**

- **Config-Driven:** Control all pipeline logic via YAML configuration
- **Flexible I/O:** Read/write from CSV, GeoPackage, PostGIS, and APIs
- **Spatial Analysis:** Built on GeoPandas for geographic data operations
- **Derived Metrics:** Automatic per-capita rate calculations and z-scores
- **Crosswalks:** Area-weighted LGA↔PHN spatial joined tables
- **Web Interfaces:** REST API (FastAPI) and interactive dashboard (Streamlit)
- **Docker Ready:** Full containerization for easy deployment
- **Well Tested:** Comprehensive test suite with >80% coverage

Use Cases
=========

1. **Health Surveillance:** Monitor health conditions across LGAs
2. **Planning:** Support public health system planning and resource allocation
3. **Research:** Enable geospatial health research at regional level
4. **Reporting:** Generate standardized health indicators and maps
5. **Integration:** Connect disparate health and geographic data sources

Data Flow
=========

.. code-block:: text

    Input Sources (CSV, PostGIS)
            ↓
    Load Geography (LGA boundaries)
            ↓
    Join Datasets to Geography
            ↓
    Compute Derived Metrics
            ↓
    Apply Transforms (z-scores, etc)
            ↓
    Generate Crosswalks (optional)
            ↓
    Export (GeoPackage, CSV, PNG map)
            ↓
    Web API & Dashboard

Architecture
============

The pipeline consists of three main components:

**ETL (Extract-Transform-Load)**
  - Reads data from multiple sources
  - Applies transformations and joins
  - Generates derived indicators
  - Exports to various formats

**API (REST)**
  - FastAPI-based REST endpoints
  - Query LGA data and metrics
  - Download results in multiple formats
  - Generate quickmaps on-demand

**Dashboard (Web UI)**
  - Interactive Streamlit interface
  - Visualize health metrics
  - Create custom reports
  - Download data

Supported Data Formats
======================

**Input:**
- CSV (text data)
- Shapefile / GeoPackage (geographic)
- PostGIS / PostgreSQL (spatial database)
- JSON / GeoJSON (geographic)

**Output:**
- GeoPackage (single-file geodatabase)
- CSV (tabular data)
- PNG (choropleth maps)
- PostGIS (database storage)
- JSON / GeoJSON (web formats)

System Requirements
===================

**Minimum:**
- Python 3.8+
- 2GB RAM
- 1GB disk space

**Recommended (Production):**
- Python 3.11+
- 8GB RAM
- 50GB disk space
- Docker & Docker Compose
- PostgreSQL 12+ with PostGIS

**Optional:**
- Nginx/Apache (reverse proxy)
- Redis (caching)
- Sentry (error tracking)
- Prometheus/Grafana (monitoring)

Contributing
============

Contributions are welcome! See :ref:`contributing` for guidelines.

License
=======

This project is licensed under the MIT License - see LICENSE file for details.

Support
=======

- **Issues:** GitHub Issues
- **Documentation:** https://geohealth-pipeline.readthedocs.io
- **Email:** support@example.com

Next Steps
==========

- :ref:`installation` - Get started with setup
- :ref:`quick_start` - Run your first pipeline
- :ref:`user_guide` - Learn all features
- :ref:`deployment` - Deploy to production
