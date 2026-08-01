const state = { corpus: null, byLeaf: new Map(), currentPage: null, unit: 'page', edits: {} };
const previewImageCache = new Map();
const hdImageCache = new Map();
const hdFailures = new Map();
const PREVIEW_RETRY_DELAYS = [0, 1500, 4000];
const HD_DWELL_TIME = 1200;
const HD_MIN_START_INTERVAL = 15000;
const HD_FAILURE_COOLDOWN = 60000;
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
    setScanStatus('HD loaded through IIIF');
    return;
  }
  if (previewImageCache.get(page.leaf)?.status !== 'loaded') {
    setScanStatus('Loading preview from Gallica…');
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
      setScanStatus(`Retrying Gallica preview (${attempt + 1}/${PREVIEW_RETRY_DELAYS.length})…`);
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
    setScanStatus('Gallica preview unavailable', 'preview');
    toast('The Gallica preview could not be loaded. Retry when ready.');
  }
}

function updatePageImages(leaf) {
  const generation = ++imageLoadGeneration;
  if (hdManager.candidate?.page.leaf !== leaf) clearHDCandidate();
  setScanStatus('Loading preview from Gallica…');
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

function pageEdits(page) {
  if (!state.edits[page.page_id]) {
    try { state.edits[page.page_id] = JSON.parse(localStorage.getItem(`nippo-edits:${page.page_id}`)) || {}; }
    catch (_) { state.edits[page.page_id] = {}; }
  }
  return state.edits[page.page_id];
}

function persistEdits(page) {
  localStorage.setItem(`nippo-edits:${page.page_id}`, JSON.stringify(pageEdits(page)));
  updateSubmitBar();
}

function updateSubmitBar() {
  if (!state.currentPage) return;
  const count = Object.keys(pageEdits(state.currentPage)).length;
  $('#submit-bar').classList.toggle('hidden', count === 0);
  $('#change-count').textContent = `${count} proposed line correction${count === 1 ? '' : 's'}`;
}

function showPage(leaf, unit = 'page', update = true) {
  const page = state.byLeaf.get(leaf);
  if (!page) return;
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
  if (unit === 'column-1') return page.zones.filter(zone => zone.id === 'header-column-1' || zone.id === 'column-1' || zone.id.startsWith('column-1-'));
  if (unit === 'column-2') return page.zones.filter(zone => zone.id === 'header-column-2' || zone.id === 'column-2' || zone.id.startsWith('column-2-'));
  return page.zones.filter(zone => zone.kind !== 'column');
}

function continuousHTML(page, unit) {
  if (!page.processed) return '<div class="empty"><div><strong>Not yet processed</strong><p>The Gallica scan is available now; transcription will appear here when produced.</p></div></div>';
  return zonesFor(page, unit).map(zone => `<section><h3>${escapeHTML(zone.label)}</h3>${zone.lines.map(line => `<div class="continuous-line indent-${line.indent}"><code class="line-id">${escapeHTML(line.id)}</code><span>${renderRuns(line.runs)}</span></div>`).join('')}</section>`).join('');
}

function scanPane(page) {
  return `<section class="scan-pane"><div class="pane-toolbar"><strong>Gallica scan</strong><span class="push scan-status">Loading preview from Gallica…</span><button class="preview-retry hidden" type="button" data-action="retry-preview">Retry preview</button><button class="hd-retry hidden" type="button" data-action="retry-hd">Retry HD</button><a href="${page.gallica}" target="_blank" rel="noreferrer">Open in Gallica</a></div><div class="scan-frame"><img data-iiif-page alt=""></div></section>`;
}

function lineImageStatus() {
  return `<div class="line-image-status"><span class="scan-status">Loading preview from Gallica…</span><button class="preview-retry hidden" type="button" data-action="retry-preview">Retry preview</button><button class="hd-retry hidden" type="button" data-action="retry-hd">Retry HD</button></div>`;
}

function renderPageContent() {
  const page = state.currentPage;
  if (page.processed && ['column-1', 'column-2'].includes(state.unit)) {
    const lines = page.zones.filter(item => item.kind === 'column' && (item.id === state.unit || item.id.startsWith(`${state.unit}-`))).flatMap(item => item.lines);
    $('#page-content').innerHTML = `<div class="line-list">${lineImageStatus()}${lines.map(line => lineHTML(page, line)).join('')}</div>`;
  } else {
    $('#page-content').innerHTML = `<div class="page-comparison">${scanPane(page)}<section class="text-pane"><div class="pane-toolbar"><strong>${page.processed ? 'Level 1 transcription' : 'Transcription'}</strong>${page.source ? `<a class="push" href="${page.source}" target="_blank" rel="noreferrer">Source Markdown</a>` : ''}</div><div class="continuous-text">${continuousHTML(page, state.unit)}</div></section></div>`;
  }
  refreshPageImageUI(page);
}

function cropStyle(page, crop) {
  const [x, y, width, height] = crop;
  return `--ratio:${width}/${height};--image-width:${page.width / width * 100}%;--move-x:${-x / page.width * 100}%;--move-y:${-y / page.height * 100}%`;
}

function visualDiff(before, after) {
  if (before === after) return escapeHTML(after);
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start]) start++;
  let end = 0;
  while (end < before.length - start && end < after.length - start && before[before.length - 1 - end] === after[after.length - 1 - end]) end++;
  const prefix = after.slice(0, start);
  const changed = after.slice(start, after.length - end || undefined);
  const suffix = end ? after.slice(after.length - end) : '';
  return `${escapeHTML(prefix)}<mark class="diff-added">${escapeHTML(changed || '∅')}</mark>${escapeHTML(suffix)}`;
}

function lineHTML(page, line) {
  const edit = pageEdits(page)[line.id];
  const current = edit ? edit.after : line.text;
  const comment = edit?.comment || '';
  return `<article class="line-row ${edit ? 'changed' : ''}" data-line="${line.id}"><div class="line-head"><code>${line.id}</code><button class="context-toggle" type="button" aria-expanded="false">Show context</button></div><button class="line-crop" type="button" style="aspect-ratio:${line.crop[2]}/${line.crop[3]}" data-crop='${JSON.stringify(line.crop)}' data-context='${JSON.stringify(line.context_crop)}' aria-label="Show context for ${line.id}"><img loading="lazy" data-iiif-page alt="" style="width:${page.width / line.crop[2] * 100}%;transform:translate(${-line.crop[0] / page.width * 100}% ,${-line.crop[1] / page.height * 100}%)"></button><div class="line-text-row"><button class="line-text indent-${line.indent}" type="button" data-action="edit">${edit ? visualDiff(line.text, current) : renderRuns(line.runs)}</button>${comment ? `<button class="comment-preview" type="button" data-action="edit" title="${escapeHTML(comment)}">${escapeHTML(comment)}</button>` : ''}</div></article>`;
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

function openEditor(row) {
  if (row.querySelector('.edit-form')) return;
  const lineId = row.dataset.line;
  const line = state.currentPage.zones.filter(item => item.kind === 'column').flatMap(item => item.lines).find(item => item.id === lineId);
  const edit = pageEdits(state.currentPage)[lineId];
  row.insertAdjacentHTML('beforeend', `<form class="edit-form"><textarea name="transcription" aria-label="Revised transcription">${escapeHTML(edit?.after || line.text)}</textarea><textarea name="comment" aria-label="Comment" placeholder="Optional comment">${escapeHTML(edit?.comment || '')}</textarea><div class="edit-actions"><button type="button" data-action="cancel">Cancel</button>${edit ? '<button type="button" data-action="revert">Revert</button>' : ''}<button class="primary" type="submit">OK</button></div></form>`);
  row.querySelector('[name="transcription"]').focus();
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) try { await navigator.clipboard.writeText(text); return true; } catch (_) {}
  const area = document.createElement('textarea'); area.value = text; area.style.position = 'fixed'; area.style.opacity = '0'; document.body.appendChild(area); area.select(); const ok = document.execCommand('copy'); area.remove(); return ok;
}

async function submitCorrections() {
  const page = state.currentPage;
  const changes = Object.entries(pageEdits(page)).map(([line, edit]) => ({ line, before: edit.before, after: edit.after, ...(edit.comment ? {comment: edit.comment} : {}) }));
  const payload = JSON.stringify({ schema: 1, page: page.view, base_commit: state.corpus.commit, changes }, null, 2);
  const issueURL = `https://github.com/${state.corpus.repository}/issues/new?template=transcription-correction.md&title=${encodeURIComponent(`[${page.view}] Transcription corrections`)}`;
  const issueWindow = window.open('about:blank', '_blank');
  const copied = await copyText(payload);
  if (issueWindow) issueWindow.location = issueURL; else window.location.href = issueURL;
  if (copied) toast('Correction JSON copied. Paste it into the Issue.');
  else { prompt('Copy this correction JSON, then paste it into the Issue:', payload); toast('Clipboard unavailable; the payload was displayed.'); }
}

document.addEventListener('click', event => {
  if (event.target.closest('[data-action="retry-preview"]')) return updatePageImages(state.currentPage.leaf);
  if (event.target.closest('[data-action="retry-hd"]')) return queueHD(state.currentPage, false);
  const card = event.target.closest('.page-card'); if (card) return showPage(Number(card.dataset.leaf));
  const tab = event.target.closest('#view-tabs button'); if (tab) return showPage(state.currentPage.leaf, tab.dataset.unit);
  const row = event.target.closest('.line-row');
  if (row) {
    if (event.target.closest('.context-toggle,.line-crop')) { const button = row.querySelector('.context-toggle'); const expanded = button.getAttribute('aria-expanded') !== 'true'; button.setAttribute('aria-expanded', String(expanded)); button.textContent = expanded ? 'Hide context' : 'Show context'; setCrop(row, expanded); return; }
    if (event.target.closest('[data-action="edit"]')) return openEditor(row);
    if (event.target.closest('[data-action="cancel"]')) { row.querySelector('.edit-form').remove(); return; }
    if (event.target.closest('[data-action="revert"]')) { delete pageEdits(state.currentPage)[row.dataset.line]; persistEdits(state.currentPage); renderPageContent(); return; }
  }
});

document.addEventListener('submit', event => {
  const form = event.target.closest('.edit-form'); if (!form) return;
  event.preventDefault();
  const row = form.closest('.line-row');
  const line = state.currentPage.zones.filter(item => item.kind === 'column').flatMap(item => item.lines).find(item => item.id === row.dataset.line);
  const after = form.elements.transcription.value;
  const comment = form.elements.comment.value.trim();
  if (after === line.text && !comment) delete pageEdits(state.currentPage)[line.id];
  else pageEdits(state.currentPage)[line.id] = {before: line.text, after, comment};
  persistEdits(state.currentPage); renderPageContent();
});

$('#home').addEventListener('click', () => showOverview());
$('#filter').addEventListener('change', renderGrid); $('#sort').addEventListener('change', renderGrid);
$('#previous').addEventListener('click', () => showPage(state.currentPage.leaf - 1, state.unit));
$('#next').addEventListener('click', () => showPage(state.currentPage.leaf + 1, state.unit));
function go() { const leaf = Number($('#leaf-input').value); if (state.byLeaf.has(leaf)) showPage(leaf, state.unit); }
$('#go').addEventListener('click', go); $('#leaf-input').addEventListener('keydown', event => { if (event.key === 'Enter') go(); });
$('#discard-all').addEventListener('click', () => { if (!confirm('Discard all proposed corrections for this page?')) return; state.edits[state.currentPage.page_id] = {}; persistEdits(state.currentPage); renderPageContent(); });
$('#submit').addEventListener('click', submitCorrections);

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
