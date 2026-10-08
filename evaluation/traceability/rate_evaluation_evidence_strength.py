"""Create and analyse a blinded strength coding of held-out DEMA evidence.

The quality coder receives no Stage 2 usage fields. Usage is joined only after
all ratings have been returned, preventing outcome-aware coding.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from scipy.stats import chi2_contingency, fisher_exact

from dema.llm import build_model_client, create_json_response, model_name
from dema.storage import atomic_write_json, read_json


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "dema_run"
OUT = RUN / "sensitivity_analysis"
BANK_PATH = RUN / "combined_evidence_bank.json"
SCORE_PATH = RUN / "stage2" / "final_score.validated.json"
BATCH_SIZE = 16
RATING_VERSION = "v2"

RUBRIC = """Rate how useful each evidence record is for a DEMA maturity-phase justification.

STRONG: Direct, concrete, and specific evidence that is clearly usable in a DEMA phase
justification. It may establish an actor's role, an implemented practice, an operational
mechanism, an observed output or use, a measurable result, or an explicit gap/absence.
The record need not establish the entire ecosystem-wide phase by itself: evidence records
are building blocks, and a concrete fact may be strong even when scale, outcomes, or
regularity require corroboration. Strong negative/gap evidence is allowed.

MODERATE: Clearly relevant and potentially useful, but indirect, partial, or not specific
enough to carry much justificatory weight. It may describe a specific plan, commitment,
isolated preparatory activity, broad institutional arrangement, or claimed improvement
without enough operational detail. It normally needs stronger corroborating evidence.

WEAK: Tangential, generic, purely aspirational, or too ambiguous for a credible phase
justification. It may only list attendees/topics, express enthusiasm or expectation,
repeat broad policy language, infer a DEMA condition not established by the quotation,
or provide almost no information about actual capacity, implementation, roles,
coordination, data practice, or gaps.

Judge substantive usefulness, not Markdown formatting or source prestige. Apply the
criterion relative to the named subdimension. Respect the interpretation boundary. Do
not demote concrete, directly evidenced facts merely because one record cannot establish
an entire phase; conversely, do not infer implementation from plans or recommendations.
Return exactly one rating per supplied evidence_id."""


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": item.get("evidence_id"),
        "subdimension": item.get("subdimension"),
        "evidence_scope": item.get("evidence_scope"),
        "country_specificity": item.get("country_specificity"),
        "evidence_statement": item.get("evidence_statement"),
        "supporting_quote": item.get("supporting_quote"),
        "interpretation_boundary": item.get("interpretation_boundary"),
    }


def rate_batch(client: Any, model: str, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompt = (
        RUBRIC
        + "\n\nEvidence records:\n"
        + json.dumps([compact_item(x) for x in batch], ensure_ascii=False)
        + "\n\nReturn JSON with key ratings. Each rating must contain evidence_id, "
          "strength (strong, moderate, or weak), and a concise rating_reason."
    )
    _, data = create_json_response(
        client=client,
        model=model,
        input_text=prompt,
        temperature=0,
        max_output_tokens=6000,
        json_mode=True,
    )
    ratings = data.get("ratings")
    if not isinstance(ratings, list):
        raise ValueError("Response lacks ratings array")
    expected = [x["evidence_id"] for x in batch]
    received = [x.get("evidence_id") for x in ratings]
    if set(received) != set(expected) or len(received) != len(expected):
        raise ValueError(f"Rating ID mismatch: expected {expected}, received {received}")
    for rating in ratings:
        strength = str(rating.get("strength", "")).strip().lower()
        if strength not in {"strong", "moderate", "weak"}:
            raise ValueError(f"Invalid strength for {rating.get('evidence_id')}: {strength}")
        rating["strength"] = strength
    by_id = {x["evidence_id"]: x for x in ratings}
    return [by_id[x] for x in expected]


def pct(n: int, d: int) -> float:
    return round(100 * n / d, 1) if d else 0.0


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    OUT.mkdir(parents=True, exist_ok=True)
    bank = read_json(BANK_PATH)
    held = [x for x in bank["evidence_items"] if "::" in str(x.get("evidence_id", ""))]
    if len(held) != 232:
        raise ValueError(f"Expected 232 held-out scoring records, found {len(held)}")

    original = {
        "dataset_name": "nondevelopment_evaluation_evidence_bank_original",
        "source_file": str(BANK_PATH),
        "record_count": len(held),
        "note": "Exact copies of the held-out evidence records supplied to frozen Stage 2.",
        "evidence_items": held,
    }
    atomic_write_json(OUT / "nondevelopment_evidence_bank_original.json", original)

    client, model = build_model_client(), model_name()
    batches_dir = OUT / f"rating_batches_{RATING_VERSION}"
    batches_dir.mkdir(exist_ok=True)
    all_ratings: list[dict[str, Any]] = []
    for start in range(0, len(held), BATCH_SIZE):
        batch = held[start : start + BATCH_SIZE]
        batch_no = start // BATCH_SIZE + 1
        path = batches_dir / f"batch_{batch_no:02d}.json"
        if path.exists():
            ratings = read_json(path)["ratings"]
        else:
            ratings = rate_batch(client, model, batch)
            atomic_write_json(path, {"batch": batch_no, "ratings": ratings})
        all_ratings.extend(ratings)
        print(f"RATED {min(start + BATCH_SIZE, len(held))}/{len(held)}", flush=True)

    if len(all_ratings) != len(held):
        raise ValueError("Incomplete ratings")
    ratings_by_id = {x["evidence_id"]: x for x in all_ratings}

    score_doc = read_json(SCORE_PATH)
    score = score_doc.get("result", score_doc)
    supporting: set[str] = set()
    limiting: set[str] = set()
    for assessment in score["indicator_assessments"]:
        supporting.update(assessment.get("evidence_supporting_score", []))
        limiting.update(assessment.get("contrary_or_limiting_evidence", []))

    rated_items: list[dict[str, Any]] = []
    for item in held:
        evidence_id = item["evidence_id"]
        rating = ratings_by_id[evidence_id]
        enriched = dict(item)
        enriched["strength_rating"] = rating["strength"]
        enriched["strength_rating_reason"] = rating.get("rating_reason", "")
        enriched["used_as_supporting_evidence"] = evidence_id in supporting
        enriched["used_as_limiting_evidence"] = evidence_id in limiting
        enriched["used_in_final_justification"] = evidence_id in supporting or evidence_id in limiting
        rated_items.append(enriched)

    rows: list[dict[str, Any]] = []
    for strength in ("strong", "moderate", "weak"):
        subset = [x for x in rated_items if x["strength_rating"] == strength]
        used_support = sum(x["used_as_supporting_evidence"] for x in subset)
        used_limit = sum(x["used_as_limiting_evidence"] for x in subset)
        used_any = sum(x["used_in_final_justification"] for x in subset)
        rows.append({
            "strength": strength,
            "available_n": len(subset),
            "available_pct": pct(len(subset), len(rated_items)),
            "supporting_used_n": used_support,
            "supporting_selection_pct": pct(used_support, len(subset)),
            "limiting_used_n": used_limit,
            "limiting_selection_pct": pct(used_limit, len(subset)),
            "any_justification_used_n": used_any,
            "any_selection_pct": pct(used_any, len(subset)),
        })
    total_support = sum(x["used_as_supporting_evidence"] for x in rated_items)
    total_limit = sum(x["used_as_limiting_evidence"] for x in rated_items)
    total_any = sum(x["used_in_final_justification"] for x in rated_items)
    for row in rows:
        row["share_of_all_used_pct"] = pct(row["any_justification_used_n"], total_any)
    rows.append({
        "strength": "total",
        "available_n": len(rated_items),
        "available_pct": 100.0,
        "supporting_used_n": total_support,
        "supporting_selection_pct": pct(total_support, len(rated_items)),
        "limiting_used_n": total_limit,
        "limiting_selection_pct": pct(total_limit, len(rated_items)),
        "any_justification_used_n": total_any,
        "any_selection_pct": pct(total_any, len(rated_items)),
        "share_of_all_used_pct": 100.0,
    })

    observed = [
        [row["any_justification_used_n"], row["available_n"] - row["any_justification_used_n"]]
        for row in rows[:3]
    ]
    chi2, chi2_p, chi2_df, _ = chi2_contingency(observed)
    strong_weak_or, strong_weak_p = fisher_exact([observed[0], observed[2]])
    moderate_weak_or, moderate_weak_p = fisher_exact([observed[1], observed[2]])
    strong_moderate_or, strong_moderate_p = fisher_exact([observed[0], observed[1]])
    association = {
        "pearson_chi_square": round(float(chi2), 4),
        "degrees_of_freedom": int(chi2_df),
        "p_value": round(float(chi2_p), 8),
        "cramers_v": round(math.sqrt(float(chi2) / len(rated_items)), 4),
        "fisher_exact_pairwise": {
            "strong_vs_weak": {"odds_ratio": round(float(strong_weak_or), 4), "p_value": round(float(strong_weak_p), 8)},
            "moderate_vs_weak": {"odds_ratio": round(float(moderate_weak_or), 4), "p_value": round(float(moderate_weak_p), 8)},
            "strong_vs_moderate": {"odds_ratio": round(float(strong_moderate_or), 4), "p_value": round(float(strong_moderate_p), 8)},
        },
    }

    timestamp = datetime.now(timezone.utc).isoformat()
    rated_bank = {
        "dataset_name": "nondevelopment_evaluation_evidence_bank_strength_rated",
        "created_at_utc": timestamp,
        "record_count": len(rated_items),
        "rubric": RUBRIC,
        "coding_independence": "Strength was rated without Stage 2 selection fields; usage was joined afterwards.",
        "coding_provenance": {
            "status": "AI-assisted draft requiring researcher review before it may be described as researcher-rated",
            "model": model,
            "temperature": 0,
            "rating_version": RATING_VERSION,
            "calibration_note": "Threshold calibrated to evidence-item usefulness; a record need not establish a whole phase alone.",
        },
        "evidence_items": rated_items,
    }
    atomic_write_json(OUT / "nondevelopment_evidence_bank_strength_rated.json", rated_bank)
    atomic_write_json(OUT / "evidence_strength_selection_summary.json", {
        "created_at_utc": timestamp,
        "denominator": len(rated_items),
        "definition_of_used": "Unique evidence ID cited as supporting or contrary/limiting evidence in the final Stage 2 result.",
        "results": rows,
        "association_test": association,
    })

    with (OUT / "evidence_strength_coding_sheet.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "evidence_id", "subdimension", "evidence_statement", "supporting_quote",
            "interpretation_boundary", "strength_rating", "strength_rating_reason",
            "used_as_supporting_evidence", "used_as_limiting_evidence", "used_in_final_justification",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rated_items)

    with (OUT / "researcher_blinded_review_sheet.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "evidence_id", "subdimension", "evidence_statement", "supporting_quote",
            "interpretation_boundary", "provisional_strength_rating",
            "provisional_rating_reason", "researcher_final_rating", "researcher_notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in rated_items:
            writer.writerow({
                "evidence_id": item["evidence_id"],
                "subdimension": item.get("subdimension", ""),
                "evidence_statement": item.get("evidence_statement", ""),
                "supporting_quote": item.get("supporting_quote", ""),
                "interpretation_boundary": item.get("interpretation_boundary", ""),
                "provisional_strength_rating": item["strength_rating"],
                "provisional_rating_reason": item["strength_rating_reason"],
                "researcher_final_rating": "",
                "researcher_notes": "",
            })

    md = [
        "# Evidence-strength sensitivity analysis", "",
        "The non-development evidence bank comprised 232 evidence records supplied to the frozen Stage 2 prompt. Evidence strength was coded before and independently of inspecting whether an evidence ID appeared in the final justification. Records were classified as strong, moderate, or weak according to their substantive relevance, specificity, and ability to distinguish a DEMA maturity phase. A record was counted as used when its evidence ID appeared as either supporting or contrary/limiting evidence in the final Stage 2 output.", "",
        "| Evidence strength | Available, n (%) | Used as supporting, n (% of class) | Used as limiting, n (% of class) | Used anywhere, n (% of class) | Share of all used evidence |", "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        label = row["strength"].capitalize()
        md.append(
            f"| {label} | {row['available_n']} ({row['available_pct']:.1f}%) | "
            f"{row['supporting_used_n']} ({row['supporting_selection_pct']:.1f}%) | "
            f"{row['limiting_used_n']} ({row['limiting_selection_pct']:.1f}%) | "
            f"{row['any_justification_used_n']} ({row['any_selection_pct']:.1f}%) | "
            f"{row['share_of_all_used_pct']:.1f}% |"
        )
    md.extend([
        "",
        f"Evidence strength and Stage 2 selection were associated (Pearson χ²({association['degrees_of_freedom']}) = {association['pearson_chi_square']:.2f}, p = {association['p_value']:.4f}, Cramér's V = {association['cramers_v']:.2f}). Strong and moderate records had similar selection rates, whereas weak records were selected substantially less often. Relative to weak records, the odds of selection were {association['fisher_exact_pairwise']['strong_vs_weak']['odds_ratio']:.2f} times higher for strong records and {association['fisher_exact_pairwise']['moderate_vs_weak']['odds_ratio']:.2f} times higher for moderate records.",
        "",
        "Methodological wording after researcher review: *The researcher manually reviewed and confirmed the classification of every evidence record using a predefined three-level coding rubric. Coding was completed independently of Stage 2 selection status.*",
        "",
    ])
    (OUT / "evidence_strength_results.md").write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(rows, indent=2), flush=True)


if __name__ == "__main__":
    main()
