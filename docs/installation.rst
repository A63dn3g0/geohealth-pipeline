.. _installation:

============
Installation
============

Prerequisites
=============

Before installing, ensure you have:

- **Python 3.8 or higher** (3.11+ recommended)
- **pip** (usually comes with Python)
- **git** (for cloning the repository)
- **PostgreSQL 12+** with PostGIS extension (for database workflows)
- **Docker & Docker Compose** (for containerized deployment)

Verify Prerequisites
====================

::

    python --version        # Should be 3.8+
    pip --version           # Should work
    git --version           # Should work
    psql --version          # PostgreSQL (optional)
    docker --version        # Docker (optional)
    docker-compose --version # Compose (optional)

Installation Methods
====================

Method 1: Pip Install (Recommended for Users)
==============================================

Install from PyPI:

::

    pip install geohealth-pipeline

Verify installation:

::

    python -c "import geohealth_pipeline_Project; print('OK')"

Method 2: Development Install (For Contributors)
=================================================

Clone the repository:

::

    git clone https://github.com/your-org/geohealth-pipeline.git
    cd geohealth-pipeline

Create virtual environment:

::

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

Install in development mode:

::

    pip install -e ".[dev]"

Verify installation:

::

    pytest -v

Method 3: Docker Install (Recommended for Production)
=====================================================

Prerequisites: Docker Desktop or Docker Engine

::

    docker pull geohealth-pipeline:1.0.0

Or build locally:

::

    git clone https://github.com/your-org/geohealth-pipeline.git
    cd geohealth-pipeline
    docker build -t geohealth-pipeline:1.0.0 .

Quick Verification
===================

**Check package contents:**

::

    python -c "import geohealth_pipeline_Project; print(dir())"

**Run demo:**

::

    python geohealth_pipeline_Project.py --demo

**Expected output:**

::

    INFO Pipeline complete
    INFO Rows: 6 | Columns: 11
    INFO CSV: ./outputs/geohealth_lga.csv
    INFO GPKG: ./outputs/geohealth.gpkg
    INFO Map PNG: ./outputs/geohealth_quickmap.png

Virtual Environments
====================

It's recommended to use a virtual environment to avoid conflicts with system packages.

**Using venv (built-in):**

::

    python -m venv venv
    source venv/bin/activate       # Linux/Mac
    # or
    venv\Scripts\activate           # Windows

**Using conda (if you have Anaconda):**

::

    conda create -n geohealth python=3.11
    conda activate geohealth

**Using Poetry:**

::

    poetry install
    poetry shell

PostgreSQL & PostGIS (Optional)
===============================

For database workflows, install PostgreSQL with PostGIS:

**On Ubuntu/Debian:**

::

    sudo apt-get install postgresql postgresql-contrib postgis

**On macOS (with Homebrew):**

::

    brew install postgresql postgis

**On Windows:**

Download from `PostgreSQL official site <https://www.postgresql.org/download/windows/>`_

**Using Docker:**

::

    docker run --name geohealth-db \
      -e POSTGRES_PASSWORD=password \
      -e POSTGRES_DB=geohealth \
      -p 5432:5432 \
      postgis/postgis:15-3.3

Troubleshooting Installation
=============================

**ModuleNotFoundError: No module named 'geopandas'**

Ensure you installed with all dependencies:

::

    pip install -e ".[dev]"  # From source
    # or
    pip install geohealth-pipeline  # From PyPI

**Spatial library conflicts**

If you have issues with spatial libraries (libspatialindex, etc.), try:

::

    # On Ubuntu
    sudo apt-get install libspatialindex-dev libgdal-dev

    # On macOS
    brew install spatialindex gdal

**PostgreSQL connection errors**

Check PostgreSQL is running and accessible:

::

    psql -h localhost -U postgres -c "SELECT version();"

**Docker permission denied**

Add your user to docker group:

::

    sudo usermod -aG docker $USER
    # Log out and log back in

Next Steps
==========

After installation:

1. :ref:`quick_start` - Run your first pipeline
2. :ref:`configuration` - Configure data sources
3. :ref:`user_guide` - Learn all features
4. :ref:`deployment` - Deploy to production

Getting Help
============

If you encounter issues:

1. Check :ref:`troubleshooting` guide
2. Search `GitHub Issues <https://github.com/your-org/geohealth-pipeline/issues>`_
3. Create a new issue with:
   - Python version
   - Installation method
   - Error message
   - Steps to reproduce

Upgrading
=========

To upgrade to the latest version:

::

    pip install --upgrade geohealth-pipeline

**From source:**

::

    cd geohealth-pipeline
    git pull origin main
    pip install -e ".[dev]"
