const state = {data: null, selected: new Set(), images: new Map(), candidates: [], focusedIndex: -1, total: 0};
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));

function candidateKey(page, candidate) { return `${page.view}/${candidate.line}#${candidate.occurrence}`; }
function storageKey() { return `nippo-st-audit:${state.data.scope}`; }

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
  const retained = state.selected.size;
  const converted = state.total - retained;
  $('#selected-count').textContent = retained;
  $('#convert-count').textContent = converted;
  $('#footer-retain-count').textContent = retained;
  $('#footer-convert-count').textContent = converted;
}

function payload() {
  const replacements = [];
  for (const page of state.data.pages) {
    for (const candidate of page.candidates) {
      if (state.selected.has(candidateKey(page, candidate))) continue;
      replacements.push({
        page: page.view,
        line: candidate.line,
        occurrence: candidate.occurrence,
        before: candidate.before,
        after: candidate.after,
        base_line_version: candidate.base_line_version,
      });
    }
  }
  return JSON.stringify({schema: 1, task: state.data.task, scope: state.data.scope, base_commit: state.data.base_commit, replacements}, null, 2);
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
  state.candidates.forEach((node, candidateIndex) => { node.tabIndex = candidateIndex === state.focusedIndex ? 0 : -1; });
  const node = state.candidates[state.focusedIndex];
  node.focus({preventScroll: true});
  if (scroll) node.scrollIntoView({block: 'center', inline: 'nearest', behavior: 'smooth'});
}

function verticalNeighbour(direction) {
  if (state.focusedIndex < 0) return direction > 0 ? 0 : state.candidates.length - 1;
  const current = state.candidates[state.focusedIndex].getBoundingClientRect();
  const centreX = current.left + current.width / 2;
  const choices = state.candidates.map((node, index) => ({index, rect: node.getBoundingClientRect()})).filter(({rect}) => direction > 0 ? rect.top > current.top + 2 : rect.top < current.top - 2);
  if (!choices.length) return state.focusedIndex;
  choices.sort((a, b) => {
    const rowDistanceA = Math.abs(a.rect.top - current.top);
    const rowDistanceB = Math.abs(b.rect.top - current.top);
    if (rowDistanceA !== rowDistanceB) return rowDistanceA - rowDistanceB;
    return Math.abs(a.rect.left + a.rect.width / 2 - centreX) - Math.abs(b.rect.left + b.rect.width / 2 - centreX);
  });
  return choices[0].index;
}

function toggleCandidate(index) {
  const checkbox = state.candidates[index]?.querySelector('input[data-key]');
  if (!checkbox) return;
  checkbox.checked = !checkbox.checked;
  checkbox.dispatchEvent(new Event('change', {bubbles: true}));
}

function occurrenceContext(candidate) {
  const start = Math.max(0, candidate.token_start - 10);
  const end = Math.min(candidate.line_text.length, candidate.token_end + 10);
  return `${start ? '…' : ''}${candidate.line_text.slice(start, end)}${end < candidate.line_text.length ? '…' : ''}`;
}

function render() {
  state.total = state.data.pages.reduce((sum, page) => sum + page.candidates.length, 0);
  $('#audit-scope').textContent = state.data.scope.replace('-', '–');
  $('#candidate-count').textContent = state.total;
  $('#confirmed-count').textContent = state.data.confirmed_long_s;
  if (!state.total) {
    $('#audit-list').innerHTML = '<p class="completion"><strong>This audit is complete.</strong> All remaining ſt occurrences in this scope have been confirmed as genuine long-s forms.</p>';
    state.candidates = [];
    updateCounts();
    return;
  }
  let globalIndex = 0;
  $('#audit-list').innerHTML = state.data.pages.map(page => `<section class="page-group" data-page="${page.leaf}"><div class="page-heading"><h2>${page.view}</h2><span>${page.candidates.length} candidates</span><a href="${page.gallica}" target="_blank" rel="noreferrer">Open full scan ↗</a></div><div class="tile-grid">${page.candidates.map((candidate, pageIndex) => { const key = candidateKey(page, candidate); const index = globalIndex++; return `<article class="candidate" tabindex="-1" data-candidate-index="${index}"><canvas data-leaf="${page.leaf}" data-page-index="${pageIndex}" aria-label="Scan crop for ${escapeHTML(key)}"></canvas><label class="candidate-footer"><input type="checkbox" data-key="${escapeHTML(key)}"${state.selected.has(key) ? ' checked' : ''} aria-label="Retain true long s in ${escapeHTML(key)}"><span class="candidate-text"><small class="candidate-id">${escapeHTML(key)}</small><span class="candidate-context">${escapeHTML(occurrenceContext(candidate))}</span></span></label></article>`; }).join('')}</div></section>`).join('');
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
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault();
    const direction = event.key === 'ArrowRight' ? 1 : -1;
    const start = state.focusedIndex < 0 ? (direction > 0 ? 0 : state.candidates.length - 1) : state.focusedIndex + direction;
    setFocusedIndex(start);
  } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault();
    setFocusedIndex(verticalNeighbour(event.key === 'ArrowDown' ? 1 : -1));
  } else if (event.code === 'Space' && state.focusedIndex >= 0) {
    event.preventDefault();
    toggleCandidate(state.focusedIndex);
  }
});

document.addEventListener('click', event => {
  const candidate = event.target.closest('.candidate');
  if (!candidate || event.target.closest('input,label')) return;
  setFocusedIndex(Number(candidate.dataset.candidateIndex), false);
  toggleCandidate(state.focusedIndex);
});

$('#copy-json').addEventListener('click', async () => {
  if (await copyText(payload())) toast('JSON copied.');
  else prompt('Copy this JSON:', payload());
});

$('#open-issue').addEventListener('click', () => {
  const title = `[st-audit ${state.data.scope}] Human review results`;
  const url = `https://github.com/${state.data.repository}/issues/new?template=st-ligature-audit.md&title=${encodeURIComponent(title)}`;
  window.open(url, '_blank', 'noopener');
});

fetch('st-audit.json').then(response => {
  if (!response.ok) throw new Error('Could not load ſt / st audit data');
  return response.json();
}).then(data => {
  state.data = data;
  restoreSelection();
  render();
}).catch(error => {
  $('#audit-list').innerHTML = `<p class="loading">${escapeHTML(error.message)}</p>`;
});
