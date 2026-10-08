# Prompt refinement log

| Version | Prompt SHA-256 | Checks | Complete cases | Finding and action |
|---|---|---:|---:|---|
| P0 | `8BC0F174945D09EE0B8BFDBA1B14CC978B39220726143775E45E5DC6BD3EDAED` | 42/45 | 10/12 | A contradicted implementation requirement was treated as satisfied, and identical A.1.1 Phase 2/3 wording was given an invented distinction. |
| P1 | `A136686C64937CA6EABDCF541926B7F3AE3B2F46F4467800F8DE8FAB598F9010` | 42/45 | 10/12 | Added narrative rules for contradictions and duplicate phase descriptions. The failures persisted, so P1 was rejected. |
| P2 | `B2C474ED94FF3E7B43260FC57CB3EC81E273A568925EB1C77BA9A1E3A197D5DA` | 39/45 | 9/12 | Added a mandatory gating procedure. Original failures persisted and a scope-generalization regression appeared in CAL-01. |
| P3 | `29FF4793D24813B088929678E9ACB2A77FAD961D94CE6D13E28A3C600EC573C6` | 45/45 | 12/12 | Added an explicit assigned-phase requirement matrix and ambiguity field. Prespecified checks passed, but CAL-09 incorrectly treated optional fee wording as a mandatory unmet criterion. |
| P4 | `883FC330BC82BD2BF5824A80E6F9F518DB3FC73E6AC429B505DD7635F1EA619F` | 45/45 | 12/12 | Distinguished mandatory criteria from conditional wording. All prespecified checks passed and the matrix inconsistency did not recur. P4 was selected and frozen. |

All versions were run on the same 12 cases at temperature 0 using deployment `gpt-4.1-students`. All requests and responses are preserved under `runs/`. P4 was then applied once to the six-case temporally separated test set and passed 23/23 checks and 6/6 complete cases. The test set was assistant-authored in the same session and was not independently blinded.

