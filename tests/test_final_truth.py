import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class FinalTruthTests(unittest.TestCase):
    def test_population_boundaries_and_stage1_results(self):
        manifest = read_json("outputs/canonical_final/manifest.json")
        development = read_json(
            "data/development/stage2/final_development_bank_audit.json"
        )
        stage2_development = read_json("experiments/stage2/bank_manifest.json")

        self.assertEqual(manifest["run_id"], "dema-20260917T132056Z")
        self.assertEqual(manifest["held_out_chunk_count"], 30)
        self.assertEqual(len({row["source_id"] for row in manifest["chunks"]}), 14)
        self.assertEqual(manifest["stage1_accepted_rows"], 232)
        self.assertEqual(manifest["stage1_rejected_rows"], 6)
        self.assertEqual(manifest["base_evidence_count"], 390)
        self.assertEqual(manifest["combined_evidence_count"], 622)

        self.assertEqual(development["generated"], 428)
        self.assertEqual(development["technical_status_counts"]["PASS_EXACT"], 395)
        self.assertEqual(development["technical_status_counts"]["PASS_NORMALIZED"], 6)
        self.assertEqual(development["technical_status_counts"]["REPAIR_REQUIRED"], 7)
        self.assertEqual(development["technical_status_counts"]["FAIL"], 20)
        self.assertEqual(development["ais_status_counts"]["FULLY_ATTRIBUTABLE"], 204)
        self.assertEqual(development["ais_status_counts"]["PARTIALLY_ATTRIBUTABLE"], 211)
        self.assertEqual(development["ais_status_counts"]["NOT_ATTRIBUTABLE"], 13)
        self.assertEqual(development["retained_for_maturity_scoring"], 390)
        self.assertEqual(stage2_development["source_rows"], 390)
        self.assertEqual(stage2_development["prepared_rows"], 389)
        self.assertEqual(
            stage2_development["source_bank_sha256"].lower(),
            "94a062f211ce77dcea686bff849ceee25c082380246c48b2acb9ae63d4aafd59",
        )

    def test_frozen_prompt_identities(self):
        manifest = read_json("outputs/canonical_final/manifest.json")
        self.assertEqual(manifest["stage1"]["version"], 6)
        self.assertEqual(
            manifest["stage1"]["sha256"],
            "d2436f48ec0c9ff693f2b4f1964adc21e179995ec11905d1bf70902bcd8c355c",
        )
        self.assertEqual(manifest["stage2"]["version"], 1)
        self.assertEqual(
            manifest["stage2"]["sha256_crlf"],
            "a3734a364931d5aaa90188c82eee400b0812023a5d4dcb14da70d917067669af",
        )

    def test_all_31_final_scores(self):
        validated = read_json("outputs/canonical_final/final_score.validated.json")
        actual = {
            row["indicator_code"]: row["phase_score"]
            for row in validated["result"]["indicator_assessments"]
        }
        expected = {
            "A.1.1": 3, "A.1.2": 3, "A.1.3": 2, "A.1.4": 3,
            "A.2.1": 3, "A.2.2": 3, "A.2.3": 1, "A.2.4": 3,
            "B.1.1": 3, "B.1.2": 3, "B.1.3a": 3, "B.1.3b": 3,
            "B.1.3c": 3, "B.1.3d": 3, "B.1.3e": 3, "B.1.3f": 3,
            "B.2.1": 3, "B.2.2": 3, "B.2.3": 3, "B.3.1": 3,
            "B.3.2": 3, "C.1.1": 3, "C.1.2": 3, "C.1.3": 1,
            "C.1.4": 1, "C.1.5": 3, "C.2.1": 3, "C.2.2": 3,
            "C.2.3": 3, "C.3.1": 3, "C.3.2": 3,
        }
        self.assertEqual(actual, expected)
        self.assertEqual(Counter(actual.values()), Counter({3: 27, 1: 3, 2: 1}))

    def test_negative_control_outcomes(self):
        results = read_json(
            "evaluation/negative_controls/stage2_60_strong_blinded_results.json"
        )
        self.assertEqual(results["genuine_records_available"], 60)
        self.assertEqual(results["synthetic_controls_available"], 155)
        self.assertEqual(results["unique_controls_used"], 105)
        self.assertEqual(results["contaminated_indicators"], 27)
        self.assertEqual(results["phase_changed_indicators"], 28)

        comparisons = {
            "matched_A_1_2_source_level.json": (2, 2, 0),
            "matched_A_1_2_subdimension.json": (2, 2, 0),
            "matched_B_1_3e.json": (2, 1, -1),
        }
        for filename, expected in comparisons.items():
            result = read_json(f"evaluation/negative_controls/{filename}")
            actual = (
                result["control_free"]["phase_score"],
                result["five_controls"]["phase_score"],
                result["effect"]["phase_change"],
            )
            self.assertEqual(actual, expected)

    def test_truth_table_contains_critical_denominators(self):
        table = (ROOT / "FINAL_TRUTH_TABLE.md").read_text(encoding="utf-8")
        for statement in (
            "**622 = 390 + 232**",
            "**238/238 (100.0%)**",
            "**232/238**",
            "**Not evaluated / no authoritative AIS outcome retained**",
            "**666 = 428 + 238**",
            "The frozen Stage 1 development output was therefore used to develop Stage 2.",
        ):
            self.assertIn(statement, table)


if __name__ == "__main__":
    unittest.main()
