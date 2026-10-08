"""Read-only traceability analysis for reporting the frozen DEMA experiment."""
from collections import Counter
from pathlib import Path
import csv
import json
import re


ROOT = Path(__file__).resolve().parents[2]
DEV_ROOT = ROOT / "final_substantive_corpus_files" / "development sources"
HELD_ROOT = ROOT / "final_substantive_corpus_files" / "chunks"
BASE = json.loads((ROOT / "evidence_bank_v4_indicator_defined_for_maturity_scoring.json").read_text(encoding="utf-8"))
COMBINED = json.loads((ROOT / "dema_run" / "combined_evidence_bank.json").read_text(encoding="utf-8"))
SCORE = json.loads((ROOT / "dema_run" / "stage2" / "final_score.json").read_text(encoding="utf-8"))
REJECTED = json.loads((ROOT / "dema_run" / "stage1_rejected_rows.json").read_text(encoding="utf-8"))


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def source_id(item):
    explicit = str(item.get("source_id", ""))
    if re.fullmatch(r"\d{3}", explicit):
        return explicit
    for field in ("source_chunk", "source_file"):
        match = re.search(r"(?<!\d)(\d{3})(?!\d)", str(item.get(field, "")))
        if match:
            return match.group(1)
    return None


def chunk_path(item):
    relative = str(item.get("source_chunk", "")).replace("\\", "/")
    if not relative:
        return None
    root = DEV_ROOT if str(item.get("evidence_id", "")).startswith("V4ID-") else HELD_ROOT
    return root.joinpath(*relative.split("/"))


def completeness(items):
    fields = ("evidence_id", "supporting_quote", "source_url", "page_number", "source_chunk", "source_file")
    result = {field: sum(nonblank(item.get(field)) for item in items) for field in fields}
    result["source_locator_either"] = sum(
        nonblank(item.get("source_chunk")) or nonblank(item.get("source_file")) for item in items
    )
    return result


def duplicate_summary(items, field):
    counts = Counter(str(item.get(field, "")).strip() for item in items if nonblank(item.get(field)))
    groups = {value: count for value, count in counts.items() if count > 1}
    return {
        "duplicate_groups": len(groups),
        "records_in_duplicate_groups": sum(groups.values()),
        "excess_repetitions": sum(count - 1 for count in groups.values()),
    }


def corpus_trace(items):
    result = Counter()
    for item in items:
        path = chunk_path(item)
        if path is not None and not path.exists():
            # Some development paths exceed the legacy Windows MAX_PATH limit.
            long_path = Path("\\\\?\\" + str(path.resolve()))
            if long_path.exists():
                path = long_path
        if path is None or not path.exists():
            result["chunk_missing"] += 1
            continue
        result["chunk_found"] += 1
        text = path.read_text(encoding="utf-8")
        quote = str(item.get("supporting_quote", ""))
        if quote and quote in text:
            result["quote_exact"] += 1
        elif item.get("technical_validation_status") == "PASS_NORMALIZED":
            result["quote_normalized_status"] += 1
        else:
            result["quote_not_exact"] += 1
        page = str(item.get("page_number", "")).strip()
        marker = re.compile(rf"page_number=[\"']?{re.escape(page)}(?:\D|$)")
        heading = re.compile(rf"^## Page {re.escape(page)}\s*$", re.MULTILINE)
        if page and (marker.search(text) or heading.search(text)):
            result["page_marker_found"] += 1
        else:
            result["page_marker_not_found"] += 1
    return dict(result)


def strict_quote_failures(items):
    failures = []
    for item in items:
        path = chunk_path(item)
        if path is not None and not path.exists():
            long_path = Path("\\\\?\\" + str(path.resolve()))
            if long_path.exists():
                path = long_path
        if path is None or not path.exists():
            continue
        quote = str(item.get("supporting_quote", ""))
        if quote and quote not in path.read_text(encoding="utf-8"):
            failures.append({
                "evidence_id": item.get("evidence_id"),
                "source_id": source_id(item),
                "page_number": item.get("page_number"),
                "technical_status": item.get("technical_validation_status"),
            })
    return {
        "count": len(failures),
        "by_source": Counter(item["source_id"] for item in failures),
        "by_status": Counter(item["technical_status"] for item in failures),
        "items": failures,
    }


with (ROOT / "final_substantive_corpus_files" / "corpus_index.csv").open(encoding="utf-8-sig", newline="") as handle:
    corpus_index = {row["source_id"]: row for row in csv.DictReader(handle)}


def url_match(items):
    matches = mismatches = missing = 0
    for item in items:
        sid = source_id(item)
        url = str(item.get("source_url", "")).strip()
        expected = corpus_index.get(sid, {}).get("source_url", "").strip()
        if not url:
            missing += 1
        elif expected and url == expected:
            matches += 1
        else:
            mismatches += 1
    return {"matches_index": matches, "mismatches_index": mismatches, "missing": missing}


base_items = BASE["evidence_items"]
combined_items = COMBINED["evidence_items"]
held_items = [item for item in combined_items if not str(item["evidence_id"]).startswith("V4ID-")]
lookup = {str(item["evidence_id"]): item for item in combined_items}
references = []
for assessment in SCORE["indicator_assessments"]:
    references.extend(assessment.get("evidence_supporting_score", []))
    references.extend(assessment.get("contrary_or_limiting_evidence", []))
unique_references = sorted(set(references))
cited_items = [lookup[reference] for reference in unique_references if reference in lookup]

report = {
    "development_flow": {
        "generated": BASE["generated_row_count"],
        "technical_accepted_before_ais": BASE["technically_accepted_before_ais"],
        "ais_counts_all_generated": BASE["ais_status_counts_all_generated_rows"],
        "final_scoring_items": len(base_items),
        "total_excluded": BASE["generated_row_count"] - len(base_items),
        "retention_percent": round(100 * len(base_items) / BASE["generated_row_count"], 1),
        "final_technical_statuses": Counter(item.get("technical_validation_status") for item in base_items),
        "final_ais_statuses": Counter(item.get("ais_validation_status") for item in base_items),
    },
    "held_out_flow": {
        "generated": len(held_items) + len(REJECTED),
        "retained": len(held_items),
        "excluded": len(REJECTED),
        "retention_percent": round(100 * len(held_items) / (len(held_items) + len(REJECTED)), 1),
        "rejection_reasons": Counter(reason for row in REJECTED for reason in row["reasons"]),
    },
    "combined": {
        "items": len(combined_items),
        "unique_ids": len(set(str(item["evidence_id"]) for item in combined_items)),
        "completeness": completeness(combined_items),
        "development_completeness": completeness(base_items),
        "held_out_completeness": completeness(held_items),
        "technical_statuses_development": Counter(item.get("technical_validation_status") for item in base_items),
        "duplicate_quotes": duplicate_summary(combined_items, "supporting_quote"),
        "duplicate_statements": duplicate_summary(combined_items, "evidence_statement"),
        "development_corpus_trace": corpus_trace(base_items),
        "held_out_corpus_trace": corpus_trace(held_items),
        "development_strict_quote_failures": strict_quote_failures(base_items),
        "url_index_comparison": url_match(combined_items),
    },
    "final_justifications": {
        "references": len(references),
        "unique_referenced_ids": len(unique_references),
        "resolved_references": sum(reference in lookup for reference in references),
        "unresolved_reference_occurrences": sum(reference not in lookup for reference in references),
        "cited_item_completeness": completeness(cited_items),
        "cited_corpus_trace": corpus_trace(cited_items),
        "cited_strict_quote_failures": strict_quote_failures(cited_items),
        "cited_url_index_comparison": url_match(cited_items),
    },
}

print(json.dumps(report, ensure_ascii=False, indent=2, default=dict))
