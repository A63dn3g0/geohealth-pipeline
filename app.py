"""GeoHealth NSW: real public-source dashboard (no database required)."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from analysis.forecast import ForecastUnavailable, forecast_monthly_counts, forecast_quarterly_rate, forecast_annual_rate
from analysis.geography import join_key
from etl.audit_geography import audit_lhd_geojson, GeographyAuditError

ROOT = Path(__file__).resolve().parent
OBSERVATIONS = ROOT / "data/processed/observations.csv"
BOUNDARIES = ROOT / "data/raw/nsw_lhd_boundaries.geojson"


RESOURCE_DIR = ROOT / "data/processed/resources"

@st.cache_data(show_spinner=False)
def load_resources() -> dict[str, pd.DataFrame]:
    names = ("lhd_profiles", "funding_allocations", "ngo_grant_awards",
             "lhd_resource_coverage", "source_register")
    paths = {name: RESOURCE_DIR / (name + ".csv") for name in names}
    if not all(path.is_file() for path in paths.values()):
        return {}
    return {name: pd.read_csv(path) for name, path in paths.items()}

def resource_dashboard(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("NSW LHD population and resources")
    st.caption("15 district profiles; initial FY2025–26 operating allocations and separate "
               "multi-year NGO awards. Missing data does not equal zero.")
    profiles, funding, grants, coverage = (tables[k] for k in (
        "lhd_profiles", "funding_allocations", "ngo_grant_awards", "lhd_resource_coverage"))
    district = st.selectbox("Resource district", sorted(profiles.lhd_short_name.unique()),
                            key="resource_lhd")
    p = profiles.loc[profiles.lhd_short_name.eq(district)].iloc[0]
    c = coverage.loc[coverage.lhd_id.eq(p.lhd_id)].iloc[0]
    population_vintage = (
        str(int(p.population_reference_year)) if pd.notna(p.population_reference_year)
        else "exact reference year unverified"
    )
    st.metric("Reported district population", f"{int(p.population_estimate):,}")
    st.caption(f"Population vintage: {population_vintage}; source: {p.source_url}")
    metrics = [k for k in (
        "aboriginal_and_torres_strait_islander_pct", "born_overseas_pct",
        "speaks_language_other_than_english_pct", "age_70_plus_pct", "age_65_plus_pct",
        "unemployment_pct", "households_with_children_low_income_pct",
        "completed_year_12_or_equivalent_pct", "limited_spoken_english_pct",
        "people_age_65_plus_living_alone_pct", "seifa_irsd_population_weighted_score",
    ) if k in profiles.columns]
    st.dataframe(pd.DataFrame({"indicator": metrics, "value": [p[k] for k in metrics]}),
                 hide_index=True)
    st.info(f"Socioeconomic coverage: {p.socioeconomic_completeness}. "
            "LHD IRSD remains unknown until SA1 geography and population weighting are validated.")
    st.markdown("**FY2025–26 initial operating allocations**")
    selected = funding.loc[funding.lhd_id.eq(p.lhd_id)]
    st.dataframe(selected[["funding_stream", "amount_aud", "allocation_class",
                            "budget_scope", "quality", "source_url"]], hide_index=True)
    st.caption("Full district service budgets, partial MH purchased-service components "
               "and combined unsplit MH+AOD budgets have distinct scopes and must not be summed.")
    st.markdown("**Multi-year NGO AOD hub grant awards**")
    awards = grants.loc[grants.lhd_id.eq(p.lhd_id)]
    if len(awards):
        st.dataframe(awards[["recipient", "awarded_amount_aud", "program_term_years",
                             "attribution_type", "source_url"]], hide_index=True)
    else:
        st.info("No recipient-locality AOD award in this extract; this is not evidence of zero funding.")
    st.warning("Grant awards are multi-year recipient-location associations, not annual expenditure "
               "or verified service catchment. They may overlap other allocations.")
    st.markdown("**All-LHD resource coverage / missingness**")
    st.dataframe(coverage, hide_index=True)
    st.caption("No funding-per-resident or funding-gap ranking: district population reference years "
               "are mixed or unknown, and operating budgets are not residence-attributed expenditure.")
    for title, key in (("District profiles", "lhd_profiles"),
                       ("Operating allocations", "funding_allocations"),
                       ("NGO awards", "ngo_grant_awards"),
                       ("Coverage", "lhd_resource_coverage"),
                       ("Source register", "source_register")):
        frame=tables[key]
        st.download_button("Export " + title + " CSV", frame.to_csv(index=False).encode("utf-8"),
                           file_name="geohealth_"+key+".csv", mime="text/csv",
                           key="download_"+key)

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
        resources = load_resources()
        if resources:
            st.info("The resource profiles are available independently of the outcome files.")
            resource_dashboard(resources)
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
    elif selected.frequency.iloc[0] == "annual":
        span = f"FY{first.year}–{str(first.year+1)[-2:]} to FY{last.year}–{str(last.year+1)[-2:]}"
    else:
        span = f"{first:%b %Y} to {last:%b %Y}"
    st.caption(f"{geography} · {indicator} · {span} · {selected.unit.iloc[0]} ({selected.value_kind.iloc[0]})")
    if selected.value_kind.iloc[0] == "rate":
        if selected.frequency.iloc[0] == "annual":
            st.info("AOD: annual financial-year **age-standardised hospitalisation rates** per 100,000; not presentation counts, distinct people or prevalence. These rates are adjusted to the Australian 2001 reference population.")
        else:
            st.info("Mental-health ED: quarterly **crude** rates per 100,000, not presentation counts or illness prevalence. Crude rates are NOT age-adjusted.")
    if "All LHDs" in selected.geography_name.values:
        st.caption("The published All LHDs aggregate includes suppressed districts and records without an LHD; it is a benchmark, not an average of the displayed districts.")
    if geography == "LHD" and selected.indicator_id.iloc[0] == "healthstats_mh_ed_quarterly_crude_rate":
        st.caption("Mental-health ED source suppresses Far West and Western NSW; no values are imputed.")
    if selected.frequency.iloc[0] == "census":
        st.caption("SEIFA is reported at **2021 LGA geography**, not LHD. Lower IRSD score/decile signifies relatively greater disadvantage. Rankings are ordinal and must not be averaged across areas.")
    if selected.frequency.iloc[0] == "annual":
        st.caption("AOD observations use **financial years (July–June)**, not calendar years. Hospitalisation and ED-presentations measures must not be added or directly equated.")
    resource_tables = load_resources()
    tab_names = ["Overview", "Map", "Jurisdiction", "Trends & forecast", "Funding & resources"]
    if resource_tables:
        tab_names.append("Population & resources")
    tabs = st.tabs(tab_names)
    with tabs[0]:
        latest = selected[(selected.period == last) & (selected.geography_name != "All LHDs")]
        st.metric("Published individual jurisdictions at latest period", len(latest))
        if latest.empty:
            st.warning("No reported local observations for the latest period.")
        st.caption("Values are not summed automatically: indicators can be rates, counts or incomplete coverage.")
        st.plotly_chart(px.bar(latest.sort_values("value", ascending=False),
            x="geography_name", y="value", title=f"Latest period: {last:%b %Y}"),
            use_container_width=True)
    with tabs[1]:
        latest = selected[selected.period == last]
        if geography == "LGA":
            st.info("LGA SEIFA values are available for comparison and ranking; an official 2021 LGA polygon layer is not yet loaded. LHD geometry cannot be used to display LGA scores.")
        else:
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
        census = area_data.frequency.eq("census").all()
        quarterly = (area_data.frequency.eq("quarterly").all() and area_data.value_kind.eq("rate").all())
        annual = (area_data.frequency.eq("annual").all() and area_data.value_kind.eq("rate").all())
        if census:
            horizon = 0
            st.info("No forecast for cross-sectional 2021 Census SEIFA indexes or deciles.")
        elif quarterly:
            horizon = st.select_slider("Forecast horizon (quarters)", options=[1, 2, 4, 8], value=4)
        elif annual:
            horizon = st.select_slider("Forecast horizon (financial years)", options=[1, 2, 3], value=1)
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
            if census:
                raise ForecastUnavailable("SEIFA Census indexes are cross-sectional socioeconomic measures, not a time series.")
            forecast, metadata = (forecast_annual_rate(area_data, horizon=horizon) if annual
                                  else forecast_quarterly_rate(area_data, horizon=horizon) if quarterly
                                  else forecast_monthly_counts(area_data, horizon=horizon))
            figure.add_trace(go.Scatter(x=forecast.period, y=forecast.upper_95,
                line=dict(width=0), showlegend=False, mode="lines"))
            figure.add_trace(go.Scatter(x=forecast.period, y=forecast.lower_95,
                line=dict(width=0), fill="tonexty", fillcolor="rgba(120,120,120,0.2)",
                name="Approximate backtest-error band", mode="lines"))
            figure.add_trace(go.Scatter(x=forecast.period, y=forecast.predicted,
                mode="lines+markers", line=dict(dash="dash"), name="Forecast"))
            st.caption(f"Selected model: {metadata['model']}; rolling-origin MAE: {metadata['backtest_mae']}. {metadata['interval_method']}.")
            st.caption("Forecast error bands are exploratory and not statistically calibrated. Forecasts describe service utilisation, not underlying illness prevalence.")
            if annual:
                st.warning("AOD projections use an old financial-year series (latest FY2023–24). Interpret near-term projections cautiously: changes in practice, coding or public policy can invalidate naive extrapolation.")
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
    if resource_tables:
        with tabs[5]:
            resource_dashboard(resource_tables)
    else:
        st.caption("LHD resource profiles not loaded; run python -m etl.resources with the six original source files.")
    with st.expander("Provenance and interpretation"):
        st.dataframe(selected[["indicator", "agency", "source_url", "unit", "frequency", "data_status"]].drop_duplicates(), hide_index=True)
        st.caption("Service access, capacity, coding and referral changes can alter utilisation independently of underlying population need.")
    st.download_button("Export current indicator (CSV)", selected.to_csv(index=False).encode("utf-8"),
                       file_name="geohealth_export.csv", mime="text/csv")

if __name__ == "__main__":
    main()
