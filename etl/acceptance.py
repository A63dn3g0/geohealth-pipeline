"""Real-source GeoHealth acceptance gate. Run locally after installing source CSVs.

Produces a machine-readable report; intentionally fails without source files.
Unit tests and GitHub CI never substitute fixtures for this real-data gate.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from analysis.geography import join_key
from etl.build import build as build_outcomes
from etl.resources import ROOT, build_resources


def run_acceptance(root: Path = ROOT) -> dict:
    root = Path(root)
    obs = build_outcomes(root)
    resources = build_resources(root)
    expected = {
        "healthstats_mh_ed_quarterly_crude_rate": 588,
        "healthstats_aod_hospitalisation_annual_asr": 368,
        "abs_seifa_2021_lga": 2176,
    }
    counts = obs.groupby("source_id").size().to_dict()
    if counts != expected:
        raise ValueError(f"Real-source observation count mismatch: {counts} != {expected}")
    specs = {
        "healthstats_mh_ed_quarterly_crude_rate": ("LHD", "quarterly", "rate", 14),
        "healthstats_aod_hospitalisation_annual_asr": ("LHD", "annual", "rate", 16),
        "abs_seifa_2021_lga": ("LGA", "census", None, 128),
    }
    for source_id, (geography, freq, kind, n_geo) in specs.items():
        frame = obs.loc[obs.source_id.eq(source_id)]
        if (not frame.geography_type.eq(geography).all()
                or not frame.frequency.eq(freq).all()
                or (kind is not None and not frame.value_kind.eq(kind).all())
                or frame.geography_name.nunique() != n_geo):
            raise ValueError(f"Real-data geography or unit/frequency mismatch for {source_id}")
        if frame.duplicated(["geography_type", "geography_name", "indicator_id", "period"]).any():
            raise ValueError(f"Duplicate observations found for {source_id}")
        if geography == "LHD":
            if not {"lower_ci_95", "upper_ci_95"}.issubset(frame):
                raise ValueError("Published observation CI missing")
            if not (frame.lower_ci_95.le(frame.value) & frame.value.le(frame.upper_ci_95)).all():
                raise ValueError("Published observed rate outside source confidence interval")
    tables = resources["tables"]
    expected_outputs = {
        "lhd_profiles": 15, "funding_allocations": 31,
        "ngo_grant_awards": 9, "lhd_resource_coverage": 15,
        "source_register": 12,
    }
    actual_outputs = {k: len(v) for k, v in tables.items()}
    if actual_outputs != expected_outputs:
        raise ValueError(f"Resource output count mismatch: {actual_outputs}")
    lhd_names = {
        join_key(name) for name in tables["lhd_profiles"].lhd_short_name
    }
    for source_id in ("healthstats_mh_ed_quarterly_crude_rate",
                      "healthstats_aod_hospitalisation_annual_asr"):
        observations = obs[obs.source_id.eq(source_id)]
        geo_names = {join_key(s) for s in observations.geography_name if s != "All LHDs"}
        if not geo_names <= lhd_names:
            raise ValueError(f"Unmatched {source_id} LHD names: {sorted(geo_names-lhd_names)}")
    grant_total = int(tables["ngo_grant_awards"].awarded_amount_aud.sum())
    if grant_total != 23545000:
        raise ValueError("Grant total disagrees with supplied award decisions")
    if tables["lhd_profiles"]["seifa_irsd_population_weighted_score"].notna().any():
        raise ValueError("No source-verified LHD-level IRSD score is available")
    if not tables["lhd_resource_coverage"]["funding_per_resident_eligible"].eq(False).all():
        raise ValueError("Mixed-vintage populations cannot support per-capita rankings")
    report = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "result": "PASS",
        "observation_counts": counts,
        "resource_tables": actual_outputs,
        "sum_four_year_ngo_awards_aud_not_annualised": grant_total,
        "lhd_profile_count": len(tables["lhd_profiles"]),
        "pending_human_review": [
            "Streamlit rendered views with real CSVs and real government boundaries",
            "Commercial government data reuse licensing/permissions",
            "Population reference-year harmonisation",
            "Incomplete LHD funding and SA1-to-LHD socioeconomic correspondence",
        ],
    }
    path = root / "data/processed/real_data_acceptance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run_acceptance(), indent=2))
