from pathlib import Path


here = Path(__file__).resolve().parent
p3 = (here / "prompt_versions" / "P3_full_prompt.txt").read_text(encoding="utf-8-sig")
old = "For every requirement of the proposed assigned phase, return an entry in `assigned_phase_requirement_checks` with:"
new = (
    "First distinguish mandatory requirements from optional or conditional context. Clauses using "
    "`may`, `might`, `if applicable`, `where applicable`, examples introduced by `e.g.`, or other expressly "
    "conditional wording do not have to be observed for the phase to be supported. Do not include an optional "
    "or conditional clause as a separate gating requirement unless the evidence makes that condition applicable. "
    "Do not weaken mandatory wording such as `are`, `is`, `must`, `regularly`, `routinely`, `systematically`, "
    "`across`, or `throughout`.\n\n"
    "For every mandatory requirement of the proposed assigned phase, return an entry in "
    "`assigned_phase_requirement_checks` with:"
)
if p3.count(old) != 1:
    raise ValueError("P3 anchor not unique")
result = p3.replace(old, new, 1)
old_check = "Before returning, verify that every assigned-phase requirement has status `SUPPORTED`, the phase score agrees with those checks, scope has not been generalized, and any substantively identical adjacent phases are explicitly reported."
new_check = (
    "Before returning, verify that every mandatory assigned-phase requirement is represented exactly once in "
    "`assigned_phase_requirement_checks`, every returned status is `SUPPORTED`, optional or inapplicable conditional "
    "clauses are not treated as missing requirements, the phase score agrees with the checks, scope has not been "
    "generalized, and any substantively identical adjacent phases are explicitly reported."
)
if result.count(old_check) != 1:
    raise ValueError("P3 pre-return check anchor not unique")
result = result.replace(old_check, new_check, 1)
out = here / "prompt_versions" / "P4_full_prompt.txt"
out.write_text(result, encoding="utf-8")
print(out)
