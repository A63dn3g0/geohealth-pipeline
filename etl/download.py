"""Download NSW government LHD boundaries, with checksum and source metadata."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SERVICE = "https://portal.data.nsw.gov.au/arcgis/rest/services/Hosted/SAPHARI_Version_LHD_Areas_2/FeatureServer/0/query"

def download_lhd(root: Path = ROOT) -> Path:
    params = urlencode({"where": "1=1", "outFields": "lhd_code,lhd_name",
        "returnGeometry": "true", "outSR": "4326", "f": "geojson"})
    url = SERVICE + "?" + params
    with urlopen(Request(url, headers={"User-Agent": "GeoHealth-public-data/0.1"}), timeout=60) as resp:
        payload = resp.read()
    doc = json.loads(payload)
    features = doc.get("features", [])
    if doc.get("type") != "FeatureCollection" or len(features) < 10:
        raise ValueError("NSW boundary service did not return sufficient real LHD polygons")
    if any(not feature.get("geometry") or not feature.get("properties", {}).get("lhd_name")
           for feature in features):
        raise ValueError("Boundary record missing polygon or official name")
    target = root / "data/raw/nsw_lhd_boundaries.geojson"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    target.with_suffix(".provenance.json").write_text(json.dumps({
        "url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "agency": "NSW Ministry of Health / Data.NSW"}, indent=2), encoding="utf-8")
    return target

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundaries", action="store_true", help="Download official LHD polygons")
    args = parser.parse_args()
    if not args.boundaries:
        parser.error("Specify --boundaries")
    print(download_lhd())
