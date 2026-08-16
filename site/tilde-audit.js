const state = {data: null, selected: new Set(), images: new Map(), candidates: [], focusedIndex: -1};
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));

function candidateKey(page, candidate) { return `${page.view}/${candidate.line}#${candidate.occurrence}`; }
function storageKey() { return `nippo-tilde-audit:${state.data.scope}`; }

function candidateVersions() {
  return new Map(state.data.pages.flatMap(page => page.candidates.map(candidate => [candidateKey(page, candidate), candidate.base_line_version])));
}

function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.classList.remove('hidden');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.add('hidden'), 2200);
}

function fallbackCopy(value) {
  const area = document.createElement('textarea');
  area.value = value;
  area.style.position = 'fixed';
  area.style.opacity = '0';
  document.body.appendChild(area);
  area.select();
  const copied = document.execCommand('copy');
  area.remove();
  return copied;
}

function copyText(value) {
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(value).then(() => true, () => fallbackCopy(value));
  return Promise.resolve(fallbackCopy(value));
}

function restoreSelection() {
  const versions = candidateVersions();
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey()));
    const selections = saved?.schema === 2 ? saved.selections : {};
    state.selected = new Set(Object.entries(selections).filter(([key, version]) => versions.get(key) === version).map(([key]) => key));
  } catch (_) {
    state.selected = new Set();
  }
  saveSelection();
}

function saveSelection() {
  const versions = candidateVersions();
  const selections = Object.fromEntries([...state.selected].filter(key => versions.has(key)).map(key => [key, versions.get(key)]));
  localStorage.setItem(storageKey(), JSON.stringify({schema: 2, selections}));
}

function updateCounts() {
  $('#selected-count').textContent = state.selected.size;
  $('#footer-count').textContent = state.selected.size;
}

function payload() {
  const swaps = [];
  for (const page of state.data.pages) {
    for (const candidate of page.candidates) {
      if (!state.selected.has(candidateKey(page, candidate))) continue;
      swaps.push({page: page.view, line: candidate.line, occurrence: candidate.occurrence, before: candidate.before, after: candidate.after, base_line_version: candidate.base_line_version});
    }
  }
  return JSON.stringify({schema: 1, task: state.data.task, scope: state.data.scope, base_commit: state.data.base_commit, swaps}, null, 2);
}

function drawCandidates(page, image) {
  document.querySelectorAll(`canvas[data-leaf="${page.leaf}"]`).forEach(canvas => {
    if (canvas.dataset.drawn) return;
    const candidate = page.candidates[Number(canvas.dataset.pageIndex)];
    const [x, y, width, height] = candidate.crop;
    const scaleX = image.naturalWidth / page.width;
    const scaleY = image.naturalHeight / page.height;
    canvas.width = Math.max(1, Math.round(width * scaleX));
    canvas.height = Math.max(1, Math.round(height * scaleY));
    canvas.getContext('2d').drawImage(image, x * scaleX, y * scaleY, width * scaleX, height * scaleY, 0, 0, canvas.width, canvas.height);
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

function setFocusedIndex(index, scroll = true) {
  if (!state.candidates.length) return;
  state.focusedIndex = Math.max(0, Math.min(index, state.candidates.length - 1));
  state.candidates.forEach((node, candidateIndex) => node.tabIndex = candidateIndex === state.focusedIndex ? 0 : -1);
  const node = state.candidates[state.focusedIndex];
  node.focus({preventScroll: true});
  if (scroll) node.scrollIntoView({block: 'center', behavior: 'smooth'});
}

function toggleCandidate(index) {
  const node = state.candidates[index];
  if (!node) return;
  const checkbox = node.querySelector('input[data-key]');
  checkbox.checked = !checkbox.checked;
  checkbox.dispatchEvent(new Event('change', {bubbles: true}));
}

function render() {
  const total = state.data.pages.reduce((sum, page) => sum + page.candidates.length, 0);
  $('#audit-scope').textContent = state.data.scope.replace('-', '–');
  $('#candidate-count').textContent = total;
  let globalIndex = 0;
  $('#audit-list').innerHTML = state.data.pages.map(page => `<section class="page-group" data-page="${page.leaf}"><div class="page-heading"><h2>${page.view}</h2><span>${page.candidates.length} candidates</span><a href="${page.gallica}" target="_blank" rel="noreferrer">Open full scan ↗</a></div>${page.candidates.map((candidate, pageIndex) => { const key = candidateKey(page, candidate); const index = globalIndex++; return `<article class="candidate" tabindex="-1" data-candidate-index="${index}"><div class="crop-wrap"><canvas data-leaf="${page.leaf}" data-page-index="${pageIndex}" aria-label="Scan crop for ${escapeHTML(key)}"></canvas><div class="candidate-meta"><span class="line-id">${escapeHTML(key)}</span><span class="line-context">${escapeHTML(candidate.line_text)}</span></div></div><label class="swap-choice"><input type="checkbox" data-key="${escapeHTML(key)}"${state.selected.has(key) ? ' checked' : ''}><span><strong>${escapeHTML(candidate.before)}</strong><i aria-hidden="true">→</i><strong>${escapeHTML(candidate.after)}</strong><small>Move tilde</small></span></label></article>`; }).join('')}</section>`).join('');
  state.candidates = [...document.querySelectorAll('.candidate')];
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

document.addEventListener('focusin', event => {
  const candidate = event.target.closest('.candidate');
  if (!candidate) return;
  state.focusedIndex = Number(candidate.dataset.candidateIndex);
});

document.addEventListener('change', event => {
  const checkbox = event.target.closest('input[data-key]');
  if (!checkbox) return;
  if (checkbox.checked) state.selected.add(checkbox.dataset.key);
  else state.selected.delete(checkbox.dataset.key);
  saveSelection();
  updateCounts();
});

document.addEventListener('keydown', event => {
  if (event.metaKey || event.ctrlKey || event.altKey || event.target.closest('button,a')) return;
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault();
    const direction = event.key === 'ArrowDown' ? 1 : -1;
    const start = state.focusedIndex < 0 ? (direction > 0 ? 0 : state.candidates.length - 1) : state.focusedIndex + direction;
    setFocusedIndex(start);
  } else if (event.code === 'Space' && state.focusedIndex >= 0) {
    event.preventDefault();
    toggleCandidate(state.focusedIndex);
  }
});

$('#copy-json').addEventListener('click', async () => {
  if (await copyText(payload())) toast('JSON copied.');
  else prompt('Copy this JSON:', payload());
});

$('#open-issue').addEventListener('click', () => {
  const title = `[tilde-audit ${state.data.scope}] Human review results`;
  const url = `https://github.com/${state.data.repository}/issues/new?template=tilde-carrier-audit.md&title=${encodeURIComponent(title)}`;
  window.open(url, '_blank', 'noopener');
});

fetch('tilde-audit.json').then(response => {
  if (!response.ok) throw new Error('Could not load tilde audit data');
  return response.json();
}).then(data => {
  state.data = data;
  restoreSelection();
  render();
}).catch(error => {
  $('#audit-list').innerHTML = `<p class="loading">${escapeHTML(error.message)}</p>`;
});
