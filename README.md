# DEMA research pipeline and reproducibility archive

This repository is the research handover for an LLM-assisted Data Ecosystem
Maturity Assessment (DEMA) of Togo. It contains:

- the runnable two-stage extraction and scoring pipeline;
- the static assessment dashboard;
- frozen prompts and the authoritative final run;
- development experiments, evaluations, figures, and provenance records.

The output is a **documentary pre-assessment for expert review**. It is not a
replacement for an in-country DEMA process, stakeholder validation, or Red
Cross decision-making.

> **Authorized internal sharing only.** The repository contains archived
> third-party documents, quotations, and country-assessment material. Read
> [INTERNAL_USE.md](INTERNAL_USE.md) before sharing it or changing repository
> visibility.

## Start here

| Goal | Start with |
|---|---|
| Inspect the final assessment without API access | `outputs/canonical_final/` and the dashboard |
| Understand the research design | `docs/research_workflow.md` and `docs/data_split_and_leakage_controls.md` |
| Check the authoritative thesis values | `FINAL_TRUTH_TABLE.md` |
| Understand what is current versus historical | `HANDOVER.md` and `REPOSITORY_AUDIT.md` |
| Re-execute the pipeline | The credentialed workflow below |

The canonical recorded run is `dema-20260917T132056Z`. It contains 232
accepted held-out evidence records, a 622-record combined evidence bank, and
31 final indicator assessments. These saved files are the authoritative
research record; a new execution is a new run, not a replacement.

## Architecture

```text
Prepared Markdown chunks (external conversion step)
        |
        v
Stage 1: GPT-4.1 evidence extraction
        |  exact contiguous-quotation gate
        v
Accepted held-out evidence + frozen development evidence bank
        |
        v
Stage 2: GPT-4.1 maturity scoring for 31 indicators
        |  indicator coverage and evidence-ID checks
        v
Validated JSON assessment
        |
        v
Static DEMA dashboard
```

The pipeline retrieves pinned prompt versions from Langfuse and verifies their
hashes before making model calls. The exact prompt snapshots are also committed
under `prompts/stage1/frozen/` and `prompts/stage2/frozen/`.

Document acquisition, Docling conversion, OCR, and chunk creation happened
upstream. Their implementation is not in this repository. Prepared inputs and
conversion provenance are retained under `data/`.

## Repository structure

| Path | Role |
|---|---|
| `pipeline/` | Current executable implementation |
| `dashboard/` | Current Vite dashboard and canonical-data generator |
| `data/` | Prepared development/final inputs, source archive, and provenance |
| `outputs/canonical_final/` | Authoritative final run; do not overwrite |
| `prompts/*/frozen/` | Exact production prompt snapshots and manifests |
| `prompts/*/development/` | Historical prompt lineages |
| `experiments/` | Historical calibration and sensitivity work |
| `evaluation/` | Traceability, negative-control, evidence-quality, and expert-review results |
| `reports/`, `figures/` | Research communication outputs |
| `docs/` | Methods, limitations, reproducibility, and artefact register |
| `tests/` | Offline pipeline and saved-output integrity checks |

Historical experiment scripts are preserved for provenance. Some contain paths
from the original Windows workspaces and are not supported production entry
points. See the READMEs in those areas before running them.

## Prerequisites

- Python 3.12 (reference version)
- Node.js 22 and npm (dashboard only)
- Authorized Langfuse access to both pinned prompts (pipeline reruns only)
- An authorized Azure OpenAI or OpenAI endpoint with the configured GPT-4.1
  deployment (pipeline reruns only)

## Install and verify without model calls

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "pipeline"
python -m unittest discover -s tests -v
python scripts/preflight.py
```

On macOS or Linux, activate with `source .venv/bin/activate` and run the tests
as `PYTHONPATH=pipeline python -m unittest discover -s tests -v`.

The tests and preflight do not contact Langfuse or OpenAI.

## Credentials and configuration

Copy `.env.example` to `pipeline/.env` and fill it locally. Never commit that
file. The pipeline supports:

- `AI_PROVIDER=azure`: requires `AZURE_OPENAI_ENDPOINT`,
  `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT`;
- `AI_PROVIDER=openai`: requires `OPENAI_API_KEY`; `OPENAI_BASE_URL` and
  `OPENAI_MODEL` are optional;
- both providers: require `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and
  `LANGFUSE_HOST`.

For Azure, `AZURE_OPENAI_ENDPOINT` must be the OpenAI-compatible base URL used
by the installed OpenAI client, normally ending in `/openai/v1/`. The model
value is the Azure deployment name, not only the underlying model family.

Check readiness without exposing values:

```powershell
python scripts/preflight.py --require-credentials
```

## Input data

Stage 1 expects a directory tree of Markdown processing units and recursively
processes every `.md` file. The canonical corpus uses units of up to
approximately ten pages. Each
file should preserve page markers from the conversion process and should carry
stable `source_id`, `source_url`, and processing-unit provenance. See
`data/sample_input/example_chunk.md` for the expected shape.

The sample illustrates formatting only. It is not an evaluation dataset and a
no-cost mock pipeline is not implemented.

## Run the pipeline

### Full two-stage workflow

The current production entry point runs Stage 1 and Stage 2 together:

```powershell
$env:PYTHONPATH = "pipeline"
python pipeline/main.py `
  --chunks data/final_assessment/chunks `
  --base-bank data/final_assessment/base_evidence_bank.json `
  --output working-runs/my-run
```

Equivalent shell command:

```bash
PYTHONPATH=pipeline python pipeline/main.py \
  --chunks data/final_assessment/chunks \
  --base-bank data/final_assessment/base_evidence_bank.json \
  --output working-runs/my-run
```

This command makes paid/external API calls. It retrieves and verifies the
frozen Langfuse prompts, extracts evidence from every Markdown chunk, combines
accepted rows with the supplied base bank, scores all 31 indicators, and writes
a run manifest plus intermediate artefacts. Completed Stage 1 chunks are
resumable when their input and prompt hashes match.

Separate Stage 1-only and Stage 2-only command-line entry points are **not
implemented**. The functions exist within the combined pipeline, but the
supported CLI is the full workflow above.

Never point a rerun at `outputs/canonical_final/`. New runs belong under the
ignored `working-runs/` directory and require review before promotion.

## Outputs

A completed run contains:

- `manifest.json`: run identity, prompts, inputs, progress, and call metadata;
- `stage1/`: per-chunk requests, responses, parsed outputs, and validation;
- `stage1_rejected_rows.json`: rows excluded by the exact-quotation gate;
- `combined_evidence_bank.json`: the Stage 1/Stage 2 boundary;
- `stage2/`: batch artefacts and consolidated `final_score.validated.json`.

The committed canonical equivalents are under `outputs/canonical_final/`.

## Dashboard

The dashboard uses saved canonical files and makes no model calls:

```powershell
Set-Location dashboard
npm ci
npm run dev
```

For a production build and data-integrity check:

```powershell
npm run build
npm run check:data
```

`dashboard/public/`, `dashboard/dist/`, and `dashboard/node_modules/` are
generated locally and intentionally ignored. The generated site includes
copies of cited archived sources; do not publish it without the review required
by `INTERNAL_USE.md`.

## Research record and limitations

The eight-source development population, 14-source held-out Stage 1 population,
and complete 22-source final assessment are distinct. Their authoritative
denominators are in `FINAL_TRUTH_TABLE.md`.

Important limitations include documentary and conversion bias, model
variability, dependence on external hosted services, and the distinction
between textual traceability and factual validity. See `docs/limitations.md`
and `docs/reproducibility.md` for the complete handover notes.
