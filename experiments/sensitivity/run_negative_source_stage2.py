"""Run frozen Stage 2 P5 on the 60-strong negative-source test bank."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from dema.config import SCORING_PROMPT_CRLF_SHA256
from dema.llm import build_model_client, call_model_json, model_name
from dema.pipeline import (
    SCORING_EVIDENCE_FIELDS,
    build_scoring_batches,
    remove_redundant_source_locator_citations,
    repair_evidence_id_padding,
    validate_stage2,
)
from dema.prompts import get_langfuse_client, get_scoring_prompt, scoring_prompt_snapshot
from dema.storage import atomic_write_json, read_json, sha256_text, utc_now


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "dema_run" / "negative_source_test" / "nondevelopment_evidence_bank_60_strong_plus_controls_blinded.json"
EXPERIMENT_MANIFEST = ROOT / "dema_run" / "negative_source_test" / "negative_source_test_60_strong_blinded_manifest.json"
OUTPUT = ROOT / "dema_run" / "negative_source_test" / "stage2_60_strong_blinded"
BASELINE = ROOT / "dema_run" / "stage2" / "final_score.validated.json"


def analyse(final_score: dict[str, Any], bank: dict[str, Any]) -> dict[str, Any]:
    baseline_doc = read_json(BASELINE)
    baseline = baseline_doc.get("result", baseline_doc)
    baseline_phase = {x["indicator_code"]: x["phase_score"] for x in baseline["indicator_assessments"]}
    experiment = read_json(EXPERIMENT_MANIFEST)
    mapping = experiment["blind_id_mapping"]
    control_ids = {x["experimental_evidence_id"] for x in mapping if x["record_type"] == "control"}
    genuine_ids = {x["experimental_evidence_id"] for x in mapping if x["record_type"] == "genuine"}
    rows: list[dict[str, Any]] = []
    all_control_support: set[str] = set()
    all_control_limit: set[str] = set()
    all_genuine: set[str] = set()
    contaminated = 0
    changed = 0
    for assessment in final_score["indicator_assessments"]:
        code = assessment["indicator_code"]
        supporting = set(assessment.get("evidence_supporting_score", []))
        limiting = set(assessment.get("contrary_or_limiting_evidence", []))
        control_support = supporting & control_ids
        control_limit = limiting & control_ids
        genuine_used = (supporting | limiting) & genuine_ids
        any_controls = control_support | control_limit
        if any_controls:
            contaminated += 1
        phase_delta = assessment["phase_score"] - baseline_phase[code]
        if phase_delta:
            changed += 1
        all_control_support |= control_support
        all_control_limit |= control_limit
        all_genuine |= genuine_used
        rows.append({
            "indicator_code": code,
            "baseline_phase": baseline_phase[code],
            "experimental_phase": assessment["phase_score"],
            "phase_delta": phase_delta,
            "control_supporting_ids": sorted(control_support),
            "control_limiting_ids": sorted(control_limit),
            "genuine_used_ids": sorted(genuine_used),
        })
    unique_controls = all_control_support | all_control_limit
    return {
        "bank_records": len(bank["evidence_items"]),
        "genuine_records_available": len(genuine_ids),
        "synthetic_controls_available": len(control_ids),
        "unique_controls_used": len(unique_controls),
        "control_citation_rate_pct": round(100 * len(unique_controls) / len(control_ids), 1),
        "controls_used_as_supporting": len(all_control_support),
        "controls_used_as_limiting": len(all_control_limit),
        "contaminated_indicators": contaminated,
        "indicator_contamination_rate_pct": round(100 * contaminated / len(rows), 1),
        "unique_genuine_records_used": len(all_genuine),
        "phase_changed_indicators": changed,
        "phase_instability_rate_pct": round(100 * changed / len(rows), 1),
        "indicator_results": rows,
    }


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    langfuse = get_langfuse_client()
    prompt = get_scoring_prompt(langfuse)
    bank = read_json(INPUT)
    if bank.get("evidence_item_count") != 215:
        raise ValueError("Expected the 215-record 60-strong experimental bank")
    identifiers = [str(x["evidence_id"]) for x in bank["evidence_items"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate evidence IDs")
    evidence_lookup = {x["evidence_id"]: x for x in bank["evidence_items"]}
    scope = bank["scoring_scope"]
    run_id = datetime.now(timezone.utc).strftime("dema-negative-source-%Y%m%dT%H%M%SZ")
    model = model_name()
    client = build_model_client()
    atomic_write_json(OUTPUT / "prompt_stage2.json", scoring_prompt_snapshot(prompt))
    manifest = {
        "run_id": run_id,
        "status": "stage2_running",
        "started_at": utc_now(),
        "experiment": "60 strong evaluation records plus 155 synthetic low-quality controls",
        "input_bank": str(INPUT),
        "input_bank_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "evidence_count": len(identifiers),
        "indicator_count": len(scope),
        "model": model,
        "temperature": 0,
        "stage2_prompt": {"name": prompt.name, "version": prompt.version, "crlf_sha256": SCORING_PROMPT_CRLF_SHA256},
        "calls": [],
    }
    manifest_path = OUTPUT / "manifest.json"
    if manifest_path.exists():
        old = read_json(manifest_path)
        manifest["run_id"] = old.get("run_id", run_id)
        manifest["started_at"] = old.get("started_at", manifest["started_at"])
    atomic_write_json(manifest_path, manifest)
    print(f"PROMPT VERIFIED | {prompt.name} v{prompt.version} | {SCORING_PROMPT_CRLF_SHA256[:12]}", flush=True)
    print(f"BANK VERIFIED | evidence={len(identifiers)} | indicators={len(scope)}", flush=True)

    items = [
        {field: item[field] for field in SCORING_EVIDENCE_FIELDS if field in item}
        for item in bank["evidence_items"]
    ]
    scoring_batches = build_scoring_batches(scope)
    final_assessments: list[dict[str, Any]] = []
    summaries: list[str] = []
    warnings: list[str] = []
    for index, batch_scope in enumerate(scoring_batches, start=1):
        codes = [x["indicator_code"] for x in batch_scope]
        instruction = (
            "Score every indicator in scoring_scope exactly once using only evidence_items. "
            "Evidence IDs are condition-specific: cite only exact evidence_id strings present in this "
            "current evidence_items array. Do not recall IDs from a prior assessment, construct omitted "
            "sequence IDs, or cite an unavailable record. If relevant evidence is absent, use the frozen "
            "prompt's documentary-gap rule. Apply the frozen all-requirements rule strictly: select only "
            "a phase for which every assigned phase requirement can be marked SUPPORTED; if any requirement "
            "would be NOT_DEMONSTRATED, lower the assigned phase."
        )
        if codes == ["A.1.3"]:
            instruction = (
                "Score A.1.3 exactly once using only evidence_items. Follow the frozen P5 JSON schema "
                "exactly: score_reasoning must be 180-350 words and evidence citation fields must be arrays. "
                "Cite only exact evidence_id strings present in the current evidence_items array; do not recall "
                "or reconstruct IDs from any prior assessment."
            )
        batch_bank = {
            **{key: value for key, value in bank.items() if key not in {"scoring_scope", "evidence_items"}},
            "scoring_scope": batch_scope,
            "instruction": instruction,
            "evidence_item_count": len(items),
            "evidence_items": items,
        }
        databank = json.dumps(batch_bank, ensure_ascii=False, indent=2)
        compiled = prompt.compile(databank=databank)
        slug = f"batch_{index:02d}_{codes[0].replace('.', '_')}_to_{codes[-1].replace('.', '_')}"
        if codes == ["A.1.3"]:
            slug += "_retry"
        prefix = OUTPUT / "batches" / slug
        validated_path = prefix.with_suffix(".validated.json")
        if validated_path.exists():
            cached = read_json(validated_path)
            result = cached["result"]
            batch_warnings = cached.get("warnings", [])
            call_meta = cached.get("call", {})
            validate_stage2(result, batch_scope, set(identifiers))
            print(f"STAGE 2 [{index:02d}/{len(scoring_batches)}] RESUME {','.join(codes)}", flush=True)
        else:
            parsed_path = prefix.with_suffix(".json")
            response_path = prefix.with_suffix(".response.json")
            if parsed_path.exists() and response_path.exists():
                result = read_json(parsed_path)
                response_record = read_json(response_path)
                call_meta = {
                    "response_id": response_record.get("id"),
                    "usage": response_record.get("usage", {}),
                    "elapsed_seconds": 0,
                    "reused_completed_response": True,
                }
                print(f"STAGE 2 [{index:02d}/{len(scoring_batches)}] REUSE  {','.join(codes)}", flush=True)
            else:
                print(f"STAGE 2 [{index:02d}/{len(scoring_batches)}] START  {','.join(codes)} | chars={len(compiled):,}", flush=True)
                result, call_meta = call_model_json(
                    client=client,
                    langfuse=langfuse,
                    prompt_object=prompt,
                    compiled_prompt=compiled,
                    stage_name="dema-stage2-negative-source-sensitivity-p5",
                    model=model,
                    temperature=0,
                    max_output_tokens=32768,
                    metadata={
                        "run_id": manifest["run_id"],
                        "experiment": "negative-source-60-strong",
                        "batch_index": index,
                        "batch_total": len(scoring_batches),
                        "scoring_scope": codes,
                        "evidence_count": len(items),
                        "databank_sha256": sha256_text(databank),
                    },
                    artifact_prefix=prefix,
                    json_mode=True,
                )
            result, repairs = repair_evidence_id_padding(
                result, set(identifiers), prefix="EV", match_suffix=True
            )
            result, locator_repairs = remove_redundant_source_locator_citations(result, evidence_lookup)
            repairs.extend(locator_repairs)
            batch_warnings = validate_stage2(result, batch_scope, set(identifiers))
            atomic_write_json(validated_path, {
                "validated_at": utc_now(), "warnings": batch_warnings,
                "citation_repairs": repairs, "call": call_meta, "result": result,
            })
            print(f"STAGE 2 [{index:02d}/{len(scoring_batches)}] DONE   {','.join(codes)} | warnings={len(batch_warnings)}", flush=True)
        final_assessments.extend(result["indicator_assessments"])
        if str(result.get("assessment_summary", "")).strip():
            summaries.append(result["assessment_summary"].strip())
        warnings.extend(f"batch {index}: {warning}" for warning in batch_warnings)
        manifest["calls"].append({"batch": index, "scope": codes, **call_meta})
        manifest["batches_completed"] = index
        atomic_write_json(manifest_path, manifest)

    by_code = {x["indicator_code"]: x for x in final_assessments}
    final_assessments = [by_code[x["indicator_code"]] for x in scope]
    retry_number = len(scoring_batches)
    warnings = [w for w in warnings if "A.1.3:" not in w or w.startswith(f"batch {retry_number}:")]
    final_score = {
        "country": bank.get("country", "Togo"),
        "framework_version": "current DEMA maturity framework supplied in frozen Stage 2 P5",
        "assessment_summary": "\n\n".join(summaries),
        "indicator_assessments": final_assessments,
    }
    validate_stage2(final_score, scope, set(identifiers))
    atomic_write_json(OUTPUT / "final_score.json", final_score)
    atomic_write_json(OUTPUT / "final_score.validated.json", {
        "validated_at": utc_now(), "warnings": warnings, "result": final_score,
    })
    analysis = analyse(final_score, bank)
    atomic_write_json(OUTPUT / "negative_source_results.json", analysis)
    manifest.update({
        "status": "complete", "completed_at": utc_now(),
        "validation_warnings": warnings, "results": analysis,
    })
    atomic_write_json(manifest_path, manifest)
    langfuse.flush()
    print("COMPLETE", flush=True)
    print(json.dumps({key: value for key, value in analysis.items() if key != "indicator_results"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
