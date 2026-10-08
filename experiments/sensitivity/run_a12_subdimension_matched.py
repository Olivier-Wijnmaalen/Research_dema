"""Matched A.1.2 test using only strong A.1 Roles evidence plus controls."""

from __future__ import annotations

import json
import random
from pathlib import Path

from dotenv import load_dotenv

from dema.config import SCORING_PROMPT_CRLF_SHA256
from dema.llm import build_model_client, model_name
from dema.prompts import get_langfuse_client, get_scoring_prompt
from dema.storage import atomic_write_json, read_json as read
from experiments.sensitivity.run_b13e_matched_sensitivity import run_condition


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dema_run" / "negative_source_test" / "a12_subdimension_matched"
RATED = ROOT / "dema_run" / "sensitivity_analysis" / "nondevelopment_evidence_bank_strength_rated.json"
COMBINED = ROOT / "dema_run" / "combined_evidence_bank.json"
BLINDED_BANK = ROOT / "dema_run" / "negative_source_test" / "nondevelopment_evidence_bank_60_strong_plus_controls_blinded.json"
BLINDED_MANIFEST = ROOT / "dema_run" / "negative_source_test" / "negative_source_test_60_strong_blinded_manifest.json"
TARGET = {"indicator_code": "A.1.2", "indicator_name": "Roles are known & identified, for the coordinator"}
SEED = 20260920


def build_banks():
    rated = read(RATED)["evidence_items"]
    genuine_old_ids = sorted(
        x["evidence_id"] for x in rated
        if x["strength_rating"] == "strong" and x.get("subdimension") == "A.1 Roles"
    )
    if len(genuine_old_ids) != 5:
        raise ValueError(f"Expected five strong A.1 records, found {len(genuine_old_ids)}")
    originals = {x["evidence_id"]: x for x in read(COMBINED)["evidence_items"]}
    genuine = [("genuine", old_id, dict(originals[old_id])) for old_id in genuine_old_ids]

    blinded = read(BLINDED_BANK)
    blinded_items = {x["evidence_id"]: x for x in blinded["evidence_items"]}
    old_mapping = read(BLINDED_MANIFEST)["blind_id_mapping"]
    control_meta = [
        x for x in old_mapping
        if x["record_type"] == "control" and x["target_indicator_code"] == TARGET["indicator_code"]
    ]
    if len(control_meta) != 5:
        raise ValueError(f"Expected five A.1.2 controls, found {len(control_meta)}")
    controls = [("control", x["experimental_evidence_id"], dict(blinded_items[x["experimental_evidence_id"]])) for x in control_meta]
    meta_by_old = {x["experimental_evidence_id"]: x for x in control_meta}

    tagged = genuine + controls
    random.Random(SEED).shuffle(tagged)
    items = []
    mapping = []
    for index, (record_type, old_id, item) in enumerate(tagged, start=1):
        new_id = f"EV-{index:04d}"
        item["evidence_id"] = new_id
        items.append(item)
        row = {
            "experimental_evidence_id": new_id,
            "record_type": record_type,
            "original_evidence_id": old_id if record_type == "genuine" else None,
        }
        if record_type == "control":
            row["control_class"] = meta_by_old[old_id]["control_class"]
        mapping.append(row)

    genuine_ids = {x["experimental_evidence_id"] for x in mapping if x["record_type"] == "genuine"}
    control_ids = {x["experimental_evidence_id"] for x in mapping if x["record_type"] == "control"}
    baseline_items = [x for x in items if x["evidence_id"] in genuine_ids]
    common = {
        "country": "Togo",
        "scoring_scope": [TARGET],
        "instruction": "Score A.1.2 exactly once using only evidence_items. Cite only exact evidence IDs present and apply the all-requirements rule strictly.",
    }
    baseline = {**common, "dataset_name": "a12_subdimension_condition_1", "evidence_item_count": 5, "evidence_items": baseline_items}
    treatment = {**common, "dataset_name": "a12_subdimension_condition_2", "evidence_item_count": 10, "evidence_items": items}
    analyst = {
        "indicator": TARGET,
        "selection_rule": "All five non-development records rated strong and assigned by Stage 1 to A.1 Roles; treatment adds five A.1.2 controls.",
        "random_seed": SEED,
        "mapping": mapping,
        "genuine_ids": sorted(genuine_ids),
        "control_ids": sorted(control_ids),
    }
    return baseline, treatment, analyst


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    OUT.mkdir(parents=True, exist_ok=True)
    baseline, treatment, analyst = build_banks()
    atomic_write_json(OUT / "analyst_manifest.json", analyst)
    langfuse = get_langfuse_client()
    prompt = get_scoring_prompt(langfuse)
    client = build_model_client()
    model = model_name()
    print(f"PROMPT VERIFIED {prompt.name} v{prompt.version} {SCORING_PROMPT_CRLF_SHA256[:12]}", flush=True)
    baseline_result = run_condition(
        "control_free", baseline, prompt, langfuse, client, model,
        target=TARGET, output=OUT,
    )
    treatment_result = run_condition(
        "five_controls", treatment, prompt, langfuse, client, model,
        target=TARGET, output=OUT,
    )
    control_ids = set(analyst["control_ids"])
    base = baseline_result["result"]["indicator_assessments"][0]
    treated = treatment_result["result"]["indicator_assessments"][0]
    comparison = {
        "indicator": TARGET,
        "design": analyst["selection_rule"],
        "control_free": base,
        "five_controls": treated,
        "effect": {
            "phase_change": treated["phase_score"] - base["phase_score"],
            "controls_used_positively": sorted(set(treated["evidence_supporting_score"]) & control_ids),
            "controls_used_as_limiting": sorted(set(treated["contrary_or_limiting_evidence"]) & control_ids),
        },
    }
    atomic_write_json(OUT / "matched_comparison.json", comparison)
    langfuse.flush()
    print(json.dumps(comparison["effect"], indent=2), flush=True)


if __name__ == "__main__":
    main()
