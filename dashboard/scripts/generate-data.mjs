import { createHash } from 'node:crypto';
import { copyFile, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const appDirectory = path.resolve(scriptDirectory, '..');
const projectDirectory = path.resolve(appDirectory, '..');

const scorePath = path.join(projectDirectory, 'outputs', 'canonical_final', 'final_score.validated.json');
const evidencePath = path.join(projectDirectory, 'outputs', 'canonical_final', 'combined_evidence_bank.json');
const corpusPath = path.join(projectDirectory, 'data', 'provenance', 'corpus_index.csv');
const downloadsPath = path.join(projectDirectory, 'data', 'final_assessment', 'source_archive');
const outputPath = path.join(appDirectory, 'public', 'data.json');

const [scoreText, evidenceText, corpusText] = await Promise.all([
  readFile(scorePath, 'utf8'),
  readFile(evidencePath, 'utf8'),
  readFile(corpusPath, 'utf8'),
]);

const scoreDocument = JSON.parse(scoreText);
const evidenceDocument = JSON.parse(evidenceText);
const corpusRows = parseCsv(corpusText);
const sourceIndex = new Map(corpusRows.map((row) => [row.source_id, row]));
const downloadedFiles = await readdir(downloadsPath);
const archiveFileBySource = new Map(
  downloadedFiles
    .map((fileName) => [fileName.match(/^(\d{3})\./)?.[1], fileName])
    .filter(([sourceNumber]) => sourceNumber),
);
const bankIndex = new Map(evidenceDocument.evidence_items.map((item) => [normaliseId(item.evidence_id), item]));

const phaseNames = {
  1: 'Incomplete, ad hoc',
  2: 'Recognized but reactive',
  3: 'Managed and defined',
  4: 'Controlled, optimizing',
  5: 'State of the art, transformational',
};

const dimensionMeta = {
  A: {
    label: 'Actors & roles',
    description: 'People, mandates, coordination, and the capabilities required to sustain the ecosystem.',
    color: '#f5a623',
    pale: '#fff5dd',
  },
  B: {
    label: 'Data value chain',
    description: 'The supply, infrastructure, standards, accessibility, and practical use of data.',
    color: '#15a6a6',
    pale: '#e4f7f5',
  },
  C: {
    label: 'Data ecosystem governance',
    description: 'Trust, accountability, policy, investment, collaboration, and inclusion.',
    color: '#ef5b5b',
    pale: '#ffebea',
  },
};

const subdimensionLabels = {
  'A.1': 'Roles',
  'A.2': 'Capacity',
  'B.1': 'Data supply (quality & production)',
  'B.2': 'Data infrastructure (enablers)',
  'B.3': 'Data demand (use)',
  'C.1': 'Governance, ethics & trust',
  'C.2': 'Policies, standards & resources',
  'C.3': 'Collaboration & inclusion',
};

const sourceTitles = {
  '001': 'ANPC Bulletin No. 33 · July–September 2026',
  '005': 'Early warning partners join forces in Togo',
  '006': 'Agro-hydro-climatic outlook for northern Togo',
  '007': 'National mapping of meteorological data',
  '008': 'GIZ Togo project profile',
  '010': 'Togo national disaster risk reduction strategy',
  '011': 'Multi-hazard early warning and action framework for Africa',
  '015': 'Digital Transformation Strategy for Africa 2020–2030',
  '018': 'Open Data Day 2020 · Togo report',
  '019': 'Togo hydromet and early warning services',
  '020': 'ECOWAS field monitors for early warning in Togo',
  '022': 'ANPC training activities',
  '023': 'Local partnerships and cooperation report',
  '024': 'Togo data protection profile',
  '026': 'Regional disaster risk reduction platforms',
  '027': 'ANPC 2024 PDNA · Yoto, Anié and Tchamba',
  '028': 'ANPC in-depth post-disaster assessment 2024',
  '029': 'National civil protection policy · Horizon 2030',
  '030': 'National contingency plan 2022',
  '031': 'Météo Togo technical document',
  '032': 'MENTD–World Bank PANT environmental and social plan',
  '033': 'Togo national geodata portal',
};

const assessment = scoreDocument.result;
const indicators = assessment.indicator_assessments.map((indicator) => {
  const evidenceRoles = new Map();
  const addRole = (id, role) => {
    if (!id) return;
    const key = normaliseId(id);
    if (!evidenceRoles.has(key)) evidenceRoles.set(key, new Set());
    evidenceRoles.get(key).add(role);
  };

  for (const id of indicator.evidence_supporting_score ?? []) addRole(id, 'supporting');
  for (const id of indicator.contrary_or_limiting_evidence ?? []) addRole(id, 'limiting');
  for (const check of indicator.assigned_phase_requirement_checks ?? []) {
    for (const id of check.evidence_ids ?? []) addRole(id, 'requirement');
  }

  return {
    code: indicator.indicator_code,
    name: indicator.indicator_name,
    phase_score: indicator.phase_score,
    phase_name: phaseNames[indicator.phase_score],
    matched_phase_requirement: indicator.matched_phase_requirement,
    score_reasoning: indicator.score_reasoning,
    next_phase_gap: indicator.next_phase_gap,
    limiting_reasoning: indicator.contrary_or_limiting_reasoning,
    framework_ambiguity: indicator.framework_ambiguity,
    requirement_checks: (indicator.assigned_phase_requirement_checks ?? []).map((check) => ({
      requirement: check.requirement,
      status: check.status,
      explanation: check.explanation,
      evidence_ids: (check.evidence_ids ?? []).map(normaliseId),
    })),
    evidence_refs: [...evidenceRoles].map(([id, roles]) => ({ id, roles: [...roles] })),
  };
});

const evidenceUsage = new Map();
for (const indicator of indicators) {
  for (const reference of indicator.evidence_refs) {
    if (!evidenceUsage.has(reference.id)) evidenceUsage.set(reference.id, []);
    evidenceUsage.get(reference.id).push({ indicator_code: indicator.code, roles: reference.roles });
  }
}

const evidence = [...evidenceUsage].map(([id, usedBy]) => {
  const original = bankIndex.get(id);
  const sourceNumber = sourceNumberFor(original, id);
  const corpusSource = sourceIndex.get(sourceNumber);
  const sourceUrl = original?.source_url || corpusSource?.source_url || '';
  const archiveFile = archiveFileBySource.get(sourceNumber);
  const page = original?.page_number ? String(original.page_number) : '';

  return {
    id,
    source_number: sourceNumber,
    source_file: original?.source_file || corpusSource?.downloaded_file?.split(/[\\/]/).pop() || `${sourceNumber} source`,
    source_url: sourceUrl,
    trace_url: traceUrl(sourceUrl, page),
    archive_url: archiveFile ? `/sources/${archiveFile}` : '',
    archive_trace_url: archiveFile ? traceUrl(`/sources/${archiveFile}`, page) : '',
    page_number: page,
    statement:
      original?.evidence_statement ||
      'Source cited directly in the final assessment requirement check. Open the source to inspect the underlying record.',
    supporting_quote: original?.supporting_quote || '',
    assessment_use: original?.use_in_country_assessment || '',
    interpretation_boundary: original?.interpretation_boundary || '',
    evidence_scope: original?.evidence_scope || 'Country-specific',
    country_specificity: original?.country_specificity || 'Direct source citation',
    dimension: original?.dimension || '',
    subdimension: original?.subdimension || '',
    technical_validation_status: original?.technical_validation_status || 'SOURCE_REFERENCE',
    ais_validation_status: original?.ais_validation_status || 'NOT_APPLICABLE',
    confidence_identification: original?.confidence_identification ?? null,
    confidence_classification: original?.confidence_classification ?? null,
    used_by: usedBy,
  };
});

const unlinkedEvidence = evidence.filter((item) => !item.source_url);
if (unlinkedEvidence.length) {
  throw new Error(`Every cited evidence record must have a source URL. Missing: ${unlinkedEvidence.map((item) => item.id).join(', ')}`);
}

const unarchivedEvidence = evidence.filter((item) => !item.archive_url);
if (unarchivedEvidence.length) {
  throw new Error(`Every cited evidence record must have an archived source. Missing: ${unarchivedEvidence.map((item) => item.id).join(', ')}`);
}

const sourceAnalysis = await Promise.all(
  corpusRows
    .filter((source) => source.download_status === 'ok' && archiveFileBySource.has(source.source_id))
    .map(async (source) => {
      const sourceNumber = source.source_id;
      const fileName = archiveFileBySource.get(sourceNumber);
      const sourceItems = evidenceDocument.evidence_items.filter(
        (item) => sourceNumberFor(item, item.evidence_id) === sourceNumber,
      );
      const fileBuffer = await readFile(path.join(downloadsPath, fileName));
      const isPdf = fileName.toLocaleLowerCase().endsWith('.pdf');
      const length = isPdf
        ? pdfLength(fileBuffer, source.page_count)
        : webpageLength(fileBuffer.toString('utf8'));
      const citedItems = evidence.filter((item) => item.source_number === sourceNumber);
      const evidenceCount = sourceItems.length;

      return {
        source_number: sourceNumber,
        source_name: sourceName(sourceNumber, sourceItems[0]?.source_file, fileName),
        source_url: source.source_url,
        format: isPdf ? 'PDF' : 'Web page',
        page_estimate: length.pages,
        page_estimate_method: length.method,
        word_count: length.wordCount,
        evidence_item_count: evidenceCount,
        cited_evidence_count: citedItems.length,
        evidence_per_page: rate(evidenceCount, length.pages),
        cited_evidence_per_page: rate(citedItems.length, length.pages),
      };
    }),
);

const dimensions = Object.entries(dimensionMeta).map(([id, meta]) => {
  const dimensionIndicators = indicators.filter((indicator) => indicator.code.startsWith(`${id}.`));
  const subdimensionIds = [...new Set(dimensionIndicators.map((indicator) => indicator.code.match(/^[A-C]\.\d/)?.[0]))].filter(Boolean);
  return {
    id,
    ...meta,
    visual_score: mean(dimensionIndicators.map((indicator) => indicator.phase_score)),
    phase_distribution: phaseDistribution(dimensionIndicators),
    evidence_count: evidence.filter((item) => item.used_by.some((usage) => usage.indicator_code.startsWith(`${id}.`))).length,
    subdimensions: subdimensionIds.map((subdimensionId) => {
      const subdimensionIndicators = dimensionIndicators.filter((indicator) => indicator.code.startsWith(`${subdimensionId}.`));
      return {
        id: subdimensionId,
        label: subdimensionLabels[subdimensionId],
        visual_score: mean(subdimensionIndicators.map((indicator) => indicator.phase_score)),
        indicators: subdimensionIndicators,
      };
    }),
  };
});

const output = {
  generated_at: new Date().toISOString(),
  country: assessment.country,
  framework_version: assessment.framework_version,
  assessment_summary: assessment.assessment_summary,
  validated_at: scoreDocument.validated_at,
  scale: { minimum: 1, maximum: 5 },
  phase_names: phaseNames,
  visual_summary_method:
    'Arithmetic means summarize indicator phase scores for visualization only. Individual indicator scores and their matched requirements remain authoritative.',
  overall_visual_score: mean(indicators.map((indicator) => indicator.phase_score)),
  phase_distribution: phaseDistribution(indicators),
  dimensions,
  evidence,
  source_analysis: sourceAnalysis,
  source_analysis_method: {
    evidence_scope: 'All evidence records produced in the combined evidence bank; cited evidence is the subset used by the final assessment.',
    pdf_length: 'PDF length uses the document page count recorded during conversion or the PDF page-object count when that value is unavailable.',
    webpage_length: 'Webpage length is estimated from extracted visible text at 500 words per page equivalent, with a minimum of one page.',
  },
  traceability: {
    cited_evidence_count: evidence.length,
    linked_evidence_count: evidence.filter((item) => item.source_url).length,
    archived_evidence_count: evidence.filter((item) => item.archive_url).length,
    source_document_count: new Set(evidence.map((item) => item.source_number)).size,
    evidence_bank_count: evidenceDocument.evidence_item_count,
  },
  provenance: {
    final_score_file: 'outputs/canonical_final/final_score.validated.json',
    final_score_sha256: sha256(scoreText),
    evidence_bank_file: 'outputs/canonical_final/combined_evidence_bank.json',
    evidence_bank_sha256: sha256(evidenceText),
    corpus_index_file: 'data/provenance/corpus_index.csv',
    corpus_index_sha256: sha256(corpusText),
  },
};

const publicSourcesPath = path.join(appDirectory, 'public', 'sources');
await mkdir(publicSourcesPath, { recursive: true });
const citedArchiveFiles = [...new Set(evidence.map((item) => path.basename(item.archive_url)))];
await Promise.all(
  citedArchiveFiles.map((fileName) => copyFile(path.join(downloadsPath, fileName), path.join(publicSourcesPath, fileName))),
);
await writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
console.log(
  `Generated ${path.relative(projectDirectory, outputPath)} with ${indicators.length} indicators, ${evidence.length} linked evidence records, and ${citedArchiveFiles.length} archived sources.`,
);

function normaliseId(value) {
  return String(value).trim().replaceAll('/', '\\');
}

function sourceNumberFor(item, id) {
  const candidates = [item?.source_file, item?.source_chunk, id].filter(Boolean);
  for (const candidate of candidates) {
    const match = String(candidate).match(/(?:^|[\\/])(\d{3})(?:_|\.|[\\/])|^(\d{3})(?:_|\.|[\\/])/);
    if (match) return match[1] || match[2];
  }
  return '—';
}

function traceUrl(url, page) {
  if (!url || !page) return url;
  const firstPage = page.match(/\d+/)?.[0];
  if (!firstPage) return url;
  const looksLikePdf = /\.pdf(?:$|[?#])/i.test(url) || /drive\.google\.com\/file/i.test(url);
  return looksLikePdf ? `${url.split('#')[0]}#page=${firstPage}` : url;
}

function mean(values) {
  if (!values.length) return null;
  return Math.round((values.reduce((sum, value) => sum + value, 0) / values.length) * 100) / 100;
}

function rate(count, pages) {
  return Math.round((count / pages) * 100) / 100;
}

function pdfLength(buffer, recordedPageCount) {
  const recorded = Number(recordedPageCount);
  if (Number.isFinite(recorded) && recorded > 1) {
    return { pages: recorded, method: 'Recorded PDF pages', wordCount: null };
  }
  const pageObjects = buffer.toString('latin1').match(/\/Type\s*\/Page\b/g)?.length ?? 0;
  return {
    pages: Math.max(1, pageObjects),
    method: 'PDF page-object count',
    wordCount: null,
  };
}

function webpageLength(html) {
  const visibleText = html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ')
    .replace(/<svg\b[^>]*>[\s\S]*?<\/svg>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&(?:nbsp|amp|quot|apos|lt|gt|#\d+|#x[\da-f]+);/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  const wordCount = visibleText.match(/[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*/gu)?.length ?? 0;
  return {
    pages: Math.max(1, Math.round((wordCount / 500) * 10) / 10),
    method: 'Estimated at 500 words per page equivalent',
    wordCount,
  };
}

function sourceName(sourceNumber, sourceFile, archiveFile) {
  if (sourceTitles[sourceNumber]) return sourceTitles[sourceNumber];
  const rawName = sourceFile || archiveFile;
  return path.basename(rawName, path.extname(rawName))
    .replace(/^\d{3}[_-]?/, '')
    .replaceAll('_', ' ')
    .replaceAll('-', ' ')
    .replace(/\s+/g, ' ')
    .trim() || `Source ${archiveFile.slice(0, 3)}`;
}

function phaseDistribution(items) {
  return Object.fromEntries(
    Object.keys(phaseNames).map((phase) => [phase, items.filter((item) => Number(item.phase_score) === Number(phase)).length]),
  );
}

function sha256(text) {
  return createHash('sha256').update(text).digest('hex');
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (character === '"') {
      if (quoted && text[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === ',' && !quoted) {
      row.push(cell);
      cell = '';
    } else if ((character === '\n' || character === '\r') && !quoted) {
      if (character === '\r' && text[index + 1] === '\n') index += 1;
      row.push(cell);
      if (row.some((value) => value.length)) rows.push(row);
      row = [];
      cell = '';
    } else {
      cell += character;
    }
  }
  if (cell.length || row.length) {
    row.push(cell);
    rows.push(row);
  }
  const [rawHeaders, ...values] = rows;
  const headers = rawHeaders.map((header) => header.replace(/^\uFEFF/, ''));
  return values.map((valuesRow) => Object.fromEntries(headers.map((header, index) => [header, valuesRow[index] ?? ''])));
}
