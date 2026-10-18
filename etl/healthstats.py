"""Strict source adapter for HealthStats NSW LHD quarterly crude-rate exports.

The title says "monthly" but data for LHD geography are QUARTERLY RATES.
The source 95% confidence intervals describe observed rates, not forecasts.
"""
from __future__ import annotations
import csv
import re
from pathlib import Path
import pandas as pd

HEADERS=("Age (years)","Presentation type","Sex","LHD","Period",
         "Crude rate per 100,000 population","LL 95% CI","UL 95% CI")
AGE="Total: 12 years and over"
PRESENTATIONS="Total mental health presentations"
QUARTER=re.compile(r"^\d{4}-Q[1-4]$")

def parse_healthstats_lhd(path: Path, source: dict) -> pd.DataFrame:
    if (source.get("geography_type")!="LHD" or source.get("frequency")!="quarterly"
            or source.get("value_kind")!="rate"):
        raise ValueError("LHD export must be quarterly observed rates, not monthly counts")
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows=list(csv.reader(handle))
    if len(rows)<4 or len(rows[0])!=1 or "Mental health related emergency department visits (monthly)" not in rows[0][0]:
        raise ValueError("Unexpected HealthStats indicator title")
    if tuple(rows[1])!=HEADERS:
        raise ValueError("Unexpected HealthStats columns: "+repr(rows[1]))
    records=[]; footnotes=[]; in_footer=False
    for row in rows[2:]:
        if len(row)==8 and QUARTER.fullmatch(row[4].strip()):
            if in_footer:
                raise ValueError("Unexpected data row after HealthStats footer")
            records.append(row)
        else:
            in_footer=True
            footnotes.append(" ".join(row))
    if not records:
        raise ValueError("No quarterly LHD observations in source")
    if "Data at LHD and PHN levels are reported by quarters." not in "\n".join(footnotes):
        raise ValueError("Missing confirmation of quarterly LHD frequency")
    raw=pd.DataFrame(records, columns=HEADERS)
    for col,expected in [("Age (years)",AGE),("Presentation type",PRESENTATIONS),("Sex","Persons")]:
        if not raw[col].eq(expected).all():
            raise ValueError("Unexpected source stratum: "+col)
    if raw.LHD.isna().any() or raw.LHD.str.strip().eq("").any():
        raise ValueError("Missing LHD")
    if raw.duplicated(["LHD","Period"]).any():
        raise ValueError("Duplicate LHD/quarter")
    numeric=raw[list(HEADERS[5:])].apply(pd.to_numeric, errors="raise")
    if numeric.isna().any().any():
        raise ValueError("Missing or suppressed numerical rates")
    v=numeric[HEADERS[5]]; lo=numeric[HEADERS[6]]; hi=numeric[HEADERS[7]]
    if ((lo<0)|(lo>v)|(v>hi)).any():
        raise ValueError("Reported confidence bounds inconsistent with rate")
    periods=pd.PeriodIndex(raw.Period, freq="Q").to_timestamp()
    result=pd.DataFrame({
        "geography_type":"LHD","geography_name":raw.LHD.str.strip(),
        "indicator_id":source["id"],"indicator":source["indicator"],
        "period":periods.strftime("%Y-%m-%d"),"period_label":raw.Period,
        "value":v.astype(float),"lower_ci_95":lo.astype(float),"upper_ci_95":hi.astype(float),
        "unit":source["unit"],"value_kind":"rate","frequency":"quarterly",
        "source_id":source["id"],"source_url":source["source_url"],
        "agency":source["agency"],"data_status":"observed",
        "is_aggregate":raw.LHD.eq("All LHDs"),"age_band":AGE,"sex":"Persons",
        "presentation_type":PRESENTATIONS,
    })
    return result.sort_values(["geography_name","period"]).reset_index(drop=True)

def footer_metadata(path: Path) -> dict:
    lines=Path(path).read_text(encoding="utf-8-sig").splitlines()
    return {
        "source_release":next((s for s in lines if s.startswith("Date data updated:")),None),
        "citation":next((s for s in lines if "https://www.healthstats.nsw.gov.au/r/" in s),None),
        "suppression_note":next((s for s in lines if "Far West LHD has been suppressed" in s),None),
        "source_notes_preserved_in_raw":True,
    }
