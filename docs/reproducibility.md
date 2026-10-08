# Reproducibility

## Inspecting the recorded run

The canonical run can be audited without credentials or paid calls. Its minimum record is:

- `outputs/canonical_final/manifest.json`;
- `outputs/canonical_final/combined_evidence_bank.json`;
- `outputs/canonical_final/final_score.validated.json`;
- `prompts/stage1/frozen/prompt_stage1.json`;
- `prompts/stage2/frozen/prompt_stage2.json`;
- `data/final_assessment/chunks/` and `data/provenance/`.

Run the unit tests from the repository root with `PYTHONPATH=pipeline`. The saved-output test expects 622 unique evidence records and 31 complete indicator assessments.

## Re-execution

Python 3.12 is the reference runtime. Install `requirements.txt`, configure `pipeline/.env`, and run `python pipeline/main.py`. The code retrieves pinned Langfuse prompt versions and verifies their hashes before using the model. Outputs are written atomically and completed Stage 1 chunks are resumable.

Exact byte-for-byte regeneration is not guaranteed because hosted models and external services can change. The committed snapshots and outputs are the reproducible record; a re-execution is a new run that should receive a new manifest and review.

## Dashboard

Node.js 22 is the CI runtime. `npm ci` uses the lockfile. `npm run build` first regenerates dashboard data from the canonical output and source archive, then builds the static site.

## Environment capture

The repository retains dependency lower bounds rather than a complete Python lockfile because the original workspaces did not contain one. For a formal archival release, create and test a locked environment, record the operating system and model deployment identifiers, and tag the exact Git commit.
