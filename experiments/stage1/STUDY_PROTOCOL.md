# DEMA Stage 1 lenient-traceability prompt-development protocol

This is a new calibration study and does not overwrite the earlier V5–V9 analysis.

- Prompt family: `dema-lenient-calibration/evidence-extraction`.
- Versions: one V6-derived baseline followed by exactly five sequential prompt mutations (six full-corpus runs).
- Corpus: the same fixed 30 processing units listed in `output/newframework-compact-all-chunks/chunk-manifest.json`.
- Segmentation represented by the corpus: at most 10 pages per paginated unit with one repeated boundary page.
- Fixed generation conditions: `gpt-4.1-students`, temperature 0, maximum output 32,768 tokens, country Togo, one retained generation per chunk. A failed execution may be retried once and must be archived.
- Fixed task components: authoritative DEMA framework, output schema, corpus, schema checker and lenient technical validator.
- Evidence-item schema compliance is calculated row by row: valid evidence items divided by all generated evidence items. Each item is checked for the exact permitted row fields, string types, non-empty required values, permitted enumerations, a valid page format and its deterministic sequential evidence ID. Webpage page numbers must be empty. JSON parseability and top-level envelope errors are reported separately and are not called evidence-item schema compliance.
- Lenient traceability accepts exact and previously approved normalized matches plus a closed format-equivalence whitelist: first-character case only, Markdown emphasis markers, duplicated list-marker hyphens, and adjacent OCR apostrophe/quotation-mark artifacts. Every transformation is labelled. General fuzzy matching is prohibited.
- Deterministic repairs remain restricted to one added terminal punctuation mark, page reference and source URL. Internal omissions, invented ellipses, non-contiguous stitching and substantive reconstruction remain failures.
- Each mutation must respond to the immediately preceding run's observed failure modes. The exact added, removed or altered instructions must be logged before the next run.
- Eligibility: all 30 outputs must parse, evidence-item schema compliance must be 100%, and candidate-row yield must be at least 90% of the new baseline. Top-level envelope errors are a separately reported disqualifier.
- Primary selection metric among eligible versions: post-repair lenient traceability percentage across all generated rows.
- Tie rule: differences below one percentage point are ties; prefer the higher strict exact-match percentage, then the earlier and less-complex prompt.
- AIS is post-selection only and cannot guide mutations or selection.
- Freeze package: exact prompt text, Langfuse version/labels, configuration, SHA-256, mutation log, schema report, traceability report and failure audit.
