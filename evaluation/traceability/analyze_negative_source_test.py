"""Produce detailed tables for the blinded negative-source Stage 2 run."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from dema.storage import read_json as read


ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "dema_run" / "negative_source_test"
RUN = TEST / "stage2_60_strong_blinded"
BANK = TEST / "nondevelopment_evidence_bank_60_strong_plus_controls_blinded.json"
MANIFEST = TEST / "negative_source_test_60_strong_blinded_manifest.json"
FINAL = RUN / "final_score.validated.json"
BASELINE = ROOT / "dema_run" / "stage2" / "final_score.validated.json"


def pct(n: int, d: int) -> float:
    return round(100 * n / d, 1) if d else 0.0


def main() -> None:
    bank = read(BANK)
    evidence = {x["evidence_id"]: x for x in bank["evidence_items"]}
    manifest = read(MANIFEST)
    mapping = {x["experimental_evidence_id"]: x for x in manifest["blind_id_mapping"]}
    controls = {key for key, value in mapping.items() if value["record_type"] == "control"}
    genuine = {key for key, value in mapping.items() if value["record_type"] == "genuine"}
    final_doc = read(FINAL)
    final = final_doc.get("result", final_doc)
    baseline_doc = read(BASELINE)
    baseline = baseline_doc.get("result", baseline_doc)
    baseline_phase = {x["indicator_code"]: x["phase_score"] for x in baseline["indicator_assessments"]}

    citations: list[dict[str, Any]] = []
    indicator_rows: list[dict[str, Any]] = []
    for assessment in final["indicator_assessments"]:
        code = assessment["indicator_code"]
        support = assessment.get("evidence_supporting_score", [])
        limiting = assessment.get("contrary_or_limiting_evidence", [])
        for role, identifiers in (("supporting", support), ("limiting", limiting)):
            for evidence_id in identifiers:
                if evidence_id not in controls:
                    continue
                meta = mapping[evidence_id]
                citations.append({
                    "indicator_code": code,
                    "experimental_phase": assessment["phase_score"],
                    "citation_role": role,
                    "evidence_id": evidence_id,
                    "control_class": meta["control_class"],
                    "target_indicator_code": meta["target_indicator_code"],
                    "target_aligned": code == meta["target_indicator_code"],
                    "supporting_quote": evidence[evidence_id]["supporting_quote"],
                    "evidence_statement": evidence[evidence_id]["evidence_statement"],
                    "interpretation_boundary": evidence[evidence_id]["interpretation_boundary"],
                })
        control_support = [x for x in support if x in controls]
        control_limit = [x for x in limiting if x in controls]
        genuine_used = sorted((set(support) | set(limiting)) & genuine)
        indicator_rows.append({
            "indicator_code": code,
            "baseline_full_pipeline_phase": baseline_phase[code],
            "experimental_phase": assessment["phase_score"],
            "phase_delta": assessment["phase_score"] - baseline_phase[code],
            "supporting_control_citations": len(control_support),
            "limiting_control_citations": len(control_limit),
            "unique_controls_used": len(set(control_support) | set(control_limit)),
            "genuine_records_used": len(genuine_used),
        })

    with (RUN / "negative_source_citations.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(citations[0]))
        writer.writeheader()
        writer.writerows(citations)
    with (RUN / "indicator_comparison.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(indicator_rows[0]))
        writer.writeheader()
        writer.writerows(indicator_rows)

    by_class: list[dict[str, Any]] = []
    for control_class in sorted({mapping[x]["control_class"] for x in controls}):
        available = {x for x in controls if mapping[x]["control_class"] == control_class}
        support = {x["evidence_id"] for x in citations if x["control_class"] == control_class and x["citation_role"] == "supporting"}
        limiting = {x["evidence_id"] for x in citations if x["control_class"] == control_class and x["citation_role"] == "limiting"}
        used = support | limiting
        by_class.append({
            "control_class": control_class,
            "available": len(available),
            "supporting_unique": len(support),
            "limiting_unique": len(limiting),
            "any_unique": len(used),
            "selection_rate_pct": pct(len(used), len(available)),
        })

    unique_support = {x["evidence_id"] for x in citations if x["citation_role"] == "supporting"}
    unique_limit = {x["evidence_id"] for x in citations if x["citation_role"] == "limiting"}
    unique_any = unique_support | unique_limit
    supporting_phase1 = [x for x in citations if x["citation_role"] == "supporting" and x["experimental_phase"] == 1]
    supporting_above1 = [x for x in citations if x["citation_role"] == "supporting" and x["experimental_phase"] > 1]
    aligned = sum(bool(x["target_aligned"]) for x in citations)
    summary = {
        "bank_records": len(evidence),
        "genuine_available": len(genuine),
        "controls_available": len(controls),
        "control_citation_occurrences": len(citations),
        "supporting_control_occurrences": sum(x["citation_role"] == "supporting" for x in citations),
        "limiting_control_occurrences": sum(x["citation_role"] == "limiting" for x in citations),
        "unique_controls_used": len(unique_any),
        "unique_supporting_controls": len(unique_support),
        "unique_limiting_controls": len(unique_limit),
        "unique_control_selection_rate_pct": pct(len(unique_any), len(controls)),
        "indicators_with_any_control": sum(x["unique_controls_used"] > 0 for x in indicator_rows),
        "indicator_contamination_rate_pct": pct(sum(x["unique_controls_used"] > 0 for x in indicator_rows), len(indicator_rows)),
        "supporting_control_occurrences_for_phase_1": len(supporting_phase1),
        "supporting_control_occurrences_for_phase_above_1": len(supporting_above1),
        "target_aligned_control_occurrences": aligned,
        "target_alignment_pct": pct(aligned, len(citations)),
        "unique_genuine_records_used": len({identifier for row in final["indicator_assessments"] for field in ("evidence_supporting_score", "contrary_or_limiting_evidence") for identifier in row.get(field, []) if identifier in genuine}),
        "experimental_phase_distribution": {str(phase): sum(x["experimental_phase"] == phase for x in indicator_rows) for phase in range(1, 6)},
        "phase_changes_vs_full_pipeline_baseline": sum(x["phase_delta"] != 0 for x in indicator_rows),
        "validation_warnings": final_doc.get("warnings", []),
        "by_control_class": by_class,
    }
    (RUN / "negative_source_detailed_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Negative-source sensitivity results", "",
        "The frozen Stage 2 P5 prompt (temperature 0) evaluated a blinded bank containing 60 strong genuine records and 155 synthetic low-quality controls. All records used neutral `EV-####` identifiers, and record order was randomized. Control identities were revealed only after scoring.", "",
        "| Measure | Result |", "|---|---:|",
        f"| Genuine records available | {len(genuine)} |",
        f"| Synthetic controls available | {len(controls)} |",
        f"| Unique controls used | {len(unique_any)} ({pct(len(unique_any), len(controls)):.1f}%) |",
        f"| Unique controls used as supporting evidence | {len(unique_support)} |",
        f"| Unique controls used as limiting evidence | {len(unique_limit)} |",
        f"| Control-citation occurrences | {len(citations)} |",
        f"| Indicators containing at least one control | {summary['indicators_with_any_control']}/31 ({summary['indicator_contamination_rate_pct']:.1f}%) |",
        f"| Genuine records used | {summary['unique_genuine_records_used']}/60 ({pct(summary['unique_genuine_records_used'], 60):.1f}%) |",
        "", "## Control use by construction type", "",
        "| Control type | Available | Supporting | Limiting | Used anywhere | Selection rate |", "|---|---:|---:|---:|---:|---:|",
    ]
    for row in by_class:
        md.append(f"| {row['control_class'].replace('_', ' ').title()} | {row['available']} | {row['supporting_unique']} | {row['limiting_unique']} | {row['any_unique']} | {row['selection_rate_pct']:.1f}% |")
    md.extend([
        "", "## Interpretation", "",
        f"Stage 2 cited {len(unique_any)} of the 155 controls. Most control citations were used to characterize missing or insufficient evidence, but {len(unique_support)} controls were placed in the supporting-evidence field. Of the supporting-control citation occurrences, {len(supporting_phase1)} supported Phase 1 assignments and {len(supporting_above1)} appeared in assessments above Phase 1. This indicates that the pipeline frequently treated topically matched but non-probative records as usable evidence, particularly as evidence of limitation or documentary absence.", "",
        "The experimental phase distribution was 18 indicators at Phase 1 and 13 at Phase 2. No indicator received Phase 3 or above. These phase changes must not be attributed solely to synthetic controls because the experimental bank also excluded the development evidence bank and 172 of the 232 genuine evaluation records. A matched 60-strong bank without controls is required to isolate the causal effect of control injection on phase scores.", "",
    ])
    (RUN / "negative_source_results.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
