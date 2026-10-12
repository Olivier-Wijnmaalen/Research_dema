# Historical research experiments

This directory is a provenance archive, not the supported pipeline entry point.

- `stage1/` preserves extraction-prompt calibration and traceability work.
- `stage2/` preserves maturity-scoring prompt development and behavioural tests.
- `sensitivity/` preserves negative-source and order-sensitivity experiments.

Scripts may refer to the original `OPENAI_AZURE_V1`, `FINAL_SCORE`, or
`full_assesmnet_line` Windows workspaces. Those paths describe the historical
execution context and are intentionally not rewritten. Saved inputs,
configurations, and outputs must not be altered when preparing new runs.

Use `pipeline/main.py` for the current workflow. Re-run a historical experiment
only after reviewing its inputs, service calls, cost, and output destination.
