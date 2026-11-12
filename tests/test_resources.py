"""Test source-faithful resource joins, funding partitions and missing-data rules.

Test fixtures are artificial and excluded from all production tables.
"""
from __future__ import annotations
import csv
from pathlib import Path
import pytest
import pandas as pd
from etl.resources import build_resources, ResourceValidationError, FILES
from etl.audit_geography import EXPECTED_LHDS

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def fixture(root: Path):
    raw = root/"data/raw"
    names = EXPECTED_LHDS
    lhd_ids = {name: "NSW_LHD_"+name.upper().replace(" ","_") for name in names}
    pop=[];ses=[];joined=[];budgets=[];grants=[]
    for i,name in enumerate(names):
        lid=lhd_ids[name]
        population=120000+i*1000
        pop.append(dict(lhd_id=lid,lhd_short_name=name,population_estimate=str(population),
            population_reference_year="2025" if i==0 else "",
            population_approximate="yes" if i==0 else "not_specified",
            quality_note="Test records only",source_url="https://example.org/pop",
            aboriginal_and_torres_strait_islander_pct="4.5",
            born_overseas_pct="", speaks_language_other_than_english_pct="",
            age_70_plus_pct="",age_65_plus_pct=""))
        ses.append(dict(lhd_id=lid,lhd_short_name=name,census_year="2021",
            completeness="source_verified_indicators" if i==0 else "awaiting_LHD_aggregate_from_SA1_data",
            unemployment_pct="5" if i==0 else "",
            households_with_children_low_income_pct="",completed_year_12_or_equivalent_pct="",
            limited_spoken_english_pct="",people_age_65_plus_living_alone_pct="",
            seifa_irsd_population_weighted_score="",
            source_url="https://example.org/ses",source_page_number=""))
        joined.append(dict(lhd_id=lid,lhd_short_name=name,population_estimate=str(population),
            population_reference_year="2025" if i==0 else "",
            MH_operating_budget_FY2025_26_aud="",
            AOD_operating_budget_FY2025_26_aud="",
            MH_purchased_service_component_FY2025_26_aud="",
            MH_AOD_combined_unsplit_FY2025_26_aud=""))
        for stream in ("MH","AOD"):
            budgets.append(dict(lhd_id=lid,lhd_short_name=name,financial_year="2025-26",
                funding_stream=stream,amount_aud="",
                budget_scope="not_available_separately",quality="not_disclosed_as_separate_service_budget_in_retrieved_sources",
                source_url="",amount_basis="initial allocation (expense budget); not actual expenditure",
                geographic_attribution="LHD operational delivery footprint; not allocation by place of residence"))
    # Four full split pairs, one partial, one combined: 10 amounts.
    for idx in (1,2,3,4):
        name=names[idx];lid=lhd_ids[name]
        for stream in ("MH","AOD"):
            amount=10000000+idx*1000000+(500000 if stream=="AOD" else 0)
            budget=next(x for x in budgets if x["lhd_id"]==lid and x["funding_stream"]==stream)
            budget.update(amount_aud=str(amount),budget_scope="separate_district_service_budget",
                          source_url="https://example.org/budget",quality="source_verified")
            col=f"{stream}_operating_budget_FY2025_26_aud"
            next(x for x in joined if x["lhd_id"]==lid)[col]=str(amount)
    central=next(x for x in budgets if x["lhd_id"]==lhd_ids[names[0]] and x["funding_stream"]=="MH")
    central.update(amount_aud="76240000",
       budget_scope="MH_ABF_purchased_service_components_only_not_full_district_MH_budget",
       source_url="https://example.org/partial",quality="source_verified")
    next(x for x in joined if x["lhd_id"]==lhd_ids[names[0]])[
        "MH_purchased_service_component_FY2025_26_aud"]="76240000"
    combined=dict(budgets[0]);combined.update(lhd_id=lhd_ids[names[5]],lhd_short_name=names[5],
       funding_stream="MH_AOD_UNSPLIT",amount_aud="70213000",
       budget_scope="combined_service_budget_no_valid_MH_AOD_split",
       source_url="https://example.org/combined",quality="source_verified_combined_only")
    budgets.append(combined)
    next(x for x in joined if x["lhd_id"]==lhd_ids[names[5]])[
        "MH_AOD_combined_unsplit_FY2025_26_aud"]="70213000"
    for i in range(9):
        name=names[i%7]
        grants.append(dict(lhd_id=lhd_ids[name],lhd_short_name=name,recipient=f"Test organisation {i}",
            grant_program="NSW Alcohol and Other Drug Hub Grants",awarded_amount_aud=str(200000+i*1000),
            annualised_amount_aud="",program_term_years="4",
            attribution_type="location_of_recipient_as_published_NOT_verified_full_service_catchment",
            additivity_warning="Do not add to operating budget",source_url="https://example.org/grants"))
    sources=[dict(dataset="pop",title="Population",url="https://example.org/pop",
                 location="report",notes="Test-only")]
    for kind, rows in {"population":pop,"socioeconomic":ses,"budgets":budgets,
                       "grants":grants,"joined_reference":joined,"source_register":sources}.items():
        write_csv(raw/FILES[kind],rows)
    return raw

def test_build_all_validated_resource_layers(tmp_path):
    fixture(tmp_path)
    output=build_resources(tmp_path)
    tables=output["tables"]
    assert {k:len(v) for k,v in tables.items()}=={
       "lhd_profiles":15,"funding_allocations":31,
       "ngo_grant_awards":9,"lhd_resource_coverage":15,"source_register":1}
    coverage=tables["lhd_resource_coverage"]
    assert coverage["funding_per_resident_eligible"].eq(False).all()
    assert coverage["mh_full_operating_aud"].notna().sum()==4
    assert coverage["aod_full_operating_aud"].notna().sum()==4
    assert coverage["mh_partial_component_aud"].notna().sum()==1
    assert coverage["mh_aod_unsplit_aud"].notna().sum()==1
    assert coverage["ngo_awards_multiyear_recipient_locality_aud"].notna().sum()==7
    assert tables["lhd_profiles"]["seifa_irsd_population_weighted_score"].isna().all()
    assert len(output["provenance"]["raw_file_sha256"])==6
    assert (tmp_path/"data/processed/resources/resource_provenance.json").is_file()

def test_missing_budget_stays_unknown(tmp_path):
    fixture(tmp_path)
    funding=build_resources(tmp_path)["tables"]["funding_allocations"]
    unknown=funding[funding.allocation_class.eq("not_disclosed")]
    assert len(unknown)==21
    assert unknown.amount_aud.isna().all()
    assert not funding.loc[funding.allocation_class.eq("combined_unsplit"),
                            "funding_stream"].eq("MH").any()

def test_missing_source_fails_before_output(tmp_path):
    raw=fixture(tmp_path)
    (raw/FILES["grants"]).unlink()
    with pytest.raises(FileNotFoundError,match="grants"):
        build_resources(tmp_path)
    assert not (tmp_path/"data/processed/resources").exists()

def test_joined_budget_reconciliation_fails_closed(tmp_path):
    raw=fixture(tmp_path)
    path=raw/FILES["joined_reference"];df=pd.read_csv(path,dtype=str,keep_default_na=False)
    ix=df["MH_operating_budget_FY2025_26_aud"].ne("").idxmax()
    df.loc[ix,"MH_operating_budget_FY2025_26_aud"]="999"
    df.to_csv(path,index=False)
    with pytest.raises(ResourceValidationError,match="Budget pivot"):
        build_resources(tmp_path)

def test_reject_invented_irsd(tmp_path):
    raw=fixture(tmp_path)
    path=raw/FILES["socioeconomic"];df=pd.read_csv(path,dtype=str,keep_default_na=False)
    df.loc[0,"seifa_irsd_population_weighted_score"]="990.1"
    df.to_csv(path,index=False)
    with pytest.raises(ResourceValidationError,match="invented LHD IRSD"):
        build_resources(tmp_path)

def test_reject_annualised_ngo_grants(tmp_path):
    raw=fixture(tmp_path)
    path=raw/FILES["grants"];df=pd.read_csv(path,dtype=str,keep_default_na=False)
    df.loc[0,"annualised_amount_aud"]="200000"
    df.to_csv(path,index=False)
    with pytest.raises(ResourceValidationError,match="annualise"):
        build_resources(tmp_path)
