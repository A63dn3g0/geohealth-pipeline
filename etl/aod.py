"""Strict HealthStats NSW AOD hospitalisation LHD CSV adapter.

The attachment reports ANNUAL financial-year AGE-STANDARDISED rates per
100,000, not monthly events, crude rates, hospitalisation counts, or people.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
import pandas as pd

AOD_HEADERS = (
    "LHD", "Diagnosis drug category", "Period",
    "Age standardised rate per 100,000 population", "LL 95% CI", "UL 95% CI",
)
TITLE = "Alcohol and other drug-related hospitalisations by LHD for Total alcohol and other drug-related"
CATEGORY = "Total alcohol and other drug-related"
YEAR = re.compile(r"^(\d{2})/(\d{2})$")

def _financial_year_start(value: str) -> str:
    match = YEAR.fullmatch(value.strip())
    if match is None:
        raise ValueError("Expected financial year YY/YY, e.g. 23/24")
    first, last = map(int, match.groups())
    if first > 99 or (first + 1) % 100 != last:
        raise ValueError("Nonconsecutive financial-year label: " + value)
    if first > 60:  # Reject century ambiguity: only 2000–2060 supported.
        raise ValueError("Ambiguous historical financial year: " + value)
    return f"20{first:02d}-07-01"

def parse_aod_lhd_annual(path: Path, source: dict) -> pd.DataFrame:
    if (source.get("adapter") != "healthstats_aod_lhd_annual"
            or source.get("geography_type") != "LHD"
            or source.get("frequency") != "annual"
            or source.get("value_kind") != "rate"
            or source.get("unit") != "age-standardised hospitalisations per 100,000 population"):
        raise ValueError("AOD source is annual age-standardised LHD rates")
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 4 or len(rows[0]) != 1 or rows[0][0].strip() != TITLE:
        raise ValueError("Unexpected AOD HealthStats indicator title")
    if tuple(rows[1]) != AOD_HEADERS:
        raise ValueError("Unexpected AOD export header: " + repr(rows[1]))
    records, footer, after_data = [], [], False
    for row in rows[2:]:
        if len(row) == 6 and YEAR.fullmatch(row[2].strip()):
            if after_data:
                raise ValueError("Observation after HealthStats footer")
            records.append(row)
        else:
            after_data = True
            if row:
                footer.append(" ".join(row))
    if not records:
        raise ValueError("AOD source contains no annual observations")
    notes = "\n".join(footer)
    if ("Rates were age-adjusted using the Australian population as at 30 June 2001."
            not in notes or "Figures are based on where a person resides" not in notes):
        raise ValueError("Missing required HealthStats age-standardisation / residence metadata")
    raw = pd.DataFrame(records, columns=AOD_HEADERS)
    if not raw["Diagnosis drug category"].eq(CATEGORY).all():
        raise ValueError("Unexpected diagnosis category; source-matched total required")
    if raw["LHD"].str.strip().eq("").any() or raw["LHD"].isna().any():
        raise ValueError("Missing LHD label")
    if raw.duplicated(["LHD", "Period"]).any():
        raise ValueError("Duplicate AOD LHD / year")
    measurement = raw[list(AOD_HEADERS[3:])].apply(
        lambda col: pd.to_numeric(col.str.replace(",", "", regex=False), errors="raise")
    )
    if measurement.isna().any().any():
        raise ValueError("Missing, suppressed or invalid numeric values")
    value, lower, upper = (measurement[col].to_numpy(dtype=float) for col in AOD_HEADERS[3:])
    if ((lower < 0) | (lower > value) | (value > upper)).any():
        raise ValueError("Inconsistent published rate and confidence interval")
    starts = raw["Period"].map(_financial_year_start)
    years = pd.to_datetime(starts)
    for _, group in raw.assign(_start=years).groupby("LHD"):
        chronological = sorted(group["_start"])
        expected = pd.date_range(chronological[0], chronological[-1], freq="YS-JUL")
        if list(expected) != chronological:
            raise ValueError("Missing annual reporting periods for " + group["LHD"].iloc[0])
    result = pd.DataFrame({
        "geography_type": "LHD",
        "geography_name": raw["LHD"].str.strip(),
        "indicator_id": source["id"], "indicator": source["indicator"],
        "period": starts, "period_label": raw["Period"].map(lambda x: "FY20" + x),
        "value": value, "lower_ci_95": lower, "upper_ci_95": upper,
        "unit": source["unit"], "value_kind": "rate", "frequency": "annual",
        "source_id": source["id"], "source_url": source["source_url"],
        "agency": source["agency"], "data_status": "observed",
        "is_aggregate": raw["LHD"].eq("All LHDs"),
        "rate_method": "age_standardised", "period_type": "financial_year",
        "diagnosis_category": CATEGORY,
    })
    return result.sort_values(["geography_name", "period"]).reset_index(drop=True)

def aod_footer_metadata(path: Path) -> dict:
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    lines = [s.strip().strip('"') for s in lines]
    return {
        "citation": next((s for s in lines if "https://www.healthstats.nsw.gov.au/r/137803" in s), None),
        "age_standardisation_standard": "Australian population at 30 June 2001",
        "count_definition": "Hospitalisations, principal or additional diagnoses",
        "source_notes_preserved_in_raw": True,
    }
