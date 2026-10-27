"""GeoHealth NSW: real public-source dashboard (no database required)."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from analysis.forecast import ForecastUnavailable, forecast_monthly_counts, forecast_quarterly_rate
from analysis.geography import join_key
from etl.audit_geography import audit_lhd_geojson, GeographyAuditError

ROOT = Path(__file__).resolve().parent
OBSERVATIONS = ROOT / "data/processed/observations.csv"
BOUNDARIES = ROOT / "data/raw/nsw_lhd_boundaries.geojson"

@st.cache_data(show_spinner=False)
def load_observations() -> pd.DataFrame:
    if not OBSERVATIONS.is_file():
        return pd.DataFrame()
    data = pd.read_csv(OBSERVATIONS)
    data["period"] = pd.to_datetime(data["period"])
    return data

@st.cache_data(show_spinner=False)
def load_geojson() -> dict | None:
    if BOUNDARIES.is_file():
        data = json.loads(BOUNDARIES.read_text(encoding="utf-8"))
        if data.get("type") == "FeatureCollection":
            return data
    return None

def draw_map(latest: pd.DataFrame, boundaries: dict | None) -> None:
    if boundaries is None:
        st.info("Download official LHD geometry: python -m etl.download --boundaries")
        return
    if not latest.geography_type.eq("LHD").all():
        st.info("Map currently supports LHD source observations; no PHN/LGA allocation is inferred.")
        return
    try:
        audit_lhd_geojson(boundaries)
    except GeographyAuditError as error:
        st.error(f"Map withheld: official boundary integrity check failed: {error}")
        return
    geo = json.loads(json.dumps(boundaries))
    for feature in geo["features"]:
        feature["properties"]["JOIN_KEY"] = join_key(feature["properties"].get("lhd_name", ""))
    values = latest[latest.geography_name != "All LHDs"].copy()
    if values.empty:
        st.info("All LHDs is a published benchmark, not a separate geographic polygon.")
        return
    values["JOIN_KEY"] = values.geography_name.map(join_key)
    keys = {f["properties"]["JOIN_KEY"] for f in geo["features"]}
    not_matched = sorted(set(values.loc[~values.JOIN_KEY.isin(keys), "geography_name"]))
    if not_matched:
        st.warning("Missing geography matches (not reassigned): " + ", ".join(not_matched))
    values = values[values.JOIN_KEY.isin(keys)]
    if values.empty:
        return
    fig = px.choropleth(values, geojson=geo, locations="JOIN_KEY",
        featureidkey="properties.JOIN_KEY", color="value",
        hover_name="geography_name", title="Latest source-observed period")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=560)
    st.plotly_chart(fig, use_container_width=True)

def main() -> None:
    st.set_page_config(page_title="GeoHealth NSW", layout="wide")
    st.title("GeoHealth NSW")
    st.caption("Public-source utilisation dashboard · observed service activity is not illness prevalence")
    st.warning("Data-use restriction: HealthStats NSW prohibits commercial use or resale of its downloadable data. This dashboard is for internal research/testing only until written permission or a suitable licence is obtained. See docs/DATA_LICENSING.md.")
    data = load_observations()
    if data.empty:
        st.warning("No verified government observations loaded. GeoHealth does not invent analytical data.")
        st.markdown("Place the unchanged quarterly **NSW HealthStats LHD.csv** export in `data/raw/NSW_HealthStats_LHD.csv`, then run `python -m etl.build` and refresh the dashboard. The source is already configured in `config/sources.json`. The export reports LHD **quarterly crude rates per 100,000**, not monthly counts, despite its title. See [HealthStats NSW](https://www.healthstats.nsw.gov.au/r/135943) for the source.")
        st.info("Optional map: python -m etl.download --boundaries")
        return
    geography = st.sidebar.selectbox("Jurisdiction type", sorted(data.geography_type.unique()))
    subset = data[data.geography_type == geography]
    indicator_names = dict(zip(subset.indicator, subset.indicator_id))
    indicator = st.sidebar.selectbox("Indicator", sorted(indicator_names))
    selected = subset[subset.indicator_id == indicator_names[indicator]].copy()
    area = st.sidebar.selectbox("Jurisdiction", sorted(selected.geography_name.unique()))
    first, last = selected.period.min(), selected.period.max()
    if selected.frequency.iloc[0] == "quarterly":
        span = f"{first.year}-Q{first.quarter} to {last.year}-Q{last.quarter}"
    else:
        span = f"{first:%b %Y} to {last:%b %Y}"
    st.caption(f"{geography} · {indicator} · {span} · {selected.unit.iloc[0]} ({selected.value_kind.iloc[0]})")
    if selected.value_kind.iloc[0] == "rate":
        st.info("These are source-published crude rates per 100,000, NOT presentation counts or mental illness prevalence. Crude rates are not adjusted for age differences.")
    if "All LHDs" in selected.geography_name.values:
        st.caption("The published All LHDs aggregate includes suppressed districts and records without an LHD; it is a benchmark, not an average of the displayed districts.")
    if geography == "LHD":
        st.caption("Far West and Western NSW LHDs are suppressed in this export. Values are not imputed.")
    tabs = st.tabs(["Overview", "Map", "Jurisdiction", "Trends & forecast", "Funding & resources"])
    with tabs[0]:
        latest = selected[(selected.period == last) & (selected.geography_name != "All LHDs")]
        st.metric("Published individual jurisdictions at latest period", len(latest))
        st.caption("Values are not summed automatically: indicators can be rates, counts or incomplete coverage.")
        st.plotly_chart(px.bar(latest.sort_values("value", ascending=False),
            x="geography_name", y="value", title=f"Latest period: {last:%b %Y}"),
            use_container_width=True)
    with tabs[1]:
        latest = selected[selected.period == last]
        draw_map(latest, load_geojson())
    area_data = selected[selected.geography_name == area].sort_values("period")
    with tabs[2]:
        st.subheader(area)
        options=sorted(selected.geography_name.unique())
        comparison=st.multiselect("Compare LHDs", options, default=[area], max_selections=5)
        compare_data=selected[selected.geography_name.isin(comparison)]
        if not compare_data.empty:
            st.plotly_chart(px.line(compare_data, x="period", y="value",
                color="geography_name", labels={"value":selected.unit.iloc[0]}, markers=False),
                use_container_width=True)
        fields=["period","value","unit"]
        if {"lower_ci_95","upper_ci_95"}.issubset(area_data.columns):
            fields += ["lower_ci_95","upper_ci_95"]
            st.caption("Lower/upper 95% CI columns describe *observed* rates, not forecasts.")
        st.dataframe(area_data[fields], hide_index=True)
    with tabs[3]:
        quarterly = (area_data.frequency.eq("quarterly").all() and area_data.value_kind.eq("rate").all())
        if quarterly:
            horizon = st.select_slider("Forecast horizon (quarters)", options=[1, 2, 4, 8], value=4)
        else:
            horizon = st.select_slider("Forecast horizon (months)", options=[3, 6, 12], value=12)
        figure = go.Figure()
        if {"lower_ci_95","upper_ci_95"}.issubset(area_data.columns):
            figure.add_trace(go.Scatter(x=area_data.period, y=area_data.upper_ci_95,
                mode="lines", line=dict(width=0), showlegend=False))
            figure.add_trace(go.Scatter(x=area_data.period, y=area_data.lower_ci_95,
                mode="lines", line=dict(width=0), fill="tonexty",
                fillcolor="rgba(90,145,180,0.16)", name="Published 95% CI (observed)"))
        figure.add_trace(go.Scatter(x=area_data.period, y=area_data.value,
            name="Observed", mode="lines+markers"))
        try:
            forecast, metadata = (forecast_quarterly_rate(area_data, horizon=horizon) if quarterly
                                  else forecast_monthly_counts(area_data, horizon=horizon))
            figure.add_trace(go.Scatter(x=forecast.period, y=forecast.upper_95,
                line=dict(width=0), showlegend=False, mode="lines"))
            figure.add_trace(go.Scatter(x=forecast.period, y=forecast.lower_95,
                line=dict(width=0), fill="tonexty", fillcolor="rgba(120,120,120,0.2)",
                name="Approximate backtest-error band", mode="lines"))
            figure.add_trace(go.Scatter(x=forecast.period, y=forecast.predicted,
                mode="lines+markers", line=dict(dash="dash"), name="Forecast"))
            st.caption(f"Selected model: {metadata['model']}; rolling-origin MAE: {metadata['backtest_mae']}. {metadata['interval_method']}.")
            st.caption("Forecast error bands are exploratory and not statistically calibrated. Forecasts concern utilisation rates, not underlying mental-health prevalence.")
            st.dataframe(forecast, hide_index=True)
        except ForecastUnavailable as error:
            st.info("Forecast withheld: " + str(error))
        st.plotly_chart(figure, use_container_width=True)
    with tabs[4]:
        funding = data[(data.geography_type == geography) & (data.value_kind == "amount")]
        if funding.empty:
            st.info("No verified geographically attributable funding data loaded. State budget totals will not be redistributed without a valid method.")
        else:
            st.dataframe(funding.sort_values("period", ascending=False), hide_index=True)
            st.warning("Check original source and funding/allocation status before policy comparisons.")
    with st.expander("Provenance and interpretation"):
        st.dataframe(selected[["indicator", "agency", "source_url", "unit", "frequency", "data_status"]].drop_duplicates(), hide_index=True)
        st.caption("Service access, capacity, coding and referral changes can alter utilisation independently of underlying population need.")
    st.download_button("Export current indicator (CSV)", selected.to_csv(index=False).encode("utf-8"),
                       file_name="geohealth_export.csv", mime="text/csv")

if __name__ == "__main__":
    main()
