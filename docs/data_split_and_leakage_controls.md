# Data split and leakage controls

## Split

Eight sources were marked as development sources in `data/provenance/corpus_index.csv`: `001`, `010`, `018`, `027`, `030`, `031`, `032`, and `033`. Their prepared chunks were used during prompt research. The frozen development evidence bank contributes 390 records at the final pipeline boundary.

The final Stage 1 run processed 30 held-out chunks from 14 non-development sources: `005`, `006`, `007`, `008`, `011`, `015`, `019`, `020`, `022`, `023`, `024`, `026`, `028`, and `029`. The final assessment then scored the combined development-plus-held-out evidence bank.

## Controls retained in the repository

- Development and final-assessment inputs are in separate directories.
- Prompt lineages are distinct from frozen production snapshots.
- The canonical manifest records prompt names, versions, hashes, input hashes, and run metadata.
- Stage 1 validates quotations against the exact supplied chunk.
- Stage 2 rejects unknown evidence citations.
- Synthetic/negative-control sources are isolated under experiments and are not part of the canonical evidence bank.
- The committed canonical output is read-only by convention; new runs write to ignored working directories.

## Important interpretation

“Held out” applies to Stage 1 prompt development: the 14 final sources were not used to tune that extraction prompt. Stage 2 necessarily receives the combined bank, including the frozen development records, because its target is the full documentary assessment. This is therefore a controlled development/final-source separation, not a claim of a fully independent external validation dataset.

See `data/provenance/corpus_index.csv` and `outputs/canonical_final/manifest.json` for the authoritative source labels and executed chunk list.
