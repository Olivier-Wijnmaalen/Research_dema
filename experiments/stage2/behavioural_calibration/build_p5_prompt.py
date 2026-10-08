from pathlib import Path


here = Path(__file__).resolve().parent
p4 = (here / "prompt_versions" / "P4_full_prompt.txt").read_text(encoding="utf-8-sig")

anchor = "DEPTH AND EXPLANATORY STANDARD"
amendment = """OUTPUT-COMPLIANCE SELF-AUDIT FOR THE FINAL SELECTED PHASE

Immediately before returning the JSON, run a final self-audit for each indicator:
1. Re-read the assigned `phase_score` and the `assigned_phase_requirement_checks`.
2. If any assigned-phase requirement has status `CONTRADICTED` or `NOT_DEMONSTRATED`, the assigned phase is invalid. Lower the phase and rebuild the requirement checks for the lower phase until every mandatory requirement of the assigned phase is `SUPPORTED`.
3. Do not hide an unmet mandatory requirement by omitting it from the requirement-check list. If a mandatory requirement is relevant to the assigned phase, it must appear exactly once.
4. Do not include optional, illustrative, or inapplicable conditional clauses as gating requirements. However, mandatory wording such as `are`, `is`, `must`, `regularly`, `routinely`, `systematically`, `across`, and `throughout` remains gating.
5. Confirm that `score_reasoning` explicitly distinguishes documented absence, documented weakness, and a documentary evidence gap.

This self-audit changes output admissibility only. It does not change any DEMA phase definition and does not permit a higher phase without evidence."""

if p4.count(anchor) != 1:
    raise ValueError(f"Expected one insertion anchor: {anchor}")

result = p4.replace(anchor, amendment + "\n\n" + anchor, 1)
out = here / "prompt_versions" / "P5_full_prompt.txt"
out.write_text(result, encoding="utf-8")
print(out)
