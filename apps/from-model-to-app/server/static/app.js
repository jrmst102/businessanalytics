/* Client logic for the three-tab dashboard.
 *
 * Every number displayed comes from the Python engine API (/api/*). This file
 * only renders responses, validates nothing analytically, and keeps the
 * session rule from the specification: one active fitted model per browser
 * session; changing the model or parameter clears the fit, metrics and prior
 * prediction until "Train model" is clicked again.
 */
'use strict';

const $ = (id) => document.getElementById(id);

// One session per browser tab, like Streamlit's session state.
const sessionId = sessionStorage.getItem('session-id') ||
  (() => { const v = crypto.randomUUID(); sessionStorage.setItem('session-id', v); return v; })();

const state = {
  meta: null,
  columns: [],
  rows: [],
  active: null,          // {choice, parameterId} of the trained configuration
  chart: null,
};

const fmt = {
  r2: (v) => (v === null ? 'N/A' : v.toFixed(3)),
  two: (v) => v.toFixed(2),
  mape: (v) => (v === null ? 'N/A' : `${v.toFixed(2)}%`),
  int: (v) => v.toLocaleString('en-US'),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId, ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({ error: 'Unexpected server response.' }));
  return { ok: response.ok, status: response.status, body };
}

/* ------------------------------- Tabs ---------------------------------- */
document.querySelectorAll('.tab').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((b) => {
      b.classList.toggle('active', b === button);
      b.setAttribute('aria-selected', b === button ? 'true' : 'false');
    });
    document.querySelectorAll('.tab-panel').forEach((panel) => {
      panel.classList.toggle('hidden', panel.id !== `tab-${button.dataset.tab}`);
    });
  });
});

/* ------------------------------ Data tab ------------------------------- */
function selectedValues(select) {
  return Array.from(select.selectedOptions).map((o) => o.value);
}

function filteredRows() {
  const stores = new Set(selectedValues($('filter-stores')));
  const categories = new Set(selectedValues($('filter-categories')));
  const needle = $('filter-search').value.trim().toLowerCase();
  const col = Object.fromEntries(state.columns.map((name, i) => [name, i]));
  return state.rows.filter((row) => {
    if (!stores.has(String(row[col.store_id]))) return false;
    if (!categories.has(String(row[col.category]))) return false;
    if (!needle) return true;
    return [row[col.store_id], row[col.category], row[col.weekday]]
      .some((v) => String(v).toLowerCase().includes(needle));
  });
}

const MAX_TABLE_ROWS = 1000;

function renderTable(rows) {
  const head = `<thead><tr>${state.columns.map((c) => `<th>${c}</th>`).join('')}</tr></thead>`;
  const body = rows.slice(0, MAX_TABLE_ROWS)
    .map((row) => `<tr>${row.map((v) => `<td>${v}</td>`).join('')}</tr>`).join('');
  $('data-table').innerHTML = head + `<tbody>${body}</tbody>`;
  const shown = Math.min(rows.length, MAX_TABLE_ROWS);
  $('table-caption').textContent =
    `${fmt.int(rows.length)} of ${fmt.int(state.rows.length)} rows in view` +
    (rows.length > MAX_TABLE_ROWS ? ` (first ${fmt.int(shown)} displayed).` : '.');
}

function renderChart(rows) {
  const col = Object.fromEntries(state.columns.map((name, i) => [name, i]));
  const totals = new Map();
  for (const row of rows) {
    const date = row[col.date];
    totals.set(date, (totals.get(date) || 0) + row[col.units_sold]);
  }
  const dates = Array.from(totals.keys()).sort();
  const values = dates.map((d) => totals.get(d));
  if (state.chart) state.chart.destroy();
  state.chart = new Chart($('sales-chart'), {
    type: 'line',
    data: {
      labels: dates,
      datasets: [{
        label: 'Total units sold',
        data: values,
        borderColor: '#356DA8',
        backgroundColor: '#356DA8',
        borderWidth: 2,
        pointRadius: 0,
        pointHitRadius: 8,
        tension: 0,
      }],
    },
    options: {
      animation: false,
      plugins: {
        legend: { display: false },  // single named series; the heading names it
        tooltip: { intersect: false, mode: 'index' },
      },
      interaction: { intersect: false, mode: 'index' },
      scales: {
        x: { ticks: { maxTicksLimit: 10, color: '#6b7a89' }, grid: { display: false },
             title: { display: true, text: 'Date', color: '#3e4c59' } },
        y: { ticks: { color: '#6b7a89' }, grid: { color: '#e4ebf2' },
             title: { display: true, text: 'Total units sold', color: '#3e4c59' } },
      },
    },
  });
}

function refreshDataView() {
  const rows = filteredRows();
  renderTable(rows);
  renderChart(rows);
}

/* ------------------------------ Model tab ------------------------------ */
function choiceMeta(name) {
  return state.meta.choices.find((c) => c.name === name);
}

function currentConfig() {
  return { choice: $('model-choice').value, parameterId: $('model-parameter').value };
}

function renderParameterControl() {
  const choice = choiceMeta($('model-choice').value);
  $('parameter-label').textContent = choice.parameter_label;
  $('model-parameter').innerHTML = choice.options
    .map((o) => `<option value="${o.id}" ${o.id === choice.default_id ? 'selected' : ''}>${o.label}</option>`)
    .join('');
  $('how-it-predicts').textContent = choice.how_it_predicts;
  renderEnsembleNote();
  loadEngineSource(choice.name);
}

function renderEnsembleNote() {
  const choice = choiceMeta($('model-choice').value);
  const note = choice.ensemble_notes ? choice.ensemble_notes[$('model-parameter').value] : null;
  $('ensemble-note').classList.toggle('hidden', !note);
  $('ensemble-note').textContent = note || '';
}

async function loadEngineSource(choice) {
  const { ok, body } = await api(`/api/source?choice=${encodeURIComponent(choice)}`);
  $('engine-source').textContent = ok ? body.source : 'Source unavailable.';
}

// A model or parameter change invalidates the fit, metrics and prediction.
function invalidateIfChanged() {
  const config = currentConfig();
  if (state.active &&
      (state.active.choice !== config.choice || state.active.parameterId !== config.parameterId)) {
    state.active = null;
    renderModelResults(null);
    renderPrediction(null);
    renderTestGate();
  }
}

function renderModelResults(result) {
  $('model-results').classList.toggle('hidden', !result);
  $('no-results').classList.toggle('hidden', !!result);
  if (!result) return;
  const s = result.scores;
  $('metric-r2').textContent = fmt.r2(s.R2);
  $('metric-mse').textContent = fmt.two(s.MSE);
  $('metric-rmse').textContent = fmt.two(s.RMSE);
  $('metric-mape').textContent = fmt.mape(s.MAPE);

  const notes = [];
  if (s.R2 === null && s.R2_note) notes.push(`<p class="warning">${s.R2_note}</p>`);
  if (s.MAPE === null && s.MAPE_note) notes.push(`<p class="warning">${s.MAPE_note}</p>`);
  else if (s.zero_excluded_from_mape > 0) {
    notes.push(`<p class="muted">MAPE excludes ${fmt.int(s.zero_excluded_from_mape)} observations ` +
      `with zero actual sales (documented reporting policy); the other metrics use all ` +
      `${fmt.int(s.observations)} test observations.</p>`);
  }
  for (const warning of result.warnings) notes.push(`<p class="warning">Training warning: ${warning}</p>`);
  $('metric-notes').innerHTML = notes.join('');

  const mapeText = s.MAPE === null
    ? 'Its MAPE is not defined because no held-out observation has positive actual sales.'
    : `Its MAPE is ${fmt.two(s.MAPE)}% across ${fmt.int(s.positive_observations)} positive-sales observations.`;
  $('interpretation').textContent =
    `This model's RMSE is ${fmt.two(s.RMSE)} units per store/category/day on the held-out dates. ` +
    `${mapeText} R² is dimensionless and can be negative; it is not percentage accuracy. ` +
    'These are historical evaluation results, not a prediction interval or a guarantee for one new forecast.';
  $('provenance').textContent =
    `Evaluation period: ${result.test_start} to ${result.test_end} (${fmt.int(result.test_rows)} ` +
    `held-out test observations). Fitted on ${result.development_start} to ${result.development_end} ` +
    `(training + validation, ${fmt.int(result.development_rows)} rows) in ` +
    `${result.fit_seconds.toFixed(1)} s.` +
    (result.training_epochs ? ` Network training epochs: ${result.training_epochs}.` : '');
  $('historical-note').textContent = result.historical_note;
}

async function trainModel() {
  const config = currentConfig();
  const button = $('train-button');
  button.disabled = true;
  $('train-status').textContent = config.choice === 'Ensemble regression'
    ? 'Training the ensemble — it fits its four classroom members…'
    : `Training ${config.choice}…`;
  try {
    const { ok, body } = await api('/api/train', {
      method: 'POST',
      body: JSON.stringify({ choice: config.choice, parameter_id: config.parameterId }),
    });
    if (!ok) {
      state.active = null;
      renderModelResults(null);
      renderPrediction(null);
      $('train-status').innerHTML = `<span class="error-box">${body.error || 'Training failed.'} ` +
        'Previous results were cleared; prediction stays unavailable until a model trains successfully.</span>';
    } else {
      state.active = config;
      renderModelResults(body);
      renderPrediction(null);
      $('train-status').textContent = '';
    }
  } catch (error) {
    state.active = null;
    renderModelResults(null);
    $('train-status').innerHTML = `<span class="error-box">The server is not reachable: ${error.message}</span>`;
  } finally {
    button.disabled = false;
    renderTestGate();
  }
}

/* ------------------------------ Test tab ------------------------------- */
function renderTestGate() {
  const trained = !!state.active;
  $('test-gate').classList.toggle('hidden', trained);
  $('test-form').classList.toggle('hidden', !trained);
}

function renderPrediction(p) {
  const target = $('prediction');
  $('predict-errors').innerHTML = '';
  target.classList.toggle('hidden', !p);
  if (!p) { target.innerHTML = ''; return; }
  const s = p.scores;
  const parameterLabel = choiceMeta(p.choice).options.find((o) => o.id === p.parameter_id).label;
  const parts = [];
  parts.push(`<p class="predicted-headline">Predicted daily sales: ${p.predicted.toFixed(2)} units</p>`);
  if (p.negative) {
    parts.push('<p class="error-box">The raw prediction is negative, which is not a valid physical ' +
      'sales estimate. It is shown unclipped to preserve classroom behavior; treat it as a model limitation.</p>');
  }
  parts.push(`<p><strong>Model:</strong> ${p.choice}, ` +
    `${choiceMeta(p.choice).parameter_label.toLowerCase()}: ${parameterLabel}.</p>`);
  parts.push(`<p><strong>Accepted inputs:</strong> store ${p.canonical.store_id}, category ` +
    `“${p.canonical.category}” (canonical form of what you typed), date ${p.canonical.date} → ` +
    `weekday ${p.canonical.weekday}, day of year ${p.canonical.day_of_year}.</p>`);
  for (const notice of p.notices) parts.push(`<p class="warning">${notice}</p>`);
  parts.push(`<p><strong>Historical test metrics:</strong> R² ${fmt.r2(s.R2)} · ` +
    `MSE ${fmt.two(s.MSE)} · RMSE ${fmt.two(s.RMSE)} · MAPE ${fmt.mape(s.MAPE)}</p>`);
  parts.push('<p class="muted">These metrics describe historical held-out observations, not the ' +
    'accuracy of this new prediction. The actual outcome for your typed observation is not known ' +
    'unless you entered it.</p>');
  if (p.actual_eval) {
    const a = p.actual_eval;
    const ape = a.ape_percent === null ? 'N/A (actual is zero)' : `${a.ape_percent.toFixed(2)}%`;
    parts.push(`<p><strong>This example only:</strong> actual ${a.actual.toFixed(2)} units; ` +
      `signed error (actual − predicted) ${a.signed_error >= 0 ? '+' : ''}${a.signed_error.toFixed(2)} ` +
      `— positive means underprediction; absolute error ${a.absolute_error.toFixed(2)}; ` +
      `percentage error (APE, this one row, not MAPE) ${ape}. This single observation does not ` +
      'update the historical metrics and is never used for training.</p>');
  }
  target.innerHTML = parts.join('');
}

async function predictOne() {
  if (!state.active) return;
  const button = $('predict-button');
  button.disabled = true;
  try {
    const { ok, status, body } = await api('/api/predict', {
      method: 'POST',
      body: JSON.stringify({
        choice: state.active.choice,
        parameter_id: state.active.parameterId,
        store: $('input-store').value,
        category: $('input-category').value,
        date: $('input-date').value,
        actual: $('input-actual').value,
      }),
    });
    if (!ok) {
      renderPrediction(null);
      const messages = body.errors || [body.error || `Prediction failed (${status}).`];
      $('predict-errors').innerHTML = messages.map((m) => `<p class="error-box">${m}</p>`).join('');
    } else {
      renderPrediction(body);
    }
  } finally {
    button.disabled = false;
  }
}

/* ------------------------------- Startup ------------------------------- */
async function start() {
  const [meta, dataset] = await Promise.all([api('/api/meta'), api('/api/dataset')]);
  if (!meta.ok || !dataset.ok) {
    $('dataset-facts').innerHTML =
      `<span class="error-box">${meta.body.error || dataset.body.error || 'The engine API is not reachable.'}</span>`;
    return;
  }
  state.meta = meta.body;
  state.columns = dataset.body.columns;
  state.rows = dataset.body.rows;

  const f = state.meta.facts;
  $('source-link').href = state.meta.source_url;
  $('dataset-facts').innerHTML =
    `<strong>${fmt.int(f.Observations)}</strong> observations · <strong>${f.Stores}</strong> stores · ` +
    `<strong>${f.Categories}</strong> categories · <strong>${f['First date']}</strong> to ` +
    `<strong>${f['Last date']}</strong>`;

  for (const [id, values] of [['filter-stores', state.meta.stores], ['filter-categories', state.meta.categories]]) {
    $(id).innerHTML = values.map((v) => `<option value="${v}" selected>${v}</option>`).join('');
    $(id).addEventListener('change', refreshDataView);
  }
  $('filter-search').addEventListener('input', refreshDataView);
  refreshDataView();

  $('model-choice').innerHTML = state.meta.choices
    .map((c) => `<option value="${c.name}">${c.name}</option>`).join('');
  $('model-choice').addEventListener('change', () => { renderParameterControl(); invalidateIfChanged(); });
  $('model-parameter').addEventListener('change', () => { renderEnsembleNote(); invalidateIfChanged(); });
  $('train-button').addEventListener('click', trainModel);
  renderParameterControl();

  $('valid-stores').textContent = 'Stores: ' + state.meta.stores.join(', ');
  $('valid-categories').textContent = 'Categories: ' + state.meta.categories.join(', ');
  $('use-example').addEventListener('click', () => {
    $('input-store').value = '3';
    $('input-category').value = 'Bakery';
    $('input-date').value = '2025-10-15';
    $('input-actual').value = '';
  });
  $('predict-button').addEventListener('click', predictOne);
  $('input-date').addEventListener('keydown', (e) => { if (e.key === 'Enter') predictOne(); });
  renderTestGate();
}

start();
