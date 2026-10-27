# NSW LHD geographic QA

### What the current audit checks

`python -m etl.download --boundaries` fetches a government ArcGIS FeatureServer GeoJSON, checks the complete 15-jurisdiction NSW LHD set, polygon types, non-empty codes and names, unique geography labels and a conservative NSW latitude/longitude envelope **before** caching the file.

`python -m etl.audit_geography --boundaries data/raw/nsw_lhd_boundaries.geojson` reports mapped and suppressed districts.

- **13 source-published LHDs:** individually colourable using their directly observed rates.
- **Far West and Western NSW:** geometry should be present but source observations are suppressed, so these districts remain uncoloured.
- **All LHDs:** statewide reporting benchmark, not an extra polygon. Do not add it to individual-district arithmetic averages.
- **No postcode/LGA/PHN back-allocation:** original source geography is LHD.
- The official boundary vintage should be recorded; use NSW source definitions rather than geographic assumptions.

### What remains unverified

This environment can read GitHub and source documentation, but cannot call the government's live ArcGIS endpoint in the same Python runtime used for integration tests. Therefore, the live service's actual JSON fields, geometry type and successful rendering **have not been verified**. Tests use deliberately artificial polygons **only in the test module**, not as dashboard data. A rejected geometry layer produces an explicit error rather than a misleading map.

### Manual acceptance (run with internet access)

```bash
python -m etl.download --boundaries
python -m etl.audit_geography --boundaries data/raw/nsw_lhd_boundaries.geojson
python -m etl.build
streamlit run app.py
```

Inspect all district joins in the map and confirm the source-missing Far West/Western NSW polygons have no colour. Check NSW Health's source licence terms before any external publication.
