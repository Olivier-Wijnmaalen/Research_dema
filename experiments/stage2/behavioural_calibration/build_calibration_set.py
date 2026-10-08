import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
PROMPT = ROOT / "DEMA_Final_Scoring_Prompt_Documentary_Gap_Aware.txt"


def extract_indicator(code: str) -> dict:
    text = PROMPT.read_text(encoding="utf-8-sig")
    normalized = re.escape(code)
    match = re.search(
        rf"INDICATOR {normalized}\.?\s+[^\w\r\n]+\s+(.+?)\r?\n(?P<body>.*?)(?=\r?\n\s*(?:-{{20,}}|={{20,}}))",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError(f"Indicator {code} not found")
    phases = {}
    for phase, wording in re.findall(
        r"Phase ([1-5])\s+[^\w\r\n]+\s+[^:]+:\r?\n(.*?)(?=\r?\n\s*Phase [1-5]\s+[^\w\r\n]+|\Z)",
        match.group("body"),
        flags=re.DOTALL,
    ):
        phases[phase] = " ".join(line.strip() for line in wording.strip().splitlines())
    if set(phases) != set("12345"):
        raise ValueError(f"Expected five phases for {code}, got {sorted(phases)}")
    return {"indicator_code": code, "indicator_name": match.group(1).strip(), "phase_descriptions": phases}


def ev(eid, source, statement, proves, limits="", scope="national", metadata="matching", quote=""):
    return {
        "evidence_id": eid,
        "source_number": source,
        "source_file": f"{source.lower()}_fictional_document.pdf",
        "reference_source_url": "",
        "page_number": "1",
        "dimension": metadata,
        "subdimension": metadata,
        "evidence_scope": scope,
        "country_specificity": "fictional-country specific",
        "evidence_statement": statement,
        "evidence_directly_proves": proves,
        "limitations_or_weaknesses": limits,
        "supporting_quote": quote or statement,
    }


def make_case(cid, country, code, subdimension, evidence):
    indicator = extract_indicator(code)
    indicator["subdimension"] = subdimension
    return {
        "case_id": cid,
        "country": country,
        "scoring_scope": f"Indicator {code} only: {indicator['indicator_name']}",
        "indicator": indicator,
        "evidence_items": evidence,
    }


cases = [
    make_case("CAL-01", "Lydora", "C.3.2", "Collaboration & inclusion", [
        ev("E0001", "S01", "The Lydora Risk Office and provincial data units exchange files only when a flood response project requests them.", "Project-bound, on-demand inter-agency collaboration.", quote="Exchange occurs when a response project requests it."),
        ev("E0002", "S02", "One university laboratory and one software company signed a six-month memorandum containing a data-sharing protocol for a coastal pilot.", "One formal short-term partnership with a data-sharing protocol.", "The pilot covers one coast and the national coordinator is not a party.", "local"),
        ev("E0003", "S03", "No evidence in the partnership register shows regular ecosystem-wide coordination meetings or strategic partnerships led by the national authority.", "A direct register finding about missing regular national mechanisms.", "Register current to June 2026."),
    ]),
    make_case("CAL-02", "Norwyn", "B.2.3", "Data supply", [
        ev("E0001", "S01", "The Cabinet approved the Norwyn AI Readiness Roadmap, which states that an integrated cloud platform will be procured in 2027.", "Formal intention to procure a future platform.", "Does not show procurement, deployment, or operation."),
        ev("E0002", "S02", "A current workflow review found that offices transfer spreadsheets by email and analysts manually re-enter records.", "Current manual and fragmented workflows.", quote="Analysts manually re-enter emailed spreadsheets."),
    ]),
    make_case("CAL-03", "East Verdan", "A.2.1", "Capacity", [
        ev("E0001", "S01", "The East Verdan Data Office delivered one two-day spreadsheet course for national emergency staff in March 2026.", "One sporadic national training event.", "No regular programme, career incentive, retention measure, or subnational coverage."),
        ev("E0002", "S02", "A ministry newsletter repeats the Data Office announcement that one two-day spreadsheet course was delivered in March 2026.", "Repetition of S01.", "Newsletter cites S01 and is not independent corroboration."),
        ev("E0003", "S03", "A partner bulletin reproduces the ministry newsletter's statement about the same March 2026 course.", "Second-hand repetition of S01 through S02.", "No independent observation or additional course."),
    ]),
    make_case("CAL-04", "Bellmare", "B.1.3d", "Data quality", [
        ev("E0001", "S01", "The Bellmare Operations Centre reports that all provincial incident records are uploaded within 24 hours under a weekly update schedule.", "An official claim of defined and rapid reporting.", "Self-reported performance; no underlying timestamps."),
        ev("E0002", "S02", "An independent audit of the same system and quarter found a written weekly schedule but a median upload delay of 18 days; 7 of 10 provinces missed every weekly deadline.", "Defined schedule exists, but routine implementation is seriously inconsistent.", "Independent audit of the same period and system."),
        ev("E0003", "S03", "The system manual defines weekly uploads for incident data.", "A defined reporting timeframe.", "Does not establish compliance."),
    ]),
    make_case("CAL-05", "Orinth", "C.2.2", "Policies, standards & resources", [
        ev("E0001", "S01", "The reviewed 2026 budget volume contains no identifiable line for a data coordinating unit or database-management training.", "Documentary gap within one reviewed budget volume.", "Silence does not prove that no allocation exists elsewhere."),
        ev("E0002", "S02", "The Auditor-General states that the Emergency Data Directorate had no training funds in fiscal year 2025 and cancelled all planned secure-data courses.", "Explicit absence of training funds for a named unit and year.", "Does not establish every government budget."),
    ]),
    make_case("CAL-06", "Selucia", "B.2.2", "Data supply", [
        ev("E0001", "S01", "The Selucia Meteorological Service uses a common hazard classification and metadata template with the Water Agency for flood datasets.", "Two actors use agreed standards for a key domain.", "Adoption outside the flood domain is not shown."),
        ev("E0002", "S02", "A national warehouse purchased redundant servers and increased storage capacity by 80 percent.", "Technical storage capacity only.", "Does not address definitions, classifications, formats, or metadata standards.", metadata="B.2.2 common standards"),
        ev("E0003", "S03", "A compliance review found no systematic monitoring of the flood standard and uneven use among municipal offices.", "Uneven implementation and absent systematic monitoring."),
    ]),
    make_case("CAL-07", "Pelas", "C.3.1", "Collaboration & inclusion", [
        ev("E0001", "S01", "Rural and urban community committees submit observations through a national feedback portal and meet quarterly with producers in every province.", "Nationwide rural/urban connections and an operating feedback mechanism.", metadata="B.1 accessibility"),
        ev("E0002", "S02", "Meeting records show community comments prompted changes to two warning-map legends.", "Feedback is used in dissemination decisions.", "Records do not show community involvement throughout collection and analysis.", metadata="B.3 use"),
    ]),
    make_case("CAL-08", "Tavira", "C.2.2", "Policies, standards & resources", [
        ev("E0001", "S01", "The 2026 Appropriations Act allocates a modest recurring line to the National Data Coordination Unit for information-sharing procedures.", "Formal budget allocation for a coordinating unit and standardized information sharing."),
        ev("E0002", "S02", "The Ministry of Finance training annex allocates funds for quarterly database-management training for technical support staff.", "Allocated training budget for database-management staff."),
        ev("E0003", "S03", "The allocations do not fund secure infrastructure or systematic recruitment and retention of trained staff.", "Direct limit against Phase 4 investment requirements."),
    ]),
    make_case("CAL-09", "Umberia", "B.1.1", "Data supply", [
        ev("E0001", "S01", "A portal in Northbank municipality publishes flood layers in reusable geospatial formats with complete metadata and a help desk.", "Strong accessibility features in one municipality.", "One of 64 municipalities; no national integration or monitoring.", "local"),
        ev("E0002", "S02", "National agencies usually send static PDF summaries by email after a written request; metadata fields are inconsistent.", "National accessibility remains manual, slow, and poorly reusable."),
    ]),
    make_case("CAL-10", "Virelia", "B.1.3a", "Data quality", [
        ev("E0001", "S01", "A 2024 agency brochure says incident figures are accurate and checked carefully.", "A general self-assertion of accuracy.", "No method, sample, reference source, or results."),
        ev("E0002", "S02", "A 2026 independent technical review sampled all five key datasets and found predefined validation procedures were routinely used with authoritative registries, although two regional offices applied them inconsistently.", "Routine predefined validation with authoritative sources, uneven across actors.", "Does not show systematic triangulation with multiple independent sources or routine discrepancy resolution."),
        ev("E0003", "S03", "The 2026 validation manual specifies checks against the civil registry and geocoded asset register.", "Standard procedures and named authoritative references."),
    ]),
    make_case("CAL-11", "West Aster", "C.2.1", "Policies, standards & resources", [
        ev("E0001", "S01", "The formally adopted West Aster National Data Strategy sets objectives for sharing, interoperability, metadata standards, cataloguing, and assigns the Digital Records Agency to central storage.", "A formal comprehensive strategy with objectives and institutional arrangements."),
        ev("E0002", "S02", "The strategy has no scheduled review mechanism and has not been revised since adoption in 2022.", "No periodic review or update."),
        ev("E0003", "S03", "An implementation review found that the planned catalogue was not yet operational.", "The catalogue is not implemented.", "Implementation weakness does not negate existence of the formal strategy."),
    ]),
    make_case("CAL-12", "Zafran", "A.1.1", "Roles", [
        ev("E0001", "S01", "The Zafran Disaster Secretariat maintains an endorsed list identifying ministries, relief organisations, universities, and telecommunications firms active in the data ecosystem.", "Key government and non-government actors are identified."),
        ev("E0002", "S02", "The list describes customary tasks, but the legal review found that several agencies' data roles are not defined in laws or official mandates.", "Roles are known but not always legally defined."),
        ev("E0003", "S03", "No reviewed record demonstrates that a fully endorsed institutional framework is operationalized in practice.", "No documentary support for Phase 4 operationalization.", "Documentary gap, not proof of real-world absence."),
    ]),
]


def check(cid, check_id, rule, description, critical=True):
    return {"check_id": f"{cid}-{check_id}", "rule": rule, "description": description, "critical": critical}


keys = [
    {"case_id":"CAL-01","primary_rules":["R1","R5","R8"],"acceptable_phase":[2],"supported_requirements":["Limited inter-agency collaboration occurs on demand or during a project."],"unsupported_requirements":["Broad ecosystem communication.","National-authority short-term partnerships across academia, NGOs, and private sector.","Regular strategic coordination and widespread formal protocols."],"must_retain":["E0003"],"required_reasoning":["Treat E0002 as an isolated local advanced feature and keep the ecosystem score at Phase 2.","Explain missing Phase 3 breadth and national coordination."],"failure_behaviours":["Assign Phase 3 or 4 because one pilot memorandum contains a protocol.","Ignore E0003."],"checks":[check("CAL-01","01","R1","Phase score equals 2."),check("CAL-01","02","R1","Does not generalize the coastal pilot to the ecosystem."),check("CAL-01","03","R5","Retains and explains E0003."),check("CAL-01","04","R8","Names the unsupported Phase 3 communication and partnership requirements.")]},
    {"case_id":"CAL-02","primary_rules":["R2","R8"],"acceptable_phase":[1],"supported_requirements":["Current workflows are manual and fragmented."],"unsupported_requirements":["Existing technical foundations for AI-enabled workflows.","Operational cloud access or experimental AI use."],"must_retain":["E0002"],"required_reasoning":["Separate approval of a future roadmap from current operation.","Use Phase 1 as a documentary/substantive match based on E0002."],"failure_behaviours":["Describe the planned platform as operational.","Assign Phase 2 solely because a roadmap was approved."],"checks":[check("CAL-02","01","R2","Phase score equals 1."),check("CAL-02","02","R2","Explicitly distinguishes future procurement from present implementation."),check("CAL-02","03","R8","Identifies operational digital foundations or experimental AI use as missing for Phase 2.")]},
    {"case_id":"CAL-03","primary_rules":["R4","R8"],"acceptable_phase":[2],"supported_requirements":["One sporadic basic national training was initiated."],"unsupported_requirements":["Regular capacity-building programmes.","Career incentives.","Subnational institutionalization and follow-up support."],"must_retain":[],"required_reasoning":["Recognize E0002 and E0003 as repetitions of E0001, not independent corroboration."],"failure_behaviours":["Infer regularity from three records.","Count the records as three courses."],"checks":[check("CAL-03","01","R1","Phase score equals 2."),check("CAL-03","02","R4","Identifies the shared lineage and does not count three independent events."),check("CAL-03","03","R8","Names regular programming and career incentives as unsupported Phase 3 elements.")]},
    {"case_id":"CAL-04","primary_rules":["R5","R2"],"acceptable_phase":[2],"supported_requirements":["A written update schedule exists.","Actual reporting is delayed and inconsistent."],"unsupported_requirements":["Routine updating according to the schedule.","Timeliness aligned with operational requirements."],"must_retain":["E0002"],"required_reasoning":["Prefer the direct independent audit for actual performance while retaining the official claim.","Distinguish a defined schedule from its routine implementation."],"failure_behaviours":["Assign Phase 3 based only on the manual or self-report.","Silently discard either side of the conflict."],"checks":[check("CAL-04","01","R1","Phase score equals 2."),check("CAL-04","02","R5","Explicitly addresses the conflict and gives a reasoned preference to E0002."),check("CAL-04","03","R2","Distinguishes formal schedule from implementation."),check("CAL-04","04","R8","Identifies routine compliance as the Phase 3 gap.")]},
    {"case_id":"CAL-05","primary_rules":["R3","R5"],"acceptable_phase":[1],"supported_requirements":["A named directorate explicitly had no training funds in FY2025."],"unsupported_requirements":["Sporadic/event-based funding.","National absence of every relevant allocation."],"must_retain":["E0001","E0002"],"required_reasoning":["Describe E0001 as a documentary gap and E0002 as explicit bounded absence."],"failure_behaviours":["Claim the entire country has no relevant budget solely from E0001.","Treat E0002 as mere documentary silence."],"checks":[check("CAL-05","01","R1","Phase score equals 1."),check("CAL-05","02","R3","Uses documentary-gap language for E0001."),check("CAL-05","03","R3","Uses factual but scope-bounded absence language for E0002."),check("CAL-05","04","R5","Retains both records and their different implications.")]},
    {"case_id":"CAL-06","primary_rules":["R6","R8"],"acceptable_phase":[3],"supported_requirements":["Common classification and metadata standards are used by multiple actors for a key domain.","Implementation is uneven and not systematically monitored."],"unsupported_requirements":["Wide consistent adoption across most actors and datasets."],"must_retain":["E0003"],"required_reasoning":["Exclude E0002 from substantive support despite matching metadata."],"failure_behaviours":["Use server capacity as proof of common standards.","Assign Phase 4 despite limited domain and uneven adoption."],"checks":[check("CAL-06","01","R1","Phase score equals 3."),check("CAL-06","02","R6","Does not use E0002 as maturity support."),check("CAL-06","03","R5","Retains E0003."),check("CAL-06","04","R8","Names wide and consistent adoption as missing for Phase 4.")]},
    {"case_id":"CAL-07","primary_rules":["R6","R8"],"acceptable_phase":[3],"supported_requirements":["Rural and urban stakeholders across the country make data connections.","An operating feedback mechanism exists."],"unsupported_requirements":["Active community involvement throughout the full data cycle.","Phase 5 inclusion of all named vulnerable groups."],"must_retain":[],"required_reasoning":["Use substantively relevant evidence despite mismatching retrieval metadata."],"failure_behaviours":["Exclude the evidence because metadata points elsewhere.","Infer full-cycle involvement from feedback on dissemination."],"checks":[check("CAL-07","01","R1","Phase score equals 3."),check("CAL-07","02","R6","Uses E0001 and E0002 based on content despite metadata."),check("CAL-07","03","R8","Identifies full-data-cycle involvement as missing for Phase 4.")]},
    {"case_id":"CAL-08","primary_rules":["R7","R8"],"acceptable_phase":[3],"supported_requirements":["A modest formal allocation supports a coordinating unit and information-sharing procedures.","A separate allocation funds database-management training for technical staff."],"unsupported_requirements":["Investment in secure technical and legal infrastructure.","Systematic investment in trained staff."],"must_retain":["E0003"],"required_reasoning":["Combine E0001 and E0002 as complementary support for Phase 3."],"failure_behaviours":["Reject Phase 3 because no single source proves both allocations.","Combine the records into claims of Phase 4 investment."],"checks":[check("CAL-08","01","R1","Phase score equals 3."),check("CAL-08","02","R7","Uses E0001 and E0002 jointly with each contribution stated."),check("CAL-08","03","R5","Retains E0003."),check("CAL-08","04","R8","Names secure infrastructure and systematic staff investment as Phase 4 gaps.")]},
    {"case_id":"CAL-09","primary_rules":["R1","R6"],"acceptable_phase":[2],"supported_requirements":["National access commonly occurs by request through static reports with inconsistent metadata."],"unsupported_requirements":["National systematic cataloguing and standardized reusable formats.","Interoperable open systems with monitoring."],"must_retain":["E0002"],"required_reasoning":["Keep the local portal bounded to one municipality."],"failure_behaviours":["Generalize the local portal to national or ecosystem-wide Phase 3/4 maturity."],"checks":[check("CAL-09","01","R1","Phase score equals 2."),check("CAL-09","02","R6","Preserves the municipal scope of E0001."),check("CAL-09","03","R5","Uses E0002 to characterize national practice."),check("CAL-09","04","R8","Names national systematic cataloguing and reusable access as missing.")]},
    {"case_id":"CAL-10","primary_rules":["R5","R6"],"acceptable_phase":[3],"supported_requirements":["Standard validation procedures are routinely applied to key datasets with authoritative reference sources.","Implementation varies across regional offices."],"unsupported_requirements":["Systematic triangulation using multiple independent or authoritative sources.","Routine documented discrepancy resolution."],"must_retain":["E0002"],"required_reasoning":["Give more weight to the specific independent review and manual than the generic brochure, based on substance and authority."],"failure_behaviours":["Assign Phase 4 or 5 from the brochure's word 'accurate'.","Ignore regional inconsistency."],"checks":[check("CAL-10","01","R1","Phase score equals 3."),check("CAL-10","02","R5","Explains evidential weight using specificity, authority, and recency."),check("CAL-10","03","R6","Does not treat the brochure as proof of a validation method."),check("CAL-10","04","R8","Names systematic triangulation and discrepancy resolution as Phase 4 gaps.")]},
    {"case_id":"CAL-11","primary_rules":["R2","R8"],"acceptable_phase":[3],"supported_requirements":["A formal strategy covers data sharing, interoperability, standards, management, cataloguing, and institutional arrangements.","The strategy is not regularly reviewed."],"unsupported_requirements":["Regular review and updating.","An operational catalogue."],"must_retain":["E0003"],"required_reasoning":["Credit Phase 3's formal-policy requirement even though one planned mechanism is unimplemented.","Do not claim implementation from adoption."],"failure_behaviours":["Reduce the score below Phase 3 solely because the catalogue is not operational.","Assign Phase 4 despite absent review."],"checks":[check("CAL-11","01","R1","Phase score equals 3."),check("CAL-11","02","R2","Separates policy existence from catalogue implementation."),check("CAL-11","03","R5","Retains E0003 without letting it negate the formal-policy criterion."),check("CAL-11","04","R8","Identifies regular review and updating as Phase 4 gaps.")]},
    {"case_id":"CAL-12","primary_rules":["R1","R3","R8"],"acceptable_phase":[2,3],"supported_requirements":["Key actors are identified.","Roles are not always defined through official/legal mechanisms."],"unsupported_requirements":["A fully endorsed and operationalized institutional framework.","Dynamic system-wide collaborative innovation."],"must_retain":["E0003"],"required_reasoning":["Acknowledge that the framework gives substantively identical Phase 2 and Phase 3 descriptions.","Use documentary-gap language for Phase 4 operationalization."],"failure_behaviours":["Invent a substantive distinction between Phases 2 and 3.","Assign Phase 4.","Claim operationalization does not exist in reality."],"checks":[check("CAL-12","01","R1","Phase score is 2 or 3 under the prespecified ambiguity."),check("CAL-12","02","R1","Explicitly acknowledges identical Phase 2/3 substantive wording."),check("CAL-12","03","R3","Describes Phase 4 operationalization as not demonstrated, not factually nonexistent."),check("CAL-12","04","R8","Identifies endorsement plus operationalization as the Phase 4 boundary.")]},
]


def validate():
    assert len(cases) == 12 and len(keys) == 12
    assert [c["case_id"] for c in cases] == [k["case_id"] for k in keys]
    seen_check_ids = set()
    for case, key in zip(cases, keys):
        ids = [e["evidence_id"] for e in case["evidence_items"]]
        assert len(ids) == len(set(ids))
        assert set(key["must_retain"]).issubset(ids)
        assert key["acceptable_phase"]
        assert all(1 <= phase <= 5 for phase in key["acceptable_phase"])
        assert set(case["indicator"]["phase_descriptions"]) == set("12345")
        for item in key["checks"]:
            assert item["check_id"] not in seen_check_ids
            seen_check_ids.add(item["check_id"])
            assert item["rule"] in {f"R{i}" for i in range(1, 9)}
    covered = {item["rule"] for key in keys for item in key["checks"]}
    assert covered == {f"R{i}" for i in range(1, 9)}, covered


validate()
case_payload = {"set_name": "DEMA synthetic calibration set v1", "contains_real_togo_material": False, "cases": cases}
key_payload = {
    "set_name": "DEMA calibration answer keys v1",
    "written_before_model_run": True,
    "authorship": "Assistant-constructed draft for researcher review",
    "researcher_approved": False,
    "keys": keys,
}

cases_path = OUT / "calibration_cases.json"
keys_path = OUT / "calibration_answer_keys.json"
cases_path.write_text(json.dumps(case_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
keys_path.write_text(json.dumps(key_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

manifest = {
    "prompt_sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest().upper(),
    "calibration_cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest().upper(),
    "calibration_answer_keys_sha256": hashlib.sha256(keys_path.read_bytes()).hexdigest().upper(),
    "case_count": len(cases),
    "check_count": sum(len(k["checks"]) for k in keys),
    "rule_coverage": {f"R{i}": sum(item["rule"] == f"R{i}" for k in keys for item in k["checks"]) for i in range(1, 9)},
    "model_runs_completed": 0,
}
(OUT / "calibration_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
