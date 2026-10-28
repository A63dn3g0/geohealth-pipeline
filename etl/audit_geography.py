"""Audit official NSW Local Health District boundary joins without redistributing health data.

The expected jurisdiction labels are administrative geography names only.
Missing LHDs in HealthStats are suppressed, not zero and not reconstructed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from analysis.geography import join_key

# 13 individually published districts in the supplied 2026 HealthStats export.
REPORTED_LHDS = (
    "Sydney", "South Western Sydney", "South Eastern Sydney",
    "Illawarra Shoalhaven", "Western Sydney", "Nepean Blue Mountains",
    "Northern Sydney", "Central Coast", "Hunter New England",
    "Northern NSW", "Mid North Coast", "Southern NSW", "Murrumbidgee",
)
SUPPRESSED_LHDS = ("Far West", "Western NSW")
EXPECTED_LHDS = REPORTED_LHDS + SUPPRESSED_LHDS

class GeographyAuditError(ValueError):
    pass

def _positions(value):
    """Walk a GeoJSON coordinate tree to inspect every vertex."""
    if isinstance(value, (list, tuple)) and len(value) >= 2 and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) for x in value[:2]
    ):
        yield float(value[0]), float(value[1])
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _positions(item)

def audit_lhd_geojson(doc: dict) -> dict:
    if doc.get("type") != "FeatureCollection":
        raise GeographyAuditError("Expected GeoJSON FeatureCollection")
    features = doc.get("features")
    if not isinstance(features, list) or len(features) < len(EXPECTED_LHDS):
        raise GeographyAuditError("Incomplete official NSW LHD polygon collection")
    observed = {}
    for feature in features:
        props = feature.get("properties") or {}
        label = props.get("lhd_name")
        code = props.get("lhd_code")
        if not isinstance(label, str) or not label.strip():
            raise GeographyAuditError("LHD polygon missing official name")
        if not isinstance(code, str) or not code.strip():
            raise GeographyAuditError("LHD polygon missing official code")
        key = join_key(label)
        if key in observed:
            raise GeographyAuditError("Duplicate LHD polygon name: " + label)
        geom = feature.get("geometry") or {}
        if geom.get("type") not in ("Polygon", "MultiPolygon"):
            raise GeographyAuditError("Expected polygon geometry for " + label)
        coords = geom.get("coordinates")
        points = list(_positions(coords))
        if len(points) < 4:
            raise GeographyAuditError("Missing polygon vertices for " + label)
        if any(not (140 <= lng <= 170 and -41 <= lat <= -25)
               for lng, lat in points):
            raise GeographyAuditError("Geometry outside NSW territory/islands sanity envelope for " + label)
        observed[key] = {"name": label, "code": code}
    expected = {join_key(name): name for name in EXPECTED_LHDS}
    missing = [name for key, name in expected.items() if key not in observed]
    unexpected = [info["name"] for key, info in observed.items() if key not in expected]
    if missing or unexpected:
        raise GeographyAuditError(
            "Official source/HealthStats geography mismatch. Missing: "
            + repr(missing) + " Unexpected: " + repr(unexpected)
        )
    return {
        "geometry_count": len(features),
        "reported_lhds_mapped": len(REPORTED_LHDS),
        "suppressed_lhds_uncoloured": list(SUPPRESSED_LHDS),
        "not_a_polygon": "All LHDs",
        "join_complete": True,
        "official_geography_codes": [observed[join_key(name)]["code"] for name in REPORTED_LHDS],
        "source_geography_labels": [observed[join_key(name)]["name"] for name in EXPECTED_LHDS],
    }

def audit_file(path: Path) -> dict:
    return audit_lhd_geojson(json.loads(path.read_text(encoding="utf-8")))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundaries", default="data/raw/nsw_lhd_boundaries.geojson")
    args = parser.parse_args()
    print(json.dumps(audit_file(Path(args.boundaries)), indent=2))
