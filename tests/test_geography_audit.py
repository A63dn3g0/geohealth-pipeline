"""Boundary audit tests use fake POLYGONS only as test fixtures, never map data."""
import pytest
from etl.audit_geography import EXPECTED_LHDS, GeographyAuditError, audit_lhd_geojson

def collection():
    features=[]
    for i, name in enumerate(EXPECTED_LHDS):
        x=145+(i%5)*0.25; y=-36+(i//5)*0.5
        features.append({"type":"Feature","properties":{"lhd_name":name+" LHD","lhd_code":f"T{i:02d}"},
                         "geometry":{"type":"Polygon","coordinates":[[
                             [x,y],[x+0.2,y],[x+0.2,y+0.2],[x,y+0.2],[x,y]
                         ]]}})
    return {"type":"FeatureCollection","features":features}

def test_expected_lhd_coverage_and_suppression():
    audit=audit_lhd_geojson(collection())
    assert audit["join_complete"]
    assert audit["reported_lhds_mapped"]==13
    assert audit["suppressed_lhds_uncoloured"]==["Far West","Western NSW"]
    assert audit["not_a_polygon"]=="All LHDs"

def test_missing_geography_refused():
    doc=collection()
    doc["features"].pop()
    with pytest.raises(GeographyAuditError,match="Incomplete"):
        audit_lhd_geojson(doc)

def test_duplicate_name_refused():
    doc=collection()
    doc["features"][1]["properties"]["lhd_name"]=doc["features"][0]["properties"]["lhd_name"]
    with pytest.raises(GeographyAuditError,match="Duplicate"):
        audit_lhd_geojson(doc)

def test_invalid_coordinates_refused():
    doc=collection()
    doc["features"][0]["geometry"]["coordinates"][0][0][0]=180
    with pytest.raises(GeographyAuditError,match="outside NSW"):
        audit_lhd_geojson(doc)

def test_no_code_refused():
    doc=collection()
    doc["features"][0]["properties"].pop("lhd_code")
    with pytest.raises(GeographyAuditError,match="official code"):
        audit_lhd_geojson(doc)
