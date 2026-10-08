"""Read-only final integrity summary for the frozen DEMA run."""
from collections import Counter
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2] / "dema_run"
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
bank = json.loads((root / "combined_evidence_bank.json").read_text(encoding="utf-8"))
score_path = root / "stage2" / "final_score.json"
final = json.loads(score_path.read_text(encoding="utf-8"))
rejected = json.loads((root / "stage1_rejected_rows.json").read_text(encoding="utf-8"))
evidence_ids = {str(item["evidence_id"]) for item in bank["evidence_items"]}
rows = final["indicator_assessments"]
references = [
    evidence_id
    for assessment in rows
    for field in ("evidence_supporting_score", "contrary_or_limiting_evidence")
    for evidence_id in assessment.get(field, [])
]
repairs = []
for call in manifest.get("stage2_calls", []):
    codes = call["scope"]
    stem = (
        f"batch_{call['batch']:02d}_{codes[0].replace('.', '_')}_to_"
        f"{codes[-1].replace('.', '_')}_fullbank"
    )
    candidates = sorted((root / "stage2").glob(f"{stem}*.validated.json"))
    if not candidates:
        raise FileNotFoundError(f"No validated artifact found for {stem}")
    # A suffixed file is a later retry and therefore supersedes the base artifact.
    validation = json.loads(candidates[-1].read_text(encoding="utf-8"))
    repairs.extend(validation.get("citation_repairs", []))

summary = {
    "status": manifest["status"],
    "chunks": manifest["held_out_chunk_count"],
    "stage1_accepted": manifest["stage1_accepted_rows"],
    "stage1_rejected": manifest["stage1_rejected_rows"],
    "combined_evidence": manifest["combined_evidence_count"],
    "indicators": len(rows),
    "unique_indicator_codes": len({row["indicator_code"] for row in rows}),
    "phase_distribution": dict(sorted(Counter(row["phase_score"] for row in rows).items())),
    "unknown_list_references": sorted(set(references) - evidence_ids),
    "citation_repairs": len(repairs),
    "rejection_reasons": dict(Counter(
        reason for item in rejected for reason in item["reasons"]
    )),
    "warnings": manifest.get("stage2_validation_warnings", []),
    "stage1_usage": manifest.get("stage1_usage", {}),
    "stage2_batches": len(manifest.get("stage2_calls", [])),
    "final_sha256": hashlib.sha256(score_path.read_bytes()).hexdigest(),
    "final_bytes": score_path.stat().st_size,
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
