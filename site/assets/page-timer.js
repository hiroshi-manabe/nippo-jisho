/* Local viewing-time aid only; never part of a correction payload. */
(function (root) {
  function createTimer(storage, now) {
    let page = null, visible = true, started = null, elapsed = 0, paused = false;
    const key = id => `nippo-page-time-v1:${id}`;
    function total() { return elapsed + (started === null ? 0 : Math.max(0, now() - started)); }
    function save() {
      if (!page) return;
      elapsed = total(); started = visible && !paused ? now() : null;
      try { storage.setItem(key(page), String(elapsed)); } catch {}
    }
    return {
      total,
      save,
      paused: () => paused,
      pause(value) {
        save(); paused = value; started = page && visible && !paused ? now() : null;
        if (page) { try { storage.setItem(key(page) + ':paused', String(paused)); } catch {} }
      },
      select(id) {
        if (id === page) return;
        save(); page = id; elapsed = 0; paused = false;
        if (page) { try { elapsed = Math.max(0, Number(storage.getItem(key(page))) || 0); } catch {} }
        if (page) { try { paused = storage.getItem(key(page) + ':paused') === 'true'; } catch {} }
        started = page && visible && !paused ? now() : null;
      },
      visibility(value) {
        save(); visible = value; started = page && visible && !paused ? now() : null;
      },
      reset(id) {
        try { storage.removeItem(key(id)); } catch {}
        if (id === page) { elapsed = 0; started = visible && !paused ? now() : null; }
      }
    };
  }
  function format(ms) {
    const seconds = Math.floor(ms / 1000), minutes = Math.floor(seconds / 60);
    return minutes < 60 ? `${minutes}:${String(seconds % 60).padStart(2, '0')}`
      : `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  }
  if (typeof module === 'object' && module.exports) { module.exports = {createTimer, format}; return; }
  let storage;
  try { storage = root.localStorage; } catch { storage = {getItem: () => null, setItem() {}, removeItem() {}}; }
  const timer = createTimer(storage, () => performance.now());
  let selectedPage = null;
  const display = () => {
    document.getElementById('page-timer').hidden = !selectedPage;
    document.getElementById('page-time').textContent = `Time on page: ${format(timer.total())}`;
    const button = document.getElementById('page-time-pause');
    button.textContent = timer.paused() ? 'Resume' : 'Pause';
    button.setAttribute('aria-label', timer.paused() ? 'Resume page timer' : 'Pause page timer');
  };
  document.getElementById('page-time-pause').addEventListener('click', () => { timer.pause(!timer.paused()); display(); });
  document.getElementById('page-time-reset').addEventListener('click', () => { timer.reset(selectedPage); display(); });
  root.NippoPageTimer = {
    select(id) { selectedPage = id; timer.select(id); display(); },
    reset(id) { timer.reset(id); display(); }
  };
  timer.visibility(!document.hidden);
  document.addEventListener('visibilitychange', () => { timer.visibility(!document.hidden); display(); });
  root.addEventListener('pagehide', () => timer.visibility(false));
  root.addEventListener('pageshow', () => timer.visibility(!document.hidden));
  setInterval(display, 1000);
  setInterval(() => timer.save(), 5000);
})(globalThis);
