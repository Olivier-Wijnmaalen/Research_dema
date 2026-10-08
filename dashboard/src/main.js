import './styles.css';

const app = document.querySelector('#app');
const state = {
  view: 'overview',
  indicator: '',
  evidence: '',
  evidenceQuery: '',
  evidenceRole: 'all',
  evidenceIndicator: 'all',
  evidencePage: 1,
  sourceMetric: 'count',
  sourcesExpanded: false,
  mobileNavOpen: false,
};

let data;
let indicators = [];
let evidenceIndex = new Map();

boot();

async function boot() {
  try {
    const response = await fetch('/data.json');
    if (!response.ok) throw new Error(`Could not load assessment data (${response.status}).`);
    data = await response.json();
    indicators = data.dimensions.flatMap((dimension) =>
      dimension.subdimensions.flatMap((subdimension) =>
        subdimension.indicators.map((indicator) => ({ ...indicator, dimension, subdimension })),
      ),
    );
    evidenceIndex = new Map(data.evidence.map((evidence) => [evidence.id, evidence]));
    readLocation();
    state.indicator ||= indicators[0]?.code;
    render();
    bindEvents();
  } catch (error) {
    app.innerHTML = `<main class="fatal"><p class="eyebrow">Unable to start</p><h1>Assessment data could not be loaded.</h1><p>${escapeHtml(error.message)}</p></main>`;
  }
}

function bindEvents() {
  app.addEventListener('click', handleClick);
  app.addEventListener('input', handleInput);
  app.addEventListener('change', handleChange);
  window.addEventListener('popstate', () => {
    readLocation();
    render();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && state.evidence) closeEvidence();
    if (event.key === '/' && state.view === 'evidence' && !event.target.matches('input, textarea, select')) {
      event.preventDefault();
      document.querySelector('#evidence-search')?.focus();
    }
  });
}

function handleClick(event) {
  const viewButton = event.target.closest('[data-view]');
  if (viewButton) {
    event.preventDefault();
    state.view = viewButton.dataset.view;
    state.mobileNavOpen = false;
    state.evidence = '';
    state.evidencePage = 1;
    writeLocation();
    render();
    scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  const menuButton = event.target.closest('[data-menu]');
  if (menuButton) {
    state.mobileNavOpen = !state.mobileNavOpen;
    render();
    return;
  }

  const indicatorButton = event.target.closest('[data-indicator]');
  if (indicatorButton) {
    event.preventDefault();
    state.indicator = indicatorButton.dataset.indicator;
    state.view = 'assessment';
    state.evidence = '';
    writeLocation();
    render();
    if (indicatorButton.dataset.scroll === 'detail') {
      requestAnimationFrame(() => document.querySelector('#indicator-detail')?.scrollIntoView({ behavior: 'smooth' }));
    } else {
      scrollTo({ top: 0, behavior: 'smooth' });
    }
    return;
  }

  const dimensionButton = event.target.closest('[data-dimension]');
  if (dimensionButton) {
    event.preventDefault();
    const indicator = indicators.find((item) => item.code.startsWith(`${dimensionButton.dataset.dimension}.`));
    if (indicator) state.indicator = indicator.code;
    state.view = 'assessment';
    writeLocation();
    render();
    scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  const evidenceButton = event.target.closest('[data-evidence]');
  if (evidenceButton) {
    event.preventDefault();
    state.evidence = evidenceButton.dataset.evidence;
    writeLocation();
    renderModal();
    return;
  }

  const closeButton = event.target.closest('[data-close-evidence]');
  if (closeButton || (event.target.matches('.modal-backdrop') && state.evidence)) {
    closeEvidence();
    return;
  }

  const roleButton = event.target.closest('[data-evidence-role]');
  if (roleButton) {
    state.evidenceRole = roleButton.dataset.evidenceRole;
    state.evidencePage = 1;
    renderEvidenceView();
    return;
  }

  const sourceMetricButton = event.target.closest('[data-source-metric]');
  if (sourceMetricButton) {
    state.sourceMetric = sourceMetricButton.dataset.sourceMetric;
    renderSourceAnalysisView();
    return;
  }

  const sourceExpandButton = event.target.closest('[data-source-expand]');
  if (sourceExpandButton) {
    state.sourcesExpanded = !state.sourcesExpanded;
    renderSourceAnalysisView();
    return;
  }

  const pageButton = event.target.closest('[data-page]');
  if (pageButton) {
    state.evidencePage = Number(pageButton.dataset.page);
    renderEvidenceView();
    document.querySelector('#evidence-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }

  const indicatorEvidenceButton = event.target.closest('[data-open-indicator-evidence]');
  if (indicatorEvidenceButton) {
    state.evidenceIndicator = indicatorEvidenceButton.dataset.openIndicatorEvidence;
    state.evidenceRole = 'all';
    state.evidenceQuery = '';
    state.evidencePage = 1;
    state.view = 'evidence';
    state.evidence = '';
    writeLocation();
    render();
    scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  const clearButton = event.target.closest('[data-clear-evidence]');
  if (clearButton) {
    state.evidenceQuery = '';
    state.evidenceRole = 'all';
    state.evidenceIndicator = 'all';
    state.evidencePage = 1;
    renderEvidenceView();
    return;
  }

  const copyButton = event.target.closest('[data-copy-trace]');
  if (copyButton) copyTrace(copyButton);
}

function handleInput(event) {
  if (event.target.matches('#evidence-search')) {
    state.evidenceQuery = event.target.value;
    state.evidencePage = 1;
    renderEvidenceResults();
  }
}

function handleChange(event) {
  if (event.target.matches('#evidence-indicator-filter')) {
    state.evidenceIndicator = event.target.value;
    state.evidencePage = 1;
    renderEvidenceResults();
  }
}

function render() {
  app.innerHTML = `${renderHeader()}<main id="main-content">${renderView()}</main>${renderFooter()}<div id="modal-root"></div>`;
  renderModal();
}

function renderHeader() {
  return `
    <header class="site-header">
      <a class="brand" href="?view=overview" data-view="overview" aria-label="DEMA Togo overview">
        <span class="brand-mark" aria-hidden="true"><span>D</span></span>
        <span class="brand-copy"><b>DEMA</b><small>Togo assessment</small></span>
      </a>
      <button class="menu-button" data-menu aria-expanded="${state.mobileNavOpen}" aria-label="Toggle navigation">
        ${icon(state.mobileNavOpen ? 'close' : 'menu')}
      </button>
      <nav class="site-nav ${state.mobileNavOpen ? 'is-open' : ''}" aria-label="Primary navigation">
        ${navLink('overview', 'Overview')}
        ${navLink('assessment', 'Assessment')}
        ${navLink('evidence', 'Evidence')}
      </nav>
      <div class="country-pill"><span class="togo-flag" aria-hidden="true"></span><span>Togo</span><small>Final</small></div>
    </header>`;
}

function navLink(view, label) {
  return `<a href="?view=${view}" data-view="${view}" class="${state.view === view ? 'active' : ''}">${label}</a>`;
}

function renderView() {
  if (state.view === 'assessment') return renderAssessment();
  if (state.view === 'evidence') return renderEvidence();
  return renderOverview();
}

function renderOverview() {
  const priorityIndicators = indicators.filter((indicator) => indicator.phase_score <= 2);
  return `
    <section class="hero section-shell">
      <div class="hero-copy reveal">
        <p class="eyebrow light">Data Ecosystem Maturity Assessment · Final results</p>
        <h1>Evidence into<br><em>direction.</em></h1>
        <p class="hero-lead">A transparent view of Togo’s disaster-risk data ecosystem—showing what is working, what needs attention, and the evidence behind every score.</p>
        <div class="hero-actions">
          <a href="?view=assessment" class="button button-primary" data-view="assessment">Explore the assessment ${icon('arrow')}</a>
          <a href="?view=evidence" class="button button-ghost" data-view="evidence">Browse evidence</a>
        </div>
      </div>
      <div class="hero-score reveal delay-1">
        <div class="score-orbit" aria-label="Overall visual mean ${formatScore(data.overall_visual_score)} out of 5">
          <svg viewBox="0 0 220 220" aria-hidden="true">
            <circle class="orbit-track" cx="110" cy="110" r="91"></circle>
            <circle class="orbit-progress" cx="110" cy="110" r="91" pathLength="100" stroke-dasharray="${(data.overall_visual_score / 5) * 100} 100"></circle>
          </svg>
          <div><b>${formatScore(data.overall_visual_score)}</b><span>visual mean</span></div>
        </div>
        <div class="score-caption">
          <span>31 indicators assessed</span>
          <span>Scale 1–5</span>
        </div>
        <p>${escapeHtml(data.visual_summary_method)}</p>
      </div>
    </section>

    <section class="trust-strip">
      <div><span class="pulse-dot"></span><b>Final assessment</b><small>Validated ${formatDate(data.validated_at)}</small></div>
      <div><b>${data.traceability.cited_evidence_count}/${data.traceability.cited_evidence_count}</b><small>Cited records linked</small></div>
      <div><b>${data.traceability.source_document_count}</b><small>Source documents</small></div>
      <div><b>${data.traceability.evidence_bank_count}</b><small>Records in evidence bank</small></div>
    </section>

    <section class="content-section section-shell" aria-labelledby="profile-heading">
      <div class="section-intro">
        <div><p class="eyebrow ink">Maturity profile</p><h2 id="profile-heading">Three dimensions.<br>One connected ecosystem.</h2></div>
        <p>Scores cluster around managed and defined practice, with specific gaps in AI readiness, responsible AI governance, and security implementation.</p>
      </div>
      <div class="profile-grid">
        <article class="radar-card card">
          <div class="card-heading"><div><span class="kicker">Visual comparison</span><h3>Dimension profile</h3></div><span class="scale-key">1—5</span></div>
          ${renderRadar()}
        </article>
        <div class="dimension-stack">
          ${data.dimensions.map(renderDimensionCard).join('')}
        </div>
      </div>
    </section>

    <section class="phase-section section-shell">
      <div class="phase-copy">
        <p class="eyebrow light">Distribution</p>
        <h2>Most indicators are managed and defined.</h2>
        <p>Twenty-seven of 31 indicators meet Phase 3. Four indicators sit below that level and define the clearest priorities for focused follow-up.</p>
        ${renderPhaseDistribution(data.phase_distribution)}
      </div>
      <div class="phase-legend">
        ${Object.entries(data.phase_names).map(([phase, name]) => `<div><span>${phase}</span><p><b>${escapeHtml(name)}</b><small>${data.phase_distribution[phase]} indicator${data.phase_distribution[phase] === 1 ? '' : 's'}</small></p></div>`).join('')}
      </div>
    </section>

    <section class="content-section section-shell" aria-labelledby="priority-heading">
      <div class="section-intro compact">
        <div><p class="eyebrow ink">Priority signals</p><h2 id="priority-heading">Where the next gains begin.</h2></div>
        <a class="text-link" href="?view=assessment" data-view="assessment">View all 31 indicators ${icon('arrow')}</a>
      </div>
      <div class="priority-grid">
        ${priorityIndicators.map(renderPriorityCard).join('')}
      </div>
    </section>

    <section class="evidence-callout section-shell">
      <div>
        <p class="eyebrow light">Built for scrutiny</p>
        <h2>Every claim can be traced.</h2>
        <p>The evidence library connects assessment reasoning to the exact record, source document, page, quotation, and validation result.</p>
      </div>
      <div class="callout-trace">
        <span>${icon('link')}</span>
        <div><small>Traceability coverage</small><b>100%</b><p>${data.traceability.linked_evidence_count} cited evidence links</p></div>
      </div>
      <a class="button button-white" href="?view=evidence" data-view="evidence">Open evidence library ${icon('arrow')}</a>
    </section>`;
}

function renderRadar() {
  const center = { x: 250, y: 214 };
  const radius = 145;
  const dimensions = data.dimensions;
  const point = (index, value = 5) => {
    const angle = -Math.PI / 2 + (index / dimensions.length) * Math.PI * 2;
    const length = radius * (value / 5);
    return { x: center.x + Math.cos(angle) * length, y: center.y + Math.sin(angle) * length };
  };
  const polygon = (value) => dimensions.map((_, index) => point(index, value)).map((item) => `${item.x},${item.y}`).join(' ');
  const scorePoints = dimensions.map((dimension, index) => point(index, dimension.visual_score));

  return `<svg class="radar" viewBox="0 0 500 430" role="img" aria-label="Dimension radar chart">
    ${[1, 2, 3, 4, 5].map((level) => `<polygon class="radar-ring ${level === 5 ? 'outer' : ''}" points="${polygon(level)}"></polygon>`).join('')}
    ${dimensions.map((_, index) => { const end = point(index); return `<line class="radar-axis" x1="${center.x}" y1="${center.y}" x2="${end.x}" y2="${end.y}"></line>`; }).join('')}
    <polygon class="radar-profile" points="${scorePoints.map((item) => `${item.x},${item.y}`).join(' ')}"></polygon>
    ${scorePoints.map((item, index) => `<circle class="radar-point" style="--point:${dimensions[index].color}" cx="${item.x}" cy="${item.y}" r="7"><title>${escapeHtml(dimensions[index].label)}: ${formatScore(dimensions[index].visual_score)}</title></circle>`).join('')}
    ${dimensions.map((dimension, index) => { const label = point(index, 6.15); return `<g class="radar-label" data-dimension="${dimension.id}" role="button" tabindex="0"><text x="${label.x}" y="${label.y - 5}" text-anchor="middle">${dimension.id} · ${escapeHtml(dimension.label)}</text><text class="radar-label-score" x="${label.x}" y="${label.y + 17}" text-anchor="middle">${formatScore(dimension.visual_score)}</text></g>`; }).join('')}
  </svg>`;
}

function renderDimensionCard(dimension) {
  const indicatorCount = dimension.subdimensions.reduce((total, subdimension) => total + subdimension.indicators.length, 0);
  return `<button class="dimension-card card" data-dimension="${dimension.id}" style="--accent:${dimension.color};--pale:${dimension.pale}">
    <span class="dimension-index">${dimension.id}</span>
    <span class="dimension-body"><small>${indicatorCount} indicators · ${dimension.evidence_count} evidence records</small><strong>${escapeHtml(dimension.label)}</strong><span>${escapeHtml(dimension.description)}</span></span>
    <span class="dimension-score"><b>${formatScore(dimension.visual_score)}</b><small>/ 5</small>${icon('arrow')}</span>
  </button>`;
}

function renderPhaseDistribution(distribution) {
  const total = Object.values(distribution).reduce((sum, count) => sum + count, 0);
  return `<div class="distribution" aria-label="Indicator phase distribution">
    <div class="distribution-bar">${Object.entries(distribution).map(([phase, count]) => count ? `<span class="phase-${phase}" style="width:${(count / total) * 100}%" title="Phase ${phase}: ${count}"></span>` : '').join('')}</div>
    <div class="distribution-labels"><span>Phase 1</span><span>Phase 5</span></div>
  </div>`;
}

function renderPriorityCard(indicator) {
  return `<button class="priority-card card" data-indicator="${indicator.code}">
    <span class="phase-chip phase-${indicator.phase_score}">Phase ${indicator.phase_score}</span>
    <small>${indicator.code} · ${escapeHtml(indicator.subdimension.label)}</small>
    <strong>${escapeHtml(indicator.name)}</strong>
    <p>${escapeHtml(truncate(indicator.next_phase_gap, 190))}</p>
    <span class="card-link">Open finding ${icon('arrow')}</span>
  </button>`;
}

function renderAssessment() {
  const selected = indicators.find((indicator) => indicator.code === state.indicator) ?? indicators[0];
  return `
    <section class="page-hero section-shell">
      <div><p class="eyebrow light">Final assessment · 31 indicators</p><h1>Assessment explorer</h1><p>Move from the overall profile to the exact requirement, reasoning, gap, and evidence for each indicator.</p></div>
      <div class="mini-stat"><small>Selected score</small><b>${selected.phase_score}</b><span>${escapeHtml(selected.phase_name)}</span></div>
    </section>
    <div class="assessment-shell section-shell">
      <aside class="assessment-nav" aria-label="Assessment indicators">
        <div class="assessment-nav-head"><p class="eyebrow ink">Framework</p><b>Indicators</b><span>${indicators.length} total</span></div>
        ${data.dimensions.map((dimension) => `
          <details ${selected.dimension.id === dimension.id ? 'open' : ''}>
            <summary style="--accent:${dimension.color}"><span>${dimension.id}</span><b>${escapeHtml(dimension.label)}</b><small>${formatScore(dimension.visual_score)}</small>${icon('chevron')}</summary>
            ${dimension.subdimensions.map((subdimension) => `<div class="subdimension-group"><p>${subdimension.id} · ${escapeHtml(subdimension.label)}</p>${subdimension.indicators.map((indicator) => `<button class="${indicator.code === selected.code ? 'active' : ''}" data-indicator="${indicator.code}"><span>${indicator.code}</span><b>${escapeHtml(indicator.name)}</b><i class="phase-${indicator.phase_score}">${indicator.phase_score}</i></button>`).join('')}</div>`).join('')}
          </details>`).join('')}
      </aside>
      ${renderIndicatorDetail(selected)}
    </div>`;
}

function renderIndicatorDetail(indicator) {
  const citedEvidence = indicator.evidence_refs.map((reference) => ({ ...evidenceIndex.get(reference.id), roles: reference.roles })).filter((item) => item.id);
  const supportingCount = citedEvidence.filter((item) => item.roles.includes('supporting')).length;
  const limitingCount = citedEvidence.filter((item) => item.roles.includes('limiting')).length;
  return `<article id="indicator-detail" class="indicator-detail">
    <header class="indicator-header" style="--accent:${indicator.dimension.color};--pale:${indicator.dimension.pale}">
      <div class="indicator-breadcrumb"><span>${indicator.dimension.id} · ${escapeHtml(indicator.dimension.label)}</span>${icon('chevron')}<span>${indicator.subdimension.id} · ${escapeHtml(indicator.subdimension.label)}</span></div>
      <div class="indicator-title-row">
        <div><span class="indicator-code">${indicator.code}</span><h2>${escapeHtml(indicator.name)}</h2></div>
        <div class="phase-score phase-${indicator.phase_score}"><small>Assessed</small><b>${indicator.phase_score}</b><span>Phase ${indicator.phase_score}</span></div>
      </div>
      <div class="phase-scale" aria-label="Phase ${indicator.phase_score} of 5">
        ${[1, 2, 3, 4, 5].map((phase) => `<span class="${phase <= indicator.phase_score ? 'reached' : ''}"><i></i><small>${phase}</small></span>`).join('')}
      </div>
      <p class="phase-name">${escapeHtml(indicator.phase_name)}</p>
    </header>

    <div class="indicator-content">
      <section class="finding-section matched">
        <div class="finding-icon">${icon('target')}</div>
        <div><p class="eyebrow ink">Exact matched phase requirement</p><blockquote>${escapeHtml(indicator.matched_phase_requirement)}</blockquote></div>
      </section>

      <section class="finding-section">
        <div class="finding-icon">${icon('analysis')}</div>
        <div><p class="eyebrow ink">Assessment reasoning</p><div class="prose">${paragraphs(indicator.score_reasoning)}</div></div>
      </section>

      <section class="finding-section gap-section">
        <div class="finding-icon">${icon('forward')}</div>
        <div><p class="eyebrow ink">What is needed for the next phase</p><p>${escapeHtml(indicator.next_phase_gap)}</p></div>
      </section>

      ${indicator.limiting_reasoning ? `<section class="finding-section limiting-section"><div class="finding-icon">${icon('limit')}</div><div><p class="eyebrow ink">Limiting evidence</p><p>${escapeHtml(indicator.limiting_reasoning)}</p></div></section>` : ''}

      <section class="checks-section">
        <div class="section-heading-row"><div><p class="eyebrow ink">Requirement checks</p><h3>${indicator.requirement_checks.length} assessed condition${indicator.requirement_checks.length === 1 ? '' : 's'}</h3></div></div>
        <div class="checks-list">
          ${indicator.requirement_checks.map((check, index) => `<details ${index === 0 ? 'open' : ''}><summary><span class="status status-${check.status.toLowerCase()}">${icon(check.status === 'SUPPORTED' ? 'check' : 'limit')}${escapeHtml(check.status)}</span><b>${escapeHtml(check.requirement)}</b>${icon('chevron')}</summary><div><p>${escapeHtml(check.explanation)}</p><div class="evidence-id-list">${check.evidence_ids.map((id) => `<button data-evidence="${escapeAttribute(id)}">${escapeHtml(id)}</button>`).join('')}</div></div></details>`).join('')}
        </div>
      </section>

      <section class="indicator-evidence">
        <div class="section-heading-row">
          <div><p class="eyebrow ink">Cited evidence</p><h3>${citedEvidence.length} traceable record${citedEvidence.length === 1 ? '' : 's'}</h3><p>${supportingCount} supporting${limitingCount ? ` · ${limitingCount} limiting` : ''}</p></div>
          <button class="button button-dark small" data-open-indicator-evidence="${indicator.code}">Open filtered library ${icon('arrow')}</button>
        </div>
        <div class="compact-evidence-list">
          ${citedEvidence.map((item) => renderEvidenceRow(item, item.roles)).join('')}
        </div>
      </section>
    </div>
  </article>`;
}

function renderEvidenceRow(item, roles = []) {
  return `<article class="evidence-row">
    <button class="evidence-row-main" data-evidence="${escapeAttribute(item.id)}">
      <span class="source-number">${escapeHtml(item.source_number)}</span>
      <span class="evidence-row-copy"><small>${escapeHtml(item.id)} ${item.page_number ? `· page ${escapeHtml(item.page_number)}` : ''}</small><b>${escapeHtml(item.statement)}</b><span>${roles.map(roleBadge).join('')}</span></span>
      <span class="inspect-link">Inspect ${icon('chevron')}</span>
    </button>
    <a class="source-link" href="${escapeAttribute(item.trace_url)}" target="_blank" rel="noopener noreferrer" aria-label="Open original source for ${escapeAttribute(item.id)}">Source ${icon('external')}</a>
  </article>`;
}

function renderEvidence() {
  return `
    <section class="page-hero evidence-hero section-shell">
      <div><p class="eyebrow light">Source-level traceability</p><h1>Evidence library</h1><p>Search every record cited by the final assessment. Each item connects to its source document and page wherever available.</p></div>
      <div class="trace-ring"><b>100%</b><span>linked</span><small>${data.traceability.linked_evidence_count} of ${data.traceability.cited_evidence_count} records</small></div>
    </section>
    ${renderSourceAnalysis()}
    <section id="evidence-view" class="evidence-view section-shell">
      ${renderEvidenceToolbar()}
      <div id="evidence-results">${renderEvidenceResultsMarkup()}</div>
    </section>`;
}

function renderSourceAnalysis() {
  const metric = state.sourceMetric;
  const metricKey = metric === 'density' ? 'evidence_per_page' : 'evidence_item_count';
  const citedMetricKey = metric === 'density' ? 'cited_evidence_per_page' : 'cited_evidence_count';
  const sources = [...data.source_analysis].sort((left, right) => right[metricKey] - left[metricKey]);
  const visibleSources = state.sourcesExpanded ? sources : sources.slice(0, 12);
  const maximum = Math.max(...sources.map((source) => source[metricKey]), 1);
  const totalPages = sources.reduce((sum, source) => sum + source.page_estimate, 0);
  const overallDensity = data.traceability.evidence_bank_count / totalPages;
  const pdfCount = sources.filter((source) => source.format === 'PDF').length;

  return `<section id="source-analysis" class="source-analysis section-shell" aria-labelledby="source-analysis-heading">
    <div class="source-analysis-intro">
      <div><p class="eyebrow ink">Source yield</p><h2 id="source-analysis-heading">How much evidence did each source produce?</h2></div>
      <p>Absolute counts reward longer documents. Switch to evidence per page to compare source yield after accounting for document length.</p>
    </div>
    <div class="source-stat-grid">
      <div><small>Evidence produced</small><b>${formatNumber(data.traceability.evidence_bank_count)}</b><span>all extracted records</span></div>
      <div><small>Used in final scoring</small><b>${formatNumber(data.traceability.cited_evidence_count)}</b><span>${formatPercent(data.traceability.cited_evidence_count / data.traceability.evidence_bank_count)} of extracted evidence</span></div>
      <div><small>Sources analyzed</small><b>${sources.length}</b><span>${pdfCount} PDFs · ${sources.length - pdfCount} webpages</span></div>
      <div><small>Overall yield</small><b>${formatRate(overallDensity)}</b><span>evidence items per page</span></div>
    </div>
    <article class="source-chart card">
      <header class="source-chart-head">
        <div><span class="kicker">Ranked source comparison</span><h3>${metric === 'density' ? 'Evidence items per page' : 'Evidence items produced'}</h3></div>
        <div class="metric-toggle" role="group" aria-label="Source comparison metric">
          <button class="${metric === 'count' ? 'active' : ''}" data-source-metric="count">Total items</button>
          <button class="${metric === 'density' ? 'active' : ''}" data-source-metric="density">Items / page</button>
        </div>
      </header>
      <div class="source-chart-legend"><span><i class="all-evidence"></i>All extracted evidence</span><span><i class="cited-evidence"></i>Cited in final assessment</span></div>
      <div class="source-chart-body">
        ${visibleSources.map((source, index) => renderSourceRow(source, index, maximum, metricKey, citedMetricKey)).join('')}
      </div>
      ${sources.length > 12 ? `<button class="source-expand" data-source-expand>${state.sourcesExpanded ? 'Show top 12 sources' : `Show all ${sources.length} sources`} ${icon(state.sourcesExpanded ? 'back' : 'arrow')}</button>` : ''}
    </article>
    <aside class="method-note">
      <span>${icon('analysis')}</span>
      <div><b>How length is estimated</b><p>PDFs use recorded or detected page counts. Webpages are converted to page equivalents at <strong>500 visible words per page</strong>, with a one-page minimum. “All extracted” covers the complete 622-item evidence bank; “cited” shows the records used in final scoring.</p></div>
    </aside>
  </section>`;
}

function renderSourceRow(source, index, maximum, metricKey, citedMetricKey) {
  const value = source[metricKey];
  const citedValue = source[citedMetricKey];
  const totalWidth = Math.max(value > 0 ? 1.5 : 0, (value / maximum) * 100);
  const citedWidth = Math.max(citedValue > 0 ? 1.5 : 0, (citedValue / maximum) * 100);
  const isEstimated = source.page_estimate_method.startsWith('Estimated');
  const lengthLabel = `${isEstimated ? '~' : ''}${formatPageCount(source.page_estimate)} page${source.page_estimate === 1 ? '' : 's'}`;
  const valueLabel = state.sourceMetric === 'density' ? `${formatRate(value)} / page` : `${formatNumber(value)} item${value === 1 ? '' : 's'}`;
  const citedLabel = state.sourceMetric === 'density' ? `${formatRate(citedValue)} cited / page` : `${formatNumber(citedValue)} cited`;
  return `<div class="source-row">
    <span class="source-rank">${index + 1}</span>
    <a class="source-identity" href="${escapeAttribute(source.source_url)}" target="_blank" rel="noopener noreferrer" title="Open source ${source.source_number}">
      <b>${source.source_number}</b><span>${escapeHtml(source.source_name)}</span><small>${source.format} · ${lengthLabel}${isEstimated ? ' estimate' : ''}</small>
    </a>
    <div class="source-bars" aria-label="${escapeAttribute(valueLabel)}, ${escapeAttribute(citedLabel)}">
      <span class="source-bar-total" style="width:${totalWidth}%"></span>
      <span class="source-bar-cited" style="width:${citedWidth}%"></span>
    </div>
    <div class="source-value"><b>${valueLabel}</b><small>${citedLabel}</small></div>
  </div>`;
}

function renderSourceAnalysisView() {
  const sourceAnalysis = document.querySelector('#source-analysis');
  if (sourceAnalysis) sourceAnalysis.outerHTML = renderSourceAnalysis();
}

function renderEvidenceToolbar() {
  return `<div class="evidence-toolbar">
    <label class="search-box">${icon('search')}<input id="evidence-search" type="search" value="${escapeAttribute(state.evidenceQuery)}" placeholder="Search IDs, claims, sources, or indicators…"><kbd>/</kbd></label>
    <label class="select-box"><span>Indicator</span><select id="evidence-indicator-filter"><option value="all">All indicators</option>${indicators.map((indicator) => `<option value="${indicator.code}" ${state.evidenceIndicator === indicator.code ? 'selected' : ''}>${indicator.code} · ${escapeHtml(indicator.name)}</option>`).join('')}</select>${icon('chevron')}</label>
    <div class="role-filters" aria-label="Evidence role">
      ${['all', 'supporting', 'limiting', 'requirement'].map((role) => `<button class="${state.evidenceRole === role ? 'active' : ''}" data-evidence-role="${role}">${capitalize(role)}</button>`).join('')}
    </div>
  </div>`;
}

function renderEvidenceView() {
  const view = document.querySelector('#evidence-view');
  if (!view) return;
  view.innerHTML = `${renderEvidenceToolbar()}<div id="evidence-results">${renderEvidenceResultsMarkup()}</div>`;
}

function renderEvidenceResults() {
  const results = document.querySelector('#evidence-results');
  if (results) results.innerHTML = renderEvidenceResultsMarkup();
}

function renderEvidenceResultsMarkup() {
  const filtered = filteredEvidence();
  const pageSize = 24;
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  state.evidencePage = Math.min(state.evidencePage, pages);
  const pageItems = filtered.slice((state.evidencePage - 1) * pageSize, state.evidencePage * pageSize);
  return `
    <div class="results-head"><p><b>${filtered.length}</b> evidence record${filtered.length === 1 ? '' : 's'}${state.evidenceIndicator !== 'all' ? ` for <span>${state.evidenceIndicator}</span>` : ''}</p><div class="trace-key"><span>${icon('link')} Source-linked</span><span>${icon('check')} Validation shown</span></div></div>
    ${pageItems.length ? `<div class="evidence-grid">${pageItems.map(renderEvidenceCard).join('')}</div>${renderPagination(pages)}` : `<div class="empty-state">${icon('search')}<h2>No evidence matched.</h2><p>Try a broader search or clear the active filters.</p><button class="button button-dark" data-clear-evidence>Clear filters</button></div>`}`;
}

function filteredEvidence() {
  const query = state.evidenceQuery.trim().toLocaleLowerCase();
  return data.evidence.filter((item) => {
    const usage = item.used_by ?? [];
    const indicatorMatch = state.evidenceIndicator === 'all' || usage.some((entry) => entry.indicator_code === state.evidenceIndicator);
    const roleMatch = state.evidenceRole === 'all' || usage.some((entry) => entry.roles.includes(state.evidenceRole));
    const haystack = [item.id, item.source_file, item.statement, item.supporting_quote, item.assessment_use, ...usage.map((entry) => entry.indicator_code)].join(' ').toLocaleLowerCase();
    return indicatorMatch && roleMatch && (!query || haystack.includes(query));
  });
}

function renderEvidenceCard(item) {
  const roles = [...new Set(item.used_by.flatMap((usage) => usage.roles))];
  return `<article class="evidence-card card">
    <header><span class="source-number">${escapeHtml(item.source_number)}</span><div>${roles.map(roleBadge).join('')}</div></header>
    <button class="evidence-card-body" data-evidence="${escapeAttribute(item.id)}">
      <small>${escapeHtml(item.id)}</small>
      <h2>${escapeHtml(item.statement)}</h2>
      <p>${escapeHtml(truncate(item.supporting_quote || item.assessment_use, 190))}</p>
    </button>
    <footer><span>${item.page_number ? `Page ${escapeHtml(item.page_number)}` : 'Web source'}</span><span>${item.used_by.length} indicator${item.used_by.length === 1 ? '' : 's'}</span><a href="${escapeAttribute(item.trace_url)}" target="_blank" rel="noopener noreferrer">Open source ${icon('external')}</a></footer>
  </article>`;
}

function renderPagination(pages) {
  if (pages <= 1) return '';
  const pageButtons = [];
  for (let page = 1; page <= pages; page += 1) {
    if (page === 1 || page === pages || Math.abs(page - state.evidencePage) <= 1) pageButtons.push(page);
    else if (pageButtons[pageButtons.length - 1] !== '…') pageButtons.push('…');
  }
  return `<nav class="pagination" aria-label="Evidence pages"><button data-page="${Math.max(1, state.evidencePage - 1)}" ${state.evidencePage === 1 ? 'disabled' : ''}>${icon('back')} Previous</button><div>${pageButtons.map((page) => page === '…' ? '<span>…</span>' : `<button data-page="${page}" class="${page === state.evidencePage ? 'active' : ''}" aria-current="${page === state.evidencePage ? 'page' : 'false'}">${page}</button>`).join('')}</div><button data-page="${Math.min(pages, state.evidencePage + 1)}" ${state.evidencePage === pages ? 'disabled' : ''}>Next ${icon('arrow')}</button></nav>`;
}

function renderModal() {
  const root = document.querySelector('#modal-root');
  if (!root) return;
  const item = evidenceIndex.get(state.evidence);
  if (!item) {
    root.innerHTML = '';
    document.body.classList.remove('modal-open');
    return;
  }
  document.body.classList.add('modal-open');
  const roles = [...new Set(item.used_by.flatMap((usage) => usage.roles))];
  root.innerHTML = `<div class="modal-backdrop" role="presentation"><section class="evidence-modal" role="dialog" aria-modal="true" aria-labelledby="evidence-modal-title">
    <header class="modal-head">
      <div><p class="eyebrow ink">Evidence trace</p><h2 id="evidence-modal-title">${escapeHtml(item.id)}</h2></div>
      <button data-close-evidence aria-label="Close evidence detail">${icon('close')}</button>
    </header>
    <div class="modal-body">
      <div class="trace-banner">
        <span class="source-number">${escapeHtml(item.source_number)}</span>
        <div><small>Original source</small><b>${escapeHtml(item.source_file)}</b><p>${item.page_number ? `Page ${escapeHtml(item.page_number)}` : 'Web page'}</p></div>
        <div class="trace-actions"><a class="button button-dark small" href="${escapeAttribute(item.trace_url)}" target="_blank" rel="noopener noreferrer">Original ${icon('external')}</a><a href="${escapeAttribute(item.archive_trace_url)}" target="_blank" rel="noopener noreferrer">Archived copy</a></div>
      </div>
      <section><p class="eyebrow ink">Evidence statement</p><h3>${escapeHtml(item.statement)}</h3></section>
      ${item.supporting_quote ? `<section class="quote-section"><p class="eyebrow ink">Supporting quotation</p><blockquote>${escapeHtml(item.supporting_quote)}</blockquote></section>` : ''}
      ${item.assessment_use ? `<section><p class="eyebrow ink">Use in the country assessment</p><p>${escapeHtml(item.assessment_use)}</p></section>` : ''}
      ${item.interpretation_boundary ? `<section class="boundary"><p class="eyebrow ink">Interpretation boundary</p><p>${escapeHtml(item.interpretation_boundary)}</p></section>` : ''}
      <section><p class="eyebrow ink">Used by</p><div class="used-by-list">${item.used_by.map((usage) => `<button data-indicator="${usage.indicator_code}"><b>${usage.indicator_code}</b><span>${usage.roles.map(roleBadge).join('')}</span>${icon('arrow')}</button>`).join('')}</div></section>
      <section class="validation-panel">
        <p class="eyebrow ink">Traceability & validation</p>
        <dl>
          <div><dt>Evidence ID</dt><dd>${escapeHtml(item.id)}</dd></div>
          <div><dt>Technical validation</dt><dd><span class="validation-status">${icon('check')}${escapeHtml(item.technical_validation_status)}</span></dd></div>
          <div><dt>Attribution review</dt><dd>${escapeHtml(formatStatus(item.ais_validation_status))}</dd></div>
          <div><dt>Scope</dt><dd>${escapeHtml(item.evidence_scope)}</dd></div>
          <div><dt>Source</dt><dd>${escapeHtml(item.source_file)}${item.page_number ? `, p. ${escapeHtml(item.page_number)}` : ''}</dd></div>
        </dl>
      </section>
    </div>
    <footer class="modal-footer"><a class="button button-ghost-dark" href="${escapeAttribute(item.archive_trace_url)}" target="_blank" rel="noopener noreferrer">Archived source ${icon('external')}</a><button class="button button-ghost-dark" data-copy-trace="${escapeAttribute(item.id)}">${icon('link')} Copy evidence link</button><a class="button button-primary" href="${escapeAttribute(item.trace_url)}" target="_blank" rel="noopener noreferrer">View original source ${icon('external')}</a></footer>
  </section></div>`;
}

function renderFooter() {
  return `<footer class="site-footer"><div><span class="brand-mark small" aria-hidden="true"><span>D</span></span><p><b>Data Ecosystem Maturity Assessment</b><small>Togo · Final validated outputs</small></p></div><p class="footer-note">Indicator scores are authoritative. Dimension and overall means are visual summaries.</p><nav><a href="?view=assessment" data-view="assessment">Assessment</a><a href="?view=evidence" data-view="evidence">Evidence</a></nav></footer>`;
}

function roleBadge(role) {
  return `<span class="role role-${role}">${capitalize(role)}</span>`;
}

function closeEvidence() {
  state.evidence = '';
  writeLocation();
  renderModal();
}

async function copyTrace(button) {
  const id = button.dataset.copyTrace;
  const url = new URL(window.location.href);
  url.searchParams.set('evidence', id);
  try {
    await navigator.clipboard.writeText(url.toString());
    const original = button.innerHTML;
    button.innerHTML = `${icon('check')} Link copied`;
    setTimeout(() => { if (button.isConnected) button.innerHTML = original; }, 1600);
  } catch {
    window.prompt('Copy this evidence link:', url.toString());
  }
}

function readLocation() {
  const parameters = new URLSearchParams(window.location.search);
  const view = parameters.get('view');
  if (['overview', 'assessment', 'evidence'].includes(view)) state.view = view;
  const indicator = parameters.get('indicator');
  if (indicator && indicators.some((item) => item.code === indicator)) state.indicator = indicator;
  const evidence = parameters.get('evidence');
  if (evidence && evidenceIndex.has(evidence)) state.evidence = evidence;
}

function writeLocation() {
  const url = new URL(window.location.href);
  url.search = '';
  if (state.view !== 'overview') url.searchParams.set('view', state.view);
  if (state.view === 'assessment' && state.indicator) url.searchParams.set('indicator', state.indicator);
  if (state.evidence) url.searchParams.set('evidence', state.evidence);
  history.pushState({}, '', url);
}

function paragraphs(text) {
  return String(text ?? '').split(/\n{2,}/).filter(Boolean).map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join('');
}

function formatScore(value) {
  return Number(value).toFixed(2).replace(/0$/, '');
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-GB').format(value);
}

function formatPercent(value) {
  return new Intl.NumberFormat('en-GB', { style: 'percent', maximumFractionDigits: 0 }).format(value);
}

function formatRate(value) {
  return new Intl.NumberFormat('en-GB', { maximumFractionDigits: 2 }).format(value);
}

function formatPageCount(value) {
  return new Intl.NumberFormat('en-GB', { maximumFractionDigits: 1 }).format(value);
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value));
}

function formatStatus(value) {
  return String(value || 'Not recorded').replaceAll('_', ' ').toLocaleLowerCase().replace(/^./, (letter) => letter.toLocaleUpperCase());
}

function truncate(value, length) {
  const text = String(value ?? '').trim();
  return text.length > length ? `${text.slice(0, length - 1).trim()}…` : text;
}

function capitalize(value) {
  return String(value).replace(/^./, (letter) => letter.toLocaleUpperCase());
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[character]);
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, '&#096;');
}

function icon(name) {
  const paths = {
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    back: '<path d="M19 12H5m6 6-6-6 6-6"/>',
    chevron: '<path d="m9 18 6-6-6-6"/>',
    external: '<path d="M15 4h5v5M10 14 20 4M20 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h6"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.54.54l2-2a5 5 0 0 0-7.07-7.07l-1.15 1.15M14 11a5 5 0 0 0-7.54-.54l-2 2a5 5 0 0 0 7.07 7.07l1.14-1.14"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    close: '<path d="M18 6 6 18M6 6l12 12"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
    analysis: '<path d="M4 19V9m6 10V5m6 14v-7m4 7H2"/>',
    forward: '<path d="M5 12h13m-5-5 5 5-5 5"/><path d="M19 5v14"/>',
    limit: '<path d="M12 8v5m0 3h.01"/><path d="M10.3 3.7 2.4 17.3A2 2 0 0 0 4.1 20h15.8a2 2 0 0 0 1.7-2.7L13.7 3.7a2 2 0 0 0-3.4 0Z"/>',
  };
  return `<svg class="icon icon-${name}" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${paths[name] ?? ''}</svg>`;
}
