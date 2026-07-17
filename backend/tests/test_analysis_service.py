import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from analysis_service import build_dashboard_payload, clean_csv_bytes


class AnalysisServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sample = Path(__file__).with_name("sample_All_Diets.csv").read_bytes()
        cls.rows = clean_csv_bytes(sample)

    def test_cleaning_and_summary(self):
        payload = build_dashboard_payload(self.rows)
        self.assertEqual(payload["summary"]["recipe_count"], 10)
        self.assertEqual(payload["summary"]["diet_type_count"], 4)
        paleo = next(
            row for row in payload["charts"]["average_macros_by_diet"]
            if row["diet_type"] == "Paleo"
        )
        self.assertEqual(paleo["protein_g"], 72.56)

    def test_diet_and_search_filters(self):
        vegan = build_dashboard_payload(self.rows, diet_types=["Vegan"])
        self.assertEqual(vegan["summary"]["recipe_count"], 3)
        curry = build_dashboard_payload(self.rows, search="curry")
        self.assertEqual(curry["summary"]["recipe_count"], 1)
        self.assertEqual(curry["charts"]["protein_vs_carbs"][0]["recipe_name"], "Lentil Curry")

    def test_missing_numeric_values_are_imputed(self):
        raw = (
            "Diet_type,Recipe_name,Cuisine_type,Protein(g),Carbs(g),Fat(g)\n"
            "Vegan,One,Indian,10,20,5\n"
            "Vegan,Two,Indian,,40,15\n"
        ).encode()
        rows = clean_csv_bytes(raw)
        self.assertEqual(rows[1]["Protein(g)"], 10.0)

    def test_missing_required_column_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Fat"):
            clean_csv_bytes(b"Diet_type,Recipe_name,Cuisine_type,Protein(g),Carbs(g)\n")


if __name__ == "__main__":
    unittest.main()
