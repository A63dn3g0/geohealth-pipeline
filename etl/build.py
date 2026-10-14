"""Import authoritative government CSV exports with explicit source-column mappings.

Raw files remain unchanged; no geography guessing, synthetic observations or DB.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("id", "file", "agency", "source_url", "geography_type", "frequency", "indicator", "unit", "value_kind", "columns")
KINDS = {"count", "rate", "percent", "amount", "population", "index"}
FREQ = {"monthly", "quarterly", "annual"}
GEO = {"LHD", "PHN", "LGA", "SA2", "NSW"}

def period_start(values: pd.Series, frequency: str) -> pd.Series:
    raw = values.astype("string").str.strip()
    if frequency == "annual":
        if not raw.str.fullmatch(r"\d{4}").all():
            raise ValueError("Annual period must be YYYY")
        dates = pd.to_datetime(raw + "-01-01", errors="raise")
    elif frequency == "monthly":
        if not raw.str.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?").all():
            raise ValueError("Monthly period must be YYYY-MM or YYYY-MM-DD")
        dates = pd.to_datetime(raw.str[:7] + "-01", errors="raise")
    elif frequency == "quarterly":
        if not raw.str.fullmatch(r"\d{4}-Q[1-4]").all():
            raise ValueError("Quarter must be YYYY-Q1..Q4")
        dates = pd.PeriodIndex(raw.tolist(), freq="Q").to_timestamp()
    else:
        raise ValueError(f"Unsupported frequency: {frequency}")
    return pd.Series(dates, index=values.index).dt.strftime("%Y-%m-%d")

def normalize_csv(source: dict, root: Path = ROOT) -> pd.DataFrame:
    missing = [k for k in REQUIRED if k not in source]
    if missing:
        raise ValueError(f"Source manifest missing fields: {missing}")
    if source["frequency"] not in FREQ or source["value_kind"] not in KINDS or source["geography_type"] not in GEO:
        raise ValueError(f"Invalid frequency, value kind or geography for {source['id']}")
    path = (root / source["file"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Source file path escapes project root")
    if not path.is_file():
        raise FileNotFoundError(f"Download {source['source_url']} and save at {path}")
    mapping = source["columns"]
    if not {"period", "geography", "value"} <= set(mapping):
        raise ValueError("columns must map period, geography and value")
    df = pd.read_csv(path, encoding=source.get("encoding", "utf-8-sig"), skiprows=source.get("skiprows", 0), dtype=str)
    absent = (set(mapping.values()) | set(source.get("filters", {}))) - set(df)
    if absent:
        raise ValueError(f"{source['id']}: source columns missing: {sorted(absent)}; found {list(df.columns)}")
    for column, values in source.get("filters", {}).items():
        allowed = values if isinstance(values, list) else [values]
        df = df[df[column].str.strip().isin(allowed)]
    if df.empty:
        raise ValueError(f"{source['id']}: no rows after filters")
    data = pd.DataFrame({
        "geography_type": source["geography_type"], "geography_name": df[mapping["geography"]].str.strip(),
        "indicator_id": source["id"], "indicator": source["indicator"],
        "period": period_start(df[mapping["period"]], source["frequency"]),
        "value": pd.to_numeric(df[mapping["value"]].str.replace(",", "", regex=False), errors="coerce"),
        "unit": source["unit"], "value_kind": source["value_kind"],
        "frequency": source["frequency"], "source_id": source["id"],
        "source_url": source["source_url"], "agency": source["agency"],
        "data_status": "observed",
    })
    if data.geography_name.isna().any() or data.geography_name.eq("").any():
        raise ValueError("Missing geography name")
    data = data.dropna(subset=["value"])  # suppression markers are not zero
    if data.empty:
        raise ValueError("No unsuppressed values")
    if (data.value < 0).any():
        raise ValueError("Negative values are invalid")
    keys = ["geography_type", "geography_name", "indicator_id", "period"]
    if data.duplicated(keys).any():
        raise ValueError("Repeated geography/indicator/period: filter age, sex and category strata first")
    if source["value_kind"] == "count" and (data.value % 1 != 0).any():
        raise ValueError("Count data must contain integers")
    return data.sort_values(keys).reset_index(drop=True)

def build(root: Path = ROOT, manifest: str = "config/sources.json") -> pd.DataFrame:
    sources = json.loads((root / manifest).read_text(encoding="utf-8"))["sources"]
    enabled = [s for s in sources if s.get("enabled", True)]
    if not enabled:
        raise ValueError("No enabled source; download an official CSV and configure config/sources.json")
    if len({s["id"] for s in enabled}) != len(enabled):
        raise ValueError("Source IDs must be unique")
    frames = [normalize_csv(src, root) for src in enabled]
    all_data = pd.concat(frames, ignore_index=True)
    keys = ["geography_type", "geography_name", "indicator_id", "period"]
    if all_data.duplicated(keys).any():
        raise ValueError("Duplicate observations across source manifests")
    processed = root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    all_data.to_csv(processed / "observations.csv", index=False)
    provenance = []
    for s in enabled:
        file = root / s["file"]
        provenance.append({k: s[k] for k in ["id", "agency", "source_url", "indicator", "unit", "frequency", "value_kind"]} | {
            "source_file": s["file"], "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            "retrieved_at": s.get("retrieved_at", "not recorded"), "license_reviewed": s.get("license_reviewed", False)})
    (processed / "provenance.json").write_text(json.dumps({
        "build_utc": datetime.now(timezone.utc).isoformat(), "sources": provenance}, indent=2), encoding="utf-8")
    return all_data

def inspect(path: Path) -> None:
    if path.suffix.lower() == ".xlsx":
        workbook = pd.ExcelFile(path)
        print("Sheets:", workbook.sheet_names)
        for sheet in workbook.sheet_names[:10]:
            print(sheet, pd.read_excel(path, sheet_name=sheet, nrows=3).to_string(index=False))
    else:
        df = pd.read_csv(path, nrows=5)
        print("Columns:", list(df.columns))
        print(df.to_string(index=False))

def main() -> None:
    parser = argparse.ArgumentParser(description="GeoHealth official-source ingestion")
    parser.add_argument("--inspect", type=Path, help="Inspect downloaded government CSV/XLSX headers")
    parser.add_argument("--manifest", default="config/sources.json")
    args = parser.parse_args()
    if args.inspect:
        inspect(args.inspect)
    else:
        result = build(manifest=args.manifest)
        print(f"Imported {len(result)} observed records from {result.source_id.nunique()} government dataset(s)")

if __name__ == "__main__":
    main()
