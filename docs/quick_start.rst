.. _quick_start:

===========
Quick Start
===========

This guide will get you running in 5 minutes.

Step 1: Demo Mode (No Data Required)
====================================

Run the pipeline with synthetic demo data:

::

    python geohealth_pipeline_Project.py --demo

**Expected output:**

::

    2026-02-11 22:58:58 INFO Auto-detected config file: geohealth_config.yaml
    2026-02-11 22:58:59 INFO Created 6 records
    2026-02-11 22:58:59 INFO Pipeline complete
    2026-02-11 22:58:59 INFO Rows: 6 | Columns: 11
    2026-02-11 22:58:59 INFO CSV: ./outputs/geohealth_lga.csv
    2026-02-11 22:58:59 INFO GPKG: ./outputs/geohealth.gpkg
    2026-02-11 22:58:59 INFO Map PNG: ./outputs/geohealth_quickmap.png

**Output files created in** ``outputs/``:

- ``geohealth.gpkg`` - GeoPackage with geometry and data
- ``geohealth_lga.csv`` - CSV table of LGA data
- ``geohealth_quickmap.png`` - Choropleth map visualization

Step 2: Run Tests
=================

Verify everything works:

::

    pytest -v

Expected output:

::

    test_geohealth_pipeline.py::...::test_normalise_lga_name PASSED
    test_geohealth_pipeline.py::...::test_zscore PASSED
    ...
    ====== 7 passed in 5.63s ======

Step 3: Web Interfaces
======================

**Start the API:**

::

    uvicorn api.main:app --reload

Visit http://localhost:8000/docs for Swagger documentation

**Start the Dashboard:**

::

    streamlit run dashboard/main.py

Visit http://localhost:8501 for interactive dashboard

Step 4: Run with Real Data
==========================

1. **Prepare your data files** in ``inputs/`` directory:

   - ``LGA_2025_AUST_GDA2020.gpkg`` (LGA geography) ✅ Already provided
   - ``ABS_ERP_LGA_2023.csv`` (population data)
   - ``your_health_dataset.csv`` (your data)

2. **Update config** (``geohealth_config.yaml``):

   ::

       datasets:
         - name: population
           path: ./inputs/ABS_ERP_LGA_2023.csv
           lga_field: LGA_CODE
           value_fields: [population]
           join_on: code

3. **Run pipeline:**

   ::

       python geohealth_pipeline_Project.py --config geohealth_config.yaml

Step 5: Docker Deployment
==========================

1. **Start services:**

   ::

       docker-compose up -d

2. **Access services:**

   - API: http://localhost:8000
   - Dashboard: http://localhost:8501
   - Database: localhost:5432

3. **Check status:**

   ::

       docker-compose ps

4. **View logs:**

   ::

       docker-compose logs -f

Configuration Basics
====================

The pipeline is controlled via ``geohealth_config.yaml``:

::

    output_dir: ./outputs

    geography:
      lga_shapefile: ./inputs/LGA_2025_AUST_GDA2020.gpkg
      lga_name_field: LGA_NAME25
      lga_code_field: LGA_CODE25

    datasets:
      - name: population
        path: ./inputs/ABS_ERP_LGA_2023.csv
        lga_field: LGA_CODE
        value_fields: [population]
        join_on: code

    population:
      dataset_name: population
      population_field: population

    derived_rates:
      - {numerator: count_field, as: rate_field, per_k: 1000}

    output:
      geopackage: ./outputs/geohealth.gpkg
      csv: ./outputs/geohealth_lga.csv
      quickmap_png: ./outputs/geohealth_quickmap.png

**Key sections:**

- ``geography`` - Define LGA and PHN boundaries
- ``datasets`` - List input datasets and join keys
- ``derived_rates`` - Compute per-capita metrics
- ``transforms`` - Apply z-scores, etc.
- ``output`` - Specify output formats and locations

CLI Options
===========

::

    # Demo mode (synthetic data)
    python geohealth_pipeline_Project.py --demo

    # With specific config
    python geohealth_pipeline_Project.py --config path/to/config.yaml

    # Read from PostGIS
    python geohealth_pipeline_Project.py \
      --read-postgis \
      --pg-user myuser \
      --pg-password mypass \
      --pg-db geohealth

    # Write to PostGIS
    python geohealth_pipeline_Project.py \
      --write-postgis \
      --pg-user myuser \
      --pg-password mypass \
      --pg-db geohealth

    # Show database schema
    python geohealth_pipeline_Project.py --show-db-schema

Common Tasks
============

**View generated data:**

::

    python -c "import pandas as pd; print(pd.read_csv('outputs/geohealth_lga.csv'))"

**Load GeoPackage in QGIS:**

Open QGIS → Layer → Add Layer → Vector → ``outputs/geohealth.gpkg``

**Query outputs with Python:**

::

    import geopandas as gpd
    gdf = gpd.read_file('outputs/geohealth.gpkg')
    print(gdf.head())
    gdf.plot(column='mh_any_12m_rate_per_1000', legend=True)

**Update database:**

::

    python geohealth_pipeline_Project.py \
      --config geohealth_config.yaml \
      --write-postgis \
      --pg-user geohealth \
      --pg-password geohealth \
      --pg-db geohealth

Next Steps
==========

1. :ref:`user_guide` - Learn advanced features
2. :ref:`configuration` - Detailed config reference
3. :ref:`deployment` - Deploy to production
4. :ref:`api_reference` - API documentation

Troubleshooting
===============

**Outputs don't exist:**

Check logs for errors. Ensure:
- Config file is readable
- Input data files exist (if using real data)
- ``outputs/`` directory is writable

**Config not loading:**

::

    # Verify YAML syntax
    python -c "import yaml; print(yaml.safe_load(open('geohealth_config.yaml')))"

**Data not joining:**

Check that:
- Field names match exactly (including case)
- Join keys are present in both datasets
- No data type mismatches

For more help, see :ref:`troubleshooting`.
