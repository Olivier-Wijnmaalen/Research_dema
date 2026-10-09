# Research workflow

## Stage 1: evidence extraction

Stage 1 converts prepared source chunks into structured DEMA evidence records. The pipeline attaches source and chunk metadata, checks that supporting quotations are exact contiguous substrings of the supplied chunk, separates accepted and rejected rows, and retains prompt/call metadata. Prompt development artifacts are under `prompts/stage1/development/` and `experiments/stage1/`; the exact prompt snapshot used by the canonical run is `prompts/stage1/frozen/prompt_stage1.json`.

## Mandatory evidence-bank boundary

Validated Stage 1 records are combined with the frozen 390-record development evidence bank. Evidence IDs must be unique. The resulting 622-record `outputs/canonical_final/combined_evidence_bank.json` is the explicit boundary between extraction and scoring. Extraction and scoring are never combined into one model call.

The frozen Stage 1 development bank was also the fixed source input for Stage 2 prompt development and calibration. Its Stage 2 calibration manifest records 390 source rows and 389 prepared calibration rows. After the Stage 2 prompt was frozen, the complete final run scored the original 390 development records together with 232 strictly accepted held-out records.

## Stage 2: maturity scoring

Stage 2 evaluates the evidence bank against 31 prompt-defined indicators. The validator checks indicator coverage, phase-gate structure, and cited evidence IDs. Development artifacts are under `prompts/stage2/development/` and `experiments/stage2/`; the production snapshot is `prompts/stage2/frozen/prompt_stage2.json`.

## Evaluation

- `evaluation/traceability/` audits quote attribution, rejected rows, and failure modes.
- `evaluation/evidence_quality/` contains the evidence-strength coding summary.
- `evaluation/negative_controls/` retains negative-source design and manifests.
- `experiments/sensitivity/` contains executable matched-sensitivity and order-contamination analyses.
- `reports/` contains selected methods and results documents.

## Presentation

The dashboard consumes only saved canonical artifacts and provenance records. It contains no extraction or scoring logic and can be rebuilt without model access.
