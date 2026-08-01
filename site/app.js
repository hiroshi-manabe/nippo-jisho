const state = { corpus: null, byLeaf: new Map(), currentPage: null, unit: 'page', edits: {} };
const pageImageCache = new Map();
const PAGE_IMAGE_CACHE_RADIUS = 2;
let imagePreloadGeneration = 0;
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));

function retainPageImage(page, priority = 'low') {
  let entry = pageImageCache.get(page.leaf);
  if (entry) {
    if (priority === 'high') entry.image.fetchPriority = 'high';
    return entry;
  }
  const image = new Image();
  image.decoding = 'async';
  image.fetchPriority = priority;
  const ready = new Promise(resolve => {
    image.addEventListener('load', () => resolve(true), {once: true});
    image.addEventListener('error', () => resolve(false), {once: true});
  });
  entry = {image, ready};
  pageImageCache.set(page.leaf, entry);
  image.src = page.iiif;
  return entry;
}

function updatePageImageCache(leaf) {
  const generation = ++imagePreloadGeneration;
  const retainedLeaves = new Set();
  for (let candidate = leaf - PAGE_IMAGE_CACHE_RADIUS; candidate <= leaf + PAGE_IMAGE_CACHE_RADIUS; candidate++) {
    if (state.byLeaf.has(candidate)) retainedLeaves.add(candidate);
  }
  for (const cachedLeaf of pageImageCache.keys()) {
    if (!retainedLeaves.has(cachedLeaf)) pageImageCache.delete(cachedLeaf);
  }
  const current = retainPageImage(state.byLeaf.get(leaf), 'high');
  current.ready.then(() => {
    if (generation !== imagePreloadGeneration || state.currentPage?.leaf !== leaf) return;
    const preloadNeighbors = () => {
      if (generation !== imagePreloadGeneration || state.currentPage?.leaf !== leaf) return;
      for (let distance = 1; distance <= PAGE_IMAGE_CACHE_RADIUS; distance++) {
        for (const candidate of [leaf - distance, leaf + distance]) {
          const page = state.byLeaf.get(candidate);
          if (page) retainPageImage(page);
        }
      }
    };
    if ('requestIdleCallback' in window) requestIdleCallback(preloadNeighbors, {timeout: 1500});
    else setTimeout(preloadNeighbors, 0);
  });
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
  updatePageImageCache(leaf);
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
  return `<section class="scan-pane"><div class="pane-toolbar"><strong>Gallica scan</strong><span class="push">Loaded through IIIF</span><a href="${page.gallica}" target="_blank" rel="noreferrer">Open in Gallica</a></div><div class="scan-frame"><img src="${page.iiif}" alt="Gallica scan ${page.view}"></div></section>`;
}

function renderPageContent() {
  const page = state.currentPage;
  if (page.processed && ['column-1', 'column-2'].includes(state.unit)) {
    const lines = page.zones.filter(item => item.kind === 'column' && (item.id === state.unit || item.id.startsWith(`${state.unit}-`))).flatMap(item => item.lines);
    $('#page-content').innerHTML = `<div class="line-list">${lines.map(line => lineHTML(page, line)).join('')}</div>`;
    return;
  }
  $('#page-content').innerHTML = `<div class="page-comparison">${scanPane(page)}<section class="text-pane"><div class="pane-toolbar"><strong>${page.processed ? 'Level 1 transcription' : 'Transcription'}</strong>${page.source ? `<a class="push" href="${page.source}" target="_blank" rel="noreferrer">Source Markdown</a>` : ''}</div><div class="continuous-text">${continuousHTML(page, state.unit)}</div></section></div>`;
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
  return `<article class="line-row ${edit ? 'changed' : ''}" data-line="${line.id}"><div class="line-head"><code>${line.id}</code><button class="context-toggle" type="button" aria-expanded="false">Show context</button></div><button class="line-crop" type="button" style="aspect-ratio:${line.crop[2]}/${line.crop[3]}" data-crop='${JSON.stringify(line.crop)}' data-context='${JSON.stringify(line.context_crop)}' aria-label="Show context for ${line.id}"><img loading="lazy" src="${page.iiif}" alt="" style="width:${page.width / line.crop[2] * 100}%;transform:translate(${-line.crop[0] / page.width * 100}% ,${-line.crop[1] / page.height * 100}%)"></button><div class="line-text-row"><button class="line-text indent-${line.indent}" type="button" data-action="edit">${edit ? visualDiff(line.text, current) : renderRuns(line.runs)}</button>${comment ? `<button class="comment-preview" type="button" data-action="edit" title="${escapeHTML(comment)}">${escapeHTML(comment)}</button>` : ''}</div></article>`;
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
