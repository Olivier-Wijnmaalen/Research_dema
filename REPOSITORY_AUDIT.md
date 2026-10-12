# Repository audit and retention decisions

Audit date: 2026-10-12

This audit was completed before the handover cleanup. It records what is
operational, what is archival, and what may be regenerated.

## Essential current implementation

| Area | Essential files | Finding |
|---|---|---|
| Pipeline entry | `pipeline/main.py` | Supported full-workflow CLI |
| Pipeline logic | `pipeline/dema/*.py` | Current extraction, scoring, validation, storage, prompt, and client code |
| Configuration | `.env.example`, `pipeline/dema/config.py` | Repository-relative paths; pinned prompt names, versions, and hashes |
| Canonical input | `data/final_assessment/chunks/`, `base_evidence_bank.json` | Prepared Markdown and frozen development bank |
| Canonical output | `outputs/canonical_final/*.json` | Authoritative saved run |
| Dashboard | `dashboard/src/`, `dashboard/scripts/`, package files | Current static presentation layer |
| Tests | `tests/*.py`, `.github/workflows/tests.yml` | Offline integrity and CI checks |

The pipeline calls Langfuse to retrieve two pinned text prompts and uses the
OpenAI Responses API through either an Azure OpenAI-compatible endpoint or the
OpenAI endpoint. Environment variables are documented in `.env.example`.

## Research archive: retain

The following areas are not production dependencies but are necessary to
interpret the thesis and previous runs:

- `prompts/*/development/`: prompt lineages and mutation records;
- `experiments/stage1/`: Stage 1 calibration and historical validation;
- `experiments/stage2/`: scoring-prompt calibration;
- `experiments/sensitivity/`: negative-source and order-sensitivity scripts;
- `evaluation/`: saved traceability, evidence-quality, negative-control,
  prompt-sensitivity, and expert-review results;
- `reports/` and `figures/`: thesis-facing research products;
- `data/development/` and `data/provenance/`: development populations and
  provenance;
- source archives and frozen prompt snapshots.

Some historical scripts and manifests contain absolute paths into the original
Windows workspaces. These paths are machine-specific, but changing them would
rewrite the record of the executed research. They are therefore retained and
labelled archival. They must not be treated as current entry points.

Exact duplicate prompt texts also remain where one copy represents a
development state and another represents a frozen state. Their provenance role
is more important than deduplication.

## Generated material: safe to remove and rebuild

- Python `__pycache__/` directories and `*.pyc` files;
- `.pytest_cache/` and coverage output;
- `dashboard/node_modules/`;
- `dashboard/public/` generated data and copied sources;
- `dashboard/dist/` production build;
- local runs under `working-runs/` or `outputs/local_runs/`.

No tracked research artefact was classified as safe to delete.

## Portability and reproducibility findings

- Current pipeline paths derive from the repository location and are portable
  across operating systems.
- Historical experiment scripts are not generally portable because they retain
  original paths.
- The repository does not include document acquisition, Docling conversion, or
  OCR code.
- The current CLI requires a directory of Markdown chunks and a base evidence
  bank; it is not a single-document standalone tool.
- Separate Stage 1 and Stage 2 command-line entry points do not exist.
- Exact reruns depend on external prompt/model services and are not guaranteed
  to reproduce byte-identical outputs.
- The dashboard can be rebuilt offline from committed data after npm packages
  have been installed.

## Security and sharing findings

No live OpenAI, Azure OpenAI, or Langfuse credential was detected in tracked
files during the audit. Apparent `sk-` matches in two archived source files were
parts of ordinary URLs, not API keys.

The larger sharing risk is content rather than credentials: archived
third-party documents, exact quotations, country-assessment material, and an
expert-response workbook require an authorization, copyright, and
data-protection decision before public distribution. `INTERNAL_USE.md` remains
the controlling repository notice.

## Validation observed during audit

- 14 Python unit tests passed without model calls.
- Dashboard data checks passed for 31 indicators, 240 cited evidence records,
  22 analysed sources, and complete original/archive linking.
- The canonical truth tests confirmed the frozen prompt identities, final
  population counts, final scores, and retained negative-control outcomes.
