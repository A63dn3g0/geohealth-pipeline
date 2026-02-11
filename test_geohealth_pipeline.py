import unittest
import pandas as pd
from geohealth_pipeline_Project import normalise_lga_name, zscore, demo_metrics

class TestGeoHealthPipeline(unittest.TestCase):
    def test_normalise_lga_name(self):
        s = pd.Series(["Sydney (City)", "MELBOURNE", "Brisbane 123", "Perth!"])
        norm = normalise_lga_name(s)
        expected = pd.Series(["SYDNEY CITY", "MELBOURNE", "BRISBANE 123", "PERTH"])
        pd.testing.assert_series_equal(norm, expected)

    def test_zscore(self):
        s = pd.Series([1, 2, 3, 4, 5])
        z = zscore(s)
        self.assertAlmostEqual(z.mean(), 0, places=7)
        self.assertAlmostEqual(z.std(ddof=0), 1, places=7)

    def test_demo_metrics(self):
        codes = ["00001", "00002"]
        names = ["Demo LGA 1", "Demo LGA 2"]
        df = demo_metrics(codes, names)
        self.assertIn("population", df.columns)
        self.assertIn("mh_any_12m_count", df.columns)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df["LGA_CODE"]), codes)
        self.assertEqual(list(df["LGA_NAME"]), names)

if __name__ == "__main__":
    unittest.main()
