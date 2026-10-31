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


def annual_series(n=23):
    import numpy as np
    from analysis.forecast import forecast_annual_rate
    return pd.DataFrame({
        "geography_name": "Sydney LHD",
        "period": pd.date_range("2001-07-01", periods=n, freq="YS-JUL"),
        "value": np.array([1000 + i*4.0 + (i%3)*9 for i in range(n)]),
        "frequency": "annual", "value_kind": "rate", "data_status": "observed",
    })

def test_annual_aod_forecast():
    from analysis.forecast import forecast_annual_rate
    result, metadata = forecast_annual_rate(annual_series(), horizon=3)
    assert len(result)==3
    assert result.period.iloc[0]==pd.Timestamp("2024-07-01")
    assert metadata["n_years"]==23
    assert metadata["model"] in ("last_year_naive","trailing_five_year_mean")
    assert (result.lower_95 <= result.predicted).all()

def test_annual_missing_year_refused():
    from analysis.forecast import forecast_annual_rate, ForecastUnavailable
    with pytest.raises(ForecastUnavailable,match="Missing or non-July"):
        forecast_annual_rate(annual_series().drop(index=10))

def test_annual_wrong_units_refused():
    from analysis.forecast import forecast_annual_rate, ForecastUnavailable
    data=annual_series();data["value_kind"]="count"
    with pytest.raises(ForecastUnavailable,match="annual rate"):
        forecast_annual_rate(data)
