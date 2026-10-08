## 7.2.2 Technical traceability

Technical traceability was assessed at three points in the final pipeline: the technical reconstruction of generated evidence from the source chunks, the attribution of each evidence statement to its supporting quotation, and the resolution of the evidence identifiers used in the final maturity justifications. Exclusions, normalization and deterministic repairs were retained as experimental outcomes rather than treated as invisible preprocessing.

The development-stage extraction generated 428 evidence rows. Under the frozen technical-validation policy, `PASS_EXACT` denoted a quotation that matched after Unicode NFKC and whitespace normalization, while `PASS_NORMALIZED` denoted equivalence after an additional whitelisted normalization for HTML entities or outer table boundaries. A record was labelled `REPAIR_REQUIRED` when the passage remained traceable but its page reference, URL or added terminal punctuation required correction; `FAIL` indicated that the passage could not be reconstructed under these deterministic rules. Of the 428 rows, 395 were `PASS_EXACT`, six were `PASS_NORMALIZED`, seven were `REPAIR_REQUIRED`, and 20 were `FAIL`. The strict pass rate was therefore 92.3%, the accepted pass rate was 93.7%, and the broader traceability rate—including records that were traceable but required correction—was 95.3%.

| Development technical outcome | Rows | Percentage of generated rows |
|---|---:|---:|
| PASS_EXACT | 395 | 92.3% |
| PASS_NORMALIZED | 6 | 1.4% |
| REPAIR_REQUIRED | 7 | 1.6% |
| FAIL | 20 | 4.7% |
| **Total** | **428** | **100.0%** |

The 20 non-traceable rows represented 16 distinct quoted passages because several failed passages had been reused for more than one DEMA indicator. Post-hoc examination identified three mutually exclusive failure modes. Ten rows (50.0% of technical failures) reconstructed material from tables, forms, lists or headings in a way that was not a contiguous representation of the stored source. Six rows (30.0%) contained local OCR, spacing or quotation-boundary variations that exceeded the approved normalization rules. Four rows (20.0%) combined non-contiguous source passages into a single quotation. The seven `REPAIR_REQUIRED` records consisted of five incorrect page references and two instances in which terminal punctuation had been added to the quoted passage. A further six records were retained through the approved form-table layout normalization. These results show that document layout and quotation construction, rather than missing URLs, were the principal technical obstacles to traceability.

| Development traceability failure mode | Rows | Percentage of 20 failed rows |
|---|---:|---:|
| Table, form, list or heading reconstruction | 10 | 50.0% |
| OCR, spacing or quotation-boundary variation | 6 | 30.0% |
| Composite or non-contiguous quotation | 4 | 20.0% |
| **Total non-traceable rows** | **20** | **100.0%** |

The development run also exhibited one generation-level failure. For chunk 13, six independent generation attempts ended in malformed or truncated output. Three complete evidence objects preceding the truncation point were conservatively retained, while one incomplete object was discarded without reconstruction. This represents a distinct failure mode from quotation traceability: the model produced an incomplete structured response before the technical validator could assess the unfinished row.

Attribution assessment identified a second class of failure. Across all 428 development rows, 204 were classified as fully attributable, 211 as partially attributable, and 13 as not attributable. Qualitative coding of the 13 `NOT_ATTRIBUTABLE` rows showed that five inferred the collection, availability or use of data from text that merely described activities, scenarios or information; four inferred that a planned system, tool or activity had been implemented or was operational; three added unsupported contextual, process, geographic or causal provenance; and one misclassified data-collection participants as data users. Two of these 13 rows had already failed the technical traceability assessment. Consequently, the attribution filter excluded 11 additional technically accepted rows rather than 13 additional rows.

| Attribution failure mode | Rows | Percentage of 13 NOT_ATTRIBUTABLE rows |
|---|---:|---:|
| Data collection, availability or use inferred | 5 | 38.5% |
| Implementation or operational status inferred | 4 | 30.8% |
| Unsupported context, process or provenance | 3 | 23.1% |
| Actor-role misclassification | 1 | 7.7% |
| **Total** | **13** | **100.0%** |

Combining the technical and attribution criteria retained 390 of the 428 development rows (91.1%) for maturity scoring. Thirty-eight rows were excluded: 25 failed only the technical criteria, 11 failed only the attribution criterion, and two failed both. This distinction also explains the difference between the 401 technically accepted development records and the 390 development records actually supplied to the final scoring pipeline.

The frozen prompt was then applied to the non-development corpus. It generated 238 candidate evidence rows from 30 chunks, of which 232 were retained and six were rejected because their quotations were not exact contiguous substrings of the supplied chunk. Three of these six failures were minor formatting or punctuation variations, two were localized textual or quotation-boundary variations, and one was a composite or non-contiguous quotation. The held-out exact-quotation retention rate was therefore 97.5%.

| Non-development traceability failure mode | Rows | Percentage of six rejected rows |
|---|---:|---:|
| Minor formatting or punctuation variation | 3 | 50.0% |
| Localized textual or boundary variation | 2 | 33.3% |
| Composite or non-contiguous quotation | 1 | 16.7% |
| **Total** | **6** | **100.0%** |

The combined scoring bank contained 622 evidence records: 390 development records and 232 non-development records. All 622 records had unique identifiers, supporting quotations, source URLs, page references and local chunk locators. The dedicated `source_file` field was populated for only 321 records; it was blank for 301 development records. The latter records nevertheless retained a source URL, page number and chunk path, so the omission constituted incomplete metadata rather than complete provenance loss. No content-based deduplication was applied. Thirty groups of identical quotations involving 71 records and two groups of identical evidence statements involving four records therefore remained in the bank. This repetition must be considered when interpreting evidence-item counts because separate records do not always represent independent source passages.

The 31 final maturity assessments contained 337 evidence references covering 238 distinct evidence records. Thirty citation-format occurrences required deterministic post-processing: 23 held-out identifiers contained an erroneous `V4ID-` prefix, five development identifiers lacked zero-padding, and two source-locator strings were removed where the correct evidence identifier was already present. After these transformations, all 337 references resolved to records in the evidence bank. The final identifier-resolution rate was therefore 100%, but the unprocessed scoring output was not fully compliant with the evidence-ID schema. The need for 30 citation repairs is part of the observed prompt-pipeline performance and should not be omitted from the evaluation.

Overall, the experiment demonstrated high but non-perfect technical traceability. The main failure mechanisms were document-layout reconstruction, non-contiguous quotation construction, semantic over-inference from documentary text, and malformed citation identifiers. The results further show why the retention rate of the final evidence bank should not be reported as the traceability performance of the extraction prompt: the final bank contains only records that survived the technical and attribution filters, whereas the experimentally relevant error rates arise from all generated rows.
