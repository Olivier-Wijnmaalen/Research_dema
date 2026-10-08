from pathlib import Path


root = Path(__file__).resolve().parents[1]
base = (root / "DEMA_Final_Scoring_Prompt_Documentary_Gap_Aware.txt").read_text(encoding="utf-8-sig")
amendment = (Path(__file__).resolve().parent / "prompt_versions" / "P3_amendment.txt").read_text(encoding="utf-8-sig").strip()
anchor = "DEPTH AND EXPLANATORY STANDARD"
if base.count(anchor) != 1:
    raise ValueError("Insertion anchor not unique")
result = base.replace(anchor, amendment + "\n\n" + anchor, 1)
old = '      "next_phase_gap": "specific proof or implementation required for the next phase"\n'
new = (
    '      "next_phase_gap": "specific proof or implementation required for the next phase",\n'
    '      "assigned_phase_requirement_checks": [\n'
    '        {"requirement": "atomic assigned-phase requirement", "status": "SUPPORTED", "evidence_ids": ["evidence_id"], "explanation": "why this requirement is supported"}\n'
    '      ],\n'
    '      "framework_ambiguity": "identical adjacent phase wording, or empty string"\n'
)
if result.count(old) != 1:
    raise ValueError("Output-schema anchor not unique")
result = result.replace(old, new, 1)
out = Path(__file__).resolve().parent / "prompt_versions" / "P3_full_prompt.txt"
out.write_text(result, encoding="utf-8")
print(out)
