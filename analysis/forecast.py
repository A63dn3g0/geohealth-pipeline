"""Conservative, interpretable forecasts of observed monthly service counts only.

Backtest-error bands are exploratory, not calibrated prediction intervals.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

MIN_MONTHS = 36

class ForecastUnavailable(ValueError):
    pass

def _seasonal_naive(history: np.ndarray, horizon: int) -> np.ndarray:
    return np.array([history[-12 + (i % 12)] for i in range(horizon)], dtype=float)

def _seasonal_trend(history: np.ndarray, horizon: int) -> np.ndarray:
    t = np.arange(len(history), dtype=float)
    slope = float(np.polyfit(t, history, 1)[0])
    seasonal = history - slope * t
    means = np.array([seasonal[i::12].mean() for i in range(12)])
    return np.array([means[(len(history) + i) % 12] + slope * (len(history) + i) for i in range(horizon)])

def forecast_monthly_counts(data: pd.DataFrame, horizon: int = 12) -> tuple[pd.DataFrame, dict]:
    if horizon not in range(1, 13):
        raise ValueError("Forecast horizon must be 1–12 months")
    required = {"period", "value", "frequency", "value_kind", "data_status"}
    if required - set(data):
        raise ForecastUnavailable("Missing required fields: " + ", ".join(sorted(required - set(data))))
    if not (data.frequency.eq("monthly").all() and data.value_kind.eq("count").all()
            and data.data_status.eq("observed").all()):
        raise ForecastUnavailable("Only observed monthly counts can be forecast, not rates or funding")
    series = data.copy()
    series["period"] = pd.to_datetime(series.period)
    series = series.sort_values("period").reset_index(drop=True)
    if len(series) < MIN_MONTHS:
        raise ForecastUnavailable(f"At least {MIN_MONTHS} months needed; found {len(series)}")
    if series.period.duplicated().any():
        raise ForecastUnavailable("Duplicate periods")
    expected = pd.Series(pd.date_range(series.period.iloc[0], series.period.iloc[-1], freq="MS"))
    if not series.period.equals(expected):
        raise ForecastUnavailable("Missing, irregular or non-month-start dates: do not impute silently")
    y = pd.to_numeric(series.value, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(y).all() or (y < 0).any() or not np.equal(y, np.floor(y)).all():
        raise ForecastUnavailable("Counts must be non-negative finite integers")
    if not np.any(y > 0):
        raise ForecastUnavailable("All-zero series")
    models = {"seasonal_naive": _seasonal_naive, "seasonal_linear_trend": _seasonal_trend}
    residuals = {key: [] for key in models}
    for origin in range(max(24, len(y)-12), len(y)-1):
        h = min(6, len(y)-origin)
        for name, fn in models.items():
            errors = y[origin:origin+h] - np.maximum(0, fn(y[:origin], h))
            residuals[name].extend(errors)
    mae = {name: float(np.mean(np.abs(e))) for name, e in residuals.items()}
    winner = min(mae, key=mae.get)
    pred = np.maximum(0, models[winner](y, horizon))
    bands = np.abs(residuals[winner])
    q80, q95 = np.quantile(bands, [0.8, 0.95])
    dates = pd.date_range(series.period.iloc[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    frame = pd.DataFrame({"period": dates, "predicted": pred,
        "lower_80": np.maximum(0, pred-q80), "upper_80": pred+q80,
        "lower_95": np.maximum(0, pred-q95), "upper_95": pred+q95})
    return frame, {"model": winner, "backtest_mae": mae, "n_months": len(y),
        "interval_method": "Approximate rolling-backtest error bands; not calibrated",
        "forecast_target": "observed monthly service count"}
