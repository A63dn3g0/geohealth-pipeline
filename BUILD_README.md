# GeoHealth Pipeline

A modular, config-driven pipeline for integrating, transforming, and exporting Australian health and geography data at the LGA level.

## Quick Links

- 📚 [Documentation](https://geohealth-pipeline.readthedocs.io)
- 🐛 [Issues](https://github.com/your-org/geohealth-pipeline/issues)
- 💬 [Discussions](https://github.com/your-org/geohealth-pipeline/discussions)
- 📝 [Changelog](./CHANGELOG.md)

## Features

✅ **Config-driven** - Control pipeline via YAML  
✅ **Flexible I/O** - CSV, GeoPackage, PostGIS, APIs  
✅ **Derived metrics** - Per-capita rates, z-scores  
✅ **Spatial joins** - LGA↔PHN crosswalks  
✅ **Web interfaces** - REST API + interactive dashboard  
✅ **Docker ready** - Full containerization  
✅ **Well tested** - >80% test coverage  

## Installation

**Via pip:**
```bash
pip install geohealth-pipeline
```

**From source (development):**
```bash
git clone https://github.com/your-org/geohealth-pipeline.git
cd geohealth-pipeline
pip install -e ".[dev]"
```

**Via Docker:**
```bash
docker run -p 8000:8000 geohealth-pipeline:1.0.0
```

## Quick Start

1. **Demo mode** (no data required):
   ```bash
   python geohealth_pipeline_Project.py --demo
   ```

2. **With your data:**
   ```bash
   python geohealth_pipeline_Project.py --config geohealth_config.yaml
   ```

3. **Web interfaces:**
   ```bash
   # API
   uvicorn api.main:app

   # Dashboard
   streamlit run dashboard/main.py
   ```

4. **Docker:**
   ```bash
   docker-compose up -d
   # API: http://localhost:8000
   # Dashboard: http://localhost:8501
   ```

## Project Structure

```
geohealth-pipeline/
├── geohealth_pipeline_Project.py  # Main pipeline
├── geohealth_config.yaml          # Configuration
├── api/                           # REST API (FastAPI)
├── dashboard/                     # Web UI (Streamlit)
├── etl/                          # ETL utilities
├── inputs/                       # Input data directory
├── outputs/                      # Output directory
├── docs/                         # Documentation
├── tests/                        # Test suite
├── pyproject.toml               # Package config
└── docker-compose.yml           # Container orchestration
```

## Configuration

Create `geohealth_config.yaml`:

```yaml
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

derived_rates:
  - {numerator: health_count, as: health_rate, per_k: 1000}

output:
  geopackage: ./outputs/geohealth.gpkg
  csv: ./outputs/geohealth_lga.csv
  quickmap_png: ./outputs/geohealth_quickmap.png
```

## Usage Examples

**Run pipeline:**
```bash
python geohealth_pipeline_Project.py --config geohealth_config.yaml
```

**With PostGIS:**
```bash
python geohealth_pipeline_Project.py \
  --read-postgis \
  --pg-user postgres \
  --pg-password password \
  --pg-db geohealth
```

**Query results:**
```python
import geopandas as gpd
gdf = gpd.read_file('outputs/geohealth.gpkg')
print(gdf.head())
```

## API Endpoints

```
GET  /                    Welcome message
GET  /docs               Swagger API documentation
GET  /lga                List all LGAs
GET  /crosswalk          LGA↔PHN crosswalk
GET  /lga/geojson        LGA data as GeoJSON
```

## Requirements

**Minimum:**
- Python 3.8+
- 2GB RAM
- 1GB disk

**Recommended:**
- Python 3.11+
- 8GB RAM
- Docker & Compose

## Contributing

Contributions welcome! See [CONTRIBUTING.md](./docs/contributing.rst) for guidelines.

```bash
git checkout -b feature/your-feature
# Make changes, add tests
pytest -v
black . && isort .
git push origin feature/your-feature
# Open Pull Request
```

## Testing

```bash
# Run all tests
pytest -v

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest test_geohealth_pipeline.py -v
```

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

Services:
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- Database: localhost:5432

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for production setup.

### Development Commands

```makefile
make install      # Install dependencies
make dev         # Install dev dependencies
make test        # Run tests
make lint        # Code quality checks
make format      # Auto-format code
make docs        # Build documentation
make demo        # Run demo
make docker      # Build Docker image
make up          # Start Docker services
```

## Documentation

- 📖 [Full Documentation](https://geohealth-pipeline.readthedocs.io)
- 🚀 [Installation Guide](./docs/installation.rst)
- ⚡ [Quick Start](./docs/quick_start.rst)
- 🏗️ [Architecture](./docs/architecture.md)
- 📋 [Configuration Reference](./docs/configuration.md)
- 🚢 [Deployment Guide](./docs/DEPLOYMENT.md)
- 🆘 [Troubleshooting](./docs/troubleshooting.md)

## License

MIT License - see LICENSE file

## Citation

If you use GeoHealth Pipeline in research, please cite:

```bibtex
@software{geohealth_pipeline_2026,
  author = {GeoHealth Team},
  title = {GeoHealth Pipeline: Australian LGA Health Data Integration},
  year = {2026},
  url = {https://github.com/your-org/geohealth-pipeline}
}
```

## Support

- 🐛 [Bug Reports](https://github.com/your-org/geohealth-pipeline/issues/new?template=bug_report.md)
- 💡 [Feature Requests](https://github.com/your-org/geohealth-pipeline/issues/new?template=feature_request.md)
- 💬 [Discussions](https://github.com/your-org/geohealth-pipeline/discussions)
- 📧 Email: support@example.com

## Status

| Component | Status |
|-----------|--------|
| Tests | [![Tests](https://github.com/your-org/geohealth-pipeline/actions/workflows/tests.yml/badge.svg)](https://github.com/your-org/geohealth-pipeline/actions) |
| Coverage | [![Coverage](https://codecov.io/gh/your-org/geohealth-pipeline/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/geohealth-pipeline) |
| Docs | [![Docs](https://readthedocs.org/projects/geohealth-pipeline/badge/?version=latest)](https://geohealth-pipeline.readthedocs.io) |
| Docker | [![Docker](https://img.shields.io/docker/pulls/geohealth/pipeline)](https://hub.docker.com/r/geohealth/pipeline) |

---

**Made with ❤️ for public health**
