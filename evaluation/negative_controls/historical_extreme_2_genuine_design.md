# Negative-source sensitivity test

The original non-development evidence bank was copied before constructing the experimental condition. From the 232 evidence records supplied to the baseline Stage 2 run, two genuine records were retained. To avoid subjective selection, these were sampled with fixed random seed `20260917` from the 31 records previously classified as strong and cited in the final justification. The retained records were `028_chunk_004_pages_031-040::E002` and `024_chunk_001_pages_001-010::E002`.

Five synthetic low-quality evidence records were then constructed for each of the 31 DEMA indicators, producing 155 controls. The controls were topically matched to their assigned indicator but contained no maturity-discriminating information. They represented five failure patterns: an agenda mention, a conditional future possibility, a glossary reference, attendance at an introductory presentation, and a generic non-country-specific comment. Explicit evidence of an actual ecosystem failure or absence was avoided because such information could legitimately function as limiting evidence for a low maturity phase.

The experimental bank therefore contains 157 records: two genuine records and 155 synthetic controls. Synthetic status and expected scoring value are recorded in a separate manifest and are not exposed as record-level labels in the blinded Stage 2 bank.

## Evaluation outcomes

| Outcome | Calculation |
|---|---|
| Control citation rate | Unique synthetic controls cited / 155 |
| Indicator contamination rate | Indicators citing at least one synthetic control / 31 |
| Supporting-control rate | Synthetic controls cited as supporting evidence / all supporting citations |
| Limiting-control rate | Synthetic controls cited as limiting evidence / all limiting citations |
| Phase instability | Indicators whose phase differs from the baseline / 31 |
| Score displacement | Direction and magnitude of phase changes relative to baseline |
| Genuine-evidence retention | Whether either of the two genuine records is cited in the corresponding justification |

This condition is an extreme evidence-starvation stress test because it removes 230 genuine records while adding controls. Consequently, phase changes cannot be attributed solely to control injection. A separate contamination-only condition retaining all 232 genuine records and adding the same 155 controls would be required to isolate the causal effect of negative-source injection.
