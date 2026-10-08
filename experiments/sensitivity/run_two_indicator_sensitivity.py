"""Run five reorderings and one contamination treatment for two indicators."""

from __future__ import annotations

import itertools
import json
import random
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from dotenv import load_dotenv

from dema.config import SCORING_PROMPT_CRLF_SHA256
from dema.llm import build_model_client, call_model_json, model_name
from dema.pipeline import (
    SCORING_EVIDENCE_FIELDS,
    remove_redundant_source_locator_citations,
    repair_evidence_id_padding,
    validate_stage2,
)
from dema.prompts import get_langfuse_client, get_scoring_prompt, scoring_prompt_snapshot
from dema.storage import atomic_write_json, read_json as read, sha256_text, utc_now
from experiments.sensitivity.run_a12_fullbank_order_contamination import insert_controls, jaccard, prepare_records


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dema_run" / "sensitivity_analysis" / "two_indicator_reordering_contamination"
SCOPE = [
    {"indicator_code": "A.1.2", "indicator_name": "Roles are known & identified, for the coordinator"},
    {"indicator_code": "B.1.3e", "indicator_name": "Data quality: validity"},
]
SEEDS = [20261101 + index for index in range(5)]


def make_bank(items: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return {
        "dataset_name": name,
        "country": "Togo",
        "scoring_scope": SCOPE,
        "instruction": (
            "Score A.1.2 and B.1.3e exactly once using only evidence_items. Cite only exact "
            "evidence_id strings present in this condition and apply the all-requirements rule strictly."
        ),
        "evidence_item_count": len(items),
        "evidence_items": items,
    }


def run_condition(
    name: str, bank: dict[str, Any], prompt: Any, langfuse: Any, client: Any, model: str
) -> dict[str, Any]:
    condition_dir = OUT / name
    condition_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(condition_dir / "evidence_bank.json", bank)
    identifiers = {item["evidence_id"] for item in bank["evidence_items"]}
    lookup = {item["evidence_id"]: item for item in bank["evidence_items"]}
    model_bank = {
        **bank,
        "evidence_items": [
            {field: item[field] for field in SCORING_EVIDENCE_FIELDS if field in item}
            for item in bank["evidence_items"]
        ],
    }
    databank = json.dumps(model_bank, ensure_ascii=False, separators=(",", ":"))
    compiled = prompt.compile(databank=databank)
    prefix = condition_dir / "stage2_A_1_2_B_1_3e"
    validated = prefix.with_suffix(".validated.json")
    if validated.exists():
        value = read(validated)
        validate_stage2(value["result"], SCOPE, identifiers)
        print(f"{name}: RESUME", flush=True)
        return value
    print(f"{name}: START evidence={len(identifiers)} chars={len(compiled):,}", flush=True)
    result, call = call_model_json(
        client=client,
        langfuse=langfuse,
        prompt_object=prompt,
        compiled_prompt=compiled,
        stage_name="dema-stage2-two-indicator-sensitivity-p5",
        model=model,
        temperature=0,
        max_output_tokens=32768,
        metadata={
            "experiment": "two-indicator reordering and contamination sensitivity",
            "condition": name,
            "indicators": [item["indicator_code"] for item in SCOPE],
            "evidence_count": len(identifiers),
            "databank_sha256": sha256_text(databank),
        },
        artifact_prefix=prefix,
        json_mode=True,
    )
    result, repairs = repair_evidence_id_padding(
        result, identifiers, prefix="EV", match_suffix=True
    )
    result, locator_repairs = remove_redundant_source_locator_citations(result, lookup)
    repairs.extend(locator_repairs)
    warnings = validate_stage2(result, SCOPE, identifiers)
    value = {
        "validated_at": utc_now(),
        "warnings": warnings,
        "citation_repairs": repairs,
        "call": call,
        "result": result,
    }
    atomic_write_json(validated, value)
    print(
        f"{name}: DONE assessments={len(result['indicator_assessments'])} "
        f"warnings={len(warnings)} repairs={len(repairs)}",
        flush=True,
    )
    return value


def assessment_map(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["indicator_code"]: item
        for item in value["result"]["indicator_assessments"]
    }


def summarize(
    clean_results: list[dict[str, Any]],
    contaminated_result: dict[str, Any],
    analyst: dict[str, Any],
) -> dict[str, Any]:
    clean_maps = [assessment_map(value) for value in clean_results]
    contaminated = assessment_map(contaminated_result)
    genuine_ids = {
        row["experimental_evidence_id"] for row in analyst["mapping"]
        if row["record_type"] == "genuine"
    }
    control_rows = [row for row in analyst["mapping"] if row["record_type"] == "control"]
    control_ids = {row["experimental_evidence_id"] for row in control_rows}
    control_target = {
        row["experimental_evidence_id"]: row["target_indicator_code"]
        for row in control_rows
    }
    order_results = []
    contamination_results = []
    for target in SCOPE:
        code = target["indicator_code"]
        runs = [mapping[code] for mapping in clean_maps]
        pairs = list(itertools.combinations(runs, 2))
        phases = [item["phase_score"] for item in runs]
        support_pair_scores = [
            jaccard(set(left["evidence_supporting_score"]), set(right["evidence_supporting_score"]))
            for left, right in pairs
        ]
        limiting_pair_scores = [
            jaccard(set(left["contrary_or_limiting_evidence"]), set(right["contrary_or_limiting_evidence"]))
            for left, right in pairs
        ]
        order_results.append({
            "indicator_code": code,
            "indicator_name": target["indicator_name"],
            "phase_distribution": {
                str(key): value for key, value in sorted(Counter(phases).items())
            },
            "phase_invariant": len(set(phases)) == 1,
            "pairwise_phase_agreement": round(
                sum(left["phase_score"] == right["phase_score"] for left, right in pairs)
                / len(pairs), 4
            ),
            "mean_pairwise_support_jaccard": round(mean(support_pair_scores), 4),
            "exact_support_set_pair_rate": round(sum(
                set(left["evidence_supporting_score"]) == set(right["evidence_supporting_score"])
                for left, right in pairs
            ) / len(pairs), 4),
            "mean_pairwise_limiting_jaccard": round(mean(limiting_pair_scores), 4),
            "runs": [{
                "seed": SEEDS[index],
                "phase": item["phase_score"],
                "support_count": len(item["evidence_supporting_score"]),
                "limiting_count": len(item["contrary_or_limiting_evidence"]),
                "support_ids": item["evidence_supporting_score"],
                "limiting_ids": item["contrary_or_limiting_evidence"],
            } for index, item in enumerate(runs)],
        })

        clean = clean_maps[0][code]
        treated = contaminated[code]
        clean_support = set(clean["evidence_supporting_score"]) & genuine_ids
        treated_support = set(treated["evidence_supporting_score"]) & genuine_ids
        clean_limiting = set(clean["contrary_or_limiting_evidence"]) & genuine_ids
        treated_limiting = set(treated["contrary_or_limiting_evidence"]) & genuine_ids
        positive_controls = set(treated["evidence_supporting_score"]) & control_ids
        limiting_controls = set(treated["contrary_or_limiting_evidence"]) & control_ids
        contamination_results.append({
            "indicator_code": code,
            "indicator_name": target["indicator_name"],
            "matched_clean_seed": SEEDS[0],
            "clean_phase": clean["phase_score"],
            "contaminated_phase": treated["phase_score"],
            "phase_change": treated["phase_score"] - clean["phase_score"],
            "clean_support_count": len(clean_support),
            "contaminated_support_count": len(treated_support),
            "support_retained_count": len(clean_support & treated_support),
            "support_retention_rate": round(
                len(clean_support & treated_support) / len(clean_support), 4
            ) if clean_support else 1.0,
            "support_jaccard": round(jaccard(clean_support, treated_support), 4),
            "clean_limiting_count": len(clean_limiting),
            "contaminated_limiting_count": len(treated_limiting),
            "limiting_jaccard": round(jaccard(clean_limiting, treated_limiting), 4),
            "positive_control_ids": sorted(positive_controls),
            "limiting_control_ids": sorted(limiting_controls),
            "target_matched_positive_controls": sorted(
                item for item in positive_controls if control_target[item] == code
            ),
            "target_matched_limiting_controls": sorted(
                item for item in limiting_controls if control_target[item] == code
            ),
            "clean_score_reasoning": clean["score_reasoning"],
            "contaminated_score_reasoning": treated["score_reasoning"],
            "clean_limiting_reasoning": clean["contrary_or_limiting_reasoning"],
            "contaminated_limiting_reasoning": treated["contrary_or_limiting_reasoning"],
        })
    return {
        "design": {
            "indicators": SCOPE,
            "clean_reorderings": 5,
            "contaminated_banks": 1,
            "primary_calls": 6,
            "genuine_records_per_call": len(genuine_ids),
            "controls_in_contaminated_call": len(control_ids),
            "contamination_matched_to_seed": SEEDS[0],
        },
        "order_effect": order_results,
        "contamination_effect": contamination_results,
    }


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    OUT.mkdir(parents=True, exist_ok=True)
    genuine, controls, analyst = prepare_records()
    analyst["design"] = (
        "Five clean reorderings score A.1.2 and B.1.3e together. One contaminated call "
        "uses clean ordering 1 plus all 155 controls."
    )
    analyst["seeds"] = SEEDS
    atomic_write_json(OUT / "analyst_manifest.json", analyst)
    langfuse = get_langfuse_client()
    prompt = get_scoring_prompt(langfuse)
    atomic_write_json(OUT / "prompt_stage2.json", scoring_prompt_snapshot(prompt))
    client = build_model_client()
    model = model_name()
    print(
        f"PROMPT VERIFIED {prompt.name} v{prompt.version} "
        f"{SCORING_PROMPT_CRLF_SHA256[:12]}", flush=True
    )

    clean_results = []
    clean_orders = []
    for index, seed in enumerate(SEEDS, start=1):
        ordered = list(genuine)
        random.Random(seed).shuffle(ordered)
        clean_orders.append(ordered)
        clean_results.append(run_condition(
            f"clean_{index:02d}",
            make_bank(ordered, f"two_indicator_clean_reordering_{index:02d}"),
            prompt, langfuse, client, model,
        ))
        langfuse.flush()

    contaminated_items = insert_controls(clean_orders[0], controls, SEEDS[0])
    contaminated_result = run_condition(
        "contaminated_01",
        make_bank(contaminated_items, "two_indicator_contaminated_matched_to_clean_01"),
        prompt, langfuse, client, model,
    )
    langfuse.flush()
    results = summarize(clean_results, contaminated_result, analyst)
    atomic_write_json(OUT / "quantitative_results.json", results)
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    main()
