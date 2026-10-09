# FINAL TRUTH TABLE

This file is the numerical authority for Chapters 6–9. Do not copy a number from a narrative report without checking its population and definition here.

## 1. Population boundaries

| Population | Sources | Prepared chunks | What it represents |
|---|---:|---:|---|
| Development/calibration corpus | 8 | 30 | Sources `001, 010, 018, 027, 030, 031, 032, 033`; used for prompt development and construction of the frozen 390-record base bank. |
| Held-out Stage 1 evaluation | 14 | 30 | Sources `005, 006, 007, 008, 011, 015, 019, 020, 022, 023, 024, 026, 028, 029`; processed in canonical run `dema-20260917T132056Z`. |
| Complete final scoring population | 22 | 60 | Composite of the frozen development bank and the held-out Stage 1 output. This was not one homogeneous 22-source Stage 1 generation run. |

## 2. Authoritative results

| Measure | Authoritative value | Population and definition |
|---|---|---|
| Frozen Stage 1 prompt used on held-out sources | `dema-lenient-calibration/evidence-extraction`, Langfuse version **6** | Held-out Stage 1 evaluation and canonical run only. |
| Frozen Stage 1 prompt hash | `d2436f48ec0c9ff693f2b4f1964adc21e179995ec11905d1bf70902bcd8c355c` | SHA-256 recorded by the canonical manifest and prompt snapshot. |
| Stage 1 calibration V6 result | **464** generated; **451** lenient-traceable (**97.20%**); strict exact **96.34%** | Development prompt-selection experiment. Post-freeze AIS on the 451 technically accepted rows: **291 fully**, **152 partially**, **8 not attributable**. These are not final-pipeline counts. |
| Frozen development bank actually used by the final pipeline | **428** generated; **390** retained | Separate development extraction: `dema-extraction-v4-indicator-defined-framework`, Langfuse version **1**; local prompt-file SHA-256 `7ee30eec2e879db6a187b329c31a7496da4be71268f08c8c345da62652b148c0`. Do not describe this bank as the output of frozen lenient V6. |
| Development technical traceability | **395 PASS_EXACT**, **6 PASS_NORMALIZED**, **7 REPAIR_REQUIRED**, **20 FAIL** of **428** | Strict pass **92.29%**; accepted pass **93.692%** (401/428); traceable including repair **95.327%** (408/428). |
| Development attribution | **204 fully attributable**, **211 partially attributable**, **13 not attributable** of **428** | AIS evaluated all generated development rows. Two of the 13 not-attributable rows had already failed technical validation; attribution therefore removed 11 additional technically accepted rows. |
| Development records retained | **390/428 (91.1%)** | 38 exclusions: 25 technical-only, 11 attribution-only, 2 both. This is the base bank supplied to the final run. |
| Held-out Stage 1 candidate evidence | **238** | Frozen lenient V6 on 30 held-out chunks from 14 sources. |
| Held-out Stage 1 accepted evidence | **232** | Exact-contiguous pipeline rule; **6 rejected**, giving **97.5%** strict retention. |
| Held-out retrospective lenient traceability | **238/238 (100.0%)** | A later audit reclassified all six strict rejections as traceable after non-substantive normalization. This does not change the canonical bank: it still contains 232 held-out records. |
| Held-out attribution | **Not evaluated / no authoritative AIS outcome retained** | Do not apply development AIS percentages or counts to the held-out population. |
| Complete pre-filter candidate total | **666 = 428 + 238** | Descriptive sum across two differently generated Stage 1 populations; not a single-run performance denominator. |
| Final evidence-bank size | **622 = 390 + 232** | Composite 22-source bank used for final Stage 2 scoring; all evidence IDs unique. |
| Frozen Stage 2 prompt | `dema-stage2-final-strategy-20260916-p5`, Langfuse version **1** | Canonical 31-indicator scoring run. |
| Stage 2 prompt hash | Canonical CRLF SHA-256 `a3734a364931d5aaa90188c82eee400b0812023a5d4dcb14da70d917067669af` | API-normalized SHA-256 is `19520d1d71c80ba4a4eac3db09107e82f53ff932fd1ab4bb3b935a1cdadfeeec`; always state which representation is used. |
| Stage 2 citation resolution | **337 references**, **238 distinct evidence records**, **30 deterministic citation repairs**, **100% resolved after repair** | Complete final scoring population. |
| Negative-control stress test | **105/155 controls cited (67.7%)**; controls in **27/31 indicators (87.1%)**; **41** controls used as supporting and **69** as limiting evidence; **28/31 phases differed (90.3%)** | Blinded bank contained 60 strong genuine records plus 155 synthetic controls. Phase differences versus the 622-record baseline are not a causal control effect because 562 genuine baseline records were also removed. |
| Matched negative-control checks | A.1.2 source-level: **2→2**; A.1.2 subdimension-level: **2→2**; B.1.3e: **2→1** | Five matched controls caused no phase change in two A.1.2 tests and a one-phase decrease for B.1.3e. All selected controls were used as limiting, not positive, evidence in these three matched tests. |

## 3. Final 31 scores

These values come from `outputs/canonical_final/final_score.validated.json`.

| Indicator | Score | Indicator | Score |
|---|---:|---|---:|
| A.1.1 | 3 | A.1.2 | 3 |
| A.1.3 | 2 | A.1.4 | 3 |
| A.2.1 | 3 | A.2.2 | 3 |
| A.2.3 | 1 | A.2.4 | 3 |
| B.1.1 | 3 | B.1.2 | 3 |
| B.1.3a | 3 | B.1.3b | 3 |
| B.1.3c | 3 | B.1.3d | 3 |
| B.1.3e | 3 | B.1.3f | 3 |
| B.2.1 | 3 | B.2.2 | 3 |
| B.2.3 | 3 | B.3.1 | 3 |
| B.3.2 | 3 | C.1.1 | 3 |
| C.1.2 | 3 | C.1.3 | 1 |
| C.1.4 | 1 | C.1.5 | 3 |
| C.2.1 | 3 | C.2.2 | 3 |
| C.2.3 | 3 | C.3.1 | 3 |
| C.3.2 | 3 |  |  |

Score distribution: **27 indicators at Phase 3, one at Phase 2, and three at Phase 1**.

## 4. Non-negotiable reporting rules

1. Use **451/464** only for the development V6 prompt-calibration result; never call it the held-out or final-bank result.
2. Use **232/238** for canonical held-out retention. Use **238/238** only when explicitly describing the retrospective lenient-normalization audit.
3. Do not report an attribution result for held-out Stage 1; none is retained.
4. Describe the 622-record final bank as a composite: **390 development + 232 held-out**.
5. Do not interpret the 28/31 stress-test phase changes as caused solely by controls. Use the matched results for the direct observed control effect.
6. For final maturity claims, the 31 scores in this file and the validated JSON override summaries embedded in intermediate batch outputs.

## 5. Primary artifacts

- `outputs/canonical_final/manifest.json`
- `outputs/canonical_final/combined_evidence_bank.json`
- `outputs/canonical_final/final_score.validated.json`
- `prompts/stage1/frozen/prompt_stage1.json`
- `prompts/stage2/frozen/prompt_stage2.json`
- `evaluation/traceability/lenient_traceability_evaluation.json`
- `evaluation/traceability/traceability_failure_modes.json`
- `data/development/stage2/final_development_bank_audit.json`
- `evaluation/negative_controls/stage2_60_strong_blinded_results.json`
- `evaluation/negative_controls/matched_A_1_2_source_level.json`
- `evaluation/negative_controls/matched_A_1_2_subdimension.json`
- `evaluation/negative_controls/matched_B_1_3e.json`

Last reconciled against the frozen artifacts: **2026-10-09**.
