/* Live four-criterion selection. No submit/recalculate control is necessary. */
(() => {
  'use strict';
  const form = document.getElementById('multiOptForm');
  const output = document.getElementById('multiOptResults');
  const status = document.getElementById('optLiveStatus');
  if (!form || !output) return;
  let timer, controller, generation = 0;

  function updateWeightLabels() {
    const inputs = [...form.querySelectorAll('[data-opt-weight]')];
    const total = inputs.reduce((sum, el) => sum + Number(el.value), 0);
    inputs.forEach(el => {
      const raw = document.getElementById('optRaw-' + el.name);
      const effective = document.getElementById('optNormalized-' + el.name);
      if (raw) raw.textContent = el.value;
      if (effective) effective.textContent = total > 0 ? (100 * Number(el.value) / total).toFixed(1) + '%' : '—';
    });
    syncPresets();
    return total;
  }

  const presetButtons = [...document.querySelectorAll('.rb-preset')];
  function syncPresets() {
    const vals = {};
    form.querySelectorAll('[data-opt-weight]').forEach(el => { vals[el.name] = Number(el.value); });
    presetButtons.forEach(b => {
      const w = JSON.parse(b.dataset.preset);
      b.setAttribute('aria-pressed', Object.keys(w).every(k => vals[k] === w[k]) ? 'true' : 'false');
    });
  }
  presetButtons.forEach(b => b.addEventListener('click', () => {
    const w = JSON.parse(b.dataset.preset);
    form.querySelectorAll('[data-opt-weight]').forEach(el => { if (el.name in w) el.value = w[el.name]; });
    form.dispatchEvent(new Event('change', { bubbles: true }));
  }));

  async function refresh() {
    const serial = ++generation;
    const total = updateWeightLabels();
    if (total <= 0) { status.textContent = 'At least one criterion must have a positive weight.'; return; }
    if (controller) controller.abort();
    controller = new AbortController();
    const args = new URLSearchParams(new FormData(form));
    status.textContent = 'Updating recommendation and charts…';
    try {
      const resp = await fetch('/api/optimization/fragment?' + args.toString(), {
        signal: controller.signal, headers: { 'Accept': 'text/html' }
      });
      if (!resp.ok) throw new Error('Server returned ' + resp.status);
      const html = await resp.text();
      if (serial !== generation) return;
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const card = doc.getElementById('optAnswerCard');
      const slot = document.getElementById('multiOptAnswer');
      if (card && slot) slot.replaceChildren(card);
      output.innerHTML = doc.body.innerHTML;
      status.textContent = 'Updated automatically. Weights are normalised to 100%; change any priority to explore alternatives.';
      window.history.replaceState({}, '', '/optimization?' + args.toString());
    } catch (e) {
      if (e.name !== 'AbortError') status.textContent = 'Unable to update: ' + e.message + '. Try reloading the page.';
    }
  }
  function schedule() {
    const total = updateWeightLabels();
    if (total <= 0) { status.textContent = 'At least one criterion must have a positive weight.'; return; }
    clearTimeout(timer);
    timer = setTimeout(refresh, 120);
  }
  form.addEventListener('input', schedule);
  form.addEventListener('change', schedule);
  form.addEventListener('submit', e => { e.preventDefault(); refresh(); });
  updateWeightLabels();
})();
