# DEMA final research repository

This repository is the handover record for the two-stage, LLM-assisted Togo Data Ecosystem Maturity Assessment (DEMA). It consolidates three working areas into one reviewable research package:

| Original workspace | Role in this repository |
|---|---|
| `OPENAI_AZURE_V1` | Stage 1 prompt research on the development subset |
| `FINAL_SCORE` | Stage 2 prompt research and experiments on the development subset |
| `full_assesmnet_line` | Final two-stage pipeline, held-out processing, evaluation, reports, and dashboard |

> **Internal use only.** The source archive and evidence records may contain copyrighted third-party material and country-assessment content. Read [INTERNAL_USE.md](INTERNAL_USE.md) before sharing or changing repository visibility.

## Research design

```text
Development sources
  -> Stage 1 prompt calibration
  -> Stage 2 prompt calibration
  -> freeze prompt identities and hashes

Held-out/final sources + frozen development evidence
  -> Stage 1 evidence extraction and exact-quote validation
  -> combined evidence bank (mandatory stage boundary)
  -> Stage 2 requirement-based maturity scoring
  -> validated 31-indicator assessment
  -> traceability, sensitivity, and negative-control evaluation
```

The canonical recorded run is `dema-20260917T132056Z`. It used `gpt-4.1-students`, Stage 1 prompt `dema-lenient-calibration/evidence-extraction` version 6, and Stage 2 prompt `dema-stage2-final-strategy-20260916-p5` version 1. The manifest reports 30 held-out chunks, 390 frozen base-evidence records, 622 combined evidence records, and complete coverage of 31 indicators.

## Start here

1. Use [FINAL_TRUTH_TABLE.md](FINAL_TRUTH_TABLE.md) as the numerical authority for Chapters 6–9.
2. Read [docs/research_workflow.md](docs/research_workflow.md) and [docs/data_split_and_leakage_controls.md](docs/data_split_and_leakage_controls.md).
3. Inspect [outputs/canonical_final/manifest.json](outputs/canonical_final/manifest.json) and `final_score.validated.json`.
4. Inspect the exact production prompt snapshots in `prompts/stage1/frozen/` and `prompts/stage2/frozen/`.
5. Review traceability and sensitivity findings in `evaluation/` and `reports/`.
6. Use [docs/artifact_register.csv](docs/artifact_register.csv) to trace retained artifacts to their original workspace.

## Repository map

| Path | Purpose |
|---|---|
| `pipeline/` | Production implementation and conceptual stage boundaries |
| `prompts/` | Development lineages and exact frozen snapshots |
| `data/` | Development inputs, final-assessment inputs, source archive, and provenance |
| `experiments/` | Stage-specific calibration and sensitivity code/artifacts |
| `evaluation/` | Traceability, evidence-quality, prompt-sensitivity, and negative-control results |
| `outputs/canonical_final/` | Authoritative evidence bank, validated score, and run manifest |
| `dashboard/` | Rebuildable presentation layer; generated files are not committed |
| `reports/`, `figures/` | Human-readable research products |
| `tests/` | Pipeline-boundary and saved-output integrity checks |

## Verify without making model calls

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "pipeline"
python -m unittest discover -s tests -v
```

These tests validate the stage boundary, exact-quote rejection behavior, prompt-derived scoring scope, evidence-ID integrity, and the completeness of the saved canonical output. They do not call OpenAI or Langfuse.

## Re-run the pipeline

Copy `.env.example` to `pipeline/.env`, provide authorized credentials, then run:

```powershell
$env:PYTHONPATH = "pipeline"
python pipeline/main.py
```

New model outputs go to `working-runs/latest/` and are ignored by Git until reviewed. Reruns can incur cost and may differ slightly despite fixed prompt versions and temperature settings. See [docs/reproducibility.md](docs/reproducibility.md).

## Dashboard

```powershell
Set-Location dashboard
npm ci
npm run build
npm run check:data
```

The build regenerates `dashboard/public/` and `dashboard/dist/` from canonical files. Dependency and build folders are deliberately excluded from Git.

No live credentials from the three source workspaces were copied into this repository.
