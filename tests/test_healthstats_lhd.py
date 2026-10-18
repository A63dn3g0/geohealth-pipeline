"""Source parser and quarterly forecasting contracts, with synthetic TEST FIXTURES only."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from etl.healthstats import parse_healthstats_lhd
from etl.build import build
from analysis.forecast import forecast_quarterly_rate, ForecastUnavailable

def source():
    return {"id":"mh_lhd_q","adapter":"healthstats_lhd_quarterly",
        "file":"data/raw/NSW_HealthStats_LHD.csv",
        "agency":"NSW Health","source_url":"https://www.healthstats.nsw.gov.au/r/135943",
        "geography_type":"LHD","frequency":"quarterly",
        "indicator":"Mental-health-related ED visits — crude quarterly rate",
        "unit":"presentations per 100,000 population",
        "value_kind":"rate","retrieved_at":"2026-10-18","license_reviewed":False}

def csv_fixture(tmp_path: Path):
    raw=tmp_path/"data/raw"
    raw.mkdir(parents=True)
    path=raw/"NSW_HealthStats_LHD.csv"
    lines=[
      '"Mental health related emergency department visits (monthly) test LHD"',
      '"Age (years)","Presentation type","Sex","LHD","Period","Crude rate per 100,000 population","LL 95% CI","UL 95% CI"',
    ]
    for district in ["Sydney LHD","All LHDs"]:
        for period,value in [("2025-Q1",200),("2025-Q2",220),("2025-Q3",240)]:
            lines.append(f'"Total: 12 years and over","Total mental health presentations","Persons","{district}","{period}",{value},{value-10},{value+10}')
    lines.extend(['"','"Data at LHD and PHN levels are reported by quarters."'])
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")
    return path

def test_healthstats_quarterly_parser(tmp_path):
    data=parse_healthstats_lhd(csv_fixture(tmp_path),source())
    assert len(data)==6
    assert data.frequency.eq("quarterly").all()
    assert data.value_kind.eq("rate").all()
    assert data[data.geography_name=="All LHDs"].is_aggregate.all()
    assert data[data.geography_name=="Sydney LHD"].period.iloc[-1]=="2025-07-01"
    assert data.lower_ci_95.le(data.value).all() and data.upper_ci_95.ge(data.value).all()

def test_build_with_lhd_source(tmp_path):
    csv_fixture(tmp_path)
    (tmp_path/"config").mkdir()
    (tmp_path/"config/sources.json").write_text(json.dumps({"sources":[source()]}))
    output=build(tmp_path)
    assert len(output)==6
    out=tmp_path/"data/processed/observations.csv"
    assert pd.read_csv(out).lower_ci_95.notna().all()
    prov=json.loads((tmp_path/"data/processed/provenance.json").read_text())
    assert prov["sources"][0]["observations"]==6
    assert len(prov["sources"][0]["sha256"])==64

def test_healthstats_rejects_wrong_stratum(tmp_path):
    p=csv_fixture(tmp_path)
    p.write_text(p.read_text().replace('"Persons"','"Males"',1))
    with pytest.raises(ValueError,match="stratum"):
        parse_healthstats_lhd(p,source())

def quarterly(n=42):
    dates=pd.date_range("2015-10-01",periods=n,freq="QS")
    return pd.DataFrame({"period":dates,
        "value":np.array([300+(i%4)*12+i*1.8 for i in range(n)]),
        "frequency":"quarterly","value_kind":"rate","data_status":"observed",
        "geography_name":"Sydney LHD"})

def test_quarterly_forecast_backtested():
    predictions,metadata=forecast_quarterly_rate(quarterly(),horizon=4)
    assert len(predictions)==4
    assert metadata["benchmark_mae"]>=0
    assert metadata["model"] in {"seasonal_naive","seasonal_linear_trend"}
    assert metadata["n_quarters"]==42
    assert predictions.lower_95.le(predictions.predicted).all()
    assert predictions.period.iloc[0]==pd.Timestamp("2026-04-01")

def test_quarterly_missing_quarter_refuses():
    with pytest.raises(ForecastUnavailable,match="Missing or irregular"):
        forecast_quarterly_rate(quarterly().drop(index=10))

def test_quarterly_count_refuses():
    x=quarterly(); x["value_kind"]="count"
    with pytest.raises(ForecastUnavailable,match="quarterly rates"):
        forecast_quarterly_rate(x)

def test_quarterly_insufficient_data():
    with pytest.raises(ForecastUnavailable,match="At least"):
        forecast_quarterly_rate(quarterly(18))
