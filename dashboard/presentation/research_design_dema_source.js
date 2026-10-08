import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const W = 1800;
const H = 1273;
const out = path.join(__dirname, 'research_design_dema.svg');

const C = {
  ink: '#343a40',
  line: '#596168',
  phase: '#f3f4f5',
  phaseEdge: '#d5d9dc',
  yellow: '#fff4c7',
  yellowEdge: '#c6a947',
  grey: '#eceff1',
  greyEdge: '#aab1b7',
  blue: '#dceef8',
  blueEdge: '#6f9eb8',
  red: '#f8dddd',
  redEdge: '#bd7474',
  green: '#dcefdc',
  greenEdge: '#6d9d70',
  white: '#ffffff'
};

const bg = [];
const links = [];
const nodes = [];

const esc = (s) => String(s)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;');

function line(x1, y1, x2, y2, { dashed = false, arrow = true, width = 2.2 } = {}) {
  links.push(`<path d="M ${x1} ${y1} L ${x2} ${y2}" class="flow${dashed ? ' dashed' : ''}" stroke-width="${width}"${arrow ? ' marker-end="url(#arrow)"' : ''}/>`);
}

function pathLink(d, { dashed = false, arrow = true, width = 2.2 } = {}) {
  links.push(`<path d="${d}" class="flow${dashed ? ' dashed' : ''}" stroke-width="${width}"${arrow ? ' marker-end="url(#arrow)"' : ''}/>`);
}

function htmlBox({ x, y, w, h, fill = C.grey, stroke = C.greyEdge, title = '', body = '', cls = '', radius = 8, pad = 8 }) {
  nodes.push(`
    <g class="node ${cls}">
      <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${radius}" fill="${fill}" stroke="${stroke}" stroke-width="1.7"/>
      <foreignObject x="${x + pad}" y="${y + pad - 1}" width="${w - 2 * pad}" height="${h - 2 * pad + 2}">
        <div xmlns="http://www.w3.org/1999/xhtml" class="boxtext ${cls}">
          ${title ? `<div class="boxtitle">${esc(title)}</div>` : ''}
          ${body ? `<div class="boxbody">${body}</div>` : ''}
        </div>
      </foreignObject>
    </g>`);
}

function phase(y, h, number, title, rq = '') {
  bg.push(`<rect x="10" y="${y}" width="1780" height="${h}" rx="10" fill="${C.phase}" stroke="${C.phaseEdge}" stroke-width="1.4"/>`);
  bg.push(`<rect x="18" y="${y + 8}" width="166" height="${h - 16}" rx="7" fill="${C.white}" stroke="${C.phaseEdge}" stroke-width="1.4"/>`);
  nodes.push(`<foreignObject x="31" y="${y + 17}" width="140" height="${h - 34}"><div xmlns="http://www.w3.org/1999/xhtml" class="phase-title"><span>PHASE ${number}</span>${esc(title)}</div></foreignObject>`);
  if (rq) {
    nodes.push(`<foreignObject x="1090" y="${y + 9}" width="674" height="24"><div xmlns="http://www.w3.org/1999/xhtml" class="rq">${esc(rq)}</div></foreignObject>`);
  }
}

function label(x, y, w, h, text, cls = '') {
  nodes.push(`<foreignObject x="${x}" y="${y}" width="${w}" height="${h}"><div xmlns="http://www.w3.org/1999/xhtml" class="label ${cls}">${text}</div></foreignObject>`);
}

// Title and legend
label(18, 12, 1150, 44, 'Overall research design of the LLM-assisted DEMA documentary pre-assessment', 'main-title');
label(1210, 18, 565, 30,
  `<span class="key yellow"></span>Input/framework <span class="key grey"></span>Process <span class="key blue"></span>Intermediate output <span class="key red"></span>Evaluation <span class="key green"></span>Final output`,
  'legend');

// Research inputs
label(18, 73, 166, 24, 'RESEARCH INPUTS', 'section-label');
htmlBox({ x: 205, y: 66, w: 635, h: 104, fill: C.yellow, stroke: C.yellowEdge,
  title: 'DEMA framework',
  body: 'Dimensions and indicators · descriptive framework<br/>Five maturity phases · indicator-specific maturity criteria', cls: 'input' });
htmlBox({ x: 965, y: 66, w: 635, h: 104, fill: C.yellow, stroke: C.yellowEdge,
  title: 'Fixed Togo documentary corpus',
  body: 'Compiled by 510 experts<br/>Heterogeneous documentary sources', cls: 'input' });
line(522, 170, 522, 182);
line(1282, 170, 1282, 182);

// Phase 1
phase(182, 140, '1', 'DEMA FAMILIARISATION AND WORKFLOW SPECIFICATION', 'RQ1 · Translate the existing DEMA framework into an LLM-assisted documentary workflow');
htmlBox({ x: 205, y: 217, w: 352, h: 88, title: '1  Understand DEMA',
  body: 'Concepts and indicators · maturity progression<br/>Documentary versus wider expert assessment' });
htmlBox({ x: 580, y: 217, w: 385, h: 88, title: '2  Determine information requirements',
  body: 'Stage 1 evidence · Stage 2 reasoning<br/>Provenance, traceability and expert review' });
htmlBox({ x: 988, y: 217, w: 350, h: 88, title: '3  Design workflow outputs',
  body: 'Evidence and assessment structures<br/>Linked justification · final visualisation' });
htmlBox({ x: 1361, y: 217, w: 403, h: 88, fill: C.blue, stroke: C.blueEdge,
  title: 'Specified two-stage documentary assessment workflow',
  body: 'Existing DEMA indicators and maturity criteria remain unchanged', cls: 'output dense' });
line(557, 261, 580, 261);
line(965, 261, 988, 261);
line(1338, 261, 1361, 261);

// Phase 2
phase(330, 170, '2', 'DOCUMENT PREPARATION AND STAGE 1 DEVELOPMENT');
htmlBox({ x: 205, y: 365, w: 180, h: 58, fill: C.yellow, stroke: C.yellowEdge, title: 'Fixed corpus', body: 'No source expansion', cls: 'compact' });
htmlBox({ x: 408, y: 365, w: 185, h: 58, title: 'Document preparation', body: 'Convert · clean · structure', cls: 'compact' });
htmlBox({ x: 616, y: 365, w: 205, h: 58, fill: C.blue, stroke: C.blueEdge, title: 'Development subset', body: 'Calibration material only', cls: 'compact dev' });
htmlBox({ x: 844, y: 365, w: 260, h: 58, title: 'Stage 1 prompt calibration', body: 'Develop and test iteratively', cls: 'compact dev' });
htmlBox({ x: 1127, y: 365, w: 145, h: 58, fill: C.red, stroke: C.redEdge, title: 'Prompt frozen', body: 'No further tuning', cls: 'compact freeze' });
htmlBox({ x: 1295, y: 365, w: 250, h: 58, title: 'Final Stage 1 application', body: 'Applied to fixed corpus', cls: 'compact finalapp' });
line(385, 394, 408, 394); line(593, 394, 616, 394); line(821, 394, 844, 394); line(1104, 394, 1127, 394); line(1272, 394, 1295, 394);
pathLink('M 974 423 L 974 486 L 718 486 L 718 426', { dashed: true });
label(749, 466, 210, 18, 'development feedback only', 'feedback');
htmlBox({ x: 408, y: 436, w: 696, h: 49, title: 'Stage 1 purpose',
  body: '<b>Identify</b> → <b>quote</b> → <b>classify</b> → bounded interpretation', cls: 'strip' });
htmlBox({ x: 1127, y: 436, w: 637, h: 49, fill: C.blue, stroke: C.blueEdge,
  title: 'Structured DEMA evidence bank', body: 'Source · page/location · quotation · indicator · interpretation · scope', cls: 'strip output' });
pathLink('M 1420 423 L 1420 436');

// Phase 3
phase(508, 125, '3', 'EVIDENCE VALIDATION', 'RQ2 · Traceability and substantive attribution of documentary evidence');
htmlBox({ x: 205, y: 545, w: 292, h: 70, fill: C.blue, stroke: C.blueEdge, title: 'Structured evidence bank', body: 'Stage 1 output', cls: 'output' });
htmlBox({ x: 527, y: 545, w: 704, h: 70, fill: C.red, stroke: C.redEdge, title: 'Evaluate evidence records',
  body: 'Traceability · substantive support · DEMA classification · institutional/geographic/implementation scope · overgeneralisation', cls: 'evaluation dense' });
htmlBox({ x: 1261, y: 545, w: 503, h: 70, fill: C.blue, stroke: C.blueEdge, title: 'Validated evidence bank', body: '+ identified evidence-level errors', cls: 'output' });
line(497, 580, 527, 580); line(1231, 580, 1261, 580);

// Phase 4
phase(641, 168, '4', 'STAGE 2 DEVELOPMENT AND APPLICATION');
htmlBox({ x: 205, y: 676, w: 260, h: 52, fill: C.blue, stroke: C.blueEdge, title: 'Validated evidence bank', body: 'Evidence input', cls: 'compact output' });
htmlBox({ x: 205, y: 741, w: 260, h: 52, fill: C.yellow, stroke: C.yellowEdge, title: 'DEMA maturity criteria', body: 'Indicator-specific', cls: 'compact input' });
htmlBox({ x: 500, y: 676, w: 255, h: 52, title: 'Stage 2 calibration', body: 'Develop and test prompt', cls: 'compact dev' });
htmlBox({ x: 785, y: 676, w: 145, h: 52, fill: C.red, stroke: C.redEdge, title: 'Prompt frozen', body: 'No further tuning', cls: 'compact freeze' });
htmlBox({ x: 960, y: 676, w: 250, h: 52, title: 'Final application', body: 'Across 31 DEMA indicators', cls: 'compact finalapp' });
htmlBox({ x: 500, y: 741, w: 710, h: 52, title: 'Stage 2 reasoning',
  body: 'Aggregate evidence → compare criteria → weigh supporting and limiting evidence → identify unmet criteria / next-phase gaps', cls: 'strip' });
htmlBox({ x: 1240, y: 676, w: 524, h: 117, fill: C.blue, stroke: C.blueEdge, title: '31 provisional indicator assessments',
  body: 'Maturity phase · supporting evidence · limiting/contrary evidence<br/>Evidence-linked justification · next-phase gap', cls: 'output' });
pathLink('M 465 702 L 482 702 L 482 702 L 500 702');
pathLink('M 465 767 L 482 767 L 482 702 L 500 702');
line(755, 702, 785, 702); line(930, 702, 960, 702); line(1210, 702, 1240, 702);
pathLink('M 1085 728 L 1085 741');
line(1210, 767, 1240, 767);

// Phase 5
phase(817, 202, '5', 'OUTPUT PRESENTATION AND ASSESSMENT EVALUATION', 'RQ3 · Quality, defensibility and practical usefulness of the provisional DEMA assessment');
htmlBox({ x: 205, y: 855, w: 260, h: 135, fill: C.blue, stroke: C.blueEdge, title: '31 provisional assessments',
  body: 'Shared input for presentation and evaluation', cls: 'output centre' });
htmlBox({ x: 500, y: 855, w: 410, h: 135, fill: C.blue, stroke: C.blueEdge, title: 'PRESENTATION — DEMA ecosystem visualiser',
  body: '31 provisional assessments<br/>Linked documentary evidence<br/>Maturity reasoning and provenance<br/><span class="note">Transparency output; not an analytical stage</span>', cls: 'output' });
htmlBox({ x: 950, y: 855, w: 814, h: 90, fill: C.red, stroke: C.redEdge, title: 'EVALUATION',
  body: '<b>Descriptive comparison:</b> phase correspondence; cautious interpretation of differences<br/><b>Qualitative DEMA expert review:</b> validity · concepts · formal arrangements versus implementation · scope · defensibility · usefulness · missing context', cls: 'evaluation dense' });
htmlBox({ x: 950, y: 956, w: 390, h: 48, fill: C.yellow, stroke: C.yellowEdge, title: 'Existing expert-led Togo DEMA assessment',
  body: 'Evaluation-only reference; not used as model input', cls: 'compact external' });
htmlBox({ x: 1364, y: 956, w: 400, h: 48, fill: C.red, stroke: C.redEdge, title: 'Assessment of maturity-output quality',
  body: 'Defensibility and practical usefulness', cls: 'compact evaluation' });
pathLink('M 465 922 L 482 922 L 482 922 L 500 922');
pathLink('M 465 922 L 482 922 L 482 900 L 950 900');
pathLink('M 1145 956 L 1145 948', { dashed: true });
pathLink('M 1357 945 L 1357 980 L 1364 980');

// Phase 6
phase(1027, 135, '6', 'CROSS-STAGE UNCERTAINTY AND LIMITATIONS ANALYSIS', 'RQ4 · Sources of uncertainty in the LLM-assisted documentary assessment');
const chainY = 1062, chainH = 42;
const chain = [
  [205, 220, 'Documentary corpus'], [445, 220, 'Evidence retrieval'], [685, 220, 'Evidence interpretation'],
  [925, 220, 'DEMA classification'], [1165, 220, 'Maturity reasoning'], [1405, 359, 'Provisional assessment']
];
for (const [x, w, t] of chain) htmlBox({ x, y: chainY, w, h: chainH, title: t, cls: 'chain compact' });
for (let i = 0; i < chain.length - 1; i++) line(chain[i][0] + chain[i][1], chainY + 21, chain[i + 1][0], chainY + 21);
htmlBox({ x: 205, y: 1110, w: 930, h: 46, fill: C.red, stroke: C.redEdge, title: 'Analyse uncertainty',
  body: 'Corpus limits · documentary non-observation · extraction · interpretation/scope · framework ambiguity · maturity reasoning · unavailable context', cls: 'strip evaluation dense' });
htmlBox({ x: 1165, y: 1110, w: 599, h: 46, fill: C.blue, stroke: C.blueEdge, title: 'Output',
  body: 'Sources of uncertainty · methodological limitations · recommendations for expert-supported use', cls: 'strip output dense' });
line(1135, 1133, 1165, 1133);

// Final outputs
bg.push(`<rect x="10" y="1170" width="1780" height="90" rx="10" fill="${C.green}" stroke="${C.greenEdge}" stroke-width="2"/>`);
label(30, 1186, 292, 52, 'FINAL RESEARCH<br/>OUTPUTS', 'final-title');
label(335, 1181, 1415, 65,
  `<div class="final-grid"><span>Evaluated two-stage LLM-assisted DEMA workflow</span><span>31 provisional DEMA indicator assessments</span><span>Structured and validated documentary evidence bank</span><span>DEMA ecosystem visualiser</span><span>Evaluation of traceability, validity, defensibility and uncertainty</span><span>GIMA internship research report</span></div>`,
  'final-list');

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="title desc">
  <title id="title">Overall research design of the LLM-assisted DEMA documentary pre-assessment</title>
  <desc id="desc">Six-phase MSc GIMA research design from DEMA framework and fixed documentary corpus to evaluated research outputs.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8.2" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="${C.line}"/>
    </marker>
    <style><![CDATA[
      * { box-sizing: border-box; }
      .flow { fill: none; stroke: ${C.line}; stroke-linecap: round; stroke-linejoin: round; }
      .flow.dashed { stroke-dasharray: 7 6; }
      .boxtext, .label, .phase-title { font-family: Arial, Helvetica, sans-serif; color: ${C.ink}; }
      .boxtext { width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; line-height: 1.18; }
      .boxtitle { font-size: 17.5px; font-weight: 700; margin-bottom: 3px; }
      .boxbody { font-size: 15px; font-weight: 400; }
      .compact .boxtitle { font-size: 15.8px; margin-bottom: 1px; }
      .compact .boxbody { font-size: 13.5px; }
      .dense .boxtitle { font-size: 16px; margin-bottom: 2px; }
      .dense .boxbody { font-size: 13.7px; line-height: 1.14; }
      .strip .boxtext { flex-direction: row; align-items: center; gap: 13px; }
      .strip .boxtitle { flex: 0 0 auto; margin: 0; }
      .strip .boxbody { font-size: 14px; }
      .strip.dense .boxbody { font-size: 12.4px; }
      .chain .boxtext { align-items: center; text-align: center; }
      .chain .boxtitle { margin: 0; font-size: 16px; }
      .phase-title { font-size: 16px; line-height: 1.22; font-weight: 700; }
      .phase-title span { display: block; font-size: 13px; letter-spacing: 1px; color: #6b7278; margin-bottom: 7px; }
      .rq { font-family: Arial, Helvetica, sans-serif; font-size: 13px; line-height: 20px; color: #636a70; text-align: right; font-style: italic; }
      .main-title { font-family: Arial, Helvetica, sans-serif; font-size: 27px; line-height: 40px; font-weight: 700; color: #252a2e; }
      .section-label { font-family: Arial, Helvetica, sans-serif; font-size: 13px; font-weight: 700; letter-spacing: .7px; color: #6b7278; }
      .legend { font-family: Arial, Helvetica, sans-serif; font-size: 12.5px; line-height: 24px; color: #5c646a; text-align: right; white-space: nowrap; }
      .key { display: inline-block; width: 12px; height: 12px; margin: 0 4px 0 10px; border: 1px solid #9aa0a5; vertical-align: -1px; }
      .key.yellow { background: ${C.yellow}; } .key.grey { background: ${C.grey}; } .key.blue { background: ${C.blue}; }
      .key.red { background: ${C.red}; } .key.green { background: ${C.green}; }
      .feedback { font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #6d7378; text-align: center; font-style: italic; }
      .note { font-style: italic; color: #5c646a; }
      .centre .boxtext { text-align: center; align-items: center; }
      .external .boxtitle, .evaluation.compact .boxtitle { font-size: 14.8px; }
      .external .boxbody, .evaluation.compact .boxbody { font-size: 12.8px; }
      .final-title { font-family: Arial, Helvetica, sans-serif; font-size: 21px; line-height: 1.18; font-weight: 700; color: #2e5131; }
      .final-list { font-family: Arial, Helvetica, sans-serif; color: #2d4930; }
      .final-grid { height: 100%; display: grid; grid-template-columns: 1fr 1fr; column-gap: 34px; row-gap: 3px; align-content: center; font-size: 15.5px; line-height: 1.15; }
      .final-grid span::before { content: '•'; font-weight: 700; margin-right: 8px; }
    ]]></style>
  </defs>
  <rect width="${W}" height="${H}" fill="#ffffff"/>
  ${bg.join('\n')}
  ${links.join('\n')}
  ${nodes.join('\n')}
</svg>`;

fs.writeFileSync(out, svg, 'utf8');
console.log(out);
