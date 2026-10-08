"""Run the 20-call, 31-indicator order and contamination experiment."""

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
    extract_scoring_scope,
    remove_redundant_source_locator_citations,
    repair_evidence_id_padding,
    validate_stage2,
)
from dema.prompts import get_langfuse_client, get_scoring_prompt, scoring_prompt_snapshot
from dema.storage import atomic_write_json, read_json as read, sha256_text, utc_now
from experiments.sensitivity.run_a12_fullbank_order_contamination import (
    SEEDS,
    insert_controls,
    jaccard,
    prepare_records,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dema_run" / "sensitivity_analysis" / "fullscope_order_contamination"
REFERENCE_INDICATOR = "A.1.2"


def make_bank(
    items: list[dict[str, Any]], name: str, scope: list[dict[str, str]]
) -> dict[str, Any]:
    return {
        "dataset_name": name,
        "country": "Togo",
        "scoring_scope": scope,
        "instruction": (
            "Score every one of the 31 indicators exactly once using only evidence_items. "
            "Return the indicators in scoring_scope order. Cite only exact evidence_id strings "
            "present in this condition and apply the all-requirements rule strictly. Complete all "
            "31 assessments before ending the response; an output with fewer than 31 is invalid. "
            "Keep each score_reasoning at 180-185 words. Select no more than the 6 most probative "
            "supporting evidence IDs and no more than 3 contrary-or-limiting IDs per indicator. "
            "Keep assessment_summary under 100 words, every other narrative field under 50 words, "
            "and each requirement-check explanation under 25 words. Do not enumerate the full "
            "evidence bank in any field."
        ),
        "evidence_item_count": len(items),
        "evidence_items": items,
    }


def fullscope_response_schema(scope: list[dict[str, str]]) -> dict[str, Any]:
    """Strict response schema forcing one complete 31-item assessment array."""
    requirement_check = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "requirement": {"type": "string", "maxLength": 1000},
            "status": {"type": "string", "enum": ["SUPPORTED", "NOT_DEMONSTRATED"]},
            "evidence_ids": {
                "type": "array", "items": {"type": "string"}, "maxItems": 6,
            },
            "explanation": {"type": "string", "maxLength": 400},
        },
        "required": ["requirement", "status", "evidence_ids", "explanation"],
    }
    assessment = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "indicator_code": {
                "type": "string",
                "enum": [item["indicator_code"] for item in scope],
            },
            "indicator_name": {"type": "string", "maxLength": 250},
            "phase_score": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
            "matched_phase_requirement": {"type": "string", "maxLength": 1800},
            "score_reasoning": {"type": "string", "minLength": 900, "maxLength": 1700},
            "evidence_supporting_score": {
                "type": "array", "items": {"type": "string"}, "maxItems": 6,
            },
            "contrary_or_limiting_evidence": {
                "type": "array", "items": {"type": "string"}, "maxItems": 3,
            },
            "contrary_or_limiting_reasoning": {"type": "string", "maxLength": 700},
            "next_phase_gap": {"type": "string", "maxLength": 700},
            "assigned_phase_requirement_checks": {
                "type": "array", "items": requirement_check,
            },
            "framework_ambiguity": {"type": "string", "maxLength": 500},
        },
        "required": [
            "indicator_code", "indicator_name", "phase_score", "matched_phase_requirement",
            "score_reasoning", "evidence_supporting_score", "contrary_or_limiting_evidence",
            "contrary_or_limiting_reasoning", "next_phase_gap",
            "assigned_phase_requirement_checks", "framework_ambiguity",
        ],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "country": {"type": "string", "maxLength": 100},
            "framework_version": {"type": "string", "maxLength": 200},
            "assessment_summary": {"type": "string", "maxLength": 1200},
            "indicator_assessments": {
                "type": "array", "items": assessment, "minItems": 31, "maxItems": 31,
            },
        },
        "required": ["country", "framework_version", "assessment_summary", "indicator_assessments"],
    }


def run_condition(
    name: str,
    bank: dict[str, Any],
    scope: list[dict[str, str]],
    prompt: Any,
    langfuse: Any,
    client: Any,
    model: str,
) -> dict[str, Any]:
    condition_dir = OUT / name
    condition_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(condition_dir / "evidence_bank.json", bank)
    identifiers = {item["evidence_id"] for item in bank["evidence_items"]}
    lookup = {item["evidence_id"]: item for item in bank["evidence_items"]}
    model_items = [
        {field: item[field] for field in SCORING_EVIDENCE_FIELDS if field in item}
        for item in bank["evidence_items"]
    ]
    model_bank = {**bank, "evidence_items": model_items}
    databank = json.dumps(model_bank, ensure_ascii=False, separators=(",", ":"))
    compiled = prompt.compile(databank=databank)
    prefix = condition_dir / "stage2_all_31_bounded"
    validated = prefix.with_suffix(".validated.json")
    if validated.exists():
        value = read(validated)
        validate_stage2(value["result"], scope, identifiers)
        print(f"{name}: RESUME", flush=True)
        return value
    print(
        f"{name}: START evidence={len(identifiers)} indicators={len(scope)} chars={len(compiled):,}",
        flush=True,
    )
    result, call = call_model_json(
        client=client,
        langfuse=langfuse,
        prompt_object=prompt,
        compiled_prompt=compiled,
        stage_name="dema-stage2-fullscope-order-contamination-p5",
        model=model,
        temperature=0,
        max_output_tokens=32768,
        metadata={
            "experiment": "31-indicator full-bank order and contamination sensitivity",
            "condition": name,
            "indicator_count": len(scope),
            "evidence_count": len(identifiers),
            "databank_sha256": sha256_text(databank),
        },
        artifact_prefix=prefix,
        response_schema=fullscope_response_schema(scope),
    )
    result, repairs = repair_evidence_id_padding(
        result, identifiers, prefix="EV", match_suffix=True
    )
    result, locator_repairs = remove_redundant_source_locator_citations(result, lookup)
    repairs.extend(locator_repairs)
    warnings = validate_stage2(result, scope, identifiers)
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


def by_code(value: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["indicator_code"]: item
        for item in value["result"]["indicator_assessments"]
    }


def summarize(
    clean_results: list[dict[str, Any]],
    contaminated_results: list[dict[str, Any]],
    scope: list[dict[str, str]],
    analyst: dict[str, Any],
) -> dict[str, Any]:
    clean_maps = [by_code(value) for value in clean_results]
    contaminated_maps = [by_code(value) for value in contaminated_results]
    control_rows = [row for row in analyst["mapping"] if row["record_type"] == "control"]
    control_ids = {row["experimental_evidence_id"] for row in control_rows}
    genuine_ids = {
        row["experimental_evidence_id"] for row in analyst["mapping"]
        if row["record_type"] == "genuine"
    }
    control_target = {
        row["experimental_evidence_id"]: row["target_indicator_code"]
        for row in control_rows
    }

    order_by_indicator = []
    contamination_pairs = []
    all_positive_control_citations: list[dict[str, Any]] = []
    all_limiting_control_citations: list[dict[str, Any]] = []

    for target in scope:
        code = target["indicator_code"]
        clean_assessments = [mapping[code] for mapping in clean_maps]
        phases = [item["phase_score"] for item in clean_assessments]
        run_pairs = list(itertools.combinations(clean_assessments, 2))
        order_by_indicator.append({
            "indicator_code": code,
            "indicator_name": target["indicator_name"],
            "phase_distribution": {
                str(key): value for key, value in sorted(Counter(phases).items())
            },
            "distinct_phases": len(set(phases)),
            "phase_invariant": len(set(phases)) == 1,
            "pairwise_phase_agreement": round(
                sum(left["phase_score"] == right["phase_score"] for left, right in run_pairs)
                / len(run_pairs), 4
            ),
            "mean_pairwise_support_jaccard": round(mean(
                jaccard(set(left["evidence_supporting_score"]), set(right["evidence_supporting_score"]))
                for left, right in run_pairs
            ), 4),
            "exact_support_set_pair_rate": round(
                sum(
                    set(left["evidence_supporting_score"]) == set(right["evidence_supporting_score"])
                    for left, right in run_pairs
                ) / len(run_pairs), 4
            ),
            "mean_pairwise_limiting_jaccard": round(mean(
                jaccard(set(left["contrary_or_limiting_evidence"]), set(right["contrary_or_limiting_evidence"]))
                for left, right in run_pairs
            ), 4),
        })

        for index, (clean_map, treated_map) in enumerate(
            zip(clean_maps, contaminated_maps), start=1
        ):
            clean = clean_map[code]
            treated = treated_map[code]
            clean_support = set(clean["evidence_supporting_score"]) & genuine_ids
            treated_support = set(treated["evidence_supporting_score"]) & genuine_ids
            clean_limiting = set(clean["contrary_or_limiting_evidence"]) & genuine_ids
            treated_limiting = set(treated["contrary_or_limiting_evidence"]) & genuine_ids
            positive_controls = set(treated["evidence_supporting_score"]) & control_ids
            limiting_controls = set(treated["contrary_or_limiting_evidence"]) & control_ids
            targeted_positive = {item for item in positive_controls if control_target[item] == code}
            targeted_limiting = {item for item in limiting_controls if control_target[item] == code}
            for item in sorted(positive_controls):
                all_positive_control_citations.append({
                    "seed": SEEDS[index - 1], "indicator_code": code,
                    "evidence_id": item, "target_indicator_code": control_target[item],
                    "target_matched": control_target[item] == code,
                })
            for item in sorted(limiting_controls):
                all_limiting_control_citations.append({
                    "seed": SEEDS[index - 1], "indicator_code": code,
                    "evidence_id": item, "target_indicator_code": control_target[item],
                    "target_matched": control_target[item] == code,
                })
            contamination_pairs.append({
                "seed": SEEDS[index - 1],
                "indicator_code": code,
                "indicator_name": target["indicator_name"],
                "clean_phase": clean["phase_score"],
                "contaminated_phase": treated["phase_score"],
                "phase_change": treated["phase_score"] - clean["phase_score"],
                "clean_genuine_support_count": len(clean_support),
                "contaminated_genuine_support_count": len(treated_support),
                "genuine_support_retained_count": len(clean_support & treated_support),
                "genuine_support_retention_rate": round(
                    len(clean_support & treated_support) / len(clean_support), 4
                ) if clean_support else 1.0,
                "genuine_support_jaccard": round(jaccard(clean_support, treated_support), 4),
                "genuine_limiting_jaccard": round(jaccard(clean_limiting, treated_limiting), 4),
                "positive_control_count": len(positive_controls),
                "limiting_control_count": len(limiting_controls),
                "targeted_positive_control_count": len(targeted_positive),
                "targeted_limiting_control_count": len(targeted_limiting),
                "positive_control_ids": sorted(positive_controls),
                "limiting_control_ids": sorted(limiting_controls),
            })

    total_order_pairs = len(scope) * 45
    invariant = sum(item["phase_invariant"] for item in order_by_indicator)
    phase_agreements = sum(
        round(item["pairwise_phase_agreement"] * 45)
        for item in order_by_indicator
    )
    order_summary = {
        "indicators": len(scope),
        "clean_permutations": len(clean_results),
        "indicator_runs": len(scope) * len(clean_results),
        "pairwise_indicator_comparisons": total_order_pairs,
        "phase_invariant_indicators": invariant,
        "phase_invariant_indicator_rate": round(invariant / len(scope), 4),
        "aggregate_pairwise_phase_agreement_rate": round(
            phase_agreements / total_order_pairs, 4
        ),
        "macro_mean_pairwise_support_jaccard": round(mean(
            item["mean_pairwise_support_jaccard"] for item in order_by_indicator
        ), 4),
        "macro_mean_exact_support_set_pair_rate": round(mean(
            item["exact_support_set_pair_rate"] for item in order_by_indicator
        ), 4),
        "macro_mean_pairwise_limiting_jaccard": round(mean(
            item["mean_pairwise_limiting_jaccard"] for item in order_by_indicator
        ), 4),
    }

    unchanged = sum(item["phase_change"] == 0 for item in contamination_pairs)
    increased = sum(item["phase_change"] > 0 for item in contamination_pairs)
    decreased = sum(item["phase_change"] < 0 for item in contamination_pairs)
    affected_indicators = sorted({
        item["indicator_code"] for item in contamination_pairs
        if item["phase_change"] != 0
    })
    positive_assessments = sum(item["positive_control_count"] > 0 for item in contamination_pairs)
    limiting_assessments = sum(item["limiting_control_count"] > 0 for item in contamination_pairs)
    contamination_summary = {
        "paired_indicator_comparisons": len(contamination_pairs),
        "phase_unchanged": unchanged,
        "phase_unchanged_rate": round(unchanged / len(contamination_pairs), 4),
        "phase_increased": increased,
        "phase_decreased": decreased,
        "indicators_with_any_phase_change": len(affected_indicators),
        "indicator_codes_with_any_phase_change": affected_indicators,
        "mean_genuine_support_retention_rate": round(mean(
            item["genuine_support_retention_rate"] for item in contamination_pairs
        ), 4),
        "mean_genuine_support_jaccard": round(mean(
            item["genuine_support_jaccard"] for item in contamination_pairs
        ), 4),
        "mean_genuine_limiting_jaccard": round(mean(
            item["genuine_limiting_jaccard"] for item in contamination_pairs
        ), 4),
        "assessments_with_positive_control_use": positive_assessments,
        "assessment_positive_control_rate": round(
            positive_assessments / len(contamination_pairs), 4
        ),
        "assessments_with_limiting_control_use": limiting_assessments,
        "assessment_limiting_control_rate": round(
            limiting_assessments / len(contamination_pairs), 4
        ),
        "positive_control_citation_count": len(all_positive_control_citations),
        "limiting_control_citation_count": len(all_limiting_control_citations),
        "target_matched_positive_control_citations": sum(
            item["target_matched"] for item in all_positive_control_citations
        ),
        "target_matched_limiting_control_citations": sum(
            item["target_matched"] for item in all_limiting_control_citations
        ),
        "all_control_record_assessment_exposures": len(control_ids) * len(contamination_pairs),
        "targeted_control_record_assessment_exposures": 5 * len(contamination_pairs),
    }

    reference_pairs = [
        item for item in contamination_pairs
        if item["indicator_code"] == REFERENCE_INDICATOR
    ]
    reference_justification = []
    for index, (clean_map, treated_map) in enumerate(
        zip(clean_maps, contaminated_maps), start=1
    ):
        clean = clean_map[REFERENCE_INDICATOR]
        treated = treated_map[REFERENCE_INDICATOR]
        reference_justification.append({
            "seed": SEEDS[index - 1],
            "clean_phase": clean["phase_score"],
            "contaminated_phase": treated["phase_score"],
            "score_reasoning_exact_match": clean["score_reasoning"] == treated["score_reasoning"],
            "limiting_reasoning_exact_match": (
                clean["contrary_or_limiting_reasoning"]
                == treated["contrary_or_limiting_reasoning"]
            ),
            "clean_score_reasoning": clean["score_reasoning"],
            "contaminated_score_reasoning": treated["score_reasoning"],
            "clean_limiting_reasoning": clean["contrary_or_limiting_reasoning"],
            "contaminated_limiting_reasoning": treated["contrary_or_limiting_reasoning"],
            "clean_support_ids": clean["evidence_supporting_score"],
            "contaminated_support_ids": treated["evidence_supporting_score"],
            "clean_limiting_ids": clean["contrary_or_limiting_evidence"],
            "contaminated_limiting_ids": treated["contrary_or_limiting_evidence"],
        })
    reference_summary = {
        "indicator_code": REFERENCE_INDICATOR,
        "pairs": len(reference_pairs),
        "phase_unchanged": sum(item["phase_change"] == 0 for item in reference_pairs),
        "mean_support_retention_rate": round(mean(
            item["genuine_support_retention_rate"] for item in reference_pairs
        ), 4),
        "mean_support_jaccard": round(mean(
            item["genuine_support_jaccard"] for item in reference_pairs
        ), 4),
        "mean_limiting_jaccard": round(mean(
            item["genuine_limiting_jaccard"] for item in reference_pairs
        ), 4),
        "exact_score_reasoning_matches": sum(
            item["score_reasoning_exact_match"] for item in reference_justification
        ),
        "exact_limiting_reasoning_matches": sum(
            item["limiting_reasoning_exact_match"] for item in reference_justification
        ),
    }
    return {
        "design": {
            "clean_banks": len(clean_results),
            "contaminated_banks": len(contaminated_results),
            "indicators_per_call": len(scope),
            "planned_primary_calls": len(clean_results) + len(contaminated_results),
            "genuine_records": len(genuine_ids),
            "controls_added": len(control_ids),
        },
        "order_effect": {"summary": order_summary, "by_indicator": order_by_indicator},
        "contamination_effect": {
            "summary": contamination_summary,
            "pairs": contamination_pairs,
            "positive_control_citations": all_positive_control_citations,
            "limiting_control_citations": all_limiting_control_citations,
        },
        "reference_indicator_justification": {
            "summary": reference_summary,
            "pairs": reference_justification,
        },
    }


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    OUT.mkdir(parents=True, exist_ok=True)
    genuine, controls, analyst = prepare_records()
    analyst["design"] = (
        "Ten matched bank pairs scored in 20 primary calls. Every call scores all 31 indicators. "
        "Clean banks contain all 622 genuine records; contaminated banks preserve genuine order "
        "and add all 155 blinded controls."
    )
    atomic_write_json(OUT / "analyst_manifest.json", analyst)
    langfuse = get_langfuse_client()
    prompt = get_scoring_prompt(langfuse)
    scope = extract_scoring_scope(prompt.prompt)
    if len(scope) != 31:
        raise ValueError(f"Expected 31 indicators, found {len(scope)}")
    atomic_write_json(OUT / "prompt_stage2.json", scoring_prompt_snapshot(prompt))
    client = build_model_client()
    model = model_name()
    print(
        f"PROMPT VERIFIED {prompt.name} v{prompt.version} "
        f"{SCORING_PROMPT_CRLF_SHA256[:12]} scope={len(scope)}",
        flush=True,
    )

    clean_results = []
    contaminated_results = []
    for index, seed in enumerate(SEEDS, start=1):
        ordered_genuine = list(genuine)
        random.Random(seed).shuffle(ordered_genuine)
        clean_bank = make_bank(
            ordered_genuine, f"fullscope_clean_permutation_{index:02d}", scope
        )
        contaminated_bank = make_bank(
            insert_controls(ordered_genuine, controls, seed),
            f"fullscope_contaminated_permutation_{index:02d}",
            scope,
        )
        clean_results.append(run_condition(
            f"clean_{index:02d}", clean_bank, scope, prompt, langfuse, client, model
        ))
        langfuse.flush()
        contaminated_results.append(run_condition(
            f"contaminated_{index:02d}", contaminated_bank, scope,
            prompt, langfuse, client, model
        ))
        langfuse.flush()

    results = summarize(clean_results, contaminated_results, scope, analyst)
    atomic_write_json(OUT / "quantitative_results.json", results)
    print(json.dumps({
        "order_effect": results["order_effect"]["summary"],
        "contamination_effect": results["contamination_effect"]["summary"],
        "reference_indicator": results["reference_indicator_justification"]["summary"],
    }, indent=2), flush=True)
    langfuse.flush()


if __name__ == "__main__":
    main()
