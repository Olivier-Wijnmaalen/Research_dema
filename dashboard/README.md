# Assessment dashboard

This Vite application presents the saved canonical assessment. It does not call a model and contains no extraction or scoring logic.

Run `npm ci`, `npm run build`, and `npm run check:data`. The generator reads `outputs/canonical_final/`, `data/provenance/corpus_index.csv`, and `data/final_assessment/source_archive/`. Generated `public/`, `dist/`, and dependency folders are intentionally ignored.
