"""Build source-faithful NSW LHD population, socioeconomic, funding and grant tables.

Inputs: the six 2026-10-29 NSW LHD research extracts supplied by the project
owner, saved unchanged under data/raw/. No invented values, geographic
redistribution, annualisation of grants, or per-capita funding calculations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from analysis.geography import join_key
from etl.audit_geography import EXPECTED_LHDS

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "population": "nsw_lhd_population_demographics.csv",
    "socioeconomic": "nsw_lhd_socioeconomic_2021.csv",
    "budgets": "nsw_lhd_mh_aod_budgets_2025_26.csv",
    "grants": "nsw_lhd_aod_ngo_grants_2023_2024_awards.csv",
    "joined_reference": "nsw_lhd_geodata_joined_2025_26.csv",
    "source_register": "nsw_lhd_source_register.csv",
}
SCOPES = {
    "separate_district_service_budget": "full_separate_operating",
    "MH_ABF_purchased_service_components_only_not_full_district_MH_budget": "partial_purchased_services",
    "combined_service_budget_no_valid_MH_AOD_split": "combined_unsplit",
    "not_available_separately": "not_disclosed",
}
NUMERIC_PROFILE = (
    "population_estimate",
    "aboriginal_and_torres_strait_islander_pct",
    "born_overseas_pct", "speaks_language_other_than_english_pct",
    "age_70_plus_pct", "age_65_plus_pct",
    "unemployment_pct", "households_with_children_low_income_pct",
    "completed_year_12_or_equivalent_pct", "limited_spoken_english_pct",
    "people_age_65_plus_living_alone_pct",
    "seifa_irsd_population_weighted_score",
)

class ResourceValidationError(ValueError):
    pass


def _require(df: pd.DataFrame, fields: set[str], kind: str) -> None:
    missing = fields - set(df.columns)
    if missing:
        raise ResourceValidationError(f"{kind}: missing columns {sorted(missing)}")


def _amount(series: pd.Series, label: str) -> pd.Series:
    # Empty is unknown, never zero. Whole-dollar amounts only.
    raw = series.astype("string").str.strip()
    present = raw.notna() & raw.ne("")
    if not raw[present].str.fullmatch(r"\d+").all():
        raise ResourceValidationError(f"{label}: amounts must be nonnegative whole AUD or blank")
    result = pd.to_numeric(raw.mask(~present), errors="raise").astype("Int64")
    return result


def _geography(df: pd.DataFrame, name: str, expected: set[str]) -> None:
    _require(df, {"lhd_id", "lhd_short_name"}, name)
    if df["lhd_id"].isna().any() or df["lhd_short_name"].isna().any():
        raise ResourceValidationError(f"{name}: missing geography")
    ids = set(df["lhd_id"])
    if ids != expected:
        raise ResourceValidationError(f"{name}: missing/unexpected LHD IDs {sorted(ids ^ expected)}")
    if (df.groupby("lhd_id")["lhd_short_name"].nunique() != 1).any():
        raise ResourceValidationError(f"{name}: inconsistent LHD names")


def _check_register(registry: pd.DataFrame) -> None:
    _require(registry, {"dataset", "title", "url", "location", "notes"}, "source_register")
    if registry.empty or registry["dataset"].duplicated().any():
        raise ResourceValidationError("Source register is empty or has duplicate dataset keys")
    if not registry["url"].str.startswith("https://").all():
        raise ResourceValidationError("Source register contains non-HTTPS/missing source URLs")


def build_resources(root: Path = ROOT) -> dict:
    root = Path(root)
    raw_dir = root / "data/raw"
    data: dict[str, pd.DataFrame] = {}
    hashes = {}
    for kind, filename in FILES.items():
        path = raw_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing {kind} file: {path}; use original supplied CSV")
        hashes[kind] = hashlib.sha256(path.read_bytes()).hexdigest()
        data[kind] = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    pop = data["population"].copy()
    ses = data["socioeconomic"].copy()
    budgets = data["budgets"].copy()
    grants = data["grants"].copy()
    joined = data["joined_reference"]
    registry = data["source_register"]
    _require(pop, {"population_estimate", "population_reference_year", "source_url",
                   "population_approximate", "quality_note"}, "population")
    _require(ses, {"census_year", "completeness",
                   "seifa_irsd_population_weighted_score", "source_url"}, "socioeconomic")
    _require(budgets, {"financial_year", "funding_stream", "budget_scope",
                       "amount_aud", "source_url", "quality", "amount_basis",
                       "geographic_attribution"}, "budgets")
    _require(grants, {"recipient", "grant_program", "awarded_amount_aud",
                      "annualised_amount_aud", "attribution_type", "additivity_warning",
                      "source_url", "program_term_years"}, "grants")
    _check_register(registry)
    if len(pop) != 15 or pop["lhd_id"].duplicated().any():
        raise ResourceValidationError("Expected exactly 15 unique LHD population profiles")
    expected = set(pop.lhd_id)
    names = {join_key(name) for name in EXPECTED_LHDS}
    if {join_key(name) for name in pop.lhd_short_name} != names:
        raise ResourceValidationError("Population labels do not match the 15 official LHDs")
    official_name_by_id = dict(zip(pop.lhd_id, pop.lhd_short_name))
    for kind, frame in (("socioeconomic", ses), ("budgets", budgets), ("joined_reference", joined)):
        _geography(frame, kind, expected)
        names_for_ids = frame[["lhd_id", "lhd_short_name"]].drop_duplicates()
        if any(official_name_by_id[row.lhd_id] != row.lhd_short_name
               for row in names_for_ids.itertuples(index=False)):
            raise ResourceValidationError(f"{kind}: LHD label disagrees with population geography")
    if len(ses) != 15 or ses.lhd_id.duplicated().any() or not ses.census_year.eq("2021").all():
        raise ResourceValidationError("Socioeconomic records must be one 2021 row per LHD")
    if len(joined) != 15 or joined.lhd_id.duplicated().any():
        raise ResourceValidationError("Joined reference must be 15 unique LHD rows")
    _require(joined, {"population_estimate", "population_reference_year",
                      "MH_operating_budget_FY2025_26_aud",
                      "AOD_operating_budget_FY2025_26_aud",
                      "MH_purchased_service_component_FY2025_26_aud",
                      "MH_AOD_combined_unsplit_FY2025_26_aud"}, "joined_reference")
    cross = joined.set_index("lhd_id")
    for row in pop.itertuples(index=False):
        if (str(cross.loc[row.lhd_id, "population_estimate"]) != row.population_estimate
                or str(cross.loc[row.lhd_id, "population_reference_year"]) != row.population_reference_year):
            raise ResourceValidationError("Joined reference population disagrees for " + row.lhd_id)
    socio = ses.drop(columns=["lhd_short_name"]).rename(columns={
        "source_url": "socioeconomic_source_url",
        "source_page_number": "socioeconomic_source_page_number",
        "completeness": "socioeconomic_completeness",
    })
    profile = pop.merge(socio, how="inner", on="lhd_id", validate="one_to_one")
    for col in NUMERIC_PROFILE:
        if col in profile:
            profile[col] = pd.to_numeric(profile[col].replace("", pd.NA), errors="raise")
            if (profile[col].dropna() < 0).any():
                raise ResourceValidationError(f"Invalid negative profile value in {col}")
            if col.endswith("_pct") and (profile[col].dropna() > 100).any():
                raise ResourceValidationError(f"Percentage exceeds 100 in {col}")
    if profile["population_estimate"].isna().any() or (profile["population_estimate"] <= 0).any():
        raise ResourceValidationError("Population is missing or nonpositive")
    if profile["seifa_irsd_population_weighted_score"].notna().any():
        raise ResourceValidationError("Do not accept invented LHD IRSD scores without SA1 concordance")

    if len(budgets) != 31 or not budgets.financial_year.eq("2025-26").all():
        raise ResourceValidationError("Expected 31 FY2025-26 source-budget rows")
    if set(budgets.funding_stream) != {"MH", "AOD", "MH_AOD_UNSPLIT"}:
        raise ResourceValidationError("Unexpected funding stream")
    if budgets.duplicated(["lhd_id", "funding_stream"]).any():
        raise ResourceValidationError("Duplicate funding streams")
    for stream in ("MH", "AOD"):
        if set(budgets.loc[budgets.funding_stream.eq(stream), "lhd_id"]) != expected:
            raise ResourceValidationError("Missing LHD/stream in budgets")
    budgets["amount_aud"] = _amount(budgets.amount_aud, "budget")
    budgets["allocation_class"] = budgets.budget_scope.map(SCOPES)
    if budgets.allocation_class.isna().any():
        raise ResourceValidationError("Unrecognised budget scope")
    has_value = budgets.amount_aud.notna()
    if not (has_value == budgets.allocation_class.ne("not_disclosed")).all():
        raise ResourceValidationError("Budget amount/scope conflicts: blanks must remain unknown")
    if (budgets.loc[has_value, "source_url"] == "").any():
        raise ResourceValidationError("Every sourced allocation needs a source URL")
    if (budgets.loc[has_value, "amount_basis"] !=
            "initial allocation (expense budget); not actual expenditure").any():
        raise ResourceValidationError("Unexpected budget basis")
    if not budgets.loc[budgets.allocation_class.eq("partial_purchased_services"), "funding_stream"].eq("MH").all():
        raise ResourceValidationError("Partial purchased-service entry is MH-only")
    combined = budgets[budgets.allocation_class.eq("combined_unsplit")]
    if len(combined) != 1 or combined.funding_stream.iloc[0] != "MH_AOD_UNSPLIT":
        raise ResourceValidationError("Expected exactly one unsplit MH+AOD allocation")
    expected_pivot = {
        ("MH", "full_separate_operating"): "MH_operating_budget_FY2025_26_aud",
        ("AOD", "full_separate_operating"): "AOD_operating_budget_FY2025_26_aud",
        ("MH", "partial_purchased_services"): "MH_purchased_service_component_FY2025_26_aud",
        ("MH_AOD_UNSPLIT", "combined_unsplit"): "MH_AOD_combined_unsplit_FY2025_26_aud",
    }
    for row in budgets.loc[has_value].itertuples():
        column = expected_pivot.get((row.funding_stream, row.allocation_class))
        if not column or str(cross.loc[row.lhd_id, column]) != str(row.amount_aud):
            raise ResourceValidationError("Budget pivot does not match source for " + row.lhd_id)
    if has_value.sum() != 10:
        raise ResourceValidationError("Unexpected changed funding coverage; review source files")

    if len(grants) != 9:
        raise ResourceValidationError("Expected nine separate AOD hub grant awards")
    if not set(grants.lhd_id) <= expected:
        raise ResourceValidationError("NGO grant points to unknown LHD")
    if any(official_name_by_id[row.lhd_id] != row.lhd_short_name
           for row in grants[["lhd_id", "lhd_short_name"]].drop_duplicates().itertuples(index=False)):
        raise ResourceValidationError("NGO recipient location/LHD name mismatch")
    if (grants["annualised_amount_aud"] != "").any():
        raise ResourceValidationError("Do not annualise grant award without payment schedule")
    grants["awarded_amount_aud"] = _amount(grants.awarded_amount_aud, "grant awards")
    if grants.awarded_amount_aud.isna().any():
        raise ResourceValidationError("Missing grant award amount")
    if not grants.program_term_years.eq("4").all():
        raise ResourceValidationError("Unexpected NGO multi-year grant term")
    if not grants.attribution_type.eq(
        "location_of_recipient_as_published_NOT_verified_full_service_catchment"
    ).all():
        raise ResourceValidationError("NGO location must not be treated as service catchment")
    if (grants["source_url"] == "").any():
        raise ResourceValidationError("NGO grant missing source reference")
    grants["award_scope"] = "multi_year_recipient_location_only"
    grants["additive_with_lhd_operating_budget"] = False

    def item(lhd_id: str, stream: str) -> dict:
        row = budgets[(budgets.lhd_id == lhd_id) & (budgets.funding_stream == stream)]
        if row.empty:
            return {"class": "not_disclosed", "amount": None}
        r = row.iloc[0]
        return {"class": r.allocation_class, "amount": r.amount_aud}
    coverage = []
    for p in profile.itertuples(index=False):
        mid = p.lhd_id
        mh, aod, both = (item(mid, s) for s in ("MH", "AOD", "MH_AOD_UNSPLIT"))
        award_rows = grants.loc[grants.lhd_id.eq(mid)]
        coverage.append({
            "lhd_id": mid,
            "lhd_short_name": p.lhd_short_name,
            "population_estimate": int(p.population_estimate),
            "population_reference_year": p.population_reference_year,
            "population_approximate": p.population_approximate,
            "mh_allocation_class": mh["class"],
            "aod_allocation_class": aod["class"],
            "mh_full_operating_aud": mh["amount"] if mh["class"] == "full_separate_operating" else None,
            "aod_full_operating_aud": aod["amount"] if aod["class"] == "full_separate_operating" else None,
            "mh_partial_component_aud": mh["amount"] if mh["class"] == "partial_purchased_services" else None,
            "mh_aod_unsplit_aud": both["amount"] if both["class"] == "combined_unsplit" else None,
            "ngo_award_count_recipient_locality": int(len(award_rows)),
            "ngo_awards_multiyear_recipient_locality_aud": (
                int(award_rows.awarded_amount_aud.sum()) if len(award_rows) else None
            ),
            "funding_per_resident_eligible": False,
            "funding_per_resident_caution": (
                "Not calculated: population reference years are mixed/uncertain; "
                "FY2025-26 allocations describe service entities, not resident expenditures."
            ),
        })
    coverage_df = pd.DataFrame(coverage).sort_values("lhd_short_name")
    if len(coverage_df) != 15:
        raise ResourceValidationError("Lost an LHD building coverage table")
    # All validation precedes any final output write.
    out = root / "data/processed/resources"
    out.mkdir(parents=True, exist_ok=True)
    results = {
        "lhd_profiles": profile.sort_values("lhd_short_name"),
        "funding_allocations": budgets.sort_values(["lhd_short_name", "funding_stream"]),
        "ngo_grant_awards": grants.sort_values(["lhd_short_name", "recipient"]),
        "lhd_resource_coverage": coverage_df,
        "source_register": registry,
    }
    for label, frame in results.items():
        frame.to_csv(out / f"{label}.csv", index=False)
    provenance = {
        "build_utc": datetime.now(timezone.utc).isoformat(),
        "source_redistribution_cleared": False,
        "raw_file_sha256": {FILES[k]: value for k, value in hashes.items()},
        "source_inventory_rows": {k: len(frame) for k, frame in data.items()},
        "outputs": {k: len(frame) for k, frame in results.items()},
        "restrictions": [
            "Budgets are initial FY2025-26 operating allocations, not expenditures.",
            "Murrumbidgee combined MH+AOD is unsplit.",
            "Central Coast purchased-service MH component is not full MH budget.",
            "NGO grants are four-year awards allocated by recipient location only.",
            "Population reference years are non-comparable; per-capita funding withheld.",
            "No source-verified LHD IRSD scores; do not back-allocate LGA SEIFA.",
            "Missing or suppressed values are unknown, not zero.",
        ],
    }
    (out / "resource_provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )
    return {"tables": results, "provenance": provenance}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build validated LHD resource tables")
    parser.add_argument("--root", default=str(ROOT), type=Path)
    args = parser.parse_args()
    result = build_resources(args.root)
    print(json.dumps(result["provenance"]["outputs"], indent=2))
