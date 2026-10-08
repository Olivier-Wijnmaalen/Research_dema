import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const appDirectory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(await readFile(path.join(appDirectory, 'public', 'data.json'), 'utf8'));
const indicators = data.dimensions.flatMap((dimension) =>
  dimension.subdimensions.flatMap((subdimension) => subdimension.indicators),
);
const evidenceIds = new Set(data.evidence.map((item) => item.id));
const referencedIds = new Set(indicators.flatMap((indicator) => indicator.evidence_refs.map((reference) => reference.id)));
const failures = [];

if (indicators.length !== 31) failures.push(`Expected 31 final indicators, found ${indicators.length}.`);
if (data.traceability.cited_evidence_count !== data.evidence.length) failures.push('Traceability evidence count is inconsistent.');
if (data.evidence.some((item) => !item.source_url || !item.trace_url)) failures.push('One or more evidence records has no traceable original URL.');
if (data.evidence.some((item) => !item.archive_url || !item.archive_trace_url)) failures.push('One or more evidence records has no archived source URL.');
if ([...referencedIds].some((id) => !evidenceIds.has(id))) failures.push('One or more indicator references is absent from the evidence library.');
if (data.dimensions.length !== 3) failures.push(`Expected 3 dimensions, found ${data.dimensions.length}.`);
if (!data.source_analysis?.length) failures.push('Source analysis is missing.');
if (data.source_analysis?.some((source) => !source.page_estimate || source.evidence_item_count < 0)) failures.push('One or more source-analysis records is invalid.');
if (data.source_analysis?.reduce((sum, source) => sum + source.evidence_item_count, 0) !== data.traceability.evidence_bank_count) failures.push('Source-analysis evidence counts do not reconcile to the evidence bank.');

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}

console.log(
  `Data checks passed: ${indicators.length} indicators, ${data.evidence.length} cited records, ${data.source_analysis.length} analyzed sources, ${data.traceability.linked_evidence_count} original links, ${data.traceability.archived_evidence_count} archived links.`,
);
