"""Secondary render-aware traceability check for the held-out evaluation set."""
from pathlib import Path
import json
import re
import unicodedata


ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "final_substantive_corpus_files" / "chunks"
COMBINED = json.loads((ROOT / "dema_run" / "combined_evidence_bank.json").read_text(encoding="utf-8"))
REJECTED = json.loads((ROOT / "dema_run" / "stage1_rejected_rows.json").read_text(encoding="utf-8"))


def normalize_visible_text(text: str, source: bool = False) -> str:
    text = unicodedata.normalize("NFKC", text)
    if source:
        # Remove conversion metadata and footnotes inserted between a sentence's
        # final words on one page and its continuation on the adjacent page.
        text = re.sub(
            r"\n\n\d+\s+[^\n]+\n\n## Page \d+\s*\n\n<!--.*?-->\s*\n\n",
            " ", text, flags=re.DOTALL,
        )
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
        text = re.sub(r"(?m)^## Page \d+\s*$", " ", text)
    # Markdown emphasis and list syntax are presentation rather than evidence text.
    text = text.replace("*", "")
    text = re.sub(r"(?m)^\s*-\s+", "", text)
    return re.sub(r"\s+", " ", text).strip()


accepted = [
    item for item in COMBINED["evidence_items"]
    if not str(item["evidence_id"]).startswith("V4ID-")
]
candidates = [
    {
        "evidence_id": item["evidence_id"],
        "chunk": item["source_chunk"],
        "quote": item["supporting_quote"],
        "strict_result": "PASS",
    }
    for item in accepted
]
candidates.extend(
    {
        "evidence_id": rejected["row"]["evidence_id"],
        "chunk": rejected["chunk"],
        "quote": rejected["row"]["supporting_quote"],
        "strict_result": "FAIL",
    }
    for rejected in REJECTED
)

results = []
for candidate in candidates:
    source = (CHUNKS / Path(candidate["chunk"])).read_text(encoding="utf-8")
    # The lenient criterion is monotonic: every strict pass remains a pass.
    passed = candidate["strict_result"] == "PASS" or (
        normalize_visible_text(candidate["quote"]) in normalize_visible_text(source, source=True)
    )
    results.append({
        "evidence_id": candidate["evidence_id"],
        "chunk": candidate["chunk"],
        "strict_result": candidate["strict_result"],
        "lenient_result": "PASS" if passed else "FAIL",
    })

summary = {
    "criterion": (
        "Unicode NFKC and whitespace normalization; Markdown emphasis/list markers ignored; "
        "conversion metadata and page-boundary footnote insertions ignored."
    ),
    "candidate_records": len(results),
    "strict_pass": sum(row["strict_result"] == "PASS" for row in results),
    "lenient_pass": sum(row["lenient_result"] == "PASS" for row in results),
    "lenient_fail": sum(row["lenient_result"] == "FAIL" for row in results),
    "strict_failures_reclassified_as_lenient_pass": [
        row["evidence_id"] for row in results
        if row["strict_result"] == "FAIL" and row["lenient_result"] == "PASS"
    ],
    "remaining_failures": [
        row["evidence_id"] for row in results if row["lenient_result"] == "FAIL"
    ],
}
output = ROOT / "dema_run" / "lenient_traceability_evaluation.json"
output.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(output)
