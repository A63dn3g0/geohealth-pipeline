"""Smoke-test real Streamlit startup without requiring a database or demo data."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_empty_state_dashboard_starts():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=20).run()
    assert not app.exception
    assert any("GeoHealth NSW" in heading.value for heading in app.title)
    assert len(app.warning) >= 1
