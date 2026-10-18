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
        assert not app.warning
    finally:
        target.unlink(missing_ok=True)
        st.cache_data.clear()
