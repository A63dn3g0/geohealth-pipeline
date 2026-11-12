"""Smoke-test real Streamlit startup without requiring a database or demo data."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_empty_state_dashboard_starts():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=20).run()
    assert not app.exception
    assert any("GeoHealth NSW" in heading.value for heading in app.title)
    assert len(app.warning) >= 1


def test_quarterly_lhd_dashboard_with_temporary_fixture():
    """Exercise the real quarterly-rate UI path; no test data committed as product data."""
    import pandas as pd
    import streamlit as st
    root = Path(__file__).resolve().parents[1]
    target = root / "data/processed/observations.csv"
    assert not target.exists(), "Tests must never overwrite loaded real government observations"
    periods = pd.date_range("2018-01-01", periods=32, freq="QS")
    rows = []
    for jurisdiction, offset in [("Sydney LHD", 0.0), ("All LHDs", 90.0)]:
        for i, period in enumerate(periods):
            value = 220 + offset + (i % 4) * 6 + i * 0.5
            rows.append({
                "geography_type": "LHD", "geography_name": jurisdiction,
                "indicator_id": "test_quarterly_rate",
                "indicator": "Test-only quarterly service rate",
                "period": period.strftime("%Y-%m-%d"), "value": value,
                "lower_ci_95": value - 10, "upper_ci_95": value + 10,
                "unit": "presentations per 100,000 population",
                "value_kind": "rate", "frequency": "quarterly",
                "source_id": "test_quarterly_rate", "source_url": "https://www.healthstats.nsw.gov.au/",
                "agency": "NSW Ministry of Health", "data_status": "observed",
            })
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(target, index=False)
        st.cache_data.clear()
        app = AppTest.from_file(root / "app.py", default_timeout=25).run()
        assert not app.exception
        assert len(app.tabs) == 5
        assert len(app.warning) == 1  # Explicit commercial licensing restriction
    finally:
        target.unlink(missing_ok=True)
        st.cache_data.clear()


def test_resource_panel_with_disposable_files():
    """Streamlit can render resource tab and exports while keeping source layers separate."""
    import pandas as pd
    import streamlit as st
    root=Path(__file__).resolve().parents[1]
    source=root/"data/processed/observations.csv"
    directory=root/"data/processed/resources"
    assert not source.exists() and not directory.exists(), "Do not overwrite actual data"
    files=[]
    try:
        directory.mkdir(parents=True,exist_ok=True)
        observations=[]
        for i,date in enumerate(pd.date_range("2018-01-01",periods=28,freq="QS")):
            observations.append(dict(geography_type="LHD",geography_name="Sydney LHD",
                indicator_id="test_mh",indicator="Test MH ED",period=date,
                value=100+i,frequency="quarterly",value_kind="rate",
                data_status="observed",unit="per 100,000",
                agency="Test",source_url="https://example.org"))
        pd.DataFrame(observations).to_csv(source,index=False)
        names={
            "lhd_profiles":pd.DataFrame([{
                "lhd_id":"NSW_LHD_SYDNEY","lhd_short_name":"Sydney",
                "population_estimate":740000,"population_reference_year":pd.NA,
                "socioeconomic_completeness":"awaiting_LHD_aggregate_from_SA1_data",
                "source_url":"https://example.org/pop",
                "aboriginal_and_torres_strait_islander_pct":pd.NA,
                "seifa_irsd_population_weighted_score":pd.NA}]),
            "funding_allocations":pd.DataFrame([{
                "lhd_id":"NSW_LHD_SYDNEY","funding_stream":"MH",
                "amount_aud":179814000,"allocation_class":"full_separate_operating",
                "budget_scope":"separate_district_service_budget","quality":"source_verified",
                "source_url":"https://example.org/budget"}]),
            "ngo_grant_awards":pd.DataFrame([{
                "lhd_id":"NSW_LHD_SYDNEY","recipient":"Test recipient",
                "awarded_amount_aud":2400000,"program_term_years":4,
                "attribution_type":"location_of_recipient_as_published_NOT_verified_full_service_catchment",
                "source_url":"https://example.org/grants"}]),
            "lhd_resource_coverage":pd.DataFrame([{
                "lhd_id":"NSW_LHD_SYDNEY","lhd_short_name":"Sydney",
                "population_estimate":740000,"mh_allocation_class":"full_separate_operating",
                "aod_allocation_class":"not_disclosed","funding_per_resident_eligible":False}]),
            "source_register":pd.DataFrame([{
                "dataset":"test","title":"Test", "url":"https://example.org"}]),
        }
        for name,frame in names.items():
            path=directory/(name+".csv")
            frame.to_csv(path,index=False)
            files.append(path)
        st.cache_data.clear()
        app=AppTest.from_file(root/"app.py",default_timeout=25).run()
        assert not app.exception
        assert len(app.tabs)==6
        assert any("population" in text.value.lower() for text in app.subheader)
    finally:
        source.unlink(missing_ok=True)
        for path in files:
            path.unlink(missing_ok=True)
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
        st.cache_data.clear()
