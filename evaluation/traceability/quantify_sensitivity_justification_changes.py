"""Quantify changes between baseline and negative-source justifications."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import Any

from dema.storage import read_json as read


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "dema_run" / "stage2" / "final_score.validated.json"
EXPERIMENT = ROOT / "dema_run" / "negative_source_test" / "stage2_60_strong_blinded" / "final_score.validated.json"
MAPPING = ROOT / "dema_run" / "negative_source_test" / "negative_source_test_60_strong_blinded_manifest.json"
OUTPUT = ROOT / "dema_run" / "negative_source_test" / "stage2_60_strong_blinded" / "justification_change_metrics.json"


def result(path: Path) -> dict[str, Any]:
    value = read(path)
    return value.get("result", value)


def words(text: str) -> list[str]:
    return re.findall(r"\b[^\W_]+(?:[’'-][^\W_]+)*\b", text, flags=re.UNICODE)


def citation_summary(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    support = [identifier for row in assessments for identifier in row.get("evidence_supporting_score", [])]
    limiting = [identifier for row in assessments for identifier in row.get("contrary_or_limiting_evidence", [])]
    return {
        "supporting_occurrences": len(support),
        "limiting_occurrences": len(limiting),
        "all_occurrences": len(support) + len(limiting),
        "unique_supporting": len(set(support)),
        "unique_limiting": len(set(limiting)),
        "unique_any": len(set(support) | set(limiting)),
    }


def text_metrics(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    counts = [len(words(str(row.get("score_reasoning", "")))) for row in assessments]
    text = "\n".join(str(row.get("score_reasoning", "")) for row in assessments).lower()
    patterns = {
        "no_evidence": r"\bno evidence\b",
        "not_demonstrated": r"\bnot demonstrated\b",
        "no_documentation": r"\bno documentation\b",
        "absence": r"\babsence\b",
        "insufficient": r"\binsufficient\b",
        "does_not_demonstrate": r"\bdoes not demonstrate\b",
        "documentary_gap_language_total": r"\bno evidence\b|\bnot demonstrated\b|\bno documentation\b|\babsence\b|\binsufficient\b|\bdoes not demonstrate\b",
    }
    return {
        "total_words": sum(counts),
        "mean_words": round(statistics.mean(counts), 1),
        "median_words": round(statistics.median(counts), 1),
        "minimum_words": min(counts),
        "maximum_words": max(counts),
        "below_180_words": sum(count < 180 for count in counts),
        "pattern_counts": {name: len(re.findall(pattern, text)) for name, pattern in patterns.items()},
    }


def main() -> None:
    baseline = result(BASELINE)
    experiment = result(EXPERIMENT)
    mapping_doc = read(MAPPING)
    mapping = {x["experimental_evidence_id"]: x for x in mapping_doc["blind_id_mapping"]}
    controls = {key for key, value in mapping.items() if value["record_type"] == "control"}
    genuine = {key for key, value in mapping.items() if value["record_type"] == "genuine"}

    base_rows = baseline["indicator_assessments"]
    exp_rows = experiment["indicator_assessments"]
    base_by_code = {x["indicator_code"]: x for x in base_rows}
    phase_changes = []
    for row in exp_rows:
        base_phase = base_by_code[row["indicator_code"]]["phase_score"]
        phase_changes.append(row["phase_score"] - base_phase)

    exp_all_citations = [
        identifier
        for row in exp_rows
        for field in ("evidence_supporting_score", "contrary_or_limiting_evidence")
        for identifier in row.get(field, [])
    ]
    exp_genuine_occurrences = [x for x in exp_all_citations if x in genuine]
    exp_control_occurrences = [x for x in exp_all_citations if x in controls]
    exp_genuine_unique = set(exp_genuine_occurrences)
    exp_genuine_original = {mapping[x]["original_evidence_id"] for x in exp_genuine_unique}
    baseline_ids = {
        identifier
        for row in base_rows
        for field in ("evidence_supporting_score", "contrary_or_limiting_evidence")
        for identifier in row.get(field, [])
    }
    baseline_used_retained = {
        value["original_evidence_id"]
        for value in mapping.values()
        if value["record_type"] == "genuine" and value.get("used_in_baseline_justification")
    }
    only_controls = 0
    no_controls = 0
    for row in exp_rows:
        cited = set(row.get("evidence_supporting_score", [])) | set(row.get("contrary_or_limiting_evidence", []))
        if cited & controls and not cited & genuine:
            only_controls += 1
        if not cited & controls:
            no_controls += 1

    metrics = {
        "comparison_note": "The baseline is the 622-record full-pipeline run; the experiment contains 60 retained strong evaluation records plus 155 controls. Phase change is therefore descriptive, not a control-only causal effect.",
        "phase": {
            "baseline_distribution": {str(phase): sum(x["phase_score"] == phase for x in base_rows) for phase in range(1, 6)},
            "experimental_distribution": {str(phase): sum(x["phase_score"] == phase for x in exp_rows) for phase in range(1, 6)},
            "baseline_mean": round(statistics.mean(x["phase_score"] for x in base_rows), 2),
            "experimental_mean": round(statistics.mean(x["phase_score"] for x in exp_rows), 2),
            "mean_change": round(statistics.mean(x["phase_score"] for x in exp_rows) - statistics.mean(x["phase_score"] for x in base_rows), 2),
            "unchanged": phase_changes.count(0),
            "decreased_one_phase": phase_changes.count(-1),
            "decreased_two_phases": phase_changes.count(-2),
            "increased": sum(change > 0 for change in phase_changes),
        },
        "justification_length": {
            "baseline": text_metrics(base_rows),
            "experimental": text_metrics(exp_rows),
        },
        "citations": {
            "baseline": citation_summary(base_rows),
            "experimental": citation_summary(exp_rows),
            "experimental_genuine_occurrences": len(exp_genuine_occurrences),
            "experimental_control_occurrences": len(exp_control_occurrences),
            "experimental_control_occurrence_share_pct": round(100 * len(exp_control_occurrences) / len(exp_all_citations), 1),
            "experimental_unique_genuine": len(exp_genuine_unique),
            "experimental_unique_controls": len(set(exp_control_occurrences)),
            "retained_baseline_used_genuine_records": len(baseline_used_retained),
            "retained_baseline_used_reused_in_experiment": len(exp_genuine_original & baseline_used_retained),
            "genuine_records_newly_selected_relative_to_baseline": len(exp_genuine_original - baseline_ids),
            "justifications_using_only_controls": only_controls,
            "justifications_with_no_controls": no_controls,
        },
    }
    OUTPUT.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
