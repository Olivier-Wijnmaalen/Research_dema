"""A.1.2 full-bank order and contamination sensitivity experiment.

The clean condition contains all 622 frozen-pipeline evidence records. Ten
permutations vary only record order. Each clean permutation is paired with a
contaminated condition that preserves the genuine records' relative order and
adds all 155 blinded synthetic controls at seeded positions.
"""

from __future__ import annotations

import json
import itertools
import random
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from dotenv import load_dotenv

from dema.config import SCORING_PROMPT_CRLF_SHA256
from dema.llm import build_model_client, model_name
from dema.prompts import get_langfuse_client, get_scoring_prompt, scoring_prompt_snapshot
from dema.storage import atomic_write_json, read_json as read
from experiments.sensitivity.run_b13e_matched_sensitivity import run_condition


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dema_run" / "sensitivity_analysis" / "a12_fullbank_order_contamination"
FULL_BANK = ROOT / "dema_run" / "combined_evidence_bank.json"
CONTROL_BANK = ROOT / "dema_run" / "negative_source_test" / "nondevelopment_evidence_bank_60_strong_plus_controls_blinded.json"
CONTROL_MANIFEST = ROOT / "dema_run" / "negative_source_test" / "negative_source_test_60_strong_blinded_manifest.json"
TARGET = {"indicator_code": "A.1.2", "indicator_name": "Roles are known & identified, for the coordinator"}
SEEDS = [20261001 + index for index in range(10)]


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def prepare_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    original_items = read(FULL_BANK)["evidence_items"]
    control_source = read(CONTROL_BANK)["evidence_items"]
    source_manifest = read(CONTROL_MANIFEST)["blind_id_mapping"]
    source_meta = {row["experimental_evidence_id"]: row for row in source_manifest}
    control_items = [
        item for item in control_source
        if source_meta[item["evidence_id"]]["record_type"] == "control"
    ]
    if len(original_items) != 622 or len(control_items) != 155:
        raise ValueError(
            f"Expected 622 genuine and 155 control records, found {len(original_items)} and {len(control_items)}"
        )

    genuine: list[dict[str, Any]] = []
    controls: list[dict[str, Any]] = []
    mapping: list[dict[str, Any]] = []
    for index, item in enumerate(original_items, start=1):
        copied = dict(item)
        new_id = f"EV-{index:04d}"
        old_id = copied["evidence_id"]
        copied["evidence_id"] = new_id
        genuine.append(copied)
        mapping.append({
            "experimental_evidence_id": new_id,
            "record_type": "genuine",
            "original_evidence_id": old_id,
        })
    for offset, item in enumerate(control_items, start=len(genuine) + 1):
        copied = dict(item)
        new_id = f"EV-{offset:04d}"
        source_id = copied["evidence_id"]
        copied["evidence_id"] = new_id
        metadata = source_meta[source_id]
        controls.append(copied)
        mapping.append({
            "experimental_evidence_id": new_id,
            "record_type": "control",
            "original_evidence_id": None,
            "source_experimental_id": source_id,
            "target_indicator_code": metadata["target_indicator_code"],
            "control_class": metadata["control_class"],
        })
    analyst = {
        "indicator": TARGET,
        "design": (
            "Ten paired permutations. Clean banks contain all 622 frozen-pipeline records. "
            "Contaminated banks preserve the paired genuine order and add all 155 blinded controls."
        ),
        "seeds": SEEDS,
        "genuine_record_count": len(genuine),
        "control_record_count": len(controls),
        "mapping": mapping,
    }
    return genuine, controls, analyst


def make_bank(items: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return {
        "dataset_name": name,
        "country": "Togo",
        "scoring_scope": [TARGET],
        "instruction": (
            "Score A.1.2 exactly once using only evidence_items. Cite only exact evidence_id "
            "strings present in this condition and apply the all-requirements rule strictly."
        ),
        "evidence_item_count": len(items),
        "evidence_items": items,
    }


def insert_controls(
    ordered_genuine: list[dict[str, Any]], controls: list[dict[str, Any]], seed: int
) -> list[dict[str, Any]]:
    rng = random.Random(seed + 900_000)
    ordered_controls = list(controls)
    rng.shuffle(ordered_controls)
    # Sorting tagged records by a random key inserts controls throughout the bank
    # while the genuine records retain their paired clean-condition order.
    tagged = [(rng.random(), 0, index, item) for index, item in enumerate(ordered_genuine)]
    tagged.extend((rng.random(), 1, index, item) for index, item in enumerate(ordered_controls))
    tagged.sort(key=lambda value: (value[0], value[1], value[2]))
    # Restore the genuine relative order after determining insertion slots.
    control_slots = sorted((value[0], value[3]) for value in tagged if value[1] == 1)
    slot_rng = random.Random(seed + 910_000)
    slots = sorted(slot_rng.randrange(len(ordered_genuine) + 1) for _ in control_slots)
    by_slot: dict[int, list[dict[str, Any]]] = {}
    for slot, (_, item) in zip(slots, control_slots):
        by_slot.setdefault(slot, []).append(item)
    output: list[dict[str, Any]] = []
    for index in range(len(ordered_genuine) + 1):
        output.extend(by_slot.get(index, []))
        if index < len(ordered_genuine):
            output.append(ordered_genuine[index])
    return output


def assessment(value: dict[str, Any]) -> dict[str, Any]:
    return value["result"]["indicator_assessments"][0]


def summarize(
    clean_results: list[dict[str, Any]],
    contaminated_results: list[dict[str, Any]],
    analyst: dict[str, Any],
) -> dict[str, Any]:
    genuine_ids = {
        row["experimental_evidence_id"] for row in analyst["mapping"]
        if row["record_type"] == "genuine"
    }
    control_rows = [row for row in analyst["mapping"] if row["record_type"] == "control"]
    control_ids = {row["experimental_evidence_id"] for row in control_rows}
    target_control_ids = {
        row["experimental_evidence_id"] for row in control_rows
        if row["target_indicator_code"] == TARGET["indicator_code"]
    }
    clean = [assessment(value) for value in clean_results]
    contaminated = [assessment(value) for value in contaminated_results]
    reference = clean[0]
    reference_support = set(reference["evidence_supporting_score"])
    reference_limiting = set(reference["contrary_or_limiting_evidence"])

    order_rows = []
    contamination_rows = []
    support_frequencies: Counter[str] = Counter()
    limiting_frequencies: Counter[str] = Counter()
    for index, current in enumerate(clean):
        support = set(current["evidence_supporting_score"])
        limiting = set(current["contrary_or_limiting_evidence"])
        support_frequencies.update(support)
        limiting_frequencies.update(limiting)
        order_rows.append({
            "permutation": index + 1,
            "seed": SEEDS[index],
            "phase": current["phase_score"],
            "support_count": len(support),
            "limiting_count": len(limiting),
            "support_jaccard_vs_permutation_1": round(jaccard(support, reference_support), 4),
            "limiting_jaccard_vs_permutation_1": round(jaccard(limiting, reference_limiting), 4),
        })

    total_positive_controls: set[str] = set()
    total_limiting_controls: set[str] = set()
    for index, (base, treated) in enumerate(zip(clean, contaminated)):
        base_support = set(base["evidence_supporting_score"])
        treated_support = set(treated["evidence_supporting_score"])
        base_limiting = set(base["contrary_or_limiting_evidence"])
        treated_limiting = set(treated["contrary_or_limiting_evidence"])
        positive_controls = treated_support & control_ids
        limiting_controls = treated_limiting & control_ids
        total_positive_controls |= positive_controls
        total_limiting_controls |= limiting_controls
        base_genuine_support = base_support & genuine_ids
        treated_genuine_support = treated_support & genuine_ids
        base_genuine_limiting = base_limiting & genuine_ids
        treated_genuine_limiting = treated_limiting & genuine_ids
        contamination_rows.append({
            "pair": index + 1,
            "seed": SEEDS[index],
            "clean_phase": base["phase_score"],
            "contaminated_phase": treated["phase_score"],
            "phase_change": treated["phase_score"] - base["phase_score"],
            "clean_genuine_support_count": len(base_genuine_support),
            "contaminated_genuine_support_count": len(treated_genuine_support),
            "genuine_support_retained_count": len(base_genuine_support & treated_genuine_support),
            "genuine_support_retention_rate": round(
                len(base_genuine_support & treated_genuine_support) / len(base_genuine_support), 4
            ) if base_genuine_support else 1.0,
            "genuine_support_jaccard": round(jaccard(base_genuine_support, treated_genuine_support), 4),
            "clean_genuine_limiting_count": len(base_genuine_limiting),
            "contaminated_genuine_limiting_count": len(treated_genuine_limiting),
            "genuine_limiting_jaccard": round(jaccard(base_genuine_limiting, treated_genuine_limiting), 4),
            "positive_control_count": len(positive_controls),
            "limiting_control_count": len(limiting_controls),
            "target_positive_control_count": len(positive_controls & target_control_ids),
            "target_limiting_control_count": len(limiting_controls & target_control_ids),
        })

    order_phase_counts = Counter(row["phase"] for row in order_rows)
    clean_pairs = list(itertools.combinations(clean, 2))
    order_summary = {
        "permutations": len(order_rows),
        "reference_phase": reference["phase_score"],
        "phase_distribution": {str(key): value for key, value in sorted(order_phase_counts.items())},
        "phase_stability_rate": round(
            sum(row["phase"] == reference["phase_score"] for row in order_rows) / len(order_rows), 4
        ),
        "pairwise_phase_agreement_rate": round(
            sum(left["phase_score"] == right["phase_score"] for left, right in clean_pairs)
            / len(clean_pairs), 4
        ),
        "exact_support_set_stability_rate": round(
            sum(set(item["evidence_supporting_score"]) == reference_support for item in clean) / len(clean), 4
        ),
        "mean_support_jaccard_vs_reference": round(
            mean(row["support_jaccard_vs_permutation_1"] for row in order_rows), 4
        ),
        "mean_pairwise_support_jaccard": round(mean(
            jaccard(set(left["evidence_supporting_score"]), set(right["evidence_supporting_score"]))
            for left, right in clean_pairs
        ), 4),
        "pairwise_exact_support_set_rate": round(
            sum(
                set(left["evidence_supporting_score"]) == set(right["evidence_supporting_score"])
                for left, right in clean_pairs
            ) / len(clean_pairs), 4
        ),
        "exact_limiting_set_stability_rate": round(
            sum(set(item["contrary_or_limiting_evidence"]) == reference_limiting for item in clean) / len(clean), 4
        ),
        "mean_limiting_jaccard_vs_reference": round(
            mean(row["limiting_jaccard_vs_permutation_1"] for row in order_rows), 4
        ),
        "mean_pairwise_limiting_jaccard": round(mean(
            jaccard(set(left["contrary_or_limiting_evidence"]), set(right["contrary_or_limiting_evidence"]))
            for left, right in clean_pairs
        ), 4),
        "support_selection_frequency": dict(sorted(support_frequencies.items())),
        "limiting_selection_frequency": dict(sorted(limiting_frequencies.items())),
    }
    contamination_summary = {
        "paired_comparisons": len(contamination_rows),
        "genuine_records_per_clean_bank": len(genuine_ids),
        "controls_added_per_treatment_bank": len(control_ids),
        "targeted_A_1_2_controls_per_treatment_bank": len(target_control_ids),
        "phase_unchanged_pairs": sum(row["phase_change"] == 0 for row in contamination_rows),
        "phase_stability_rate": round(
            sum(row["phase_change"] == 0 for row in contamination_rows) / len(contamination_rows), 4
        ),
        "phase_increases": sum(row["phase_change"] > 0 for row in contamination_rows),
        "phase_decreases": sum(row["phase_change"] < 0 for row in contamination_rows),
        "contaminated_phase_distribution": {
            str(key): value for key, value in sorted(Counter(
                item["phase_score"] for item in contaminated
            ).items())
        },
        "mean_genuine_support_retention_rate": round(
            mean(row["genuine_support_retention_rate"] for row in contamination_rows), 4
        ),
        "mean_genuine_support_jaccard": round(
            mean(row["genuine_support_jaccard"] for row in contamination_rows), 4
        ),
        "mean_genuine_limiting_jaccard": round(
            mean(row["genuine_limiting_jaccard"] for row in contamination_rows), 4
        ),
        "mean_positive_control_count_per_run": round(
            mean(row["positive_control_count"] for row in contamination_rows), 2
        ),
        "mean_limiting_control_count_per_run": round(
            mean(row["limiting_control_count"] for row in contamination_rows), 2
        ),
        "unique_controls_used_positively_across_runs": len(total_positive_controls),
        "unique_controls_used_as_limiting_across_runs": len(total_limiting_controls),
        "unique_target_controls_used_positively_across_runs": len(total_positive_controls & target_control_ids),
        "unique_target_controls_used_as_limiting_across_runs": len(total_limiting_controls & target_control_ids),
        "total_control_record_exposures": len(control_ids) * len(contaminated_results),
        "positive_control_exposure_rate": round(
            sum(row["positive_control_count"] for row in contamination_rows)
            / (len(control_ids) * len(contaminated_results)), 4
        ),
        "limiting_control_exposure_rate": round(
            sum(row["limiting_control_count"] for row in contamination_rows)
            / (len(control_ids) * len(contaminated_results)), 4
        ),
    }
    return {
        "indicator": TARGET,
        "order_effect": {"summary": order_summary, "runs": order_rows},
        "contamination_effect": {"summary": contamination_summary, "pairs": contamination_rows},
    }


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    OUT.mkdir(parents=True, exist_ok=True)
    genuine, controls, analyst = prepare_records()
    atomic_write_json(OUT / "analyst_manifest.json", analyst)
    langfuse = get_langfuse_client()
    prompt = get_scoring_prompt(langfuse)
    atomic_write_json(OUT / "prompt_stage2.json", scoring_prompt_snapshot(prompt))
    client = build_model_client()
    model = model_name()
    print(f"PROMPT VERIFIED {prompt.name} v{prompt.version} {SCORING_PROMPT_CRLF_SHA256[:12]}", flush=True)

    clean_results = []
    contaminated_results = []
    for index, seed in enumerate(SEEDS, start=1):
        ordered_genuine = list(genuine)
        random.Random(seed).shuffle(ordered_genuine)
        clean_bank = make_bank(ordered_genuine, f"a12_fullbank_clean_permutation_{index:02d}")
        contaminated_items = insert_controls(ordered_genuine, controls, seed)
        contaminated_bank = make_bank(
            contaminated_items, f"a12_fullbank_contaminated_permutation_{index:02d}"
        )
        clean_results.append(run_condition(
            f"clean_{index:02d}", clean_bank, prompt, langfuse, client, model,
            target=TARGET, output=OUT,
        ))
        contaminated_results.append(run_condition(
            f"contaminated_{index:02d}", contaminated_bank, prompt, langfuse, client, model,
            target=TARGET, output=OUT,
        ))
        langfuse.flush()

    results = summarize(clean_results, contaminated_results, analyst)
    atomic_write_json(OUT / "quantitative_results.json", results)
    print(json.dumps({
        "order_effect": results["order_effect"]["summary"],
        "contamination_effect": results["contamination_effect"]["summary"],
    }, indent=2), flush=True)
    langfuse.flush()


if __name__ == "__main__":
    main()
