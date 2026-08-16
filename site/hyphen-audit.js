const state = {data: null, selected: new Set(), images: new Map()};
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));

function candidateKey(page, candidate) { return `${page.view}/${candidate.line}`; }
function storageKey() { return `nippo-hyphen-audit:${state.data.base_commit}:${state.data.scope}`; }

function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.classList.remove('hidden');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.add('hidden'), 2200);
}

function fallbackCopy(text) {
  const area = document.createElement('textarea');
  area.value = text;
  area.style.position = 'fixed';
  area.style.opacity = '0';
  document.body.appendChild(area);
  area.select();
  const copied = document.execCommand('copy');
  area.remove();
  return copied;
}

function copyText(text) {
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text).then(() => true, () => fallbackCopy(text));
  return Promise.resolve(fallbackCopy(text));
}

function restoreSelection() {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey()));
    if (Array.isArray(saved)) state.selected = new Set(saved);
  } catch (_) {}
}

function saveSelection() {
  localStorage.setItem(storageKey(), JSON.stringify([...state.selected]));
}

function updateCounts() {
  const count = state.selected.size;
  $('#selected-count').textContent = count;
  $('#footer-count').textContent = count;
}

function payload() {
  const removals = [];
  for (const page of state.data.pages) {
    for (const candidate of page.candidates) {
      if (!state.selected.has(candidateKey(page, candidate))) continue;
      removals.push({
        page: page.view,
        line: candidate.line,
        before: candidate.before,
        base_line_version: candidate.base_line_version,
      });
    }
  }
  return JSON.stringify({
    schema: 1,
    task: state.data.task,
    scope: state.data.scope,
    base_commit: state.data.base_commit,
    removals,
  }, null, 2);
}

function drawCandidates(page, image) {
  document.querySelectorAll(`canvas[data-leaf="${page.leaf}"]`).forEach(canvas => {
    if (canvas.dataset.drawn) return;
    const candidate = page.candidates[Number(canvas.dataset.index)];
    const [x, y, width, height] = candidate.crop;
    const scaleX = image.naturalWidth / page.width;
    const scaleY = image.naturalHeight / page.height;
    canvas.width = Math.max(1, Math.round(width * scaleX));
    canvas.height = Math.max(1, Math.round(height * scaleY));
    canvas.getContext('2d').drawImage(
      image,
      x * scaleX,
      y * scaleY,
      width * scaleX,
      height * scaleY,
      0,
      0,
      canvas.width,
      canvas.height,
    );
    canvas.dataset.drawn = 'true';
  });
}

function loadPageImage(page) {
  if (state.images.has(page.leaf)) return;
  const image = new Image();
  image.decoding = 'async';
  image.fetchPriority = 'high';
  state.images.set(page.leaf, image);
  image.addEventListener('load', () => {
    drawCandidates(page, image);
    state.images.delete(page.leaf);
    image.removeAttribute('src');
  }, {once: true});
  image.addEventListener('error', () => {
    document.querySelectorAll(`canvas[data-leaf="${page.leaf}"]`).forEach(canvas => {
      const error = document.createElement('div');
      error.className = 'image-error';
      error.textContent = `Could not load scan ${page.view}`;
      canvas.replaceWith(error);
    });
  }, {once: true});
  image.src = page.image;
}

function render() {
  const total = state.data.pages.reduce((sum, page) => sum + page.candidates.length, 0);
  $('#audit-scope').textContent = state.data.scope.replace('-', '–');
  $('#candidate-count').textContent = total;
  $('#audit-list').innerHTML = state.data.pages.map(page => `<section class="page-group" data-page="${page.leaf}"><div class="page-heading"><h2>${page.view}</h2><span>${page.candidates.length} candidates</span><a href="${page.gallica}" target="_blank" rel="noreferrer">Open full scan ↗</a></div>${page.candidates.map((candidate, index) => { const key = candidateKey(page, candidate); return `<article class="candidate"><div class="crop-wrap"><canvas data-leaf="${page.leaf}" data-index="${index}" aria-label="Right edge of ${key}"></canvas><div class="candidate-meta"><span class="line-id">${escapeHTML(key)}</span><span class="line-text">${escapeHTML(candidate.before)}</span></div></div><label class="remove-choice"><input type="checkbox" data-key="${escapeHTML(key)}"${state.selected.has(key) ? ' checked' : ''}>Remove hyphen</label></article>`; }).join('')}</section>`).join('');
  updateCounts();
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const leaf = Number(entry.target.dataset.page);
      loadPageImage(state.data.pages.find(page => page.leaf === leaf));
      observer.unobserve(entry.target);
    }
  }, {rootMargin: '1000px 0px'});
  document.querySelectorAll('.page-group').forEach(section => observer.observe(section));
}

document.addEventListener('change', event => {
  const checkbox = event.target.closest('input[data-key]');
  if (!checkbox) return;
  if (checkbox.checked) state.selected.add(checkbox.dataset.key);
  else state.selected.delete(checkbox.dataset.key);
  saveSelection();
  updateCounts();
});

$('#copy-json').addEventListener('click', async () => {
  if (await copyText(payload())) toast('JSON copied.');
  else prompt('Copy this JSON:', payload());
});

$('#open-issue').addEventListener('click', () => {
  const title = `[hyphen-audit ${state.data.scope}] Human review results`;
  const url = `https://github.com/${state.data.repository}/issues/new?template=line-end-hyphen-audit.md&title=${encodeURIComponent(title)}`;
  window.open(url, '_blank', 'noopener');
});

fetch('hyphen-audit.json').then(response => {
  if (!response.ok) throw new Error('Could not load hyphen audit data');
  return response.json();
}).then(data => {
  state.data = data;
  restoreSelection();
  render();
}).catch(error => {
  $('#audit-list').innerHTML = `<p class="loading">${escapeHTML(error.message)}</p>`;
});
