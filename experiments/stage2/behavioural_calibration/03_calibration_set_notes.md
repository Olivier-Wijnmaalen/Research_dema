# Step 3: Calibration-set construction notes

The calibration suite contains 12 cases and 45 prespecified critical checks. All cases are fictional and use exact phase descriptions extracted from the frozen documentary-gap-aware prompt. The construction script validates the number and order of cases and keys, unique evidence IDs, valid phase ranges, five phase descriptions per indicator, valid rule mappings, required-evidence references, and coverage of R1–R8.

## Case map

| Case | Indicator | Expected phase | Main boundary |
|---|---|---:|---|
| CAL-01 | C.3.2 | 2 | One advanced local partnership amid project-bound collaboration |
| CAL-02 | B.2.3 | 1 | Approved future platform versus current manual workflow |
| CAL-03 | A.2.1 | 2 | Three records derived from one training announcement |
| CAL-04 | B.1.3d | 2 | Written schedule and self-report contradicted by implementation audit |
| CAL-05 | C.2.2 | 1 | Documentary silence versus explicit, scope-bounded absence |
| CAL-06 | B.2.2 | 3 | Substantive standard evidence plus irrelevant matching metadata |
| CAL-07 | C.3.1 | 3 | Relevant evidence stored under mismatching metadata |
| CAL-08 | C.2.2 | 3 | Complementary independent budget records |
| CAL-09 | B.1.1 | 2 | Strong municipal pilot versus weak national practice |
| CAL-10 | B.1.3a | 3 | Generic self-claim versus recent specific independent review |
| CAL-11 | C.2.1 | 3 | Formal strategy criterion despite unimplemented catalogue |
| CAL-12 | A.1.1 | 2–3 | Identical framework wording for Phases 2 and 3 |

## Files

- `calibration_cases.json`: model-facing inputs. It does not contain expected scores or answer-key criteria.
- `calibration_answer_keys.json`: assessor-only expected behaviours and binary checks. Do not include this file or its contents in model requests.
- `calibration_manifest.json`: SHA-256 hashes, counts, rule coverage, and number of completed model runs.
- `build_calibration_set.py`: reproducible constructor and structural validation.

## Freeze status

The keys were written before any model run, but they were drafted by the assistant. They should be called `assistant-constructed prespecified keys` until the researcher reviews them. Before P0 is run, the researcher should either approve them unchanged or edit them on substantive grounds without consulting model output. After that review, set `researcher_approved` to `true`, rebuild once, and treat the resulting hashes as frozen.

The uneven number of checks per rule is intentional because each case targets a particular failure mode. Results must therefore be reported both overall and by rule; R4 and R7 each have one direct critical check in this calibration suite and should not be presented as precisely estimated performance dimensions.

No model has been run and no output-informed changes have been made.
