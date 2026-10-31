import numpy as np
import pandas as pd
import pytest
from analysis.forecast import ForecastUnavailable, forecast_monthly_counts

def series(n=60, kind="count"):
    return pd.DataFrame({
        "period": pd.date_range("2020-01-01", periods=n, freq="MS"),
        "value": np.array([100 + 3*(i % 12) + i for i in range(n)]),
        "frequency": "monthly", "value_kind": kind, "data_status": "observed"
    })

def test_rolling_forecast():
    frame, meta = forecast_monthly_counts(series(), 12)
    assert len(frame) == 12
    assert (frame.lower_95 <= frame.predicted).all()
    assert (frame.upper_95 >= frame.predicted).all()
    assert meta["model"] in ("seasonal_naive", "seasonal_linear_trend")

def test_not_enough_history():
    with pytest.raises(ForecastUnavailable, match="At least"):
        forecast_monthly_counts(series(24))

def test_rates_not_forecast():
    with pytest.raises(ForecastUnavailable, match="monthly counts"):
        forecast_monthly_counts(series(kind="rate"))

def test_gap_rejected():
    with pytest.raises(ForecastUnavailable, match="Missing"):
        forecast_monthly_counts(series().drop(index=10))
