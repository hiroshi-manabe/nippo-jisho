const state = { corpus: null, byLeaf: new Map(), currentPage: null, unit: 'page', edits: {}, suggestionDismissals: {}, submissions: {}, workspacesLoaded: new Set(), staleDraft: null, staleBaseline: null };
const WORKSPACE_SCHEMA = 5;
let selectionMode = false;
const selectedLeaves = new Set();

function savedCorrectionCount(page) {
  const saved = state.edits[page.page_id] || storageJSON(editStorageKey(page))?.edits || {};
  return Object.keys(saved).length;
}

function renderBatchControls() {
  $('#selection-toggle').setAttribute('aria-pressed', String(selectionMode));
  $('#selection-toggle').textContent = selectionMode ? 'Cancel selection' : 'Select pages to submit';
  $('#selection-count').classList.toggle('hidden', !selectionMode);
  $('#selection-count').textContent = `${selectedLeaves.size} pages selected`;
  $('#submit-selected').classList.toggle('hidden', !selectionMode);
  $('#submit-selected').disabled = !selectedLeaves.size;
  $('#batch-confirmation').classList.toggle('hidden', !storageJSON('nippo-batch-awaiting')?.length);
}
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

function issueCountLabel(page) {
  const issues = page.corrections.issues_applied || 0;
  return issues ? `${issues} issue${issues === 1 ? '' : 's'} applied` : 'No issues applied';
}

function reviewStageLabel(page) {
  if (!page.processed) return 'Scan only';
  return page.ai_checked ? 'AI checked' : 'Machine draft';
}

function shortBaselineDate(page) {
  if (!page.baseline_updated_at) return '';
  return new Intl.DateTimeFormat(undefined, {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'}).format(new Date(page.baseline_updated_at));
}

function renderReviewStatus(page) {
  const stale = state.staleBaseline?.pageId === page.page_id;
  const summary = stale
    ? `${page.view} · Baseline changed`
    : [page.view, reviewStageLabel(page), shortBaselineDate(page), issueCountLabel(page)].filter(Boolean).join(' · ');
  const fullDate = page.baseline_updated_at ? new Date(page.baseline_updated_at).toLocaleString() : 'Not available';
  const commit = page.baseline_commit || state.corpus.commit;
  const commitLink = commit ? `https://github.com/${state.corpus.repository}/commit/${commit}` : null;
  const changedLines = page.corrections.distinct_lines || 0;
  $('#page-badges').innerHTML = `<details class="review-status ${stale ? 'stale' : ''}"><summary>${escapeHTML(summary)}</summary><div class="review-status-details"><dl><div><dt>Review stage</dt><dd>${escapeHTML(reviewStageLabel(page))}</dd></div><div><dt>Baseline updated</dt><dd>${escapeHTML(fullDate)}</dd></div><div><dt>Baseline commit</dt><dd>${commitLink ? `<a href="${commitLink}" target="_blank" rel="noreferrer"><code>${escapeHTML(commit.slice(0, 7))}</code></a>` : 'Not available'}</dd></div><div><dt>Human corrections</dt><dd>${escapeHTML(issueCountLabel(page))} · ${changedLines} corrected line${changedLines === 1 ? '' : 's'}</dd></div></dl>${stale ? '<p>A newer transcription for this page is available. Reload to rebase locally saved edits onto it.</p><button type="button" data-action="reload-baseline">Reload current baseline</button>' : ''}</div></details>`;
}

async function checkCorpusFreshness() {
  if (!state.corpus || !state.currentPage) return true;
  try {
    const response = await fetch(`corpus.json?fresh=${Date.now()}`, {cache: 'no-store'});
    if (!response.ok) return true;
    const latest = await response.json();
    if (latest.commit === state.corpus.commit) return true;
    const latestPage = latest.pages.find(page => page.page_id === state.currentPage.page_id);
    if (latestPage?.transcription_version !== state.currentPage.transcription_version) {
      state.staleBaseline = {pageId: state.currentPage.page_id, commit: latest.commit};
      renderReviewStatus(state.currentPage);
      return false;
    }
    state.currentPage.corrections = latestPage?.corrections || state.currentPage.corrections;
    state.staleBaseline = null;
    renderReviewStatus(state.currentPage);
    return true;
  } catch (_) {
    return true;
  }
}

function pageStateLabel(page) {
  if (page.data_state === 'machine_provisional') {
    return page.structural_review_required ? 'OCR provisional · structural review' : 'OCR provisional';
  }
  if (page.data_state === 'canonical_level1' || page.processed) return 'Level 1 transcription';
  return 'Unprocessed';
}

function pageStateClass(page) {
  if (page.data_state === 'machine_provisional') return 'provisional';
  if (page.data_state === 'canonical_level1' || page.processed) return 'good';
  return '';
}

function renderGrid() {
  renderBatchControls();
  const filter = $('#filter').value;
  const sort = $('#sort').value;
  let pages = state.corpus.pages.filter(page => filter === 'all'
    || (filter === 'processed' && page.processed)
    || (filter === 'canonical' && page.data_state === 'canonical_level1')
    || (filter === 'provisional' && page.data_state === 'machine_provisional')
    || (filter === 'quarantine' && page.structural_review_required)
    || (filter === 'unprocessed' && !page.processed)
    || (filter === 'corrected' && page.corrections.issues_applied));
  if (sort === 'recent') pages.sort((a, b) => String(b.corrections.last_applied || '').localeCompare(String(a.corrections.last_applied || '')) || a.leaf - b.leaf);
  $('#page-grid').innerHTML = pages.map(page => `<button class="page-card ${pageStateClass(page)}" type="button" data-leaf="${page.leaf}"><img loading="lazy" src="${page.thumbnail}" alt="Thumbnail of Gallica ${page.view}"><span class="card-copy"><span class="card-title">${page.view}${page.corrections.issues_applied ? `<span class="mini-badge">${page.corrections.issues_applied} issue${page.corrections.issues_applied === 1 ? '' : 's'}</span>` : ''}</span><span class="card-state">${pageStateLabel(page)}${page.corrections.distinct_lines ? ` · ${page.corrections.distinct_lines} lines corrected` : ''}</span></span></button>`).join('');
  decorateSelectionCards();
}

function decorateSelectionCards() {
  for (const card of document.querySelectorAll('#page-grid [data-leaf]')) {
    const page = state.byLeaf.get(Number(card.dataset.leaf));
    const count = savedCorrectionCount(page);
    if (selectionMode) {
      card.disabled = !count;
      card.setAttribute('aria-pressed', String(selectedLeaves.has(page.leaf)));
      card.classList.toggle('selected', selectedLeaves.has(page.leaf));
    }
    if (count) {
      const status = state.submissions[page.page_id]?.status || storageJSON(submissionStorageKey(page))?.status;
      card.querySelector('.card-copy').insertAdjacentHTML('beforeend', `<span class="card-state">${count} saved correction${count === 1 ? '' : 's'}${status === 'submitted' ? ' · Submitted' : ''}</span>`);
    }
  }
}

function storageJSON(key) {
  try { return JSON.parse(localStorage.getItem(key)); }
  catch (_) { return null; }
}

function editStorageKey(page) { return `nippo-edits:${page.page_id}`; }
function submissionStorageKey(page) { return `nippo-submission:${page.page_id}`; }

function saveWorkspace(page) {
  localStorage.setItem(editStorageKey(page), JSON.stringify({schema: WORKSPACE_SCHEMA, transcription_version: page.transcription_version, edits: state.edits[page.page_id], dismissed_suggestions: [...(state.suggestionDismissals[page.page_id] || [])]}));
  localStorage.setItem(submissionStorageKey(page), JSON.stringify({schema: WORKSPACE_SCHEMA, transcription_version: page.transcription_version, status: state.submissions[page.page_id].status}));
}

function suggestionDismissalKey(line, kind) {
  return `${line.id}:${kind}:${line.transcription_version}`;
}

function dismissMachineSuggestion(page, line, kind) {
  if (!kind) return;
  state.suggestionDismissals[page.page_id].add(suggestionDismissalKey(line, kind));
}

function seedMachineSuggestions(page) {
  const edits = state.edits[page.page_id];
  const dismissed = state.suggestionDismissals[page.page_id];
  for (const line of page.zones.flatMap(zone => zone.lines)) {
    if (edits[line.id]) continue;
    for (const kind of line.machine_suggestions || []) {
      if (dismissed.has(suggestionDismissalKey(line, kind))) continue;
      if (kind === 'ocr_terminal_hyphen' && line.text.endsWith('-')) {
        edits[line.id] = {
          before: line.text,
          after: line.text.slice(0, -1),
          note_before: line.note || '',
          note_after: line.note || '',
          message: '',
          base_line_version: line.transcription_version,
          machine_suggestion: kind,
        };
      }
    }
  }
}

function staleDraftPayload(stale) {
  const changes = Object.entries(stale.edits).map(([line, edit]) => ({line, before: edit.before, after: edit.after, note_before: edit.note_before || '', note_after: edit.note_after || '', ...(edit.message || edit.comment ? {message: edit.message || edit.comment} : {})}));
  return JSON.stringify({schema: 3, page: stale.page.view, base_transcription_version: stale.version, changes}, null, 2);
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
    const rebasedEdit = {...edit};
    delete rebasedEdit.nasal_restorations;
    const reviewFlags = {
      base_line_version: line.transcription_version,
      base_changed: true,
      ...(edit.note_after !== undefined || edit.message || edit.comment ? {comment_review_needed: true} : {}),
    };
    if (proposalMatchesLine(line, edit.after)) {
      if (edit.note_after !== undefined || edit.message || edit.comment) reconciled[lineId] = {...rebasedEdit, before: line.text, after: line.text, note_before: line.note || '', ...reviewFlags};
      continue;
    }
    const proposal = parseTypefaceNotation(edit.after);
    if (proposal.valid && edit.before === proposal.text && proposal.romanRanges.length === 0 && proposal.italicRanges.length === 0) {
      if (edit.note_after !== undefined || edit.message || edit.comment) reconciled[lineId] = {...rebasedEdit, before: line.text, after: line.text, note_before: line.note || '', ...reviewFlags};
      continue;
    }
    reconciled[lineId] = {...rebasedEdit, before: line.text, ...reviewFlags};
  }
  return {reconciled, orphaned};
}

function loadPageWorkspace(page) {
  if (state.workspacesLoaded.has(page.page_id)) return;
  const storedEdits = storageJSON(editStorageKey(page));
  const storedSubmission = storageJSON(submissionStorageKey(page));
  const isEnvelope = storedEdits?.schema >= 2 && storedEdits.edits && typeof storedEdits.edits === 'object';
  const edits = isEnvelope ? storedEdits.edits : (storedEdits && typeof storedEdits === 'object' ? storedEdits : {});
  for (const edit of Object.values(edits)) {
    if (edit.message === undefined && edit.comment) edit.message = edit.comment;
    if (edit.note_before === undefined) edit.note_before = '';
    if (edit.note_after === undefined) edit.note_after = edit.note_before;
    delete edit.comment;
    delete edit.second_opinion;
    delete edit.second_opinion_manual;
  }
  const status = storedSubmission?.status || 'draft';
  const storedVersion = isEnvelope ? storedEdits.transcription_version : page.transcription_version;
  const versionChanged = Boolean(storedVersion && page.transcription_version && storedVersion !== page.transcription_version);
  state.edits[page.page_id] = edits;
  state.suggestionDismissals[page.page_id] = new Set(
    isEnvelope && Array.isArray(storedEdits.dismissed_suggestions)
      ? storedEdits.dismissed_suggestions
      : []
  );
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
      seedMachineSuggestions(page);
      state.staleDraft = {page, version: storedVersion, edits: orphaned};
      queueMicrotask(showStaleDraftWarning);
      return;
    }
    seedMachineSuggestions(page);
    saveWorkspace(page);
    return;
  }
  const lines = pageLineMap(page);
  for (const [lineId, edit] of Object.entries(edits)) {
    const line = lines.get(lineId);
    if (line && !edit.base_line_version && edit.before === line.text) edit.base_line_version = line.transcription_version;
  }
  seedMachineSuggestions(page);
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
  $('#page-meta').textContent = page.data_state === 'machine_provisional'
    ? `${page.page_id} · machine-provisional OCR · physical lineation not yet checked`
    : page.processed ? `${page.page_id} · Level 1 ${page.status.replaceAll('_', ' ')}` : `${page.page_id} · transcription not yet processed`;
  renderReviewStatus(page);
  const notice = $('#provisional-notice');
  notice.classList.toggle('hidden', page.data_state !== 'machine_provisional');
  if (page.data_state === 'machine_provisional') {
    const detail = page.structural_review_required
      ? ` This page is structurally quarantined: ${(page.provisional_reasons || []).map(reason => escapeHTML(reason)).join('; ') || 'its line structure needs direct review'}.`
      : ' Its rows, crops, typefaces, and text still require direct comparison with the scan.';
    notice.innerHTML = `<strong>Machine-provisional candidate.</strong> This is editable review material, not canonical Level 1 data.${detail}`;
  }
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

function kanaGuideHTML(line) {
  if (line.reading_hint_status === 'not_applicable') return '';
  const hint = line.reading_hint || 'Automatic reading unavailable';
  return `<div class="kana-guide ${line.reading_hint ? '' : 'unavailable'}" aria-label="Automatic kana guide"><span>Automatic reading</span>${escapeHTML(hint)}</div>`;
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
  return zonesFor(page, unit).map(zone => `<section><h3>${escapeHTML(zone.label)}</h3>${zone.lines.map(line => `<div class="continuous-line indent-${line.indent}"><span class="line-reference"><code class="line-id">${escapeHTML(line.id)}</code><button class="copy-line-reference" type="button" data-copy-line-reference="${escapeHTML(`${page.view}/${line.id}`)}" title="Copy ${escapeHTML(`${page.view}/${line.id}`)}" aria-label="Copy full line reference">⧉</button></span><span>${renderRuns(line.runs)}</span></div>`).join('')}</section>`).join('');
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
    $('#page-content').innerHTML = `<div class="page-comparison">${scanPane(page)}<section class="text-pane"><div class="pane-toolbar"><strong>${pageStateLabel(page)}</strong>${page.source ? `<a class="push" href="${page.source}" target="_blank" rel="noreferrer">${escapeHTML(page.source_label || 'Source data')}</a>` : ''}</div><div class="continuous-text">${continuousHTML(page, state.unit)}</div></section></div>`;
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

function lineById(lineId) {
  return state.currentPage.zones.filter(item => item.kind === 'column').flatMap(item => item.lines).find(item => item.id === lineId);
}

function originalTypefaces(line) {
  return line.runs.flatMap(run => Array.from(run.text).map(() => run.typeface));
}

function quickCharacterHTML(character, index, baseIndex, changed, line, proposal, typefaces, nasalRestoration) {
  const original = baseIndex === null ? character : line.text[baseIndex];
  const originalTypeface = baseIndex === null ? (typefaces[Math.max(0, index - 1)] || 'roman') : (typefaces[baseIndex] || 'roman');
  const explicitTypeface = proposal.characters[index].style;
  const typeface = explicitTypeface || originalTypeface;
  let action = '';
  let title = '';
  let extraAttributes = '';
  const markedToken = NippoQuickEdit.knownTypefaceTokenRange(proposal.text, index, new Set(line.typeface_toggle_terms || []));
  const typefaceToken = markedToken || NippoQuickEdit.typefaceTokenRange(proposal.text, index);
  if (nasalRestoration) {
    action = 'nasal-restore';
    title = `Restore ${nasalRestoration.vowel}${nasalRestoration.consonant}`;
  } else if (typefaceToken) {
    action = 'typeface-token';
    title = 'Toggle this token between Roman and italic type';
    extraAttributes = ` data-token-start="${typefaceToken.start}" data-token-end="${typefaceToken.end}"`;
  } else if (/[sſf]/u.test(character) && /[sſf]/u.test(original)) {
    action = 's-form';
    title = 'Cycle s, long s, and f readings';
  } else if (/[gq]/iu.test(character) && /[gq]/iu.test(original)) {
    action = 'gq-form';
    title = 'Toggle g and q readings';
  } else if (/[nm]/u.test(character) && /[nm]/u.test(original)) {
    action = 'nm-form';
    const previous = proposal.characters[index - 1]?.character || '';
    const next = proposal.characters[index + 1]?.character || '';
    title = NippoQuickEdit.nextPostvocalicNasal(character, original, previous, next).kind === 'contract'
      ? 'Replace the preceding vowel and this consonant with a nasalized vowel'
      : 'Cycle lowercase n, m, and a contextual nasal abbreviation';
  } else if (/[cç]/u.test(character) && /[cç]/u.test(original)) {
    action = 'cedilla-form';
    title = 'Toggle lowercase c and ç readings';
  } else if (/[uv]/u.test(original) && ['u', 'v', 'ũ', 'ù', 'ú', 'û', 'ǔ'].includes(character)) {
    action = 'uv-form';
    title = 'Cycle lowercase u, v, and accented u readings';
  } else if (/[ij]/u.test(original) && ['i', 'j', 'ĩ', 'ì', 'í', 'î'].includes(character)) {
    action = 'ij-form';
    title = 'Cycle lowercase i, j, and accented i readings';
  } else if (NippoQuickEdit.VOWEL_CYCLES.some(cycle => cycle.includes(character.toLocaleLowerCase('und')))) {
    action = 'vowel';
    title = 'Cycle accent and tilde forms';
  } else if (NippoQuickEdit.DELETABLE.has(character)) {
    action = 'delete';
    title = character === ' ' ? 'Remove this space' : `Remove ${character}`;
  }
  const classes = ['quick-character'];
  if (action) classes.push('quick-action');
  if (changed || (explicitTypeface && explicitTypeface !== originalTypeface)) classes.push('quick-changed');
  const restorationAttributes = nasalRestoration ? ` data-nasal-vowel="${escapeHTML(nasalRestoration.vowel)}" data-nasal-consonant="${escapeHTML(nasalRestoration.consonant)}"` : '';
  const attributes = action ? ` role="button" tabindex="0" data-quick-action="${action}" data-index="${index}" data-original="${escapeHTML(original)}"${restorationAttributes}${extraAttributes} title="${escapeHTML(title)}"` : '';
  let output = escapeHTML(character);
  if (character === ' ') output = '<span class="quick-space"> </span>';
  if (typeface === 'italic') output = `<em>${output}</em>`;
  else if (typeface === 'display') output = `<strong>${output}</strong>`;
  return `<span class="${classes.join(' ')}"${attributes}>${output}</span>`;
}

function quickDeletedHTML(deletion, machineSuggestion, line) {
  if (!NippoQuickEdit.DELETABLE.has(deletion.character)) return '<span class="quick-omission" aria-label="Deleted text">∅</span>';
  const label = deletion.character === ' ' ? '␠' : deletion.character;
  const name = deletion.character === ' ' ? 'space' : deletion.character;
  const suggested = machineSuggestion === 'ocr_terminal_hyphen'
    && deletion.character === '-'
    && deletion.beforeIndex === line.text.length - 1;
  const classes = `quick-deleted${suggested ? ' quick-suggested' : ''}`;
  const title = suggested ? 'Restore hyphen · OCR suggested that no mark is printed' : `Restore ${name}`;
  return `<span class="${classes}" role="button" tabindex="0" data-quick-action="restore" data-index="${deletion.currentIndex}" data-character="${escapeHTML(deletion.character)}" title="${escapeHTML(title)}" aria-label="Restore deleted ${escapeHTML(name)}">${escapeHTML(label)}</span>`;
}

function interactiveLineHTML(line, annotatedText, nasalRestorations = [], machineSuggestion = null) {
  const proposal = NippoQuickEdit.parse(annotatedText);
  if (!proposal.valid) return styledVisualDiff(line, annotatedText);
  const alignment = NippoQuickEdit.align(line.text, proposal.text);
  const typefaces = originalTypefaces(line);
  const restorations = new Map(nasalRestorations.map(item => [item.index, item]));
  const deletions = new Map();
  for (const deletion of alignment.deletions) {
    if (!deletions.has(deletion.currentIndex)) deletions.set(deletion.currentIndex, []);
    deletions.get(deletion.currentIndex).push(deletion);
  }
  let output = '';
  for (let index = 0; index <= proposal.characters.length; index++) {
    output += (deletions.get(index) || []).map(deletion => quickDeletedHTML(deletion, machineSuggestion, line)).join('');
    if (index < proposal.characters.length) {
      output += quickCharacterHTML(proposal.characters[index].character, index, alignment.currentToBase[index], alignment.changed[index], line, proposal, typefaces, restorations.get(index));
    }
  }
  return output;
}

function lineHTML(page, line) {
  const edit = pageEdits(page)[line.id];
  const current = edit ? edit.after : line.text;
  const note = edit?.note_after ?? line.note ?? '';
  const message = edit?.message || '';
  const markers = `${edit?.machine_suggestion === 'ocr_terminal_hyphen' ? '<span class="review-marker suggestion-marker">OCR: no hyphen</span>' : ''}${edit?.base_changed ? '<span class="review-marker">Base updated</span>' : ''}${edit?.comment_review_needed ? '<span class="review-marker comment-marker">Note needs review</span>' : ''}${message ? '<span class="review-marker opinion-marker">Message to AI</span>' : ''}`;
  const reference = `${page.view}/${line.id}`;
  const annotations = `${note ? `<button class="annotation-preview comment-preview" type="button" data-action="edit" title="${escapeHTML(note)}"><span>Comment</span>${escapeHTML(note)}</button>` : ''}${message ? `<button class="annotation-preview message-preview" type="button" data-action="edit" title="${escapeHTML(message)}"><span>Message to AI</span>${escapeHTML(message)}</button>` : ''}`;
  return `<article class="line-row ${edit ? 'changed' : ''} ${edit?.machine_suggestion ? 'suggested' : ''} ${edit?.base_changed ? 'rebased' : ''}" data-line="${line.id}"><div class="line-head"><code>${line.id}</code><button class="copy-line-reference" type="button" data-copy-line-reference="${escapeHTML(reference)}" title="Copy ${escapeHTML(reference)}" aria-label="Copy full line reference">⧉</button>${markers}<button class="context-toggle" type="button" aria-expanded="false">Show context</button></div><button class="line-crop" type="button" style="aspect-ratio:${line.crop[2]}/${line.crop[3]}" data-crop='${JSON.stringify(line.crop)}' data-context='${JSON.stringify(line.context_crop)}' aria-label="Show context for ${line.id}"><img loading="lazy" data-iiif-page alt="" style="width:${page.width / line.crop[2] * 100}%;transform:translate(${-line.crop[0] / page.width * 100}% ,${-line.crop[1] / page.height * 100}%)"></button><div class="line-text-row" title="Click beside the text for the full editor"><div class="line-transcription"><div class="line-text indent-${line.indent}">${interactiveLineHTML(line, current, edit?.nasal_restorations, edit?.machine_suggestion)}</div>${kanaGuideHTML(line)}</div>${annotations ? `<div class="line-annotations">${annotations}</div>` : ''}</div></article>`;
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
  const line = lineById(row.dataset.line);
  const after = form.elements.transcription.value;
  const noteAfter = form.elements.note.value.trim();
  const message = form.elements.message.value.trim();
  const proposal = parseTypefaceNotation(after);
  if (!proposal.valid) {
    toast(proposal.error);
    form.elements.transcription.focus();
    return false;
  }
  const existing = pageEdits(state.currentPage)[line.id];
  const nasalRestorations = existing?.after === after ? existing.nasal_restorations : undefined;
  const matchesLine = proposalMatchesLine(line, after);
  if (matchesLine) dismissMachineSuggestion(state.currentPage, line, existing?.machine_suggestion);
  const noteBefore = line.note || '';
  if (matchesLine && noteAfter === noteBefore && !message) delete pageEdits(state.currentPage)[line.id];
  else pageEdits(state.currentPage)[line.id] = {before: line.text, after, note_before: noteBefore, note_after: noteAfter, message, base_line_version: line.transcription_version, ...(!matchesLine && existing?.machine_suggestion ? {machine_suggestion: existing.machine_suggestion} : {}), ...(nasalRestorations?.length ? {nasal_restorations: nasalRestorations} : {})};
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
  const line = lineById(lineId);
  const edit = pageEdits(state.currentPage)[lineId];
  row.insertAdjacentHTML('beforeend', `<form class="edit-form"><div class="transcription-editor"><textarea name="transcription" aria-label="Revised transcription">${escapeHTML(edit?.after || line.text)}</textarea>${paletteHTML()}</div><div class="comment-editor"><textarea name="note" aria-label="Durable note" placeholder="Durable line note">${escapeHTML(edit?.note_after ?? line.note ?? '')}</textarea><textarea name="message" aria-label="Message to AI" placeholder="Message to AI (always reviewed)">${escapeHTML(edit?.message || '')}</textarea></div><div class="edit-actions"><button type="button" data-action="cancel">Cancel</button>${edit ? '<button type="button" data-action="revert">Revert</button>' : ''}<button class="primary" type="submit">OK</button></div></form>`);
  const form = row.querySelector('.edit-form');
  row.querySelector('[name="transcription"]').focus();
}

function replaceRenderedLine(row, line) {
  row.outerHTML = lineHTML(state.currentPage, line);
  refreshPageImageUI(state.currentPage);
}

function applyQuickEdit(row, control) {
  const selection = window.getSelection?.();
  if (selection && !selection.isCollapsed) return;
  const lineId = row.dataset.line;
  const activeForm = document.querySelector('.edit-form');
  if (activeForm) {
    if (!saveEditor(activeForm)) return;
    renderPageContent();
    row = [...document.querySelectorAll('.line-row')].find(candidate => candidate.dataset.line === lineId);
    if (!row) return;
  }
  const line = lineById(lineId);
  const existing = pageEdits(state.currentPage)[lineId];
  const current = existing?.after || line.text;
  const index = Number(control.dataset.index);
  const action = control.dataset.quickAction;
  let after = current;
  let nasalRestorations = (existing?.nasal_restorations || []).map(item => ({...item}));
  const shiftNasalRestorations = (start, removed, inserted) => {
    const end = start + removed;
    const delta = inserted - removed;
    nasalRestorations = nasalRestorations.flatMap(item => {
      if (start <= item.index && item.index < end) return [];
      return [{...item, index: item.index >= end ? item.index + delta : item.index}];
    });
  };
  if (action === 's-form') {
    const parsed = NippoQuickEdit.parse(current);
    const character = parsed.characters[index]?.character;
    after = NippoQuickEdit.replace(current, index, index + 1, NippoQuickEdit.nextSForm(character, control.dataset.original));
  } else if (action === 'gq-form') {
    const parsed = NippoQuickEdit.parse(current);
    const character = parsed.characters[index]?.character;
    after = NippoQuickEdit.replace(current, index, index + 1, NippoQuickEdit.nextGQ(character));
  } else if (action === 'nm-form') {
    const parsed = NippoQuickEdit.parse(current);
    const character = parsed.characters[index]?.character;
    const previous = parsed.characters[index - 1]?.character || '';
    const next = parsed.characters[index + 1]?.character || '';
    const result = NippoQuickEdit.nextPostvocalicNasal(character, control.dataset.original, previous, next);
    if (result.kind === 'contract') {
      after = NippoQuickEdit.replace(current, index - 1, index + 1, result.value);
      shiftNasalRestorations(index - 1, 2, 1);
      nasalRestorations.push({index: index - 1, vowel: previous, consonant: control.dataset.original});
    } else {
      after = NippoQuickEdit.replace(current, index, index + 1, result.value);
    }
  } else if (action === 'cedilla-form') {
    const parsed = NippoQuickEdit.parse(current);
    const character = parsed.characters[index]?.character;
    after = NippoQuickEdit.replace(current, index, index + 1, NippoQuickEdit.nextCedilla(character));
  } else if (action === 'uv-form') {
    const parsed = NippoQuickEdit.parse(current);
    const character = parsed.characters[index]?.character;
    after = NippoQuickEdit.replace(current, index, index + 1, NippoQuickEdit.nextUV(character, control.dataset.original));
  } else if (action === 'ij-form') {
    const parsed = NippoQuickEdit.parse(current);
    const character = parsed.characters[index]?.character;
    after = NippoQuickEdit.replace(current, index, index + 1, NippoQuickEdit.nextIJ(character, control.dataset.original));
  } else if (action === 'vowel') {
    const parsed = NippoQuickEdit.parse(current);
    const character = parsed.characters[index]?.character;
    after = NippoQuickEdit.replace(current, index, index + 1, NippoQuickEdit.nextVowel(character, control.dataset.original));
  } else if (action === 'typeface-token') {
    const parsed = NippoQuickEdit.parse(current);
    const alignment = NippoQuickEdit.align(line.text, parsed.text);
    const typefaces = originalTypefaces(line);
    const proposalTypefaces = alignment.currentToBase.map((baseIndex, proposalIndex) => {
      if (baseIndex !== null) return typefaces[baseIndex] || 'roman';
      const previousBase = alignment.currentToBase[proposalIndex - 1];
      const nextBase = alignment.currentToBase.slice(proposalIndex + 1).find(candidate => candidate !== null);
      return typefaces[previousBase ?? nextBase] || 'roman';
    });
    after = NippoQuickEdit.toggleTypefaceRange(current, Number(control.dataset.tokenStart), Number(control.dataset.tokenEnd), proposalTypefaces);
  } else if (action === 'delete') {
    after = NippoQuickEdit.replace(current, index, index + 1, '');
    shiftNasalRestorations(index, 1, 0);
  } else if (action === 'restore') {
    after = NippoQuickEdit.replace(current, index, index, control.dataset.character, null);
    shiftNasalRestorations(index, 0, 1);
  } else if (action === 'nasal-restore') {
    after = NippoQuickEdit.replace(current, index, index + 1, control.dataset.nasalVowel + control.dataset.nasalConsonant);
    shiftNasalRestorations(index, 1, 2);
  }
  if (after === current) return;
  const noteBefore = line.note || '';
  const noteAfter = existing?.note_after ?? noteBefore;
  const message = existing?.message || '';
  if (proposalMatchesLine(line, after) && noteAfter === noteBefore && !message) {
    dismissMachineSuggestion(state.currentPage, line, existing?.machine_suggestion);
    delete pageEdits(state.currentPage)[lineId];
  } else {
    pageEdits(state.currentPage)[lineId] = {
      ...existing,
      before: line.text,
      after,
      note_before: noteBefore,
      note_after: noteAfter,
      message,
      base_line_version: line.transcription_version,
      nasal_restorations: nasalRestorations.length ? nasalRestorations : undefined,
    };
  }
  persistEdits(state.currentPage);
  replaceRenderedLine(row, line);
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) try { await navigator.clipboard.writeText(text); return true; } catch (_) {}
  const area = document.createElement('textarea'); area.value = text; area.style.position = 'fixed'; area.style.opacity = '0'; document.body.appendChild(area); area.select(); const ok = document.execCommand('copy'); area.remove(); return ok;
}

async function copyLineReference(control) {
  const reference = control.dataset.copyLineReference;
  if (await copyText(reference)) toast(`Copied ${reference}`);
  else prompt('Copy this line reference:', reference);
}

function correctionPayload(page) {
  const changes = Object.entries(pageEdits(page)).map(([line, edit]) => ({ line, before: edit.before, after: edit.after, note_before: edit.note_before || '', note_after: edit.note_after || '', ...(edit.message ? {message: edit.message} : {}) }));
  return {schema: 3, page: page.view, base_commit: state.corpus.commit, base_transcription_version: page.transcription_version, changes};
}

async function submitSelectedPages() {
  const pages = [...selectedLeaves].sort((a, b) => a - b).map(leaf => state.byLeaf.get(leaf));
  if (!pages.length) return;
  const issueWindow = window.open('about:blank', '_blank');
  try {
    const response = await fetch(`corpus.json?fresh=${Date.now()}`, {cache: 'no-store'});
    if (!response.ok) throw new Error('Could not check the current baseline. Please try again.');
    const latest = await response.json();
    const stale = pages.filter(page => latest.pages.find(p => p.page_id === page.page_id)?.transcription_version !== page.transcription_version);
    if (stale.length) throw new Error(`Newer data for ${stale.map(p => p.view).join(', ')}. Reload and review those pages before submitting.`);
    for (const page of pages) {
      const stored = storageJSON(editStorageKey(page));
      if (stored?.transcription_version && stored.transcription_version !== page.transcription_version) throw new Error(`Open ${page.view} to review its updated baseline before submitting.`);
    }
    const records = pages.map(correctionPayload);
    if (records.some(record => !record.changes.length)) throw new Error('A selected page has no saved corrections. Please select again.');
    const payload = JSON.stringify({schema: 4, pages: records}, null, 2);
    const title = pages.length <= 8 ? `[${pages.map(p => p.view).join(', ')}] Transcription corrections` : `[${pages[0].view}–${pages.at(-1).view}, ${pages.length} pages] Transcription corrections`;
    const url = `https://github.com/${state.corpus.repository}/issues/new?template=transcription-correction.md&title=${encodeURIComponent(title)}`;
    const copied = await copyText(payload);
    if (!copied) prompt('Copy this correction JSON, then paste it into the Issue:', payload);
    for (const page of pages) persistSubmission(page, 'awaiting');
    localStorage.setItem('nippo-batch-awaiting', JSON.stringify(pages.map(p => p.leaf)));
    if (issueWindow) issueWindow.location = url; else window.location.href = url;
    selectionMode = false;
    selectedLeaves.clear();
    renderGrid();
    toast('Combined correction JSON copied. Paste it into the Issue.');
  } catch (error) {
    if (issueWindow) issueWindow.close();
    alert(error.message);
  }
}

async function submitCorrections() {
  const page = state.currentPage;
  if (!await checkCorpusFreshness()) {
    toast('This page has a newer baseline. Reload it before submitting.');
    return;
  }
  const changes = Object.entries(pageEdits(page)).map(([line, edit]) => ({ line, before: edit.before, after: edit.after, note_before: edit.note_before || '', note_after: edit.note_after || '', ...(edit.message ? {message: edit.message} : {}) }));
  const payload = JSON.stringify({ schema: 3, page: page.view, base_commit: state.corpus.commit, base_transcription_version: page.transcription_version, changes }, null, 2);
  const issueURL = `https://github.com/${state.corpus.repository}/issues/new?template=transcription-correction.md&title=${encodeURIComponent(`[${page.view}] Transcription corrections`)}`;
  const issueWindow = window.open('about:blank', '_blank');
  const copied = await copyText(payload);
  persistSubmission(page, 'awaiting');
  if (issueWindow) issueWindow.location = issueURL; else window.location.href = issueURL;
  if (copied) toast('Correction JSON copied. Paste it into the Issue.');
  else { prompt('Copy this correction JSON, then paste it into the Issue:', payload); toast('Clipboard unavailable; the payload was displayed.'); }
}

document.addEventListener('click', event => {
  if (event.target.closest('[data-action="reload-baseline"]')) return window.location.reload();
  if (event.target.closest('[data-action="retry-preview"]')) return updatePageImages(state.currentPage.leaf);
  if (event.target.closest('[data-action="retry-hd"]')) return queueHD(state.currentPage, false);
  const card = event.target.closest('.page-card');
  if (card) {
    const leaf = Number(card.dataset.leaf);
    if (!selectionMode) return showPage(leaf);
    if (selectedLeaves.has(leaf)) selectedLeaves.delete(leaf);
    else selectedLeaves.add(leaf);
    renderGrid();
    return;
  }
  const tab = event.target.closest('#view-tabs button[data-unit]'); if (tab) return showPage(state.currentPage.leaf, tab.dataset.unit);
  const columnButton = event.target.closest('[data-column-leaf][data-column-unit]');
  if (columnButton) { showPage(Number(columnButton.dataset.columnLeaf), columnButton.dataset.columnUnit); window.scrollTo(0, 0); return; }
  const referenceButton = event.target.closest('[data-copy-line-reference]');
  if (referenceButton) { void copyLineReference(referenceButton); return; }
  const row = event.target.closest('.line-row');
  if (row) {
    const characterButton = event.target.closest('[data-character-key]');
    if (characterButton) return useTranscriptionKey(row.querySelector('.edit-form'), characterButton.dataset.characterKey);
    const typefaceButton = event.target.closest('[data-action="typeface-span"]');
    if (typefaceButton) return applyTypefaceSpan(row.querySelector('textarea[name="transcription"]'), typefaceButton.dataset.typeface);
    if (event.target.closest('.context-toggle,.line-crop')) { const button = row.querySelector('.context-toggle'); const expanded = button.getAttribute('aria-expanded') !== 'true'; button.setAttribute('aria-expanded', String(expanded)); button.textContent = expanded ? 'Hide context' : 'Show context'; setCrop(row, expanded); return; }
    const quickControl = event.target.closest('[data-quick-action]');
    if (quickControl) return applyQuickEdit(row, quickControl);
    if (event.target.closest('[data-action="edit"]')) return openEditor(row);
    if (event.target.closest('.line-text-row') && !event.target.closest('.line-text > *')) return openEditor(row);
    if (event.target.closest('[data-action="cancel"]')) { row.querySelector('.edit-form').remove(); return; }
    if (event.target.closest('[data-action="revert"]')) { const line = lineById(row.dataset.line); const edit = pageEdits(state.currentPage)[row.dataset.line]; dismissMachineSuggestion(state.currentPage, line, edit?.machine_suggestion); delete pageEdits(state.currentPage)[row.dataset.line]; persistEdits(state.currentPage); renderPageContent(); return; }
  }
});

document.addEventListener('keydown', event => {
  const quickControl = event.target.closest('[data-quick-action]');
  if (quickControl && (event.key === 'Enter' || event.key === ' ')) {
    event.preventDefault();
    return applyQuickEdit(quickControl.closest('.line-row'), quickControl);
  }
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
$('#discard-all').addEventListener('click', () => { if (!confirm('Discard all proposed corrections for this page?')) return; for (const [lineId, edit] of Object.entries(pageEdits(state.currentPage))) dismissMachineSuggestion(state.currentPage, lineById(lineId), edit.machine_suggestion); state.edits[state.currentPage.page_id] = {}; persistSubmission(state.currentPage, 'draft'); persistEdits(state.currentPage, true); renderPageContent(); });
$('#submit').addEventListener('click', submitCorrections);
$('#selection-toggle').addEventListener('click', () => { selectionMode = !selectionMode; selectedLeaves.clear(); renderGrid(); });
$('#submit-selected').addEventListener('click', submitSelectedPages);
for (const [id, status] of [['batch-submitted', 'submitted'], ['batch-not-yet', 'draft']]) {
  $(`#${id}`).addEventListener('click', () => {
    for (const leaf of storageJSON('nippo-batch-awaiting') || []) {
      const page = state.byLeaf.get(leaf);
      if (page && pageSubmission(page).status === 'awaiting') persistSubmission(page, status);
    }
    localStorage.removeItem('nippo-batch-awaiting');
    renderGrid();
  });
}
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
// The navigation wraps on tablets and changes height when a page is opened.
// Keep the floating baseline timestamp below it, including after rotation.
function updateTopbarHeight() {
  const height = document.querySelector('.topbar').getBoundingClientRect().height;
  document.documentElement.style.setProperty('--topbar-height', `${height}px`);
}
updateTopbarHeight();
if ('ResizeObserver' in window) {
  new ResizeObserver(updateTopbarHeight).observe(document.querySelector('.topbar'));
}
window.addEventListener('resize', updateTopbarHeight);
window.addEventListener('popstate', route);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && state.currentPage) void checkCorpusFreshness();
});

fetch(`corpus.json?fresh=${Date.now()}`, {cache: 'no-store'}).then(response => { if (!response.ok) throw new Error('Could not load corpus'); return response.json(); }).then(corpus => {
  state.corpus = corpus; state.byLeaf = new Map(corpus.pages.map(page => [page.leaf, page]));
  const canonical = corpus.pages.filter(page => page.data_state === 'canonical_level1').length;
  const provisional = corpus.pages.filter(page => page.data_state === 'machine_provisional').length;
  const scanOnly = corpus.pages.filter(page => !page.processed).length;
  const corrected = corpus.pages.filter(page => page.corrections.issues_applied).length;
  $('#summary').innerHTML = `<div><strong>${canonical}</strong><span>canonical Level 1</span></div><div><strong>${provisional}</strong><span>OCR provisional</span></div><div><strong>${scanOnly}</strong><span>scan only</span></div><div><strong>${corrected}</strong><span>with applied Issues</span></div>`;
  $('#repository-link').href = `https://github.com/${corpus.repository}`; $('#reference-version').textContent = `Reference ${corpus.reference_version}`; $('#reference-frame').src = 'reference/cheat-sheet.html'; route();
}).catch(error => { $('#page-grid').innerHTML = `<p>${escapeHTML(error.message)}</p>`; });
