import pandas as pd
import yaml
from sqlalchemy import create_engine
from fastapi import FastAPI
from pathlib import Path

app = FastAPI(title="GeoHealth LGA API")

def get_db_engine():
    config_path = Path(__file__).parent.parent / "config" / "db_config.yaml"
    with open(config_path, 'r') as f:
        db_cfg = yaml.safe_load(f)
    engine = create_engine(f"postgresql+psycopg2://{db_cfg['user']}:{db_cfg['password']}@{db_cfg['host']}:{db_cfg['port']}/{db_cfg['database']}")
    return engine

@app.get("/")
def root():
    return {"message": "Welcome to the GeoHealth LGA API"}

@app.get("/lga")
def get_lgas():
    engine = get_db_engine()
    df = pd.read_sql("SELECT lga_code, lga_name FROM lga", engine)
    return df.to_dict(orient="records")

@app.get("/crosswalk")
def get_crosswalk():
    engine = get_db_engine()
    df = pd.read_sql("SELECT * FROM lga_phn_crosswalk", engine)
    return df.to_dict(orient="records")

@app.get("/lga/geojson")
def get_lga_geojson():
    engine = get_db_engine()
    try:
        import geopandas as gpd
        gdf = gpd.read_postgis("SELECT lga_code, lga_name, geometry FROM lga", engine, geom_col="geometry")
        return gdf.__geo_interface__
    except Exception as e:
        return {"error": str(e)}
