## Live verification update — 28 October 2026

GitHub Actions successfully contacted the real Data.NSW ArcGIS service, downloaded official LHD GeoJSON, and passed the 15-jurisdiction polygon-name/code/geography audit. The first diagnostic found two flawed assumptions: full official labels ('South Eastern Sydney Local Health District') needed to match abbreviated HealthStats '... LHD' labels, and the NSW boundary extent includes offshore island territory beyond a mainland-only longitude envelope. Both have been corrected, and the latest live-geography-audit job passed.

**Verified:** real layer download, GeoJSON polygon structure, reported LHD coverage, official code/name fields, and automated map join key matching.

**Not yet verified:** actual map rendering in a human browser, geodesic topology/area validation, and commercial redistribution rights to the boundary layer.

See the latest successful GitHub Actions run: https://github.com/A63dn3g0/geohealth-pipeline/actions/runs/40680930035

---
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
