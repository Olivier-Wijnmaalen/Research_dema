# Final truth table

> **Numerical authority for Chapters 6–9.** Always identify the population before quoting a result.

## Headline facts

| Canonical run | Sources represented | Prepared chunks | Final evidence bank | Final indicators |
|---|---:|---:|---:|---:|
| `dema-20260917T132056Z` | **22** | **60** | **622** | **31** |

> **The central distinction:** the final bank is a composite, not one homogeneous 22-source Stage 1 run. It contains **390 development records + 232 held-out records**.

## Research sequence

```text
Stage 1 development on 8 sources / 30 chunks
  -> frozen 390-record Stage 1 development bank
  -> fixed source input for Stage 2 prompt development and calibration
     (389 records after Stage 2 calibration preparation)
  -> frozen Stage 2 P5 prompt

Frozen Stage 1 V6 on 14 held-out sources / 30 chunks
  -> 232 strictly accepted held-out records
  -> merge with the original 390-record development bank
  -> 622-record final bank
  -> final 31-indicator Stage 2 run
```

The frozen Stage 1 development output was therefore used to develop Stage 2. The held-out Stage 1 evidence was added only after prompt development for the complete final assessment.

## Three populations

### 1. Development and calibration

- **8 sources:** `001, 010, 018, 027, 030, 031, 032, 033`
- **30 prepared chunks**
- Used for prompt development and construction of the frozen development bank.
- Contains multiple experiments. Calibration results must not be presented as held-out results.

### 2. Held-out Stage 1 evaluation

- **14 sources:** `005, 006, 007, 008, 011, 015, 019, 020, 022, 023, 024, 026, 028, 029`
- **30 prepared chunks**
- Processed with frozen Stage 1 V6 in the canonical run.

### 3. Complete final scoring population

- **22 sources and 60 prepared chunks**
- Combines the 390-record development bank with 232 held-out records.
- Scored against all 31 indicators with frozen Stage 2 P5.

## Frozen prompt identities

### Stage 1 — held-out extraction

| Field | Authoritative value |
|---|---|
| Prompt | `dema-lenient-calibration/evidence-extraction` |
| Langfuse version | **6** |
| SHA-256 | `d2436f48ec0c9ff693f2b4f1964adc21e179995ec11905d1bf70902bcd8c355c` |
| Scope | Held-out Stage 1 evaluation only |

### Stage 2 — final scoring

| Field | Authoritative value |
|---|---|
| Prompt | `dema-stage2-final-strategy-20260916-p5` |
| Langfuse version | **1** |
| Canonical CRLF SHA-256 | `a3734a364931d5aaa90188c82eee400b0812023a5d4dcb14da70d917067669af` |
| API-normalized SHA-256 | `19520d1d71c80ba4a4eac3db09107e82f53ff932fd1ab4bb3b935a1cdadfeeec` |

Always state which Stage 2 hash representation is being reported.

## Stage 1 results by population

### Development V6 prompt-calibration experiment

| Measure | Result |
|---|---:|
| Generated records | **464** |
| Lenient-traceable records | **451 (97.20%)** |
| Strict exact rate | **96.34%** |
| Fully attributable after freeze | **291** |
| Partially attributable after freeze | **152** |
| Not attributable after freeze | **8** |

These values describe prompt selection. They are **not** the final-pipeline evidence counts.

### Development bank actually supplied to the final pipeline

This bank came from the separate `dema-extraction-v4-indicator-defined-framework` workflow, Langfuse version 1—not from lenient V6. Its local prompt-file SHA-256 is `7ee30eec2e879db6a187b329c31a7496da4be71268f08c8c345da62652b148c0`.

| Technical outcome | Records | Share of 428 |
|---|---:|---:|
| PASS_EXACT | **395** | **92.29%** |
| PASS_NORMALIZED | **6** | **1.40%** |
| REPAIR_REQUIRED | **7** | **1.64%** |
| FAIL | **20** | **4.67%** |
| **Generated** | **428** | **100%** |

| Attribution outcome | Records |
|---|---:|
| Fully attributable | **204** |
| Partially attributable | **211** |
| Not attributable | **13** |
| **AIS evaluated** | **428** |

Two of the 13 not-attributable records had already failed technical validation. The attribution filter therefore removed 11 additional technically accepted records.

**Final development retention: 390/428 (91.1%).** The 38 exclusions comprise 25 technical-only, 11 attribution-only, and 2 failing both.

### How the Stage 1 output fed Stage 2 development

| Step | Records |
|---|---:|
| Frozen Stage 1 development bank | **390** |
| Source records recorded in the Stage 2 calibration manifest | **390** |
| Records after Stage 2 calibration preparation | **389** |

The bank hash recorded by the Stage 2 calibration manifest is `94a062f211ce77dcea686bff849ceee25c082380246c48b2acb9ae63d4aafd59`. This establishes the direct provenance link from frozen Stage 1 output to Stage 2 prompt development. The one-record preparation difference belongs to Stage 2 calibration preprocessing; it does not change the 390-record development component later merged into the 622-record final bank.

### Held-out Stage 1 evaluation

| Measure | Result |
|---|---:|
| Sources | **14** |
| Chunks | **30** |
| Candidate evidence records | **238** |
| Strictly accepted records | **232** |
| Strictly rejected records | **6** |
| Canonical strict retention | **232/238 (97.5%)** |
| Retrospective lenient traceability | **238/238 (100.0%)** |
| Attribution | **Not evaluated / no authoritative AIS outcome retained** |

The later lenient audit treated all six strict rejections as traceable after non-substantive normalization. It did **not** change the canonical bank, which retains 232 held-out records.

## Complete final pipeline

| Measure | Result |
|---|---:|
| Descriptive pre-filter total | **666 = 428 + 238** |
| Development records retained | **390** |
| Held-out records retained | **232** |
| Final evidence-bank size | **622 = 390 + 232** |
| Stage 2 evidence references | **337** |
| Distinct records cited by Stage 2 | **238** |
| Deterministic citation repairs | **30** |
| Citation resolution after repair | **100%** |

The total of 666 is descriptive only: it combines evidence generated by two different Stage 1 workflows and is not a single-run performance denominator.

## Final maturity scores

Score distribution: **27 indicators at Phase 3, 1 at Phase 2, and 3 at Phase 1**.

### Dimension A — Actors, roles, and capacity

| Indicator | Description | Score |
|---|---|---:|
| A.1.1 | Roles identified for all actors | **3** |
| A.1.2 | Roles identified for the coordinator | **3** |
| A.1.3 | Diversity and representativeness of data users | **2** |
| A.1.4 | Diversity and representativeness of data producers | **3** |
| A.2.1 | Human capacity building and retention | **3** |
| A.2.2 | Institutional data-management capacity | **3** |
| A.2.3 | Readiness for responsible AI use | **1** |
| A.2.4 | Process quality | **3** |

### Dimension B — Data value chain

| Indicator | Description | Score |
|---|---|---:|
| B.1.1 | Data accessibility | **3** |
| B.1.2 | Data availability | **3** |
| B.1.3a | Data quality: accuracy | **3** |
| B.1.3b | Data quality: completeness | **3** |
| B.1.3c | Data quality: consistency | **3** |
| B.1.3d | Data quality: timeliness | **3** |
| B.1.3e | Data quality: validity | **3** |
| B.1.3f | Data quality: disaggregation | **3** |
| B.2.1 | Technical and data interoperability | **3** |
| B.2.2 | Operationalize common metadata standards | **3** |
| B.2.3 | Infrastructure and readiness for AI workflows | **3** |
| B.3.1 | Applications and use cases | **3** |
| B.3.2 | Supply meets demand | **3** |

### Dimension C — Governance and collaboration

| Indicator | Description | Score |
|---|---|---:|
| C.1.1 | Trust building among ecosystem actors | **3** |
| C.1.2 | Responsible data governance and accountability | **3** |
| C.1.3 | Responsible AI governance and accountability | **1** |
| C.1.4 | Security | **1** |
| C.1.5 | Privacy | **3** |
| C.2.1 | Data ecosystem strategy and vision | **3** |
| C.2.2 | Dedicated budget | **3** |
| C.2.3 | Incentives for ecosystem contributions | **3** |
| C.3.1 | Community engagement | **3** |
| C.3.2 | Communication and inter-agency collaboration | **3** |

Source: `outputs/canonical_final/final_score.validated.json`.

## Negative-control findings

### Blinded stress test: 60 genuine + 155 synthetic records

| Measure | Result |
|---|---:|
| Synthetic controls cited | **105/155 (67.7%)** |
| Indicators citing at least one control | **27/31 (87.1%)** |
| Controls used as supporting evidence | **41** |
| Controls used as limiting evidence | **69** |
| Phases differing from full baseline | **28/31 (90.3%)** |

> The 28 phase differences are **not a causal control effect**. The stress test also removed 562 genuine records from the 622-record baseline.

### Matched checks

| Indicator and design | Without controls | With five controls | Change |
|---|---:|---:|---:|
| A.1.2, source-level | 2 | 2 | **0** |
| A.1.2, subdimension-level | 2 | 2 | **0** |
| B.1.3e | 2 | 1 | **-1** |

In all three matched tests, selected controls were used as limiting rather than positive evidence.

## Reporting checklist

- [ ] Name the population: development, held-out, or complete final.
- [ ] Use **451/464** only for the development V6 calibration experiment.
- [ ] Use **232/238** for canonical held-out retention.
- [ ] Use **238/238** only for the retrospective lenient audit.
- [ ] Do not report held-out attribution; it was not evaluated.
- [ ] Describe the final bank as **390 development + 232 held-out**.
- [ ] State that the frozen Stage 1 development bank was the fixed input for Stage 2 prompt development.
- [ ] Do not attribute the stress-test phase shifts solely to controls.
- [ ] Use the validated JSON and the 31 scores above for final maturity claims.

## Primary artifacts

| Purpose | Artifact |
|---|---|
| Canonical run metadata | `outputs/canonical_final/manifest.json` |
| Final evidence bank | `outputs/canonical_final/combined_evidence_bank.json` |
| Final scores | `outputs/canonical_final/final_score.validated.json` |
| Frozen Stage 1 prompt | `prompts/stage1/frozen/prompt_stage1.json` |
| Frozen Stage 2 prompt | `prompts/stage2/frozen/prompt_stage2.json` |
| Development bank audit | `data/development/stage2/final_development_bank_audit.json` |
| Held-out lenient audit | `evaluation/traceability/lenient_traceability_evaluation.json` |
| Failure-mode coding | `evaluation/traceability/traceability_failure_modes.json` |
| Negative-control stress test | `evaluation/negative_controls/stage2_60_strong_blinded_results.json` |
| Matched controls | `evaluation/negative_controls/matched_*.json` |

Last reconciled against the frozen artifacts: **2026-10-09**.
