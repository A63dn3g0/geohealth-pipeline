"""AOD HealthStats annual LHD source contract. Only disposable test observations."""
import json
import pandas as pd
import pytest
from etl.aod import parse_aod_lhd_annual, _financial_year_start
from etl.build import build

def manifest():
    return {"id":"aod","adapter":"healthstats_aod_lhd_annual",
        "file":"data/raw/Alcohol and other drug hospitalisations_LHD.csv",
        "agency":"HealthStats NSW","source_url":"https://www.healthstats.nsw.gov.au/r/137803",
        "geography_type":"LHD","frequency":"annual",
        "indicator":"AOD-related hospitalisation rate",
        "unit":"age-standardised hospitalisations per 100,000 population",
        "value_kind":"rate","license_reviewed":False}

def fixture(root):
    raw=root/"data/raw";raw.mkdir(parents=True)
    p=raw/"Alcohol and other drug hospitalisations_LHD.csv"
    p.write_text(
        '"Alcohol and other drug-related hospitalisations by LHD for Total alcohol and other drug-related"\n'
        '"LHD","Diagnosis drug category","Period","Age standardised rate per 100,000 population","LL 95% CI","UL 95% CI"\n'
        '"Sydney LHD","Total alcohol and other drug-related","21/22","1,011.0","980.3","1,042.4"\n'
        '"Sydney LHD","Total alcohol and other drug-related","22/23","1,060.7","1,029.3","1,092.8"\n'
        '"All LHDs","Total alcohol and other drug-related","21/22","1,055.0","1,040.3","1,070.4"\n'
        '\n"Statistical Methods"\n'
        '"Figures are based on where a person resides rather than where they are treated."\n'
        '"Rates were age-adjusted using the Australian population as at 30 June 2001."\n',
        encoding="utf-8"
    )
    return p

def test_aod_file_parsed(tmp_path):
    x=parse_aod_lhd_annual(fixture(tmp_path),manifest())
    assert len(x)==3
    assert x.frequency.eq("annual").all()
    assert x.value_kind.eq("rate").all()
    assert x.rate_method.eq("age_standardised").all()
    assert x[x.geography_name=="Sydney LHD"].period.tolist()==["2021-07-01","2022-07-01"]
    assert x[x.geography_name=="All LHDs"].is_aggregate.all()
    assert x.value.max()==1060.7

def test_aod_import_build(tmp_path):
    fixture(tmp_path)
    (tmp_path/"config").mkdir()
    (tmp_path/"config/sources.json").write_text(json.dumps({"sources":[manifest()]}))
    records=build(tmp_path)
    assert len(records)==3
    assert (tmp_path/"data/processed/observations.csv").is_file()
    prov=json.loads((tmp_path/"data/processed/provenance.json").read_text())
    assert prov["sources"][0]["observations"]==3

def test_aod_invalid_ci_rejected(tmp_path):
    p=fixture(tmp_path);p.write_text(p.read_text().replace("980.3","1,990.3"))
    with pytest.raises(ValueError,match="confidence"):
        parse_aod_lhd_annual(p,manifest())

def test_aod_wrong_category_rejected(tmp_path):
    p=fixture(tmp_path);p.write_text(p.read_text().replace('"Sydney LHD","Total alcohol and other drug-related"','"Sydney LHD","Opioids"',1))
    with pytest.raises(ValueError,match="category"):
        parse_aod_lhd_annual(p,manifest())

def test_year_parser_rejects_nonconsecutive():
    assert _financial_year_start("23/24")=="2023-07-01"
    with pytest.raises(ValueError,match="Nonconsecutive"):
        _financial_year_start("23/25")
