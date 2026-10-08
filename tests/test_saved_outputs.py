import unittest

from dema.config import REPOSITORY_ROOT
from dema.pipeline import extract_scoring_scope, validate_stage2
from dema.storage import read_json


class SavedOutputTests(unittest.TestCase):
    def test_current_pipeline_outputs_remain_complete_and_traceable(self):
        canonical = REPOSITORY_ROOT / "outputs" / "canonical_final"
        manifest = read_json(canonical / "manifest.json")
        bank = read_json(canonical / "combined_evidence_bank.json")
        validated = read_json(canonical / "final_score.validated.json")
        prompt = read_json(
            REPOSITORY_ROOT / "prompts" / "stage2" / "frozen" / "prompt_stage2.json"
        )

        items = bank["evidence_items"]
        evidence_ids = {str(item["evidence_id"]) for item in items}
        scope = extract_scoring_scope(prompt["prompt"])
        assessment = validated["result"]

        self.assertEqual(manifest["status"], "complete")
        self.assertEqual(len(items), 622)
        self.assertEqual(len(evidence_ids), 622)
        self.assertEqual(len(scope), 31)
        self.assertEqual(len(assessment["indicator_assessments"]), 31)
        self.assertEqual(validate_stage2(assessment, scope, evidence_ids), [])


if __name__ == "__main__":
    unittest.main()
