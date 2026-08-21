const state = { corpus: null, byLeaf: new Map(), currentPage: null, unit: 'page', edits: {}, submissions: {}, workspacesLoaded: new Set(), staleDraft: null };
const WORKSPACE_SCHEMA = 3;
const previewImageCache = new Map();
const hdImageCache = new Map();
const hdFailures = new Map();
const PREVIEW_RETRY_DELAYS = [0, 1500, 4000];
const HD_DWELL_TIME = 1200;
const HD_MIN_START_INTERVAL = 0;
const HD_FAILURE_COOLDOWN = 5000;
let imageLoadGeneration = 0;
const hdManager = {candidate: null, inFlight: null, lastStartedAt: 0, timer: null};
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));

function retainImage(cache, leaf, url, priority = 'low') {
  let entry = cache.get(leaf);
  if (entry) {
    if (priority === 'high') entry.image.fetchPriority = 'high';
    return entry;
  }
  const image = new Image();
  image.decoding = 'async';
  image.fetchPriority = priority;
  entry = {image, status: 'loading', ready: null};
  const ready = new Promise(resolve => {
    image.addEventListener('load', () => { entry.status = 'loaded'; resolve(true); }, {once: true});
    image.addEventListener('error', () => {
      entry.status = 'error';
      if (cache.get(leaf) === entry) cache.delete(leaf);
      resolve(false);
    }, {once: true});
  });
  entry.ready = ready;
  cache.set(leaf, entry);
  image.src = url;
  return entry;
}

function delay(milliseconds) {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}

function setScanStatus(message, retryAction = null) {
  document.querySelectorAll('.scan-status').forEach(node => { node.textContent = message; });
  document.querySelectorAll('.preview-retry').forEach(node => { node.classList.toggle('hidden', retryAction !== 'preview'); });
  document.querySelectorAll('.hd-retry').forEach(node => { node.classList.toggle('hidden', retryAction !== 'hd'); });
}

function displayPageImage(page, url) {
  if (state.currentPage?.leaf !== page.leaf) return;
  document.querySelectorAll('img[data-iiif-page]').forEach(image => {
    if (image.src !== url) image.src = url;
  });
}

function refreshPageImageUI(page) {
  if (state.currentPage?.leaf !== page.leaf) return;
  if (hdImageCache.get(page.leaf)?.status === 'loaded') {
    displayPageImage(page, page.iiif);
    setScanStatus('HD loaded from image mirror');
    return;
  }
  if (previewImageCache.get(page.leaf)?.status !== 'loaded') {
    setScanStatus('Loading preview from image mirror…');
    return;
  }
  displayPageImage(page, page.iiif_preview);
  if (hdManager.inFlight?.leaf === page.leaf) setScanStatus('Preview loaded · loading HD…');
  else if (hdManager.candidate?.page.leaf === page.leaf) setScanStatus('Preview loaded · HD queued');
  else if (hdFailures.has(page.leaf)) setScanStatus('Preview loaded · HD unavailable', 'hd');
  else setScanStatus('Preview loaded');
}

function clearHDCandidate() {
  hdManager.candidate = null;
  if (hdManager.timer !== null) clearTimeout(hdManager.timer);
  hdManager.timer = null;
}

function pumpHDManager() {
  if (hdManager.timer !== null) clearTimeout(hdManager.timer);
  hdManager.timer = null;
  const candidate = hdManager.candidate;
  if (!candidate) return;
  if (state.currentPage?.leaf !== candidate.page.leaf) {
    clearHDCandidate();
    return;
  }
  if (hdManager.inFlight) return;
  const failureUntil = hdFailures.get(candidate.page.leaf) || 0;
  const earliestStart = Math.max(candidate.earliestAt, hdManager.lastStartedAt + HD_MIN_START_INTERVAL, failureUntil);
  const wait = earliestStart - Date.now();
  if (wait > 0) {
    hdManager.timer = setTimeout(pumpHDManager, wait);
    refreshPageImageUI(candidate.page);
    return;
  }
  void startHDRequest(candidate.page);
}

async function startHDRequest(page) {
  if (state.currentPage?.leaf !== page.leaf || hdManager.inFlight) return;
  hdManager.candidate = null;
  hdManager.lastStartedAt = Date.now();
  const entry = retainImage(hdImageCache, page.leaf, page.iiif, 'high');
  hdManager.inFlight = {leaf: page.leaf, entry};
  refreshPageImageUI(page);
  const success = await entry.ready;
  hdManager.inFlight = null;
  if (success) hdFailures.delete(page.leaf);
  else hdFailures.set(page.leaf, Date.now() + HD_FAILURE_COOLDOWN);
  if (state.currentPage?.leaf === page.leaf) refreshPageImageUI(page);
  pumpHDManager();
}

function queueHD(page, dwell = true) {
  if (hdImageCache.get(page.leaf)?.status === 'loaded' || hdManager.inFlight?.leaf === page.leaf) {
    refreshPageImageUI(page);
    return;
  }
  if (hdManager.candidate?.page.leaf !== page.leaf) {
    clearHDCandidate();
    hdManager.candidate = {page, earliestAt: Date.now() + (dwell ? HD_DWELL_TIME : 0)};
  }
  refreshPageImageUI(page);
  pumpHDManager();
}

async function loadCurrentPreview(page, generation) {
  for (let attempt = 0; attempt < PREVIEW_RETRY_DELAYS.length; attempt++) {
    const retryDelay = PREVIEW_RETRY_DELAYS[attempt];
    if (retryDelay) {
      setScanStatus(`Retrying image preview (${attempt + 1}/${PREVIEW_RETRY_DELAYS.length})…`);
      await delay(retryDelay);
    }
    if (generation !== imageLoadGeneration || state.currentPage?.leaf !== page.leaf) return;
    const entry = retainImage(previewImageCache, page.leaf, page.iiif_preview, 'high');
    if (await entry.ready) {
      if (generation !== imageLoadGeneration || state.currentPage?.leaf !== page.leaf) return;
      refreshPageImageUI(page);
      queueHD(page);
      return;
    }
  }
  if (generation === imageLoadGeneration && state.currentPage?.leaf === page.leaf) {
    setScanStatus('Image preview unavailable', 'preview');
    toast('The image preview could not be loaded. Retry when ready.');
  }
}

function updatePageImages(leaf) {
  const generation = ++imageLoadGeneration;
  if (hdManager.candidate?.page.leaf !== leaf) clearHDCandidate();
  setScanStatus('Loading preview from image mirror…');
  void loadCurrentPreview(state.byLeaf.get(leaf), generation);
}

function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.classList.remove('hidden');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.add('hidden'), 1800);
}

function route() {
  const match = location.hash.match(/^#f(\d+)(?::(page|column-1|column-2|furniture))?$/);
  if (match && state.byLeaf.has(Number(match[1]))) showPage(Number(match[1]), match[2] || 'page', false);
  else showOverview(false);
}

function showOverview(update = true) {
  imageLoadGeneration++;
  clearHDCandidate();
  state.currentPage = null;
  $('#overview').classList.remove('hidden');
  $('#page-view').classList.add('hidden');
  $('#page-nav').classList.add('hidden');
  $('#submit-bar').classList.add('hidden');
  if (update) history.pushState(null, '', '#overview');
  renderGrid();
}

function correctionLabel(page) {
  const issues = page.corrections.issues_applied || 0;
  const lines = page.corrections.distinct_lines || 0;
  return `${issues} Issue${issues === 1 ? '' : 's'} · ${lines} corrected line${lines === 1 ? '' : 's'}`;
}

function renderGrid() {
  const filter = $('#filter').value;
  const sort = $('#sort').value;
  let pages = state.corpus.pages.filter(page => filter === 'all' || (filter === 'processed' && page.processed) || (filter === 'unprocessed' && !page.processed) || (filter === 'corrected' && page.corrections.issues_applied));
  if (sort === 'recent') pages.sort((a, b) => String(b.corrections.last_applied || '').localeCompare(String(a.corrections.last_applied || '')) || a.leaf - b.leaf);
  $('#page-grid').innerHTML = pages.map(page => `<button class="page-card" type="button" data-leaf="${page.leaf}"><img loading="lazy" src="${page.thumbnail}" alt="Thumbnail of Gallica ${page.view}"><span class="card-copy"><span class="card-title">${page.view}${page.corrections.issues_applied ? `<span class="mini-badge">${page.corrections.issues_applied} issue${page.corrections.issues_applied === 1 ? '' : 's'}</span>` : ''}</span><span class="card-state">${page.processed ? 'Transcription available' : 'Unprocessed'}${page.corrections.distinct_lines ? ` · ${page.corrections.distinct_lines} lines corrected` : ''}</span></span></button>`).join('');
}

function storageJSON(key) {
  try { return JSON.parse(localStorage.getItem(key)); }
  catch (_) { return null; }
}

function editStorageKey(page) { return `nippo-edits:${page.page_id}`; }
function submissionStorageKey(page) { return `nippo-submission:${page.page_id}`; }

function saveWorkspace(page) {
  localStorage.setItem(editStorageKey(page), JSON.stringify({schema: WORKSPACE_SCHEMA, transcription_version: page.transcription_version, edits: state.edits[page.page_id]}));
  localStorage.setItem(submissionStorageKey(page), JSON.stringify({schema: WORKSPACE_SCHEMA, transcription_version: page.transcription_version, status: state.submissions[page.page_id].status}));
}

function requestsSecondOpinion(edit) {
  return edit?.second_opinion ?? Boolean(edit?.comment);
}

function staleDraftPayload(stale) {
  const changes = Object.entries(stale.edits).map(([line, edit]) => ({line, before: edit.before, after: edit.after, ...(edit.comment ? {comment: edit.comment} : {}), ...(requestsSecondOpinion(edit) ? {second_opinion: true} : {})}));
  return JSON.stringify({schema: 2, page: stale.page.view, base_transcription_version: stale.version, changes}, null, 2);
}

function showStaleDraftWarning() {
  if (!state.staleDraft || state.staleDraft.page !== state.currentPage) return;
  $('#stale-draft-page').textContent = state.staleDraft.page.view;
  const count = Object.keys(state.staleDraft.edits).length;
  $('#stale-draft-count').textContent = `${count} saved correction${count === 1 ? '' : 's'}`;
  const dialog = $('#stale-draft-dialog');
  if (!dialog.open) dialog.showModal();
}

function pageLineMap(page) {
  return new Map(page.zones.flatMap(zone => zone.lines).map(line => [line.id, line]));
}

function parseTypefaceNotation(value) {
  let text = '';
  let open = null;
  const romanRanges = [];
  const italicRanges = [];
  for (let index = 0; index < value.length; index++) {
    const character = value[index];
    if (character === '[' || character === '{') {
      if (open !== null) return {valid: false, error: 'Typeface spans cannot be nested or overlap.'};
      open = {delimiter: character, start: text.length};
    } else if (character === ']' || character === '}') {
      if (open === null) return {valid: false, error: 'A typeface span has an unmatched closing delimiter.'};
      if ((open.delimiter === '[' && character !== ']') || (open.delimiter === '{' && character !== '}')) {
        return {valid: false, error: 'A typeface span has mismatched delimiters.'};
      }
      if (open.start === text.length) return {valid: false, error: 'A typeface span cannot be empty.'};
      (open.delimiter === '[' ? romanRanges : italicRanges).push([open.start, text.length]);
      open = null;
    } else {
      text += character;
    }
  }
  if (open !== null) return {valid: false, error: 'A typeface span has no closing delimiter.'};
  return {valid: true, text, romanRanges, italicRanges};
}

function rangeContains(ranges, index) {
  return ranges.some(([start, end]) => start <= index && index < end);
}

function proposalMatchesLine(line, annotatedText) {
  const proposal = parseTypefaceNotation(annotatedText);
  if (!proposal.valid || proposal.text !== line.text) return false;
  const typefaces = line.runs.flatMap(run => Array(run.text.length).fill(run.typeface));
  const matches = (ranges, expected) => ranges.every(([start, end]) => {
    for (let index = start; index < end; index++) if (typefaces[index] !== expected) return false;
    return true;
  });
  return matches(proposal.romanRanges, 'roman') && matches(proposal.italicRanges, 'italic');
}

function reconcileEdits(page, edits) {
  const lines = pageLineMap(page);
  const reconciled = {};
  const orphaned = {};
  for (const [lineId, edit] of Object.entries(edits)) {
    const line = lines.get(lineId);
    if (!line) {
      orphaned[lineId] = edit;
      continue;
    }
    const lineChanged = edit.base_line_version
      ? edit.base_line_version !== line.transcription_version
      : edit.before !== line.text;
    if (!lineChanged) {
      reconciled[lineId] = {...edit, base_line_version: line.transcription_version};
      continue;
    }
    const reviewFlags = {
      base_line_version: line.transcription_version,
      base_changed: true,
      ...(edit.comment ? {comment_review_needed: true} : {}),
    };
    if (proposalMatchesLine(line, edit.after)) {
      if (edit.comment) reconciled[lineId] = {...edit, before: line.text, after: line.text, ...reviewFlags};
      continue;
    }
    const proposal = parseTypefaceNotation(edit.after);
    if (proposal.valid && edit.before === proposal.text && proposal.romanRanges.length === 0 && proposal.italicRanges.length === 0) {
      if (edit.comment) reconciled[lineId] = {...edit, before: line.text, after: line.text, ...reviewFlags};
      continue;
    }
    reconciled[lineId] = {...edit, before: line.text, ...reviewFlags};
  }
  return {reconciled, orphaned};
}

function loadPageWorkspace(page) {
  if (state.workspacesLoaded.has(page.page_id)) return;
  const storedEdits = storageJSON(editStorageKey(page));
  const storedSubmission = storageJSON(submissionStorageKey(page));
  const isEnvelope = storedEdits?.schema >= 2 && storedEdits.edits && typeof storedEdits.edits === 'object';
  const edits = isEnvelope ? storedEdits.edits : (storedEdits && typeof storedEdits === 'object' ? storedEdits : {});
  const status = storedSubmission?.status || 'draft';
  const storedVersion = isEnvelope ? storedEdits.transcription_version : page.transcription_version;
  const versionChanged = Boolean(storedVersion && page.transcription_version && storedVersion !== page.transcription_version);
  state.edits[page.page_id] = edits;
  state.submissions[page.page_id] = {status};
  state.workspacesLoaded.add(page.page_id);
  if (versionChanged) {
    const {reconciled, orphaned} = reconcileEdits(page, edits);
    state.edits[page.page_id] = reconciled;
    const hasRebasedEdits = Object.values(reconciled).some(edit => edit.base_changed);
    if (hasRebasedEdits || Object.keys(orphaned).length || Object.keys(reconciled).length === 0) {
      state.submissions[page.page_id] = {status: 'draft'};
    }
    if (Object.keys(orphaned).length) {
      state.staleDraft = {page, version: storedVersion, edits: orphaned};
      queueMicrotask(showStaleDraftWarning);
      return;
    }
    saveWorkspace(page);
    return;
  }
  const lines = pageLineMap(page);
  for (const [lineId, edit] of Object.entries(edits)) {
    const line = lines.get(lineId);
    if (line && !edit.base_line_version && edit.before === line.text) edit.base_line_version = line.transcription_version;
  }
  if (!isEnvelope || storedEdits.schema !== WORKSPACE_SCHEMA || storedSubmission?.schema !== WORKSPACE_SCHEMA) saveWorkspace(page);
}

function pageEdits(page) {
  loadPageWorkspace(page);
  return state.edits[page.page_id];
}

function pageSubmission(page) {
  loadPageWorkspace(page);
  return state.submissions[page.page_id];
}

function persistSubmission(page, status) {
  state.submissions[page.page_id] = {status};
  saveWorkspace(page);
  updateSubmitBar();
}

function persistEdits(page, preserveSubmission = false) {
  if (!preserveSubmission && pageSubmission(page).status !== 'draft') persistSubmission(page, 'draft');
  saveWorkspace(page);
  updateSubmitBar();
}

function updateSubmitBar() {
  if (!state.currentPage) return;
  const count = Object.keys(pageEdits(state.currentPage)).length;
  $('#submit-bar').classList.toggle('hidden', count === 0);
  $('#change-count').textContent = `${count} proposed line correction${count === 1 ? '' : 's'}`;
  const status = pageSubmission(state.currentPage).status;
  $('#submit-question').classList.toggle('hidden', status !== 'awaiting');
  $('#submitted-label').classList.toggle('hidden', status !== 'submitted');
  $('#submit-not-yet').classList.toggle('hidden', status !== 'awaiting');
  $('#mark-submitted').classList.toggle('hidden', status !== 'awaiting');
  $('#submit-again').classList.toggle('hidden', status !== 'submitted');
  $('#submit').classList.toggle('hidden', status !== 'draft');
  updateRebaseNotice();
}

function updateRebaseNotice() {
  if (!state.currentPage) return;
  const edits = Object.values(pageEdits(state.currentPage));
  const changed = edits.filter(edit => edit.base_changed).length;
  const comments = edits.filter(edit => edit.comment_review_needed).length;
  $('#rebase-notice').classList.toggle('hidden', changed === 0);
  if (!changed) return;
  let message = `The source data changed for ${changed} edited line${changed === 1 ? '' : 's'}. The saved corrections now use the current transcription as their base.`;
  if (comments) message += ` ${comments} attached comment${comments === 1 ? '' : 's'} may refer to the earlier transcription.`;
  $('#rebase-notice-text').textContent = message;
}

function showPage(leaf, unit = 'page', update = true) {
  const page = state.byLeaf.get(leaf);
  if (!page) return;
  loadPageWorkspace(page);
  state.currentPage = page;
  state.unit = page.processed ? unit : 'page';
  updatePageImages(leaf);
  $('#overview').classList.add('hidden');
  $('#page-view').classList.remove('hidden');
  $('#page-nav').classList.remove('hidden');
  $('#leaf-input').value = leaf;
  $('#previous').disabled = leaf === 1;
  $('#next').disabled = leaf === 651;
  $('#page-kicker').textContent = page.printed_page ? `Printed page ${page.printed_page}` : 'Gallica leaf';
  $('#page-title').textContent = `${page.view} · ${({'page':'Full page','column-1':'Column 1','column-2':'Column 2','furniture':'Page furniture'})[state.unit]}`;
  $('#page-meta').textContent = page.processed ? `${page.page_id} · Level 1 ${page.status.replaceAll('_', ' ')}` : `${page.page_id} · transcription not yet processed`;
  $('#page-badges').innerHTML = `<span class="badge ${page.processed ? 'good' : ''}">${page.processed ? 'Transcription available' : 'Unprocessed'}</span><span class="badge">${correctionLabel(page)}</span>${page.corrections.last_applied ? `<span class="badge">Latest ${escapeHTML(page.corrections.last_applied)}</span>` : ''}`;
  [...document.querySelectorAll('#view-tabs button')].forEach(button => { button.classList.toggle('active', button.dataset.unit === state.unit); button.disabled = !page.processed && button.dataset.unit !== 'page'; });
  renderPageContent();
  updateSubmitBar();
  showStaleDraftWarning();
  if (update) history.pushState(null, '', `#f${leaf}:${state.unit}`);
}

function renderRuns(runs) {
  return runs.map(run => {
    const text = escapeHTML(run.text);
    if (run.typeface === 'italic') return `<em>${text}</em>`;
    if (run.typeface === 'display') return `<strong>${text}</strong>`;
    return text;
  }).join('');
}

function zonesFor(page, unit) {
  if (unit === 'page') return page.zones;
  if (unit === 'column-1' || unit === 'column-2') {
    return page.zones.filter(zone => zone.id.includes(unit));
  }
  return page.zones.filter(zone => zone.kind !== 'column');
}

function columnSequence() {
  return state.corpus.pages.flatMap(page => ['column-1', 'column-2']
    .filter(unit => page.processed && zonesFor(page, unit).some(zone => zone.kind === 'column' && zone.lines.length))
    .map(unit => ({leaf: page.leaf, unit})));
}

function columnNavigationHTML(extraClass = '') {
  const sequence = columnSequence();
  const index = sequence.findIndex(item => item.leaf === state.currentPage.leaf && item.unit === state.unit);
  if (index < 0) return '';
  const previous = sequence[index - 1];
  const next = sequence[index + 1];
  const target = item => item ? `data-column-leaf="${item.leaf}" data-column-unit="${item.unit}"` : 'disabled';
  return `<nav class="column-nav ${extraClass}" aria-label="Column review navigation"><button type="button" ${target(previous)}>← Previous column</button><span>Column ${index + 1} of ${sequence.length}</span><button type="button" ${target(next)}>Next column →</button></nav>`;
}

function updateColumnNavigation() {
  const top = $('#column-nav-top');
  const visible = state.currentPage?.processed && ['column-1', 'column-2'].includes(state.unit);
  top.classList.toggle('hidden', !visible);
  top.innerHTML = visible ? columnNavigationHTML('column-nav-inline').replace(/^<nav[^>]*>|<\/nav>$/g, '') : '';
}

function continuousHTML(page, unit) {
  if (!page.processed) return '<div class="empty"><div><strong>Not yet processed</strong><p>The source scan is available now; transcription will appear here when produced.</p></div></div>';
  return zonesFor(page, unit).map(zone => `<section><h3>${escapeHTML(zone.label)}</h3>${zone.lines.map(line => `<div class="continuous-line indent-${line.indent}"><code class="line-id">${escapeHTML(line.id)}</code><span>${renderRuns(line.runs)}</span></div>`).join('')}</section>`).join('');
}

function scanPane(page) {
  return `<section class="scan-pane"><div class="pane-toolbar"><strong>Source scan</strong><span class="push scan-status">Loading preview…</span><button class="preview-retry hidden" type="button" data-action="retry-preview">Retry preview</button><button class="hd-retry hidden" type="button" data-action="retry-hd">Retry HD</button><span>Source gallica.bnf.fr / BnF</span><a href="${page.gallica}" target="_blank" rel="noreferrer">Open original</a></div><div class="scan-frame"><img data-iiif-page alt=""></div></section>`;
}

function lineImageStatus(page) {
  return `<div class="line-image-status"><span class="scan-status">Loading preview from image mirror…</span><button class="preview-retry hidden" type="button" data-action="retry-preview">Retry preview</button><button class="hd-retry hidden" type="button" data-action="retry-hd">Retry HD</button><span class="push">Source gallica.bnf.fr / BnF</span><a href="${page.gallica}" target="_blank" rel="noreferrer">Open original</a></div>`;
}

function renderPageContent() {
  const page = state.currentPage;
  if (page.processed && ['column-1', 'column-2'].includes(state.unit)) {
    const lines = zonesFor(page, state.unit).filter(item => item.kind === 'column').flatMap(item => item.lines);
    $('#page-content').innerHTML = `<div class="line-list">${lineImageStatus(page)}${lines.map(line => lineHTML(page, line)).join('')}${columnNavigationHTML('column-nav-bottom')}</div>`;
  } else {
    $('#page-content').innerHTML = `<div class="page-comparison">${scanPane(page)}<section class="text-pane"><div class="pane-toolbar"><strong>${page.processed ? 'Level 1 transcription' : 'Transcription'}</strong>${page.source ? `<a class="push" href="${page.source}" target="_blank" rel="noreferrer">Source Markdown</a>` : ''}</div><div class="continuous-text">${continuousHTML(page, state.unit)}</div></section></div>`;
  }
  updateColumnNavigation();
  refreshPageImageUI(page);
}

function cropStyle(page, crop) {
  const [x, y, width, height] = crop;
  return `--ratio:${width}/${height};--image-width:${page.width / width * 100}%;--move-x:${-x / page.width * 100}%;--move-y:${-y / page.height * 100}%`;
}

function renderStyledSlice(runs, sourceOffset, text, mark = false, fixedTypeface = null) {
  if (!text) return '';
  const typefaces = runs.flatMap(run => Array(run.text.length).fill(run.typeface));
  const pieces = [];
  for (let index = 0; index < text.length; index++) {
    const sourceIndex = Math.max(0, Math.min(typefaces.length - 1, sourceOffset + index));
    const typeface = fixedTypeface || typefaces[sourceIndex] || 'roman';
    const previous = pieces[pieces.length - 1];
    if (previous?.typeface === typeface) previous.text += text[index];
    else pieces.push({typeface, text: text[index]});
  }
  return pieces.map(piece => {
    let output = escapeHTML(piece.text);
    if (mark) output = `<mark class="diff-added">${output}</mark>`;
    if (piece.typeface === 'italic') return `<em>${output}</em>`;
    if (piece.typeface === 'display') return `<strong>${output}</strong>`;
    return output;
  }).join('');
}

function styledVisualDiff(line, after) {
  const proposal = parseTypefaceNotation(after);
  if (!proposal.valid) return escapeHTML(after);
  if (proposal.romanRanges.length || proposal.italicRanges.length) return styledTypefaceDiff(line, proposal);
  after = proposal.text;
  const before = line.text;
  if (before === after) return renderRuns(line.runs);
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start]) start++;
  let end = 0;
  while (end < before.length - start && end < after.length - start && before[before.length - 1 - end] === after[after.length - 1 - end]) end++;
  const changed = after.slice(start, after.length - end || undefined);
  const typefaces = line.runs.flatMap(run => Array(run.text.length).fill(run.typeface));
  const changedTypeface = typefaces[Math.min(start, typefaces.length - 1)] || 'roman';
  return renderStyledSlice(line.runs, 0, after.slice(0, start))
    + renderStyledSlice(line.runs, start, changed || '∅', true, changedTypeface)
    + renderStyledSlice(line.runs, before.length - end, end ? after.slice(after.length - end) : '');
}

function styledTypefaceDiff(line, proposal) {
  const before = line.text;
  const after = proposal.text;
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start]) start++;
  let end = 0;
  while (end < before.length - start && end < after.length - start && before[before.length - 1 - end] === after[after.length - 1 - end]) end++;
  const changedEnd = after.length - end;
  const typefaces = line.runs.flatMap(run => Array(run.text.length).fill(run.typeface));
  const pieces = [];
  for (let index = 0; index < after.length; index++) {
    let sourceIndex;
    if (index < start) sourceIndex = index;
    else if (index >= changedEnd) sourceIndex = before.length - (after.length - index);
    else sourceIndex = Math.min(start, Math.max(0, typefaces.length - 1));
    const originalTypeface = typefaces[sourceIndex] || 'roman';
    const forcedRoman = rangeContains(proposal.romanRanges, index);
    const forcedItalic = rangeContains(proposal.italicRanges, index);
    const typeface = forcedRoman ? 'roman' : (forcedItalic ? 'italic' : originalTypeface);
    const marked = (start <= index && index < changedEnd)
      || (forcedRoman && originalTypeface !== 'roman')
      || (forcedItalic && originalTypeface !== 'italic');
    const previous = pieces[pieces.length - 1];
    if (previous?.typeface === typeface && previous.marked === marked) previous.text += after[index];
    else pieces.push({typeface, marked, text: after[index]});
  }
  return pieces.map(piece => {
    let output = escapeHTML(piece.text);
    if (piece.marked) output = `<mark class="diff-added">${output}</mark>`;
    if (piece.typeface === 'italic') return `<em>${output}</em>`;
    if (piece.typeface === 'display') return `<strong>${output}</strong>`;
    return output;
  }).join('');
}

function lineHTML(page, line) {
  const edit = pageEdits(page)[line.id];
  const current = edit ? edit.after : line.text;
  const comment = edit?.comment || '';
  const markers = `${edit?.base_changed ? '<span class="review-marker">Base updated</span>' : ''}${edit?.comment_review_needed ? '<span class="review-marker comment-marker">Comment needs review</span>' : ''}${requestsSecondOpinion(edit) ? '<span class="review-marker opinion-marker">Second opinion</span>' : ''}`;
  return `<article class="line-row ${edit ? 'changed' : ''} ${edit?.base_changed ? 'rebased' : ''}" data-line="${line.id}"><div class="line-head"><code>${line.id}</code>${markers}<button class="context-toggle" type="button" aria-expanded="false">Show context</button></div><button class="line-crop" type="button" style="aspect-ratio:${line.crop[2]}/${line.crop[3]}" data-crop='${JSON.stringify(line.crop)}' data-context='${JSON.stringify(line.context_crop)}' aria-label="Show context for ${line.id}"><img loading="lazy" data-iiif-page alt="" style="width:${page.width / line.crop[2] * 100}%;transform:translate(${-line.crop[0] / page.width * 100}% ,${-line.crop[1] / page.height * 100}%)"></button><div class="line-text-row"><button class="line-text indent-${line.indent}" type="button" data-action="edit">${edit ? styledVisualDiff(line, current) : renderRuns(line.runs)}</button>${comment ? `<button class="comment-preview" type="button" data-action="edit" title="${escapeHTML(comment)}">${escapeHTML(comment)}</button>` : ''}</div></article>`;
}

function setCrop(row, expanded) {
  const cropNode = row.querySelector('.line-crop');
  const crop = JSON.parse(expanded ? cropNode.dataset.context : cropNode.dataset.crop);
  const page = state.currentPage;
  cropNode.style.aspectRatio = `${crop[2]}/${crop[3]}`;
  const image = cropNode.querySelector('img');
  image.style.width = `${page.width / crop[2] * 100}%`;
  image.style.transform = `translate(${-crop[0] / page.width * 100}% ,${-crop[1] / page.height * 100}%)`;
}

const TRANSCRIPTION_KEYS = {
  '1': {label: 'ſ', insert: 'ſ'},
  '2': {label: 'ç', insert: 'ç'},
  '3': {label: '◌̃', mark: '\u0303', name: 'tilde'},
  '4': {label: '◌̀', mark: '\u0300', name: 'grave accent'},
  '5': {label: '◌́', mark: '\u0301', name: 'acute accent'},
  '6': {label: 'ǒ', insert: 'ǒ'},
  '7': {label: 'ǔ', insert: 'ǔ'},
  '8': {label: 'ô', insert: 'ô'},
  '9': {label: 'û', insert: 'û'},
};

function paletteHTML() {
  const buttons = Object.entries(TRANSCRIPTION_KEYS).map(([key, item]) =>
    `<button type="button" class="character-key" data-character-key="${key}" aria-label="${item.name || `Insert ${item.label}`}"><span>${item.label}</span><kbd>${key}</kbd></button>`
  ).join('');
  return `<div class="character-palette" aria-label="Transcription characters"><div class="character-buttons">${buttons}<button type="button" class="typeface-span-key" data-action="typeface-span" data-typeface="roman" aria-label="Mark selected text as Roman type"><span>Roman</span><kbd>[ ]</kbd></button><button type="button" class="typeface-span-key" data-action="typeface-span" data-typeface="italic" aria-label="Mark selected text as italic type"><span>Italic</span><kbd>{ }</kbd></button></div><label class="literal-digits"><input type="checkbox" name="literal-digits"> Literal digits</label></div>`;
}

function replaceSelection(area, replacement, start = area.selectionStart, end = area.selectionEnd) {
  area.setRangeText(replacement, start, end, 'end');
  area.dispatchEvent(new Event('input', {bubbles: true}));
  area.focus();
}

function applyDecoration(area, mark) {
  let start = area.selectionStart;
  let end = area.selectionEnd;
  if (start === end) {
    while (start > 0 && /[\u0300-\u036f]/u.test(area.value[start - 1])) start--;
    if (start > 0) start--;
  }
  const target = area.value.slice(start, end);
  const decomposed = target.normalize('NFD');
  const base = decomposed.match(/[A-Za-z]/u)?.[0];
  if (!base || decomposed.replace(/[\u0300-\u036f]/gu, '') !== base) {
    toast('Select a single letter, or place the cursor after one.');
    area.focus();
    return;
  }
  replaceSelection(area, (base + mark).normalize('NFC'), start, end);
}

function applyTypefaceSpan(area, typeface) {
  const start = area.selectionStart;
  const end = area.selectionEnd;
  if (start === end) {
    toast(`Select the text to mark as ${typeface} type.`);
    area.focus();
    return;
  }
  const target = area.value.slice(start, end);
  if (['[', ']', '{', '}'].some(character => target.includes(character))) {
    toast('Select text that is not already marked with a typeface annotation.');
    area.focus();
    return;
  }
  const [open, close] = typeface === 'italic' ? ['{', '}'] : ['[', ']'];
  replaceSelection(area, `${open}${target}${close}`, start, end);
  area.setSelectionRange(start + 1, end + 1);
}

function useTranscriptionKey(form, key) {
  const item = TRANSCRIPTION_KEYS[key];
  const area = form.elements.transcription;
  if (!item || !area) return;
  if (item.mark) applyDecoration(area, item.mark);
  else replaceSelection(area, item.insert);
}

function saveEditor(form) {
  const row = form.closest('.line-row');
  const line = state.currentPage.zones.filter(item => item.kind === 'column').flatMap(item => item.lines).find(item => item.id === row.dataset.line);
  const after = form.elements.transcription.value;
  const comment = form.elements.comment.value.trim();
  const secondOpinion = form.elements['second-opinion'].checked;
  const secondOpinionManual = form.elements['second-opinion'].dataset.manual === 'true';
  const proposal = parseTypefaceNotation(after);
  if (!proposal.valid) {
    toast(proposal.error);
    form.elements.transcription.focus();
    return false;
  }
  if (proposalMatchesLine(line, after) && !comment && !secondOpinion) delete pageEdits(state.currentPage)[line.id];
  else pageEdits(state.currentPage)[line.id] = {before: line.text, after, comment, second_opinion: secondOpinion, second_opinion_manual: secondOpinionManual, base_line_version: line.transcription_version};
  persistEdits(state.currentPage);
  return true;
}

function openEditor(row) {
  const lineId = row.dataset.line;
  const activeForm = document.querySelector('.edit-form');
  if (activeForm) {
    if (activeForm.closest('.line-row') === row) return;
    if (!saveEditor(activeForm)) return;
    renderPageContent();
    row = [...document.querySelectorAll('.line-row')].find(candidate => candidate.dataset.line === lineId);
    if (!row) return;
  }
  const line = state.currentPage.zones.filter(item => item.kind === 'column').flatMap(item => item.lines).find(item => item.id === lineId);
  const edit = pageEdits(state.currentPage)[lineId];
  const hasStoredOpinion = typeof edit?.second_opinion === 'boolean';
  const secondOpinion = hasStoredOpinion ? edit.second_opinion : Boolean(edit?.comment);
  const opinionManual = hasStoredOpinion && edit?.second_opinion_manual;
  row.insertAdjacentHTML('beforeend', `<form class="edit-form"><div class="transcription-editor"><textarea name="transcription" aria-label="Revised transcription">${escapeHTML(edit?.after || line.text)}</textarea>${paletteHTML()}</div><div class="comment-editor"><textarea name="comment" aria-label="Comment" placeholder="Optional comment">${escapeHTML(edit?.comment || '')}</textarea><label class="second-opinion-toggle"><input type="checkbox" name="second-opinion" ${secondOpinion ? 'checked' : ''} data-manual="${opinionManual ? 'true' : 'false'}"> <span>Request second opinion</span></label></div><div class="edit-actions"><button type="button" data-action="cancel">Cancel</button>${edit ? '<button type="button" data-action="revert">Revert</button>' : ''}<button class="primary" type="submit">OK</button></div></form>`);
  const form = row.querySelector('.edit-form');
  const commentArea = form.elements.comment;
  const opinionControl = form.elements['second-opinion'];
  commentArea.addEventListener('input', () => {
    if (opinionControl.dataset.manual !== 'true') opinionControl.checked = Boolean(commentArea.value.trim());
  });
  opinionControl.addEventListener('change', () => { opinionControl.dataset.manual = 'true'; });
  row.querySelector('[name="transcription"]').focus();
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) try { await navigator.clipboard.writeText(text); return true; } catch (_) {}
  const area = document.createElement('textarea'); area.value = text; area.style.position = 'fixed'; area.style.opacity = '0'; document.body.appendChild(area); area.select(); const ok = document.execCommand('copy'); area.remove(); return ok;
}

async function submitCorrections() {
  const page = state.currentPage;
  const changes = Object.entries(pageEdits(page)).map(([line, edit]) => ({ line, before: edit.before, after: edit.after, ...(edit.comment ? {comment: edit.comment} : {}), ...(requestsSecondOpinion(edit) ? {second_opinion: true} : {}) }));
  const payload = JSON.stringify({ schema: 2, page: page.view, base_commit: state.corpus.commit, base_transcription_version: page.transcription_version, changes }, null, 2);
  const issueURL = `https://github.com/${state.corpus.repository}/issues/new?template=transcription-correction.md&title=${encodeURIComponent(`[${page.view}] Transcription corrections`)}`;
  const issueWindow = window.open('about:blank', '_blank');
  const copied = await copyText(payload);
  persistSubmission(page, 'awaiting');
  if (issueWindow) issueWindow.location = issueURL; else window.location.href = issueURL;
  if (copied) toast('Correction JSON copied. Paste it into the Issue.');
  else { prompt('Copy this correction JSON, then paste it into the Issue:', payload); toast('Clipboard unavailable; the payload was displayed.'); }
}

document.addEventListener('click', event => {
  if (event.target.closest('[data-action="retry-preview"]')) return updatePageImages(state.currentPage.leaf);
  if (event.target.closest('[data-action="retry-hd"]')) return queueHD(state.currentPage, false);
  const card = event.target.closest('.page-card'); if (card) return showPage(Number(card.dataset.leaf));
  const tab = event.target.closest('#view-tabs button'); if (tab) return showPage(state.currentPage.leaf, tab.dataset.unit);
  const columnButton = event.target.closest('[data-column-leaf][data-column-unit]');
  if (columnButton) { showPage(Number(columnButton.dataset.columnLeaf), columnButton.dataset.columnUnit); window.scrollTo(0, 0); return; }
  const row = event.target.closest('.line-row');
  if (row) {
    const characterButton = event.target.closest('[data-character-key]');
    if (characterButton) return useTranscriptionKey(row.querySelector('.edit-form'), characterButton.dataset.characterKey);
    const typefaceButton = event.target.closest('[data-action="typeface-span"]');
    if (typefaceButton) return applyTypefaceSpan(row.querySelector('textarea[name="transcription"]'), typefaceButton.dataset.typeface);
    if (event.target.closest('.context-toggle,.line-crop')) { const button = row.querySelector('.context-toggle'); const expanded = button.getAttribute('aria-expanded') !== 'true'; button.setAttribute('aria-expanded', String(expanded)); button.textContent = expanded ? 'Hide context' : 'Show context'; setCrop(row, expanded); return; }
    if (event.target.closest('[data-action="edit"]')) return openEditor(row);
    if (event.target.closest('[data-action="cancel"]')) { row.querySelector('.edit-form').remove(); return; }
    if (event.target.closest('[data-action="revert"]')) { delete pageEdits(state.currentPage)[row.dataset.line]; persistEdits(state.currentPage); renderPageContent(); return; }
  }
});

document.addEventListener('keydown', event => {
  const area = event.target.closest('.edit-form textarea[name="transcription"]');
  if (!area || event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.key === 'Enter') {
    event.preventDefault();
    if (saveEditor(area.form)) renderPageContent();
    return;
  }
  if (!TRANSCRIPTION_KEYS[event.key] || area.form.elements['literal-digits'].checked) return;
  event.preventDefault();
  useTranscriptionKey(area.form, event.key);
});

document.addEventListener('submit', event => {
  const form = event.target.closest('.edit-form'); if (!form) return;
  event.preventDefault();
  if (saveEditor(form)) renderPageContent();
});

$('#home').addEventListener('click', () => showOverview());
$('#back-to-overview').addEventListener('click', () => showOverview());
$('#filter').addEventListener('change', renderGrid); $('#sort').addEventListener('change', renderGrid);
$('#previous').addEventListener('click', () => showPage(state.currentPage.leaf - 1, state.unit));
$('#next').addEventListener('click', () => showPage(state.currentPage.leaf + 1, state.unit));
function go() { const leaf = Number($('#leaf-input').value); if (state.byLeaf.has(leaf)) showPage(leaf, state.unit); }
$('#go').addEventListener('click', go); $('#leaf-input').addEventListener('keydown', event => { if (event.key === 'Enter') go(); });
$('#discard-all').addEventListener('click', () => { if (!confirm('Discard all proposed corrections for this page?')) return; state.edits[state.currentPage.page_id] = {}; persistSubmission(state.currentPage, 'draft'); persistEdits(state.currentPage, true); renderPageContent(); });
$('#submit').addEventListener('click', submitCorrections);
$('#submit-not-yet').addEventListener('click', () => persistSubmission(state.currentPage, 'draft'));
$('#mark-submitted').addEventListener('click', () => persistSubmission(state.currentPage, 'submitted'));
$('#submit-again').addEventListener('click', () => { persistSubmission(state.currentPage, 'draft'); void submitCorrections(); });
$('#copy-stale-draft').addEventListener('click', async () => {
  if (!state.staleDraft) return;
  const payload = staleDraftPayload(state.staleDraft);
  if (await copyText(payload)) toast('Orphaned corrections copied.');
  else prompt('Copy these orphaned corrections:', payload);
});
$('#discard-stale-draft').addEventListener('click', () => {
  if (!state.staleDraft) return;
  const page = state.staleDraft.page;
  state.staleDraft = null;
  saveWorkspace(page);
  $('#stale-draft-dialog').close();
  renderPageContent();
  updateSubmitBar();
});
$('#stale-draft-dialog').addEventListener('cancel', event => event.preventDefault());

function setReference(open) { $('#reference-panel').classList.toggle('open', open); $('#reference-panel').setAttribute('aria-hidden', String(!open)); $('#reference-toggle').setAttribute('aria-expanded', String(open)); }
$('#reference-toggle').addEventListener('click', () => setReference(!$('#reference-panel').classList.contains('open'))); $('#reference-close').addEventListener('click', () => setReference(false));
document.querySelectorAll('[data-reference]').forEach(button => button.addEventListener('click', () => { document.querySelectorAll('[data-reference]').forEach(item => item.classList.toggle('active', item === button)); $('#reference-frame').src = `reference/${button.dataset.reference}.html`; }));
window.addEventListener('popstate', route);

fetch('corpus.json').then(response => { if (!response.ok) throw new Error('Could not load corpus'); return response.json(); }).then(corpus => {
  state.corpus = corpus; state.byLeaf = new Map(corpus.pages.map(page => [page.leaf, page]));
  const processed = corpus.pages.filter(page => page.processed).length; const corrected = corpus.pages.filter(page => page.corrections.issues_applied).length;
  $('#summary').innerHTML = `<div><strong>${corpus.pages.length}</strong><span>acquired leaves</span></div><div><strong>${processed}</strong><span>transcribed</span></div><div><strong>${corrected}</strong><span>with applied Issues</span></div>`;
  $('#repository-link').href = `https://github.com/${corpus.repository}`; $('#reference-version').textContent = `Reference ${corpus.reference_version}`; $('#reference-frame').src = 'reference/cheat-sheet.html'; route();
}).catch(error => { $('#page-grid').innerHTML = `<p>${escapeHTML(error.message)}</p>`; });
