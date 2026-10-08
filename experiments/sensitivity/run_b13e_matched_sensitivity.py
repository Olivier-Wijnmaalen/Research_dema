"""Run matched B.1.3e Stage 2 conditions with and without five controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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


ROOT = Path(__file__).resolve().parents[2]
SOURCE_BANK = ROOT / "dema_run" / "negative_source_test" / "nondevelopment_evidence_bank_60_strong_plus_controls_blinded.json"
SOURCE_MANIFEST = ROOT / "dema_run" / "negative_source_test" / "negative_source_test_60_strong_blinded_manifest.json"
OUT = ROOT / "dema_run" / "negative_source_test" / "b13e_matched"
TARGET = {"indicator_code": "B.1.3e", "indicator_name": "Data quality: validity"}


def build_banks(target: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = read(SOURCE_BANK)
    source_manifest = read(SOURCE_MANIFEST)
    mapping = {x["experimental_evidence_id"]: x for x in source_manifest["blind_id_mapping"]}
    genuine_ids = {key for key, value in mapping.items() if value["record_type"] == "genuine"}
    target_control_ids = {
        key for key, value in mapping.items()
        if value["record_type"] == "control" and value["target_indicator_code"] == target["indicator_code"]
    }
    if len(genuine_ids) != 60 or len(target_control_ids) != 5:
        raise ValueError(
            f"Expected 60 genuine records and five {target['indicator_code']} controls"
        )
    genuine_items = [x for x in source["evidence_items"] if x["evidence_id"] in genuine_ids]
    treatment_items = [x for x in source["evidence_items"] if x["evidence_id"] in genuine_ids | target_control_ids]
    common = {
        "country": "Togo",
        "scoring_scope": [target],
        "instruction": (
            f"Score {target['indicator_code']} exactly once using only evidence_items. "
            "Cite only exact evidence_id strings "
            "present in this condition. Apply the all-requirements rule strictly."
        ),
    }
    baseline = {**common, "dataset_name": "focused_evaluation_condition_1", "evidence_item_count": 60, "evidence_items": genuine_items}
    treatment = {**common, "dataset_name": "focused_evaluation_condition_2", "evidence_item_count": 65, "evidence_items": treatment_items}
    analyst = {
        "indicator": target,
        "design": (
            "Matched one-indicator comparison. Both conditions contain identical 60 strong "
            "genuine records in identical relative order; condition 2 adds only five "
            f"{target['indicator_code']} controls."
        ),
        "genuine_ids": sorted(genuine_ids),
        "control_ids": sorted(target_control_ids),
        "control_details": [mapping[x] for x in sorted(target_control_ids)],
    }
    return baseline, treatment, analyst


def run_condition(
    name: str,
    bank: dict[str, Any],
    prompt: Any,
    langfuse: Any,
    client: Any,
    model: str,
    *,
    target: dict[str, str],
    output: Path,
) -> dict[str, Any]:
    condition_dir = output / name
    condition_dir.mkdir(parents=True, exist_ok=True)
    bank_path = condition_dir / "evidence_bank.json"
    atomic_write_json(bank_path, bank)
    identifiers = {x["evidence_id"] for x in bank["evidence_items"]}
    lookup = {x["evidence_id"]: x for x in bank["evidence_items"]}
    model_items = [
        {field: item[field] for field in SCORING_EVIDENCE_FIELDS if field in item}
        for item in bank["evidence_items"]
    ]
    model_bank = {**bank, "evidence_items": model_items}
    databank = json.dumps(model_bank, ensure_ascii=False, indent=2)
    compiled = prompt.compile(databank=databank)
    prefix = condition_dir / f"stage2_{target['indicator_code'].replace('.', '_')}"
    validated = prefix.with_suffix(".validated.json")
    if validated.exists():
        value = read(validated)
        validate_stage2(value["result"], [target], identifiers)
        print(f"{name}: RESUME", flush=True)
        return value
    print(f"{name}: START evidence={len(identifiers)} chars={len(compiled):,}", flush=True)
    result, call = call_model_json(
        client=client,
        langfuse=langfuse,
        prompt_object=prompt,
        compiled_prompt=compiled,
        stage_name="dema-stage2-b13e-matched-sensitivity-p5",
        model=model,
        temperature=0,
        max_output_tokens=32768,
        metadata={
            "experiment": f"{target['indicator_code']} matched negative-source sensitivity",
            "condition": name,
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
    warnings = validate_stage2(result, [target], identifiers)
    value = {
        "validated_at": utc_now(), "warnings": warnings,
        "citation_repairs": repairs, "call": call, "result": result,
    }
    atomic_write_json(validated, value)
    print(f"{name}: DONE warnings={len(warnings)} repairs={len(repairs)}", flush=True)
    return value


def main(*, target: dict[str, str], output: Path) -> None:
    load_dotenv(ROOT / ".env", override=False)
    output.mkdir(parents=True, exist_ok=True)
    baseline, treatment, analyst = build_banks(target)
    atomic_write_json(output / "analyst_manifest.json", analyst)
    langfuse = get_langfuse_client()
    prompt = get_scoring_prompt(langfuse)
    atomic_write_json(output / "prompt_stage2.json", scoring_prompt_snapshot(prompt))
    client = build_model_client()
    model = model_name()
    print(f"PROMPT VERIFIED {prompt.name} v{prompt.version} {SCORING_PROMPT_CRLF_SHA256[:12]}", flush=True)
    baseline_result = run_condition(
        "control_free", baseline, prompt, langfuse, client, model,
        target=target, output=output,
    )
    treatment_result = run_condition(
        "five_controls", treatment, prompt, langfuse, client, model,
        target=target, output=output,
    )
    control_ids = set(analyst["control_ids"])
    base_assessment = baseline_result["result"]["indicator_assessments"][0]
    treatment_assessment = treatment_result["result"]["indicator_assessments"][0]
    support_controls = sorted(set(treatment_assessment["evidence_supporting_score"]) & control_ids)
    limiting_controls = sorted(set(treatment_assessment["contrary_or_limiting_evidence"]) & control_ids)
    comparison = {
        "indicator": target,
        "frozen_prompt": {"name": prompt.name, "version": prompt.version, "sha256_crlf": SCORING_PROMPT_CRLF_SHA256},
        "temperature": 0,
        "control_free": base_assessment,
        "five_controls": treatment_assessment,
        "effect": {
            "phase_change": treatment_assessment["phase_score"] - base_assessment["phase_score"],
            "controls_used_positively": support_controls,
            "controls_used_as_limiting": limiting_controls,
            "positive_control_count": len(support_controls),
            "limiting_control_count": len(limiting_controls),
        },
    }
    atomic_write_json(output / "matched_comparison.json", comparison)
    langfuse.flush()
    print(json.dumps(comparison["effect"], indent=2), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indicator-code", default=TARGET["indicator_code"])
    parser.add_argument("--indicator-name", default=TARGET["indicator_name"])
    parser.add_argument("--output", type=Path, default=OUT)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    main(
        target={
            "indicator_code": arguments.indicator_code,
            "indicator_name": arguments.indicator_name,
        },
        output=arguments.output,
    )
