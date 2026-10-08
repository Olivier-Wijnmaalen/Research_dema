import hashlib
import json
from pathlib import Path

from build_calibration_set import check, ev, make_case


OUT = Path(__file__).resolve().parent

cases = [
    make_case("HOLD-01", "Arcland", "A.2.1", "Capacity", [
        ev("E0001", "S01", "The Arcland Emergency Institute has delivered quarterly data-analysis courses for national agencies for three consecutive years.", "A regular national capacity-building programme."),
        ev("E0002", "S02", "The civil-service framework awards a specialist grade and salary increment to data analysts in the national coordinating authority.", "A formal career incentive for data specialists."),
        ev("E0003", "S03", "A single district pilot issued tablets and a user guide to twelve local officers.", "One advanced local support pilot.", "No evidence of extension across national, regional, and local levels.", "local"),
        ev("E0004", "S04", "A staffing review found advanced analysis skills remain concentrated in two national institutions and turnover is high.", "Advanced skills remain concentrated and retention remains difficult."),
    ]),
    make_case("HOLD-02", "Brinora", "C.2.1", "Policies, standards & resources", [
        ev("E0001", "S01", "Brinora's Disaster Policy recognizes risk data, interoperability, and common standards as national priorities, but it is not a comprehensive data strategy.", "Fragmented strategic recognition of data and standards."),
        ev("E0002", "S02", "A ministry newsletter repeats the Disaster Policy statement and announces that a comprehensive strategy will be drafted next year.", "Repetition and future intention.", "Cites S01; no adopted strategy."),
        ev("E0003", "S03", "A donor brief reproduces the newsletter's announcement that a strategy will be drafted.", "Second-hand repetition.", "Derived from S02 and does not establish adoption."),
    ]),
    make_case("HOLD-03", "Coravel", "B.1.3a", "Data quality", [
        ev("E0001", "S01", "A 2023 internal manual states that all key datasets undergo routine validation against authoritative registers.", "A documented formal validation procedure.", "Does not demonstrate use."),
        ev("E0002", "S02", "A 2026 independent audit of the same datasets found checks occurred only after users reported suspected errors and no sampled dataset had been routinely checked against a register.", "Reactive validation and non-implementation of the manual.", "Direct audit of current practice."),
        ev("E0003", "S03", "Staff logs show five checks initiated after complaints during 2026.", "Basic verification when concerns arise."),
    ]),
    make_case("HOLD-04", "Dameris", "C.3.1", "Collaboration & inclusion", [
        ev("E0001", "S01", "Community monitors in every province collect rainfall and impact observations using agreed forms.", "Nationwide community involvement in collection."),
        ev("E0002", "S02", "District analysis sessions include community delegates who interpret observations with technical officers and approve corrections.", "Community involvement in analysis and validation."),
        ev("E0003", "S03", "Community radio groups and village committees co-design and disseminate warning messages, then submit feedback through monthly forums.", "Community involvement in dissemination and feedback."),
        ev("E0004", "S04", "Participation records do not identify disability, migrant, refugee, minority, age, or gender-diverse groups separately.", "No documentary support for the specifically diverse participation required by Phase 5."),
    ]),
    make_case("HOLD-05", "Elandor", "B.2.2", "Data supply", [
        ev("E0001", "S01", "Two agencies use a shared landslide classification in one externally funded mountain project.", "A project-specific standard used by some organizations.", "No use outside one project.", "local", metadata="C.3 partnerships"),
        ev("E0002", "S02", "The national data centre operates a scalable cloud cluster with automated backups.", "Advanced infrastructure only.", "Does not address common definitions, classifications, formats, or metadata.", metadata="B.2.2 standards"),
        ev("E0003", "S03", "No supplied inventory documents an agreed standard used across multiple domains or routinely by actors outside the landslide project.", "Documentary gap for broader standards adoption.", "Does not prove broader standards do not exist."),
    ]),
    make_case("HOLD-06", "Faron", "B.1.1", "Data supply", [
        ev("E0001", "S01", "The Faron Data Catalogue lists all key national disaster datasets in a defined repository and provides routine metadata, CSV downloads, and documented request procedures.", "National systematic cataloguing, reusable formats, metadata, and predictable access."),
        ev("E0002", "S02", "A user audit confirms that the catalogue's documented access process is consistently followed by all national agencies.", "Implemented and predictable national access processes."),
        ev("E0003", "S03", "The weather service alone offers a real-time API and live user chat.", "One sector has Phase 5-like access features.", "No evidence of integrated APIs, interoperability, monitoring, or user-centric services across the ecosystem."),
    ]),
]

keys = [
    {"case_id":"HOLD-01","primary_rules":["R1","R6","R8"],"acceptable_phase":[3],"supported_requirements":["Regular programmes and career incentives exist.","Advanced skills remain concentrated and retention is difficult."],"unsupported_requirements":["Institutionalized national-to-local coverage and ecosystem-wide intermediaries."],"must_retain":["E0004"],"required_reasoning":["Keep the tablet pilot local and isolated."],"failure_behaviours":["Assign Phase 4 from one district pilot."],"checks":[check("HOLD-01","01","R1","Phase score equals 3."),check("HOLD-01","02","R6","Does not generalize E0003 beyond one district."),check("HOLD-01","03","R5","Retains E0004 and its retention limitation."),check("HOLD-01","04","R8","Names institutionalized national-to-local coverage as missing.")]},
    {"case_id":"HOLD-02","primary_rules":["R2","R4","R8"],"acceptable_phase":[2],"supported_requirements":["A policy recognizes risk data, interoperability, and standards in fragmented form."],"unsupported_requirements":["An adopted comprehensive data strategy with institutional arrangements."],"must_retain":[],"required_reasoning":["Separate future drafting from an adopted strategy.","Treat E0002 and E0003 as derived repetitions."],"failure_behaviours":["Assign Phase 3 because three records mention a future strategy."],"checks":[check("HOLD-02","01","R1","Phase score equals 2."),check("HOLD-02","02","R2","Distinguishes recognition and future drafting from adoption."),check("HOLD-02","03","R4","Does not count E0002 and E0003 as independent strategies or corroboration."),check("HOLD-02","04","R8","Names a formal comprehensive strategy and institutional arrangements as missing.")]},
    {"case_id":"HOLD-03","primary_rules":["R2","R5"],"acceptable_phase":[2],"supported_requirements":["Verification occurs reactively when concerns arise."],"unsupported_requirements":["Routine application of standard validation to key datasets."],"must_retain":["E0002"],"required_reasoning":["Prefer direct current audit and logs for implementation while retaining the manual as formal intention."],"failure_behaviours":["Assign Phase 3 from the manual despite audited non-implementation."],"checks":[check("HOLD-03","01","R1","Phase score equals 2."),check("HOLD-03","02","R2","Distinguishes documented procedure from actual practice."),check("HOLD-03","03","R5","Explains why E0002 and E0003 outweigh E0001 for implementation."),check("HOLD-03","04","R8","Names routine implementation as the Phase 3 gap.")]},
    {"case_id":"HOLD-04","primary_rules":["R7","R8"],"acceptable_phase":[4],"supported_requirements":["Communities are actively involved in collection, analysis, dissemination, and feedback across the country."],"unsupported_requirements":["Active inclusion of all Phase 5 named vulnerable and diverse groups."],"must_retain":["E0004"],"required_reasoning":["Combine E0001-E0003 as compatible complementary evidence of the full data cycle."],"failure_behaviours":["Reject Phase 4 because no single record covers the full cycle.","Assign Phase 5 without named-group evidence."],"checks":[check("HOLD-04","01","R1","Phase score equals 4."),check("HOLD-04","02","R7","Combines E0001, E0002, and E0003 with their distinct contributions."),check("HOLD-04","03","R5","Retains E0004."),check("HOLD-04","04","R8","Names participation of specified diverse groups as the Phase 5 gap.")]},
    {"case_id":"HOLD-05","primary_rules":["R3","R6"],"acceptable_phase":[2],"supported_requirements":["Some organizations use a standard in one project."],"unsupported_requirements":["Agreed standards used by multiple actors beyond the project or key domains ecosystem-wide."],"must_retain":["E0003"],"required_reasoning":["Use E0001 despite mismatching metadata, exclude E0002 from standards support, and describe E0003 as a documentary gap."],"failure_behaviours":["Treat cloud infrastructure as standards adoption.","Claim broader standards factually do not exist."],"checks":[check("HOLD-05","01","R1","Phase score equals 2."),check("HOLD-05","02","R6","Uses E0001 by substance despite metadata and excludes E0002 from score support."),check("HOLD-05","03","R3","Uses documentary-gap rather than factual-absence language for E0003."),check("HOLD-05","04","R8","Names multi-actor broader agreed use as the Phase 3 gap.")]},
    {"case_id":"HOLD-06","primary_rules":["R1","R6","R8"],"acceptable_phase":[3],"supported_requirements":["Key national datasets are systematically catalogued with reusable formats, routine metadata, and predictable access."],"unsupported_requirements":["Interoperable open systems, comprehensive ecosystem-wide user support, and regular accessibility monitoring."],"must_retain":[],"required_reasoning":["Treat the weather API as isolated and retain the national Phase 3 boundary."],"failure_behaviours":["Assign Phase 4 or 5 from one service's API."],"checks":[check("HOLD-06","01","R1","Phase score equals 3."),check("HOLD-06","02","R6","Does not generalize E0003 beyond the weather service."),check("HOLD-06","03","R8","Names interoperability and monitoring as higher-phase gaps.")]},
]

assert len(cases) == 6 and len(keys) == 6
assert [c["case_id"] for c in cases] == [k["case_id"] for k in keys]
for case, key in zip(cases, keys):
    ids = {e["evidence_id"] for e in case["evidence_items"]}
    assert len(ids) == len(case["evidence_items"])
    assert set(key["must_retain"]).issubset(ids)
    assert set(case["indicator"]["phase_descriptions"]) == set("12345")

case_payload = {"set_name":"DEMA synthetic temporally separated test set v1","contains_real_togo_material":False,"independently_blinded":False,"cases":cases}
key_payload = {"set_name":"DEMA test answer keys v1","written_before_test_run":True,"authorship":"Assistant-constructed in same session; not independently blinded","researcher_approved":False,"keys":keys}
case_path = OUT / "test_cases.json"
key_path = OUT / "test_answer_keys.json"
case_path.write_text(json.dumps(case_payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
key_path.write_text(json.dumps(key_payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
manifest = {
    "test_cases_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest().upper(),
    "test_answer_keys_sha256": hashlib.sha256(key_path.read_bytes()).hexdigest().upper(),
    "case_count": len(cases),
    "check_count": sum(len(k["checks"]) for k in keys),
    "independently_blinded": False,
    "model_runs_completed": 0,
}
(OUT / "test_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
