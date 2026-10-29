"""ABS LGA SEIFA adapter tests: test fixtures are not dashboard analytical data."""
import json
from pathlib import Path
import pandas as pd
import pytest
from etl.abs_seifa import parse_abs_lga_seifa
from etl.build import build

def source():
    return {"adapter":"abs_seifa_lga_2021","id":"abs_seifa_2021_lga",
       "file":"data/raw/geohealth_abs_nsw_lga_seifa_2021.csv",
       "agency":"Australian Bureau of Statistics","source_url":"https://www.abs.gov.au/",
       "geography_type":"LGA","frequency":"census","value_kind":"index",
       "indicator":"ABS SEIFA 2021 LGA","unit":"index"}

def fixture(root:Path):
    raw=root/"data/raw"; raw.mkdir(parents=True)
    records=[]
    for n in range(128):
        r={"lga_code_2021":f"{10050+n:05d}","lga_name_2021":f"Test LGA {n}",
            "geography_type":"LGA","census_2021_population":1000+n,
            "reference_year":2021,"status":"ABS_published_LGA_index"}
        for index in ("irsd","irsad","ier","ieo"):
            r.update({f"{index}_score":950+n/2,
                      f"{index}_national_decile":5,
                      f"{index}_nsw_decile":4,
                      f"{index}_nsw_percentile":50})
        records.append(r)
    special={**records[0],"lga_code_2021":"19399","lga_name_2021":"Unincorporated NSW",
             "geography_type":"special_unincorporated"}
    records.append(special)
    path=raw/"geohealth_abs_nsw_lga_seifa_2021.csv"
    pd.DataFrame(records).to_csv(path,index=False)
    return path

def test_seifa_source_keeps_lga_and_excludes_special(tmp_path):
    result=parse_abs_lga_seifa(fixture(tmp_path),source())
    assert len(result)==128*17
    assert result.geography_type.eq("LGA").all()
    assert result.geography_vintage.eq("2021").all()
    assert result.frequency.eq("census").all()
    assert result.data_status.eq("published_derived").all()
    assert result.indicator_id.nunique()==17
    assert not result.geography_name.str.contains("Unincorporated").any()

def test_seifa_pipeline(tmp_path):
    fixture(tmp_path)
    (tmp_path/"config").mkdir()
    (tmp_path/"config/sources.json").write_text(json.dumps({"sources":[source()]}))
    result=build(tmp_path)
    assert len(result)==2176
    assert (tmp_path/"data/processed/observations.csv").exists()

def test_seifa_bad_geography_refused(tmp_path):
    path=fixture(tmp_path); df=pd.read_csv(path,dtype={"lga_code_2021":str})
    df.loc[0,"geography_type"]="LHD"
    df.to_csv(path,index=False)
    with pytest.raises(ValueError,match="Expected 128"):
        parse_abs_lga_seifa(path,source())
