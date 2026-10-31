import json
from pathlib import Path
import pandas as pd
import pytest
from etl.build import build, normalize_csv, period_start

def source():
    return {"id": "mh", "file": "data/raw/official.csv", "agency": "NSW Health",
        "source_url": "https://www.healthstats.nsw.gov.au/",
        "geography_type": "LHD", "frequency": "monthly",
        "unit": "presentations", "value_kind": "count",
        "indicator": "Mental health ED", "columns": {"geography": "District", "period": "Month", "value": "Count"}}

def fixture_file(root):
    raw = root / "data/raw"
    raw.mkdir(parents=True)
    pd.DataFrame({"District": ["Sydney LHD", "Hunter New England LHD"],
        "Month": ["2024-01", "2024-01"], "Count": ["20", "<5"]}).to_csv(raw / "official.csv", index=False)

def test_parse_periods():
    assert period_start(pd.Series(["2024-01", "2024-02"]), "monthly").tolist() == ["2024-01-01", "2024-02-01"]
    assert period_start(pd.Series(["2024-Q2"]), "quarterly").tolist() == ["2024-04-01"]

def test_source_build(tmp_path):
    fixture_file(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config/sources.json").write_text(json.dumps({"sources": [source()]}))
    data = build(tmp_path)
    assert len(data) == 1
    assert data.value.iloc[0] == 20
    assert data.data_status.iloc[0] == "observed"
    assert (tmp_path / "data/processed/observations.csv").is_file()
    provenance = json.loads((tmp_path / "data/processed/provenance.json").read_text())
    assert len(provenance["sources"][0]["sha256"]) == 64

def test_reject_duplicate_strata(tmp_path):
    fixture_file(tmp_path)
    raw = tmp_path / "data/raw/official.csv"
    frame = pd.read_csv(raw)
    pd.concat([frame, frame.iloc[[0]]]).to_csv(raw, index=False)
    with pytest.raises(ValueError, match="Repeated"):
        normalize_csv(source(), tmp_path)

def test_missing_file_is_explained(tmp_path):
    with pytest.raises(FileNotFoundError, match="Download"):
        normalize_csv(source(), tmp_path)

def test_rates_do_not_become_counts(tmp_path):
    fixture_file(tmp_path)
    cfg = source()
    cfg["value_kind"] = "rate"
    cfg["unit"] = "per 100,000"
    data = normalize_csv(cfg, tmp_path)
    assert data.value_kind.tolist() == ["rate"]
