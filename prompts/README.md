# Prompt archive

`development/` directories preserve selected prompt lineages used during calibration. `frozen/` directories preserve the exact production snapshots and freeze manifests. The canonical run is authoritative: Stage 1 used `prompt_stage1.json` (Langfuse version 6, SHA-256 recorded in the run manifest), and Stage 2 used `prompt_stage2.json` (P5 / Langfuse version 1).

Some development folders contain alternative calibration families. Their presence documents research history and does not mean they were used in the canonical run.
