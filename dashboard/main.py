import pandas as pd
import geopandas as gpd
import yaml
from sqlalchemy import create_engine
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="GeoHealth LGA Dashboard", layout="wide")
st.title("GeoHealth LGA Dashboard")

st.write("This dashboard will provide interactive maps, charts, and data downloads for LGAs and PHNs.")

# Load DB config
def get_db_engine():
    config_path = Path(__file__).parent.parent / "config" / "db_config.yaml"
    with open(config_path, 'r') as f:
        db_cfg = yaml.safe_load(f)
    engine = create_engine(f"postgresql+psycopg2://{db_cfg['user']}:{db_cfg['password']}@{db_cfg['host']}:{db_cfg['port']}/{db_cfg['database']}")
    return engine

# Query LGA data
def load_lga_data():
    engine = get_db_engine()
    try:
        gdf = gpd.read_postgis("SELECT lga_code, lga_name, geometry FROM lga", engine, geom_col="geometry")
    except Exception:
        # Fallback if geometry is not present
        gdf = pd.read_sql("SELECT lga_code, lga_name FROM lga", engine)
    return gdf

gdf = load_lga_data()

st.subheader("LGA Table")
st.dataframe(gdf)

# Metrics selection and choropleth
metrics_cols = [c for c in gdf.columns if c.endswith("_per_1000") or c.endswith("_count") or c.endswith("_total")]
if metrics_cols:
    metric = st.selectbox("Select metric for choropleth map:", metrics_cols)
else:
    metric = None

if isinstance(gdf, gpd.GeoDataFrame) and "geometry" in gdf.columns and metric:
    st.subheader(f"Choropleth Map: {metric}")
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    fig, ax = plt.subplots(figsize=(8, 6))
    gdf.plot(column=metric, legend=True, ax=ax, cmap="viridis", linewidth=0.25, edgecolor="black")
    ax.set_axis_off()
    st.pyplot(fig)
else:
    if isinstance(gdf, gpd.GeoDataFrame) and "geometry" in gdf.columns:
        st.subheader("LGA Boundaries Map")
        st.map(gdf)

# Download options
st.subheader("Download Data")
st.download_button("Download CSV", gdf.to_csv(index=False), file_name="lga_data.csv", mime="text/csv")
if isinstance(gdf, gpd.GeoDataFrame) and "geometry" in gdf.columns:
    st.download_button("Download GeoJSON", gdf.to_json(), file_name="lga_data.geojson", mime="application/geo+json")
