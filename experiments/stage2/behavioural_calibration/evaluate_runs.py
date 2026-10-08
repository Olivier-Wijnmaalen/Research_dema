import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def evaluate(run_name, key_file, case_file):
    keys = json.loads((HERE / key_file).read_text(encoding="utf-8"))["keys"]
    cases = {x["case_id"]: x for x in json.loads((HERE / case_file).read_text(encoding="utf-8"))["cases"]}
    notes = json.loads((HERE / "adjudication_notes.json").read_text(encoding="utf-8"))["runs"][run_name]
    failed = notes["failed_checks"]
    run_dir = HERE / "runs" / run_name
    rows = []
    case_results = []
    structural_issues = []
    for key in keys:
        cid = key["case_id"]
        path = run_dir / "parsed" / f"{cid}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assessments = data.get("indicator_assessments", [])
        if len(assessments) != 1:
            structural_issues.append(f"{cid}: expected one assessment, got {len(assessments)}")
            assessment = {}
        else:
            assessment = assessments[0]
        valid_ids = {e["evidence_id"] for e in cases[cid]["evidence_items"]}
        cited = set(assessment.get("evidence_supporting_score", [])) | set(assessment.get("contrary_or_limiting_evidence", []))
        unknown = sorted(cited - valid_ids)
        if unknown:
            structural_issues.append(f"{cid}: unknown evidence IDs {unknown}")
        if assessment.get("indicator_code") != cases[cid]["indicator"]["indicator_code"]:
            structural_issues.append(f"{cid}: wrong indicator code")
        for item in key["checks"]:
            status = "FAIL" if item["check_id"] in failed else "PASS"
            rows.append({
                "run": run_name,
                "case_id": cid,
                "check_id": item["check_id"],
                "rule": item["rule"],
                "critical": item["critical"],
                "description": item["description"],
                "status": status,
                "adjudication_note": failed.get(item["check_id"], "Output satisfied the prespecified check on manual review."),
            })
        critical = [r for r in rows if r["case_id"] == cid and r["critical"]]
        case_results.append({"case_id":cid,"passed":all(r["status"] == "PASS" for r in critical),"checks_passed":sum(r["status"] == "PASS" for r in critical),"checks_total":len(critical),"phase_returned":assessment.get("phase_score"),"acceptable_phase":key["acceptable_phase"]})
    if structural_issues:
        raise AssertionError(structural_issues)
    summary = {
        "run": run_name,
        "checks_passed": sum(r["status"] == "PASS" for r in rows),
        "checks_total": len(rows),
        "rule_adherence_rate": sum(r["status"] == "PASS" for r in rows) / len(rows),
        "complete_cases_passed": sum(c["passed"] for c in case_results),
        "cases_total": len(case_results),
        "complete_case_pass_rate": sum(c["passed"] for c in case_results) / len(case_results),
        "by_rule": {},
        "qualitative_finding": notes["qualitative_finding"],
        "score_sheet_sha256": "assigned after writing"
    }
    for rule in [f"R{i}" for i in range(1,9)]:
        subset = [r for r in rows if r["rule"] == rule]
        summary["by_rule"][rule] = {"passed":sum(r["status"] == "PASS" for r in subset),"total":len(subset)}
    sheet_path = run_dir / "behavioural_score_sheet.json"
    sheet_path.write_text(json.dumps({"checks":rows,"cases":case_results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary["score_sheet_sha256"] = sha(sheet_path)
    (run_dir / "evaluation_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary


summaries = []
for name in ["P0_calibration","P1_calibration","P2_calibration","P3_calibration","P4_calibration"]:
    summaries.append(evaluate(name,"calibration_answer_keys.json","calibration_cases.json"))
summaries.append(evaluate("P4_test","test_answer_keys.json","test_cases.json"))
(HERE / "evaluation_results.json").write_text(json.dumps({"runs":summaries},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for item in summaries:
    print(item["run"], f'{item["checks_passed"]}/{item["checks_total"]}', f'{item["complete_cases_passed"]}/{item["cases_total"]}')
