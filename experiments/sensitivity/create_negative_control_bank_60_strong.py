"""Create a 60-strong + 155-control DEMA Stage 2 sensitivity bank."""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from experiments.sensitivity.create_negative_control_bank import synthetic_records
from dema.storage import atomic_write_json as write_json, read_json


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "dema_run"
OUT = RUN / "negative_source_test"
COMBINED = RUN / "combined_evidence_bank.json"
RATED = RUN / "sensitivity_analysis" / "nondevelopment_evidence_bank_strength_rated.json"
SEED = 20260917


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    combined = read_json(COMBINED)
    originals = [x for x in combined["evidence_items"] if "::" in str(x.get("evidence_id", ""))]
    by_id = {x["evidence_id"]: x for x in originals}
    rated = read_json(RATED)["evidence_items"]

    strong_used = sorted(
        x["evidence_id"] for x in rated
        if x["strength_rating"] == "strong" and x["used_in_final_justification"]
    )
    strong_unused = sorted(
        x["evidence_id"] for x in rated
        if x["strength_rating"] == "strong" and not x["used_in_final_justification"]
    )
    if len(strong_used) != 31 or len(strong_unused) != 52:
        raise ValueError(
            f"Expected 31 used and 52 unused strong records, found {len(strong_used)} and {len(strong_unused)}"
        )
    added = random.Random(SEED).sample(strong_unused, 29)
    retained_ids = strong_used + added
    retained = [by_id[evidence_id] for evidence_id in retained_ids]
    controls, control_manifest = synthetic_records(combined["scoring_scope"])
    control_by_old_id = {x["evidence_id"]: x for x in control_manifest}

    # Blind record type and prevent reconstruction of IDs omitted from the
    # baseline by re-keying every record into one neutral namespace, then
    # randomising order. The analyst-only mapping is stored outside the bank.
    tagged = [("genuine", dict(x)) for x in retained] + [("control", dict(x)) for x in controls]
    random.Random(SEED + 1).shuffle(tagged)
    blinded_items = []
    blind_mapping = []
    for index, (record_type, item) in enumerate(tagged, start=1):
        old_id = item["evidence_id"]
        new_id = f"EV-{index:04d}"
        item["evidence_id"] = new_id
        blinded_items.append(item)
        mapping = {
            "experimental_evidence_id": new_id,
            "record_type": record_type,
            "original_evidence_id": old_id if record_type == "genuine" else None,
        }
        if record_type == "genuine":
            mapping["used_in_baseline_justification"] = old_id in strong_used
        else:
            mapping.update({
                "control_class": control_by_old_id[old_id]["control_class"],
                "target_indicator_code": control_by_old_id[old_id]["target_indicator_code"],
                "expected_scoring_value": "none",
            })
        blind_mapping.append(mapping)

    bank = {
        "dataset_name": "held_out_evidence_bank_variant_d",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "country": combined.get("country", "Togo"),
        "scoring_scope": combined["scoring_scope"],
        "instruction": "Score every indicator in scoring_scope exactly once using only evidence_items.",
        "evidence_item_count": len(blinded_items),
        "evidence_items": blinded_items,
    }
    bank_path = OUT / "nondevelopment_evidence_bank_60_strong_plus_controls_blinded.json"
    write_json(bank_path, bank)

    manifest = {
        "experiment": "negative-source sensitivity test with strong-evidence retention",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": SEED,
        "selection_rule": "Retain all 31 strong evaluation records used in the baseline justification, then sample 29 from the remaining 52 strong records using a fixed seed.",
        "original_evaluation_records": len(originals),
        "strong_records_available": len(strong_used) + len(strong_unused),
        "retained_strong_records": len(retained),
        "retained_previously_used_strong_records": len(strong_used),
        "retained_sampled_strong_records": len(added),
        "retained_evidence_ids": retained_ids,
        "synthetic_records": len(controls),
        "synthetic_records_per_indicator": 5,
        "experimental_bank_records": len(retained) + len(controls),
        "blinding_rule": "All genuine and control records were re-keyed into a neutral EV-#### namespace and randomly ordered using seed 20260918. Record type is available only in this analyst manifest.",
        "bank_sha256": hashlib.sha256(bank_path.read_bytes()).hexdigest(),
        "blind_id_mapping": blind_mapping,
    }
    write_json(OUT / "negative_source_test_60_strong_blinded_manifest.json", manifest)

    assert len(retained) == 60
    assert len(controls) == 155
    assert bank["evidence_item_count"] == 215
    assert len({x["evidence_id"] for x in bank["evidence_items"]}) == 215
    assert not any(
        key in item
        for item in bank["evidence_items"]
        for key in ("strength_rating", "used_in_final_justification", "record_type", "control_class")
    )
    print(json.dumps({
        "strong_available": len(strong_used) + len(strong_unused),
        "strong_retained": len(retained),
        "baseline_used_strong_retained": len(strong_used),
        "sampled_additional_strong": len(added),
        "controls": len(controls),
        "total": bank["evidence_item_count"],
        "sha256": manifest["bank_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
