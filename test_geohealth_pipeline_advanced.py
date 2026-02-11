import unittest
import tempfile
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from geohealth_pipeline_Project import (
    load_geography, load_dataset, join_all, PipelineConfig, GeographyConfig, DatasetConfig, OutputConfig, export_products
)

class TestGeoHealthPipelineAdvanced(unittest.TestCase):
    def setUp(self):
        # Create a simple shapefile (GeoPackage) for geography
        self.tempdir = tempfile.TemporaryDirectory()
        self.gpkg_path = os.path.join(self.tempdir.name, "test_lga.gpkg")
        gdf = gpd.GeoDataFrame({
            "LGA_NAME_2023": ["A", "B"],
            "LGA_CODE_2023": ["001", "002"]
        }, geometry=[Polygon([(0,0),(1,0),(1,1),(0,1)]), Polygon([(1,1),(2,1),(2,2),(1,2)])], crs="EPSG:4326")
        gdf.to_file(self.gpkg_path, layer="layer1", driver="GPKG")
        # Create a simple CSV for dataset
        self.csv_path = os.path.join(self.tempdir.name, "test_data.csv")
        pd.DataFrame({"LGA_CODE": ["001", "002"], "population": [100, 200]}).to_csv(self.csv_path, index=False)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_load_geography(self):
        geo_cfg = GeographyConfig(
            lga_shapefile=self.gpkg_path,
            lga_name_field="LGA_NAME_2023",
            lga_code_field="LGA_CODE_2023"
        )
        gdf = load_geography(geo_cfg)
        self.assertEqual(len(gdf), 2)
        self.assertIn("__LGA_NAME_NORM", gdf.columns)

    def test_load_dataset(self):
        dcfg = DatasetConfig(
            name="pop",
            path=self.csv_path,
            lga_field="LGA_CODE",
            value_fields=["population"]
        )
        df = load_dataset(dcfg)
        self.assertEqual(len(df), 2)
        self.assertIn("__LGA_NAME_NORM", df.columns)

    def test_join_all(self):
        geo_cfg = GeographyConfig(
            lga_shapefile=self.gpkg_path,
            lga_name_field="LGA_NAME_2023",
            lga_code_field="LGA_CODE_2023"
        )
        gdf = load_geography(geo_cfg)
        dcfg = DatasetConfig(
            name="pop",
            path=self.csv_path,
            lga_field="LGA_CODE",
            value_fields=["population"]
        )
        joined = join_all(gdf, geo_cfg, [dcfg])
        self.assertIn("population", joined.columns)

    def test_export_products(self):
        geo_cfg = GeographyConfig(
            lga_shapefile=self.gpkg_path,
            lga_name_field="LGA_NAME_2023",
            lga_code_field="LGA_CODE_2023"
        )
        gdf = load_geography(geo_cfg)
        out_csv = os.path.join(self.tempdir.name, "out.csv")
        out_gpkg = os.path.join(self.tempdir.name, "out.gpkg")
        out_cfg = OutputConfig(geopackage=out_gpkg, csv=out_csv, layer_name="test")
        export_products(gdf, out_cfg)
        self.assertTrue(os.path.exists(out_csv))
        self.assertTrue(os.path.exists(out_gpkg))

if __name__ == "__main__":
    unittest.main()
