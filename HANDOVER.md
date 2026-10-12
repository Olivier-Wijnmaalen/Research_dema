# Project handover

## Current status

The repository contains a complete recorded DEMA research run and a runnable
implementation of the same two-stage workflow. The saved canonical result can
be inspected and presented without credentials. Re-execution requires
authorized Langfuse and model-service access and incurs external API usage.

| Component | Status | Entry point |
|---|---|---|
| Frozen research record | Complete | `outputs/canonical_final/` |
| Stage 1 + Stage 2 pipeline | Runnable with credentials | `pipeline/main.py` |
| Dashboard | Runnable without model access | `dashboard/package.json` |
| Offline integrity tests | Runnable | `tests/` |
| Input/configuration preflight | Runnable without network access | `scripts/preflight.py` |
| PDF/web-to-Markdown conversion | External/not included | See `pipeline/document_preparation/README.md` |
| Separate Stage 1-only and Stage 2-only CLIs | Not implemented | Use the combined entry point |

## Authoritative artefacts

Do not overwrite or regenerate these files in place:

- `FINAL_TRUTH_TABLE.md`;
- `outputs/canonical_final/manifest.json`;
- `outputs/canonical_final/combined_evidence_bank.json`;
- `outputs/canonical_final/final_score.validated.json`;
- `data/final_assessment/base_evidence_bank.json`;
- `prompts/stage1/frozen/` and `prompts/stage2/frozen/`;
- retained evaluation results under `evaluation/`;
- historical experiment configurations and results under `experiments/`.

The canonical run ID is `dema-20260917T132056Z`. The final bank contains 622
evidence records and the validated assessment contains all 31 DEMA indicators.

## Architectural decisions

1. **One explicit evidence-bank boundary.** Stage 2 consumes the combined bank,
   not raw documents or Stage 1 prose.
2. **Pinned remote prompts plus local snapshots.** Runtime prompt retrieval is
   verified against recorded hashes; local snapshots preserve inspectability.
3. **New runs are non-destructive.** The default output is
   `working-runs/latest/`, which Git ignores. Canonical promotion is a deliberate
   review action.
4. **Dashboard logic is separate from assessment logic.** The dashboard only
   transforms saved canonical JSON and source provenance into static assets.
5. **Historical paths are retained in research records.** Absolute paths inside
   old manifests and experiment scripts document original execution contexts;
   they are not production configuration.
6. **No claim of conversion reproducibility.** Docling/OCR implementation is
   outside this repository.

## Where a future developer should start

1. Read `README.md`, `FINAL_TRUTH_TABLE.md`, and `INTERNAL_USE.md`.
2. Run `python scripts/preflight.py` and the offline unit tests.
3. Read `pipeline/main.py` and `pipeline/dema/pipeline.py`.
4. Inspect the frozen prompt manifests before changing any prompt-related code.
5. Build the dashboard and run `npm run check:data`.
6. Treat `experiments/` as an archive unless reproducing a named study.

## Known technical constraints

- The supported CLI executes the complete two-stage workflow; it does not expose
  independent Stage 1-only or Stage 2-only commands.
- The pipeline expects a directory of prepared Markdown chunks and an existing
  base evidence bank.
- A small no-cost mocked end-to-end run is not implemented.
- Hosted model behavior and external prompt services can change; the committed
  artefacts, not a future rerun, are the reproducible research record.
- Python dependencies use tested lower bounds rather than a hash-locked
  environment. The dashboard is locked with `package-lock.json`.
- The generated dashboard contains copies of cited sources and is not approved
  for unrestricted public hosting.

## Sharing checklist

Before giving access to Red Cross staff or collaborators:

- keep the repository private unless copyright and data-protection review says
  otherwise;
- confirm recipients are authorized to view country-assessment content and the
  archived sources;
- run the offline tests, dashboard build/check, and a secret scan;
- inspect the complete Git history for secrets, not only the working tree;
- decide whether the expert-response workbook may be shared with the intended
  audience;
- tag the approved handover commit and record the environment used.

For a ZIP containing only version-controlled handover files (and therefore no
local environments, caches, or dashboard build folders), run after committing:

```powershell
git archive --format=zip --output=../dema-research-handover.zip HEAD
```
