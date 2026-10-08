"""Build the DEMA negative-source sensitivity-test evidence bank.

Creates a pristine evaluation-bank copy, retains two previously used strong
records selected with a fixed random seed, and adds five low-information
synthetic controls for every DEMA indicator. Synthetic status is recorded in a
separate manifest and is not exposed as a record-level label in the test bank.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dema.storage import atomic_write_json as write_json, read_json


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "dema_run"
OUT = RUN / "negative_source_test"
COMBINED = RUN / "combined_evidence_bank.json"
RATED = RUN / "sensitivity_analysis" / "nondevelopment_evidence_bank_strength_rated.json"
SEED = 20260917


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def broad_dimension(code: str) -> str:
    mappings = {
        "A.1": "A.1 Roles",
        "A.2": "A.2 Capacity",
        "B.1": "B.1 Data supply (quality and production)",
        "B.2": "B.2 Data infrastructure (enablers)",
        "B.3": "B.3 Data demand (use)",
        "C.1": "C.1 Governance, ethics & trust",
        "C.2": "C.2 Policies, standards & resources",
        "C.3": "C.3 Collaboration & inclusion",
    }
    for prefix, label in mappings.items():
        if code.startswith(prefix):
            return label
    raise ValueError(f"Unknown indicator code: {code}")


def synthetic_records(scoring_scope: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    serial = 1
    for indicator in scoring_scope:
        code = indicator["indicator_code"]
        name = indicator["indicator_name"]
        templates = [
            {
                "class": "agenda_mention",
                "scope": "Country-specific",
                "specificity": "Direct",
                "quote": f"The meeting agenda included a discussion item entitled ‘{name}’. Time was reserved for general observations from participants.",
                "statement": f"A meeting agenda in Togo mentioned {name} as a discussion topic.",
                "boundary": "The record only establishes that the topic appeared on an agenda; it provides no decision, implementation, practice, coverage, result, or identified gap.",
            },
            {
                "class": "future_possibility",
                "scope": "Country-specific",
                "specificity": "Indirect",
                "quote": f"Participants noted that issues related to {name} could be considered during future activities, subject to additional consultation and available resources.",
                "statement": f"Participants expressed possible future interest in {name}.",
                "boundary": "This is a conditional expression of interest and does not document a commitment, funded activity, implementation, output, or maturity-relevant condition.",
            },
            {
                "class": "glossary_reference",
                "scope": "Country-specific",
                "specificity": "Indirect",
                "quote": f"For the purposes of the introductory brochure, ‘{name}’ appeared in a glossary of terms that may be encountered in data-related discussions.",
                "statement": f"An introductory brochure included the term {name} in a glossary.",
                "boundary": "A glossary entry does not establish that the described capability, governance arrangement, or practice exists or is used in Togo.",
            },
            {
                "class": "presentation_attendance",
                "scope": "Country-specific",
                "specificity": "Direct",
                "quote": f"Attendees participated in an introductory presentation that mentioned {name}. The attendance note did not record decisions, assigned responsibilities, follow-up actions, or results.",
                "statement": f"An introductory presentation attended in Togo mentioned {name}.",
                "boundary": "Attendance and topic exposure do not demonstrate capacity, adoption, implementation, institutionalization, outcomes, or an ecosystem-level gap.",
            },
            {
                "class": "generic_external_comment",
                "scope": "Context-only",
                "specificity": "Not country-specific",
                "quote": f"A general international presentation observed that organisations sometimes discuss {name} when considering data initiatives. No country example or empirical result was supplied.",
                "statement": f"A generic international presentation referred to {name}.",
                "boundary": "The statement is generic, contains no evidence about Togo, and provides no basis for distinguishing a DEMA maturity phase.",
            },
        ]
        for number, template in enumerate(templates, start=1):
            evidence_id = f"EVT-{serial:04d}"
            source_id = f"SD-{serial:04d}"
            item = {
                "evidence_id": evidence_id,
                "dimension": broad_dimension(code),
                "subdimension": f"{code} {name}",
                "evidence_status": "Evidence present",
                "evidence_scope": template["scope"],
                "country_specificity": template["specificity"],
                "use_in_country_assessment": "Potential contextual reference requiring assessment against the quoted content.",
                "supporting_quote": template["quote"],
                "evidence_statement": template["statement"],
                "interpretation_boundary": template["boundary"],
                "source_id": source_id,
                "source_file": f"supplementary_document_{serial:04d}.pdf",
                "source_url": f"https://document-register.test/supplementary-document-{serial:04d}",
                "page_number": "1",
                "processing_unit_id": f"supplementary_document_{serial:04d}_page_001",
                "source_chunk": f"supplementary_document_{serial:04d}/page_001.md",
            }
            items.append(item)
            manifest.append({
                "evidence_id": evidence_id,
                "record_type": "synthetic_low_quality_control",
                "control_class": template["class"],
                "target_indicator_code": code,
                "target_indicator_name": name,
                "expected_scoring_value": "none",
                "reason": template["boundary"],
            })
            serial += 1
    return items, manifest


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    combined = read_json(COMBINED)
    evaluation_items = [x for x in combined["evidence_items"] if "::" in str(x.get("evidence_id", ""))]
    if len(evaluation_items) != 232:
        raise ValueError(f"Expected 232 evaluation records, found {len(evaluation_items)}")

    source_copy = {
        "dataset_name": "nondevelopment_evaluation_evidence_bank_source_copy_for_variant_b",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": len(evaluation_items),
        "scoring_scope": combined["scoring_scope"],
        "evidence_items": evaluation_items,
    }
    source_copy_path = OUT / "nondevelopment_evidence_bank_source_copy.json"
    write_json(source_copy_path, source_copy)

    rated = read_json(RATED)["evidence_items"]
    eligible = sorted(
        x["evidence_id"] for x in rated
        if x["strength_rating"] == "strong" and x["used_in_final_justification"]
    )
    retained_ids = random.Random(SEED).sample(eligible, 2)
    original_by_id = {x["evidence_id"]: x for x in evaluation_items}
    retained = [original_by_id[evidence_id] for evidence_id in retained_ids]

    synthetic, synthetic_manifest = synthetic_records(combined["scoring_scope"])
    experimental_items = retained + synthetic
    experimental_bank = {
        "dataset_name": "held_out_evidence_bank_variant_b",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "country": combined.get("country", "Togo"),
        "scoring_scope": combined["scoring_scope"],
        "instruction": "Score every indicator in scoring_scope exactly once using only evidence_items.",
        "evidence_item_count": len(experimental_items),
        "evidence_items": experimental_items,
    }
    bank_path = OUT / "nondevelopment_evidence_bank_variant_b.json"
    write_json(bank_path, experimental_bank)

    manifest = {
        "experiment": "negative-source sensitivity test",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": SEED,
        "selection_rule": "Two records sampled with a fixed seed from evaluation records rated strong and previously used in the final Stage 2 justification.",
        "source_evaluation_records": len(evaluation_items),
        "eligible_genuine_records": len(eligible),
        "retained_genuine_records": len(retained),
        "retained_genuine_evidence_ids": retained_ids,
        "indicators": len(combined["scoring_scope"]),
        "synthetic_records_per_indicator": 5,
        "synthetic_records": len(synthetic),
        "experimental_bank_records": len(experimental_items),
        "bank_sha256": sha256(bank_path),
        "design_note": "The five control classes are topically matched but contain no substantive information that can justify a maturity phase. Explicit statements of ecosystem failure were avoided because valid gap evidence could legitimately support a low maturity score.",
        "synthetic_record_manifest": synthetic_manifest,
    }
    write_json(OUT / "negative_source_test_manifest.json", manifest)

    with (OUT / "negative_source_test_manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["evidence_id", "record_type", "control_class", "target_indicator_code", "target_indicator_name", "expected_scoring_value", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(synthetic_manifest)

    # Validation invariants
    assert len(combined["scoring_scope"]) == 31
    assert len(synthetic) == 155
    assert len(experimental_items) == 157
    assert len({x["evidence_id"] for x in experimental_items}) == 157
    counts = {scope["indicator_code"]: 0 for scope in combined["scoring_scope"]}
    for row in synthetic_manifest:
        counts[row["target_indicator_code"]] += 1
    assert set(counts.values()) == {5}

    print(json.dumps({
        "source_copy_records": len(evaluation_items),
        "retained_genuine_records": retained_ids,
        "synthetic_records": len(synthetic),
        "records_per_indicator": sorted(set(counts.values())),
        "experimental_bank_records": len(experimental_items),
        "bank_sha256": manifest["bank_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
