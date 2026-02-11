# GeoHealth LGA Pipeline

A modular, config-driven pipeline for integrating, transforming, and exporting Australian health and geography data at the LGA level. Supports both file-based and PostGIS workflows.

## Features
- **Config-driven:** All data sources, joins, and outputs are defined in a YAML config file.
- **Flexible I/O:** Read/write from CSV, GeoPackage, and PostGIS (PostgreSQL/PostGIS integration).
- **Demo mode:** Generate synthetic data for testing and development.
- **Derived metrics:** Computes per-capita rates and z-scores.
- **Crosswalks:** Area-weighted LGA↔PHN crosswalks.
- **Quick mapping:** Exports a PNG choropleth for fast visual checks.
- **Database schema inspection:** Print your PostgreSQL schema from the CLI.

## Requirements
- Python 3.8+
- See `requirements.txt` or `requirements-min.txt` for dependencies.

## Usage

### Basic pipeline run (with config):
```
python geohealth_pipeline_Project.py --config geohealth_config.yaml
```

### Demo mode (synthetic data):
```
python geohealth_pipeline_Project.py --demo
```

### Auto-detect config (no --config needed if file is in project root or configs/):
```
python geohealth_pipeline_Project.py
```

### PostGIS integration
- **Write output to PostGIS:**
```
python geohealth_pipeline_Project.py --config geohealth_config.yaml --write-postgis --pg-user myuser --pg-password mypass --pg-db mydb --pg-table geohealth_lga
```
- **Read input from PostGIS:**
```
python geohealth_pipeline_Project.py --read-postgis --pg-user myuser --pg-password mypass --pg-db mydb --pg-table geohealth_lga
```

### Print PostgreSQL schema
```
python geohealth_pipeline_Project.py --show-db-schema --pg-user myuser --pg-password mypass --pg-db mydb
```

## CLI Options
- `--config` Path to YAML config file
- `--demo` Use synthetic demo data
- `--read-postgis` Read LGA layer from PostGIS
- `--write-postgis` Write LGA layer to PostGIS
- `--show-db-schema` Print PostgreSQL schema and exit
- `--pg-user`, `--pg-password`, `--pg-host`, `--pg-port`, `--pg-db`, `--pg-table` PostGIS connection options


## YAML Config Structure

The pipeline is controlled by a YAML config file. Below is a summary of the main sections and their purpose:

### Top-level keys
- `output_dir`: Directory for all outputs.
- `geography`: Defines the LGA and (optionally) PHN shapefiles and their key fields.
- `datasets`: List of input datasets to join, with join keys and value fields.
- `transforms`: Optional transforms (e.g., z-score fields).
- `population`: Which dataset/field provides population for rate calculations.
- `derived_rates`: List of per-capita rates to compute.
- `crosswalk`: Output paths for LGA↔PHN crosswalk CSVs.
- `output`: Output file paths and options (GeoPackage, CSV, PNG, etc).

### Example config
```yaml
output_dir: ./outputs
geography:
	lga_shapefile: ./inputs/ABS_LGA_2023.gpkg
	lga_name_field: LGA_NAME_2023
	lga_code_field: LGA_CODE_2023
	phn_shapefile: ./inputs/PHN_Boundaries_2023.gpkg
	phn_name_field: PHN_NAME
	phn_code_field: PHN_CODE
datasets:
	- name: abs_erp_population_lga
		path: ./inputs/ABS_ERP_LGA_2023.csv
		lga_field: LGA_CODE
		value_fields: [population]
		join_on: code
transforms:
	zscore_fields: [mh_any_12m_rate_per_1000]
population:
	dataset_name: abs_erp_population_lga
	population_field: population
derived_rates:
	- {numerator: mh_any_12m_count, as: mh_any_12m_rate_per_1000, per_k: 1000}
crosswalk:
	lga_to_phn_csv: ./outputs/crosswalk_lga_to_phn.csv
	phn_to_lga_csv: ./outputs/crosswalk_phn_to_lga.csv
output:
	geopackage: ./outputs/geohealth.gpkg
	layer_name: geohealth_lga
	csv: ./outputs/geohealth_lga.csv
	quickmap_png: ./outputs/geohealth_quickmap.png
	choropleth_field: mh_any_12m_rate_per_1000
```

See `geohealth_config.yaml` for a full, annotated example.
- Add unit tests for all key functions
- Document your YAML config structure in this README
- Consider Dockerizing for reproducible environments

## License
MIT
