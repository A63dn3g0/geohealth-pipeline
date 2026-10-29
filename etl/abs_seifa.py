"""Strict adapter for ABS SEIFA 2021 LGA index CSV extracted from the official XLSX.

Do NOT relabel LGA observations as LHD, or average ranks/deciles into districts.
The ABS-published LGA scores derive from weighted SA1 scores. An LHD-specific
index must be recalculated from SA1 observations and a versioned SA1-LHD
population crosswalk; no such crosswalk is part of this adapter.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

INDEXES = {
    "irsd": "Relative socio-economic disadvantage (IRSD)",
    "irsad": "Relative socio-economic advantage and disadvantage (IRSAD)",
    "ier": "Economic resources (IER)",
    "ieo": "Education and occupation (IEO)",
}
MEASURES = {
    "score": ("score", "index"),
    "national_decile": ("Australian decile", "decile"),
    "nsw_decile": ("NSW decile", "decile"),
    "nsw_percentile": ("NSW percentile", "percentile"),
}
ABS_URL = ("https://www.abs.gov.au/statistics/people/people-and-communities/"
           "socio-economic-indexes-areas-seifa-australia/2021")
REQUIRED = {
    "lga_code_2021", "lga_name_2021", "geography_type", "census_2021_population",
    "reference_year", "status",
} | {f"{idx}_{m}" for idx in INDEXES for m in MEASURES}


def parse_abs_lga_seifa(path: Path, source: dict) -> pd.DataFrame:
    if (source.get("adapter") != "abs_seifa_lga_2021"
            or source.get("geography_type") != "LGA"
            or source.get("frequency") != "census"
            or source.get("value_kind") != "index"):
        raise ValueError("ABS SEIFA 2021 is census-vintage LGA index data, NOT LHD scores")
    df = pd.read_csv(path, dtype={"lga_code_2021": str}, encoding="utf-8-sig")
    missing = REQUIRED - set(df)
    if missing:
        raise ValueError("Missing SEIFA columns: " + ", ".join(sorted(missing)))
    if df["lga_code_2021"].duplicated().any():
        raise ValueError("Repeated ABS 2021 LGA code")
    if not df["reference_year"].eq(2021).all():
        raise ValueError("ABS source is not uniformly 2021 Census")
    if not df["lga_code_2021"].str.fullmatch(r"1\d{4}").all():
        raise ValueError("Non-NSW geographic codes found")
    if not df["status"].eq("ABS_published_LGA_index").all():
        raise ValueError("Unexpected unpublished or transformed source status")
    special = df[df["geography_type"] == "special_unincorporated"]
    if len(special) != 1 or special["lga_code_2021"].iloc[0] != "19399":
        raise ValueError("Expected one flagged non-LGA Unincorporated NSW observation")
    regular = df[df["geography_type"] == "LGA"].copy()
    if len(regular) != 128:
        raise ValueError(f"Expected 128 NSW LGAs, found {len(regular)}")
    if regular["lga_name_2021"].isna().any() or regular["lga_name_2021"].eq("").any():
        raise ValueError("LGA label missing")
    population = pd.to_numeric(regular["census_2021_population"], errors="raise")
    if population.isna().any() or (population <= 0).any():
        raise ValueError("Invalid 2021 Census resident population")
    records = []
    for index, label in INDEXES.items():
        for measure, (suffix, unit) in MEASURES.items():
            series = pd.to_numeric(regular[f"{index}_{measure}"], errors="raise")
            if series.isna().any():
                raise ValueError(f"SEIFA missing {index} {measure}")
            if measure.endswith("decile") and not series.between(1, 10).all():
                raise ValueError("SEIFA decile outside 1–10")
            if measure.endswith("percentile") and not series.between(1, 100).all():
                raise ValueError("SEIFA percentile outside 1–100")
            if measure == "score" and not series.between(200, 1800).all():
                raise ValueError("SEIFA score outside broad validity envelope")
            records.append(pd.DataFrame({
                "geography_type": "LGA",
                "geography_name": regular["lga_name_2021"].to_numpy(),
                "geography_code": regular["lga_code_2021"].to_numpy(),
                "geography_vintage": "2021",
                "indicator_id": f"seifa_2021_{index}_{measure}",
                "indicator": f"SEIFA 2021 — {label} — {suffix}",
                "period": "2021-01-01",
                "value": series.to_numpy(dtype=float),
                "unit": unit,
                "value_kind": "index",
                "frequency": "census",
                "source_id": source["id"],
                "source_url": source["source_url"],
                "agency": source["agency"],
                "data_status": "published_derived",
            }))
    records.append(pd.DataFrame({
        "geography_type": "LGA", "geography_name": regular["lga_name_2021"].to_numpy(),
        "geography_code": regular["lga_code_2021"].to_numpy(),
        "geography_vintage": "2021",
        "indicator_id": "seifa_2021_usual_resident_population",
        "indicator": "2021 Census — usual resident population (LGA)",
        "period": "2021-01-01", "value": population.to_numpy(dtype=float),
        "unit": "persons", "value_kind": "population", "frequency": "census",
        "source_id": source["id"], "source_url": source["source_url"],
        "agency": source["agency"], "data_status": "published_derived",
    }))
    result = pd.concat(records, ignore_index=True)
    assert result.geography_type.eq("LGA").all()
    return result.sort_values(["indicator_id", "geography_code"]).reset_index(drop=True)
