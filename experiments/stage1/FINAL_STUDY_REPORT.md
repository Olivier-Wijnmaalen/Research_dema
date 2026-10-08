# Stage 1 prompt-development result

The schema checker scores evidence items, not chunks. JSON parseability and top-level contract errors are separate controls.

## Results

| Langfuse version | Iteration | Items | Schema-valid | Schema % | Traceable | Traceability % | Strict exact % | Eligible |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 0 | 435 | 426 | 97.93 | 418 | 96.09 | 94.71 | No |
| 2 | 1 | 404 | 404 | 100.00 | 380 | 94.06 | 92.33 | Yes |
| 3 | 2 | 413 | 413 | 100.00 | 402 | 97.34 | 95.88 | Yes |
| 4 | 3 | 438 | 438 | 100.00 | 423 | 96.58 | 96.12 | Yes |
| 5 | 4 | 416 | 416 | 100.00 | 408 | 98.08 | 96.15 | Yes |
| 6 | 5 | 464 | 464 | 100.00 | 451 | 97.20 | 96.34 | Yes |

## Selection

Version 6 is within 0.88 percentage points of the highest traceability rate and has the highest strict exact rate in the tie set.
The selected prompt is Langfuse version 6, labelled `frozen-lenient-stage1`.

## Post-selection AIS

AIS was run only after freezing and did not guide selection. Across 451 technically accepted rows: 291 were fully attributable, 152 partially attributable, and 8 not attributable.

## Exact mutation record

### Iteration 1 (Langfuse version 2)

Rationale: Baseline had 9 webpage page-field violations and 17 non-contiguous or reconstructed quotations, concentrated in tables, lists, and page boundaries.

Added text:

```text
FINAL ITEM SELF-CHECK — ITERATION 1
Before serialization, check every evidence item independently:
1. If INPUT_TEXT represents an unpaginated webpage, set page_number to the empty string "". Never output "not_applicable", "N/A", a URL, or descriptive text in page_number.
2. Compare supporting_quote character-for-character with one uninterrupted span in INPUT_TEXT. Preserve source punctuation, apostrophes, hyphens, spacing, line breaks, list markers, table cells, and OCR artefacts; do not silently smooth or regularise them.
3. For a table, form, or list, prefer the shortest uninterrupted span that establishes the proposition. If the desired wording would require joining cells, rows, list entries, pages, or separated fragments, use a smaller contiguous quote or omit the item.
```

### Iteration 2 (Langfuse version 3)

Rationale: Iteration 1 reached 100% item-schema compliance but had 24 traceability failures: 5 omissions, 7 stitched passages, and 12 reconstructed passages.

Added text:

```text
ATOMIC QUOTE UNIT — ITERATION 2
For each item, copy the quotation before drafting any other field. Prefer exactly one complete source sentence, one uninterrupted list item, or one uninterrupted table row. Extend beyond that unit only when the additional adjacent text is indispensable to establish the same proposition. Never use a Markdown heading, stored page label, HTML comment, metadata line, or repeated boundary page as a bridge between quotation fragments. Never replace source text with an ellipsis or omission symbol. After copying, locate the complete candidate quotation as one literal span in INPUT_TEXT; if it cannot be located, shorten it to a locatable atomic unit or omit the item.
```

### Iteration 3 (Langfuse version 4)

Rationale: Iteration 2 had 11 failures; six removed intervening source text and three reconstructed form/table text, often around page or layout boundaries.

Added text:

```text
PAGE AND TABLE BOUNDARIES — ITERATION 3
Treat every stored page marker, `## Page` label, and `<!-- source_url=... -->` metadata comment as an absolute quotation boundary. A supporting_quote must stay entirely on one side of such a boundary; do not delete the boundary and join the surrounding prose. If a sentence is split by a boundary, select a complete contiguous fragment from one side that still establishes the proposition or omit the item. For Markdown tables, copy one literal source row including its `|` separators when that row is sufficient. Do not reconstruct a row by joining visually aligned columns, wrapped OCR fragments, headers, or cells.
```

### Iteration 4 (Langfuse version 5)

Rationale: Iteration 3 had 15 failures, including seven substantial reconstructions, four webpage reconstructions, and two inserted omissions; optional atomicity was insufficient.

Added text:

```text
MANDATORY QUOTE ATOMICITY — ITERATION 4
The atomic quote unit is mandatory, not a preference. Each supporting_quote must be limited to one contiguous source sentence, one list item, one table row, or one short contiguous paragraph when the source has no sentence boundary. Do not combine multiple units into one quote. When extracting from a webpage, copy the selected Markdown source span exactly as supplied, including visible heading or emphasis markers that fall inside the selected span; do not rewrite the webpage into plain prose. A quotation containing `...`, `â€¦`, or `[...]` is permitted only when the identical omission characters already occur at the same position in INPUT_TEXT.
```

### Iteration 5 (Langfuse version 6)

Rationale: Iteration 4 had eight failures: six removed intervening source material, one inserted an omission, and one substantially altered an OCR token.

Added text:

```text
LITERAL-SPAN REJECTION TEST — ITERATION 5
Reject a candidate quotation unless all of the following are true: (a) its first character and last character delimit one substring that occurs in INPUT_TEXT; (b) every character between those boundaries is retained in the same order; (c) no page marker, metadata comment, heading, cell, list item, line, or OCR token between those boundaries has been deleted; and (d) no character, punctuation mark, space, or omission symbol has been added or corrected. When a source sentence is interrupted by stored layout material, do not quote the reconstructed sentence: choose a shorter phrase wholly between two boundaries. Perform this rejection test separately for every evidence item immediately before returning JSON.
```
