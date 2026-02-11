def print_postgres_schema(user, password, host, port, db):
    from sqlalchemy import create_engine
    try:
        from sqlalchemy import text
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
        sql = '''SELECT table_schema, table_name, column_name, data_type
                 FROM information_schema.columns
                 ORDER BY table_schema, table_name, ordinal_position;'''
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            logger.info("Schema for database:")
            for row in result:
                logger.info(row)
    except Exception as e:
        logger.error(f"Failed to query database schema: {e}")
#!/usr/bin/env python3
"""
GeoHealth LGA Pipeline (Enhanced)
---------------------------------
Features:
1) Pre-filled config with specific ABS/AIHW/PHN dataset placeholders.
2) PHN↔LGA crosswalk via spatial intersection with area weights (optional).
3) Derived per-capita rate computation from raw counts + population.
4) Demo mode that synthesizes counts + funding, then derives rates.

Dependencies:
    pip install pandas geopandas pyogrio shapely pyyaml numpy matplotlib

Run:
    python geohealth_pipeline.py --config geohealth_config.yaml
    python geohealth_pipeline.py --demo
"""

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import yaml

import matplotlib.pyplot as plt
import logging

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("geohealth_pipeline")


# ---------------------------- Utilities ----------------------------

# --- PostgreSQL/PostGIS integration ---
from sqlalchemy import create_engine



def read_lga_from_postgis(engine, table="geohealth_lga"):
    import geopandas as gpd
    sql = f"SELECT * FROM {table}"
    return gpd.read_postgis(sql, engine, geom_col="geometry")

def write_lga_to_postgis(gdf, engine, table="geohealth_lga"):
    gdf.to_postgis(table, engine, if_exists="replace", index=False)

def get_postgis_engine(user, password, host, port, db):
    import os
    # Prefer password argument, else fall back to PGPASSWORD env var
    if not password:
        password = os.environ.get("PGPASSWORD", "")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def normalise_lga_name(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.upper()
         .str.normalize("NFKD")
         .str.encode("ascii", errors="ignore")
         .str.decode("ascii")
         .str.replace(r"[^A-Z0-9\s\-]", "", regex=True)
         .str.replace(r"\s+", " ", regex=True)
         .str.strip()
    )


def ensure_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def zscore(series: pd.Series) -> pd.Series:
    mu = series.mean()
    sigma = series.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - mu) / sigma


# ---------------------------- Config structures ----------------------------

@dataclass
class DatasetConfig:
    name: str
    path: str
    lga_field: str
    value_fields: List[str]
    join_on: str = "code"  # "code" or "name"


@dataclass
class GeographyConfig:
    lga_shapefile: str
    lga_name_field: str
    lga_code_field: str
    phn_shapefile: Optional[str] = None
    phn_name_field: Optional[str] = None
    phn_code_field: Optional[str] = None


@dataclass
class PopulationConfig:
    dataset_name: str                 # name of dataset in datasets[] providing population
    population_field: str = "population"


@dataclass
class CrosswalkConfig:
    lga_to_phn_csv: Optional[str] = None
    phn_to_lga_csv: Optional[str] = None


@dataclass
class OutputConfig:
    geopackage: str
    layer_name: str = "geohealth_lga"
    csv: Optional[str] = None
    quickmap_png: Optional[str] = None
    choropleth_field: Optional[str] = None



@dataclass
class PipelineConfig:
    output_dir: str = "./outputs"
    geography: Optional[GeographyConfig] = None
    datasets: List[DatasetConfig] = field(default_factory=list)
    transforms: Dict = field(default_factory=dict)
    population: Optional[PopulationConfig] = None
    derived_rates: List[Dict] = field(default_factory=list)
    crosswalk: Optional[CrosswalkConfig] = None
    output: Optional[OutputConfig] = None
    postgis_read: Optional[dict] = None
    postgis_write: Optional[dict] = None


# ---------------------------- Demo generators ----------------------------

def demo_geography() -> gpd.GeoDataFrame:
    polys, names, codes = [], [], []
    idx = 0
    for i in range(2):
        for j in range(3):
            idx += 1
            x0, y0 = j*1.1, i*1.1
            polys.append(Polygon([(x0, y0), (x0+1, y0), (x0+1, y0+1), (x0, y0+1)]))
            names.append(f"Demo LGA {idx}")
            codes.append(f"000{idx:02d}")
    gdf = gpd.GeoDataFrame({"LGA_NAME25": names, "LGA_CODE25": codes}, geometry=polys, crs="EPSG:4326")
    return gdf


def demo_metrics(lga_codes, lga_names) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = len(lga_codes)
    df = pd.DataFrame({
        "LGA_CODE": lga_codes,
        "LGA_NAME": lga_names,
        "population": rng.integers(10000, 150000, size=n),
    })
    base = np.linspace(0.5, 2.0, n)
    df["mh_any_12m_count"] = (base * df["population"] * 0.15).round().astype(int)
    df["aod_treatment_count"] = (base[::-1] * df["population"] * 0.03).round().astype(int)
    df["mh_funding_total"] = (df["population"] * (180 + 10*base)).round(2)
    df["aod_funding_total"] = (df["population"] * (120 + 7*base)).round(2)
    return df


# ---------------------------- Loaders & Joiners ----------------------------

def load_config(path: Path) -> PipelineConfig:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    geography = GeographyConfig(**cfg["geography"])
    datasets = [DatasetConfig(**d) for d in cfg.get("datasets", [])]
    output = OutputConfig(**cfg["output"])
    population = None
    if "population" in cfg and cfg["population"]:
        population = PopulationConfig(**cfg["population"])
    crosswalk = None
    if "crosswalk" in cfg and cfg["crosswalk"]:
        crosswalk = CrosswalkConfig(**cfg["crosswalk"])

    return PipelineConfig(
        output_dir=cfg.get("output_dir", "./outputs"),
        geography=geography,
        datasets=datasets,
        transforms=cfg.get("transforms", {}),
        population=population,
        derived_rates=cfg.get("derived_rates", []),
        crosswalk=crosswalk,
        output=output,
    )


def load_geography(geo_cfg: GeographyConfig, demo: bool=False) -> gpd.GeoDataFrame:
    if demo:
        gdf = demo_geography()
        gdf["__LGA_NAME_NORM"] = normalise_lga_name(gdf[geo_cfg.lga_name_field])
        return gdf
    path = Path(geo_cfg.lga_shapefile)
    if not path.exists():
        raise FileNotFoundError(f"LGA shapefile not found at {path}")
    gdf = gpd.read_file(path)
    gdf["__LGA_NAME_NORM"] = normalise_lga_name(gdf[geo_cfg.lga_name_field])
    return gdf


def load_dataset(dcfg: DatasetConfig) -> pd.DataFrame:
    path = Path(dcfg.path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset '{dcfg.name}' not found at {path}")
    df = pd.read_csv(path)
    # Ensure we always pass a Series to normalise_lga_name
    if dcfg.lga_field in df.columns:
        df["__LGA_NAME_NORM"] = normalise_lga_name(df[dcfg.lga_field])
    else:
        df["__LGA_NAME_NORM"] = pd.Series(["" for _ in range(len(df))], index=df.index)
    return df


def join_all(gdf: gpd.GeoDataFrame, geo_cfg: GeographyConfig, datasets: List[DatasetConfig]) -> gpd.GeoDataFrame:
    merged = gdf.copy()
    for dcfg in datasets:
        df = load_dataset(dcfg)
        if dcfg.join_on == "code":
            # Ensure both join columns are string type for safe merge
            merged[geo_cfg.lga_code_field] = merged[geo_cfg.lga_code_field].astype(str)
            df[dcfg.lga_field] = df[dcfg.lga_field].astype(str)
            merged = merged.merge(
                df[[dcfg.lga_field] + dcfg.value_fields],
                left_on=geo_cfg.lga_code_field,
                right_on=dcfg.lga_field,
                how="left",
                suffixes=("", f"__{dcfg.name}")
            )
        elif dcfg.join_on == "name":
            merged["__LGA_NAME_NORM"] = merged["__LGA_NAME_NORM"].astype(str)
            df["__LGA_NAME_NORM"] = df["__LGA_NAME_NORM"].astype(str)
            merged = merged.merge(
                df[["__LGA_NAME_NORM"] + dcfg.value_fields],
                on="__LGA_NAME_NORM",
                how="left",
                suffixes=("", f"__{dcfg.name}")
            )
        else:
            raise ValueError(f"join_on must be 'code' or 'name' for dataset {dcfg.name}")
    return merged


# ---------------------------- Crosswalks ----------------------------

def build_crosswalks(lga_gdf: gpd.GeoDataFrame, cfg: GeographyConfig, crosswalk_cfg: CrosswalkConfig):
    """Create area-weighted crosswalk tables between LGA and PHN boundaries."""
    if not cfg.phn_shapefile:
        return None, None

    phn_path = Path(cfg.phn_shapefile)
    if not phn_path.exists():
        raise FileNotFoundError(f"PHN shapefile not found at {phn_path}")

    phn = gpd.read_file(phn_path)
    # Reproject to an equal-area CRS for stable area weights (Australian Albers)
    target_crs = "EPSG:3577"
    lga = lga_gdf.to_crs(target_crs)
    phn = phn.to_crs(target_crs)

    # Spatial intersection
    inter = gpd.overlay(lga[[cfg.lga_code_field, cfg.lga_name_field, "geometry"]],
                        phn[[cfg.phn_code_field or "PHN_CODE", cfg.phn_name_field or "PHN_NAME", "geometry"]],
                        how="intersection")

    inter["area"] = inter.geometry.area

    # LGA totals
    lga_area = inter.groupby(cfg.lga_code_field)["area"].sum().rename("lga_area_total")
    inter = inter.merge(lga_area, left_on=cfg.lga_code_field, right_index=True, how="left")
    inter["weight_lga_to_phn"] = inter["area"] / inter["lga_area_total"]

    # PHN totals
    phn_key = cfg.phn_code_field or "PHN_CODE"
    phn_area = inter.groupby(phn_key)["area"].sum().rename("phn_area_total")
    inter = inter.merge(phn_area, left_on=phn_key, right_index=True, how="left")
    inter["weight_phn_to_lga"] = inter["area"] / inter["phn_area_total"]

    # Export crosswalks
    if crosswalk_cfg.lga_to_phn_csv:
        out1 = Path(crosswalk_cfg.lga_to_phn_csv)
        ensure_dir(out1)
        inter[[cfg.lga_code_field, cfg.lga_name_field, phn_key, (cfg.phn_name_field or "PHN_NAME"), "weight_lga_to_phn"]]\
            .rename(columns={phn_key: "PHN_CODE"})\
            .to_csv(out1, index=False)

    if crosswalk_cfg.phn_to_lga_csv:
        out2 = Path(crosswalk_cfg.phn_to_lga_csv)
        ensure_dir(out2)
        inter[[phn_key, (cfg.phn_name_field or "PHN_NAME"), cfg.lga_code_field, cfg.lga_name_field, "weight_phn_to_lga"]]\
            .rename(columns={phn_key: "PHN_CODE"})\
            .to_csv(out2, index=False)

    return inter, phn


# ---------------------------- Transforms & Rates ----------------------------

def apply_transforms(gdf: gpd.GeoDataFrame, transforms: Dict) -> gpd.GeoDataFrame:
    for col in transforms.get("zscore_fields", []):
        if col in gdf.columns:
            gdf[f"{col}_z"] = zscore(gdf[col])
    return gdf


def compute_derived_rates(gdf: gpd.GeoDataFrame, population_field: str, derived_specs: List[Dict]) -> gpd.GeoDataFrame:
    if population_field not in gdf.columns:
        return gdf
    pop = gdf[population_field].replace(0, np.nan)
    for spec in derived_specs:
        num = spec.get("numerator")
        per = spec.get("per", population_field)
        out = spec.get("as")
        scale = spec.get("per_k", 1000)  # default per 1,000
        if not num or not out:
            continue
        denom = gdf[per].replace(0, np.nan) if per in gdf.columns else pop
        if num in gdf.columns:
            gdf[out] = (gdf[num] / denom) * scale
    return gdf


# ---------------------------- Export ----------------------------

def export_products(gdf: gpd.GeoDataFrame, out_cfg: OutputConfig):
    if out_cfg.geopackage:
        gpkg_path = Path(out_cfg.geopackage)
        ensure_dir(gpkg_path)
        gdf.to_file(gpkg_path, layer=out_cfg.layer_name, driver="GPKG")

    if out_cfg.csv:
        csv_path = Path(out_cfg.csv)
        ensure_dir(csv_path)
        cols = [c for c in gdf.columns if c != "geometry"]
        gdf[cols].to_csv(csv_path, index=False)

    if out_cfg.quickmap_png and out_cfg.choropleth_field and out_cfg.choropleth_field in gdf.columns:
        png_path = Path(out_cfg.quickmap_png)
        ensure_dir(png_path)
        fig, ax = plt.subplots(figsize=(8, 6))
        gdf.plot(column=out_cfg.choropleth_field, legend=True, ax=ax, linewidth=0.25, edgecolor="black")
        ax.set_title(f"Choropleth: {out_cfg.choropleth_field}")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(png_path, dpi=150)
        plt.close(fig)


# ---------------------------- Pipeline ----------------------------

def run_pipeline(cfg: PipelineConfig, demo: bool=False):

    # --- Optional: Read from PostGIS if requested ---
    postgis_read = getattr(cfg, 'postgis_read', None)
    if isinstance(postgis_read, dict):
        logger.info("Reading LGA layer from PostGIS...")
        try:
            engine = get_postgis_engine(
                postgis_read.get('user'),
                postgis_read.get('password'),
                postgis_read.get('host'),
                postgis_read.get('port'),
                postgis_read.get('db')
            )
            lga_gdf = read_lga_from_postgis(engine, table=postgis_read.get('table', 'geohealth_lga'))
        except Exception as e:
            logger.error(f"Failed to read from PostGIS: {e}")
            raise
    else:
        # Geography
        if not cfg.geography:
            raise ValueError("Geography config is required.")
        lga_gdf = load_geography(cfg.geography, demo=demo)

    # Demo synthetic metrics
    if demo:
        if not cfg.geography:
            raise ValueError("Geography config is required for demo mode.")
        code_field = getattr(cfg.geography, 'lga_code_field', None)
        name_field = getattr(cfg.geography, 'lga_name_field', None)
        if not code_field or not name_field:
            raise ValueError("lga_code_field and lga_name_field are required in geography config for demo mode.")
        demo_df = demo_metrics(
            lga_gdf[code_field].tolist(),
            lga_gdf[name_field].tolist()
        )
        lga_gdf = lga_gdf.merge(demo_df, left_on=code_field, right_on="LGA_CODE", how="left")

    # Join external datasets
    if cfg.datasets:
        if not cfg.geography:
            raise ValueError("Geography config is required for joining datasets.")
        lga_gdf = join_all(lga_gdf, cfg.geography, cfg.datasets)

    # Derived rates
    population_field = None
    if cfg.population:
        population_field = cfg.population.population_field
    if population_field:
        lga_gdf = compute_derived_rates(lga_gdf, population_field, cfg.derived_rates)

    # Z-scores
    lga_gdf = apply_transforms(lga_gdf, cfg.transforms)

    # Crosswalks
    if cfg.crosswalk and cfg.geography and getattr(cfg.geography, 'phn_shapefile', None):
        build_crosswalks(lga_gdf, cfg.geography, cfg.crosswalk)


    # Export
    if cfg.output:
        export_products(lga_gdf, cfg.output)

    # --- Optional: Write to PostGIS if requested ---
    postgis_write = getattr(cfg, 'postgis_write', None)
    if isinstance(postgis_write, dict):
        logger.info("Writing LGA layer to PostGIS...")
        try:
            engine = get_postgis_engine(
                postgis_write.get('user'),
                postgis_write.get('password'),
                postgis_write.get('host'),
                postgis_write.get('port'),
                postgis_write.get('db')
            )
            write_lga_to_postgis(lga_gdf, engine, table=postgis_write.get('table', 'geohealth_lga'))
        except Exception as e:
            logger.error(f"Failed to write to PostGIS: {e}")
            raise

    return lga_gdf


# ---------------------------- CLI ----------------------------

def main():
    parser = argparse.ArgumentParser(
        description="""
        GeoHealth LGA Pipeline
        ---------------------
        Integrate, transform, and export Australian health and geography data at the LGA level.
        Supports file and PostGIS workflows, demo mode, and config-driven operation.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--config", type=str, help="Path to YAML config file. If omitted, will auto-detect common locations.")
    parser.add_argument("--demo", action="store_true", help="Run with synthetic demo data (no external files required)")
    parser.add_argument("--read-postgis", action="store_true", help="Read LGA layer from PostGIS instead of file (requires connection options)")
    parser.add_argument("--write-postgis", action="store_true", help="Write LGA layer to PostGIS after processing")
    parser.add_argument("--pg-user", type=str, default="postgres", help="Postgres username")
    parser.add_argument("--pg-password", type=str, default="postgres", help="Postgres password")
    parser.add_argument("--pg-host", type=str, default="localhost", help="Postgres host")
    parser.add_argument("--pg-port", type=int, default=5432, help="Postgres port")
    parser.add_argument("--pg-db", type=str, default="postgres", help="Postgres database name")
    parser.add_argument("--pg-table", type=str, default="geohealth_lga", help="PostGIS table name")
    parser.add_argument("--show-db-schema", action="store_true", help="Print the schema of the PostgreSQL database and exit")
    args = parser.parse_args()

    if args.show_db_schema:
        print_postgres_schema(args.pg_user, args.pg_password, args.pg_host, args.pg_port, args.pg_db)
        return

    if not args.config and not args.demo:
        logger.error("No config file provided and demo mode not selected.")
        logger.error("Tip: Use --config path/to/config.yaml or --demo for synthetic data.")
        parser.print_help()
        raise SystemExit(1)

    import os
    def find_config_file():
        candidates = [
            "geohealth_config.yaml",
            os.path.join("configs", "geohealth_config.yaml"),
            os.path.join("config", "geohealth_config.yaml"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                logger.info(f"Auto-detected config file: {c}")
                return c
        logger.warning("No config file found. Running in demo mode.")
        return None

    config_path = args.config or find_config_file()
    try:
        if config_path:
            logger.info(f"Using config file: {config_path}")
            cfg = load_config(Path(config_path))
        else:
            logger.warning("No config file found. Running in demo mode with synthetic data.")
            cfg = PipelineConfig(
                output_dir="./outputs",
                geography=GeographyConfig(
                    lga_shapefile="(demo)",
                    lga_name_field="LGA_NAME_2023",
                    lga_code_field="LGA_CODE_2023",
                ),
                datasets=[],
                population=PopulationConfig(dataset_name="(demo)", population_field="population"),
                derived_rates=[
                    {"numerator": "mh_any_12m_count", "as": "mh_any_12m_rate_per_1000", "per_k": 1000},
                    {"numerator": "aod_treatment_count", "as": "aod_treatment_rate_per_1000", "per_k": 1000},
                ],
                transforms={"zscore_fields": ["mh_any_12m_rate_per_1000", "aod_treatment_rate_per_1000"]},
                crosswalk=CrosswalkConfig(
                    lga_to_phn_csv="./outputs/crosswalk_lga_to_phn.csv",
                    phn_to_lga_csv="./outputs/crosswalk_phn_to_lga.csv",
                ),
                output=OutputConfig(
                    geopackage="./outputs/geohealth.gpkg",
                    layer_name="geohealth_lga",
                    csv="./outputs/geohealth_lga.csv",
                    quickmap_png="./outputs/geohealth_quickmap.png",
                    choropleth_field="mh_any_12m_rate_per_1000",
                )
            )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Check your file paths in the config YAML.")
        raise
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

    # Attach PostGIS config if requested
    if args.read_postgis:
        cfg.postgis_read = {
            'user': args.pg_user,
            'password': args.pg_password,
            'host': args.pg_host,
            'port': args.pg_port,
            'db': args.pg_db,
            'table': args.pg_table
        }
    if args.write_postgis:
        cfg.postgis_write = {
            'user': args.pg_user,
            'password': args.pg_password,
            'host': args.pg_host,
            'port': args.pg_port,
            'db': args.pg_db,
            'table': args.pg_table
        }

    try:
        gdf = run_pipeline(cfg, demo=args.demo)
        logger.info("Pipeline complete.")
        logger.info(f"Rows: {len(gdf)} | Columns: {len(gdf.columns)}")
        if cfg.output and getattr(cfg.output, 'csv', None): logger.info(f"CSV: {getattr(cfg.output, 'csv', None)}")
        if cfg.output and getattr(cfg.output, 'geopackage', None): logger.info(f"GPKG: {getattr(cfg.output, 'geopackage', None)}")
        if cfg.output and getattr(cfg.output, 'quickmap_png', None): logger.info(f"Map PNG: {getattr(cfg.output, 'quickmap_png', None)}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()


