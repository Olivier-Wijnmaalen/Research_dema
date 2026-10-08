## 7.2.2 Technical traceability

Technical traceability was evaluated on the non-development set of 30 held-out chunks. The frozen Stage 1 prompt generated 238 candidate evidence records. Schema compliance was 100% (238/238): every generated record conformed to the required output structure and contained all mandatory fields.

The traceability score was also 100% (238/238). Every supporting quotation could be traced to its corresponding Markdown source chunk after applying non-substantive normalization for Markdown emphasis and list markers, Unicode and whitespace variation, and conversion artefacts occurring at page boundaries. The validator continued to require the substantive wording of the quotation to be present in the identified source; it did not accept paraphrased or unsupported evidence.

Six records required non-substantive normalization during matching. Three joined a sentence across a page boundary while omitting page metadata or the placement of an intervening footnote, two omitted Markdown emphasis markers, and one added a Markdown bullet marker. Because these differences affected document formatting rather than evidentiary content, all six records were treated as traceable.

| Accepted normalization mode | Evidence records | % of evaluation set |
|---|---:|---:|
| Cross-page continuation with conversion metadata or footnote placement omitted | 3 | 1.3% |
| Markdown emphasis markers omitted | 2 | 0.8% |
| Markdown bullet marker added | 1 | 0.4% |
| No normalization required | 232 | 97.5% |
| **Total traceable records** | **238** | **100.0%** |

The evaluation therefore produced 100% schema compliance and 100% evidence traceability. No generated evidence record contained a substantive quotation that could not be reconstructed from its designated Markdown source.
