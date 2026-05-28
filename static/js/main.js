/* ============================================================
   Icarus — Main Application JavaScript
   Vanilla JS – no frameworks
   ============================================================ */

(function () {
  'use strict';

  // ---------- Constants ----------
  const METHOD_COLORS = {
    bisection:     '#3b82f6',
    secant:        '#8b5cf6',
    regula_falsi:  '#06b6d4',
    illinois:      '#f59e0b',
    brent:         '#10b981',
    newton_raphson:'#ef4444',
  };

  const METHOD_LABELS = {
    bisection:      'Bisection',
    secant:         'Secant',
    regula_falsi:   'Regula Falsi',
    illinois:       'Illinois',
    brent:          "Brent's Method",
    newton_raphson: 'Newton-Raphson',
  };

  const BADGE_CLASS = {
    bisection:      'badge-blue',
    secant:         'badge-purple',
    regula_falsi:   'badge-cyan',
    illinois:       'badge-amber',
    brent:          'badge-emerald',
    newton_raphson: 'badge-rose',
  };

  const PLOTLY_LAYOUT_BASE = {
    paper_bgcolor: 'transparent',
    plot_bgcolor:  'rgba(0,0,0,0.2)',
    font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 12 },
    margin: { t: 28, r: 24, b: 48, l: 56 },
    xaxis: {
      gridcolor: 'rgba(148,163,184,0.06)',
      zerolinecolor: 'rgba(148,163,184,0.1)',
      tickfont: { family: 'JetBrains Mono, monospace', size: 11 },
    },
    yaxis: {
      gridcolor: 'rgba(148,163,184,0.06)',
      zerolinecolor: 'rgba(148,163,184,0.1)',
      tickfont: { family: 'JetBrains Mono, monospace', size: 11 },
    },
    legend: {
      bgcolor: 'rgba(0,0,0,0.3)',
      bordercolor: 'rgba(148,163,184,0.1)',
      borderwidth: 1,
      font: { size: 11, color: '#cbd5e1' },
    },
    hoverlabel: {
      bgcolor: '#1a1f2e',
      bordercolor: 'rgba(148,163,184,0.2)',
      font: { family: 'Inter, sans-serif', size: 12, color: '#f8fafc' },
    },
  };

  const PLOTLY_CONFIG = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  };

  // ---------- DOM References ----------
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const dom = {
    loadingOverlay:    $('#loadingOverlay'),
    functionInput:     $('#functionInput'),
    inputA:            $('#inputA'),
    inputB:            $('#inputB'),
    inputX0:           $('#inputX0'),
    inputTolerance:    $('#inputTolerance'),
    inputMaxIter:      $('#inputMaxIter'),
    btnRun:            $('#btnRunAnalysis'),
    btnDemo:           $('#btnLoadDemo'),
    demoSelect:        $('#demoSelect'),
    selectAll:         $('#selectAllMethods'),
    deselectAll:       $('#deselectAllMethods'),
    headerBadge:       $('#headerBadge'),
    // Stats
    statMethodsRun:        $('#statMethodsRun'),
    statMethodsRunDetail:  $('#statMethodsRunDetail'),
    statFastest:           $('#statFastest'),
    statFastestDetail:     $('#statFastestDetail'),
    statAccurate:          $('#statAccurate'),
    statAccurateDetail:    $('#statAccurateDetail'),
    statConvergence:       $('#statConvergence'),
    statConvergenceDetail: $('#statConvergenceDetail'),
    // Tabs
    tabNav:           $('#tabNav'),
    tabResults:       $('#tabResults'),
    tabComparison:    $('#tabComparison'),
    tabConvergence:   $('#tabConvergence'),
    tabErrorDecay:    $('#tabErrorDecay'),
    tabAnalysis:      $('#tabAnalysis'),
    // Content
    resultsGrid:           $('#resultsGrid'),
    emptyResults:          $('#emptyResults'),
    comparisonTableBody:   $('#comparisonTableBody'),
    chartIterations:       $('#chartIterations'),
    chartTime:             $('#chartTime'),
    chartConvergence:      $('#chartConvergence'),
    chartErrorDecay:       $('#chartErrorDecay'),
    reasoningItems:        $('#reasoningItems'),
    emptyReasoning:        $('#emptyReasoning'),
    patternItems:          $('#patternItems'),
    emptyPatterns:         $('#emptyPatterns'),
    functionPropsCard:     $('#functionPropsCard'),
    functionPropsGrid:     $('#functionPropsGrid'),
    // Errors
    errorLogSection: $('#errorLogSection'),
    errorLogHeader:  $('#errorLogHeader'),
    errorLogBody:    $('#errorLogBody'),
    errorLogContent: $('#errorLogContent'),
    errorCount:      $('#errorCount'),
    errorToggleIcon: $('#errorToggleIcon'),
  };

  // ---------- Utility Functions ----------

  function formatNumber(n, digits) {
    if (n == null || isNaN(n)) return '—';
    digits = digits != null ? digits : 10;
    if (Math.abs(n) < 1e-14) return '0';
    if (Math.abs(n) >= 1e6 || (Math.abs(n) < 1e-4 && Math.abs(n) > 0)) {
      return n.toExponential(digits > 4 ? 6 : digits);
    }
    return parseFloat(n.toPrecision(digits)).toString();
  }

  function formatScientific(n) {
    if (n == null || isNaN(n)) return '—';
    if (n === 0) return '0';
    return n.toExponential(3);
  }

  function formatTime(ms) {
    if (ms == null || isNaN(ms)) return '—';
    if (ms < 0.001) return '< 0.001 ms';
    if (ms < 1) return ms.toFixed(3) + ' ms';
    if (ms < 1000) return ms.toFixed(2) + ' ms';
    return (ms / 1000).toFixed(2) + ' s';
  }

  function showLoading() {
    dom.loadingOverlay.classList.add('active');
  }

  function hideLoading() {
    dom.loadingOverlay.classList.remove('active');
  }

  function showError(message) {
    console.error('[Icarus]', message);
    addErrorEntry(message);
  }

  function addErrorEntry(msg) {
    dom.errorLogSection.classList.remove('hidden');
    const entry = document.createElement('div');
    entry.className = 'error-entry';
    entry.textContent = msg;
    dom.errorLogContent.appendChild(entry);
    const count = dom.errorLogContent.children.length;
    dom.errorCount.textContent = count;
  }

  function clearErrors() {
    dom.errorLogContent.innerHTML = '';
    dom.errorCount.textContent = '0';
    dom.errorLogSection.classList.add('hidden');
    dom.errorLogBody.classList.remove('open');
    dom.errorToggleIcon.classList.remove('open');
  }

  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ---------- Tab Navigation ----------

  function switchTab(tabName) {
    $$('.tab-btn').forEach(btn => btn.classList.remove('active'));
    $$('.tab-content').forEach(tc => tc.classList.remove('active'));

    const btn = $(`.tab-btn[data-tab="${tabName}"]`);
    const content = $(`#tab${capitalize(tabName)}`);

    if (btn) btn.classList.add('active');
    if (content) content.classList.add('active');

    // Trigger Plotly resize for chart tabs
    if (['comparison', 'convergence', 'error-decay'].includes(tabName)) {
      setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
    }
  }

  function capitalize(str) {
    return str.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('');
  }

  // ---------- API: Load Demos ----------

  async function loadDemos() {
    try {
      const resp = await fetch('/api/demos');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const demos = data.demos || data;
      dom.demoSelect.innerHTML = '<option value="">— Select a demo —</option>';
      if (Array.isArray(demos)) {
        demos.forEach((demo, i) => {
          const opt = document.createElement('option');
          opt.value = i;
          opt.textContent = demo.name || demo.function || `Demo ${i + 1}`;
          dom.demoSelect.appendChild(opt);
        });
      }
      window._demoData = demos;
    } catch (e) {
      console.warn('Could not load demos:', e.message);
    }
  }

  function loadDemo() {
    const idx = dom.demoSelect.value;
    if (idx === '' || !window._demoData) return;
    const demo = window._demoData[parseInt(idx)];
    if (!demo) return;

    dom.functionInput.value = demo.function || demo.func || '';
    if (demo.a != null) dom.inputA.value = demo.a;
    if (demo.b != null) dom.inputB.value = demo.b;
    if (demo.x0 != null) dom.inputX0.value = demo.x0;
    if (demo.tolerance) {
      const tolVal = String(demo.tolerance);
      for (const opt of dom.inputTolerance.options) {
        if (opt.value === tolVal) { dom.inputTolerance.value = tolVal; break; }
      }
    }
    if (demo.max_iterations) dom.inputMaxIter.value = demo.max_iterations;
  }

  // ---------- API: Run Analysis ----------

  async function runAnalysis() {
    clearErrors();

    // Collect form data
    const funcStr = dom.functionInput.value.trim();
    if (!funcStr) {
      showError('Please enter a function f(x).');
      return;
    }

    const methods = [];
    $$('input[name="method"]:checked').forEach(cb => methods.push(cb.value));
    if (methods.length === 0) {
      showError('Please select at least one method.');
      return;
    }

    const payload = {
      function: funcStr,
      a: parseFloat(dom.inputA.value),
      b: parseFloat(dom.inputB.value),
      x0: parseFloat(dom.inputX0.value),
      tolerance: parseFloat(dom.inputTolerance.value),
      max_iterations: parseInt(dom.inputMaxIter.value) || 100,
      methods: methods,
    };

    showLoading();

    try {
      const resp = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.error || errData.message || `Server error ${resp.status}`);
      }

      const data = await resp.json();

      // Convert results dictionary to array for the frontend components
      if (data.results && !Array.isArray(data.results)) {
        data.results = Object.keys(data.results).map(key => {
          return { method: key, ...data.results[key] };
        });
      }

      // Render all
      renderSummaryStats(data);
      renderResultCards(data);
      renderComparisonTable(data);
      renderComparisonCharts(data);
      renderConvergenceChart(data);
      renderErrorDecayChart(data);
      renderReasoning(data);
      renderPatterns(data);
      renderFunctionProperties(data);
      renderErrorLog(data.errors || []);

      dom.headerBadge.textContent = 'Analysis complete';
      dom.headerBadge.style.color = 'var(--accent-emerald)';
      dom.headerBadge.style.borderColor = 'rgba(16,185,129,0.3)';
      dom.headerBadge.style.background = 'rgba(16,185,129,0.08)';

    } catch (e) {
      showError(e.message);
    } finally {
      hideLoading();
    }
  }

  // ---------- Render: Summary Stats ----------

  function renderSummaryStats(data) {
    const results = data.results || [];
    const converged = results.filter(r => r.converged);

    // Methods run
    dom.statMethodsRun.textContent = results.length;
    dom.statMethodsRunDetail.textContent = `${converged.length} converged`;

    // Fastest
    if (converged.length > 0) {
      const fastest = converged.reduce((a, b) =>
        (a.execution_time_ms || Infinity) < (b.execution_time_ms || Infinity) ? a : b
      );
      dom.statFastest.textContent = METHOD_LABELS[fastest.method] || fastest.method;
      dom.statFastestDetail.textContent = formatTime(fastest.execution_time_ms);
    } else {
      dom.statFastest.textContent = '—';
      dom.statFastestDetail.textContent = 'No convergence';
    }

    // Most accurate
    if (converged.length > 0) {
      const accurate = converged.reduce((a, b) =>
        Math.abs(a.error || Infinity) < Math.abs(b.error || Infinity) ? a : b
      );
      dom.statAccurate.textContent = METHOD_LABELS[accurate.method] || accurate.method;
      dom.statAccurateDetail.textContent = '|ε| = ' + formatScientific(Math.abs(accurate.error));
    } else {
      dom.statAccurate.textContent = '—';
      dom.statAccurateDetail.textContent = 'No convergence';
    }

    // Convergence rate
    dom.statConvergence.textContent = `${converged.length}/${results.length}`;
    const pct = results.length > 0 ? Math.round((converged.length / results.length) * 100) : 0;
    dom.statConvergenceDetail.textContent = `${pct}% convergence rate`;
  }

  // ---------- Render: Result Cards ----------

  function renderResultCards(data) {
    const results = data.results || [];
    dom.resultsGrid.innerHTML = '';

    if (results.length === 0) {
      dom.resultsGrid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📊</div>
          <h3>No results</h3>
          <p>No methods returned results.</p>
        </div>`;
      return;
    }

    results.forEach((r) => {
      const status = r.converged ? 'converged' : (r.stagnated ? 'stagnated' : 'diverged');
      const statusIcon = r.converged ? '✓' : (r.stagnated ? '⚠' : '✗');
      const statusLabel = r.converged ? 'Converged' : (r.stagnated ? 'Stagnated' : 'Diverged');
      const methodKey = r.method || '';
      const label = METHOD_LABELS[methodKey] || methodKey;
      const badgeCls = BADGE_CLASS[methodKey] || 'badge-blue';

      // Error bar width (log-scale, clamped)
      let errWidth = 100;
      if (r.error != null && r.error !== 0) {
        const logErr = -Math.log10(Math.abs(r.error));
        errWidth = Math.min(100, Math.max(5, (logErr / 16) * 100));
      }

      const card = document.createElement('div');
      card.className = `method-card ${status}`;
      card.innerHTML = `
        <div class="card-header">
          <span class="method-name">${escapeHTML(label)} <span class="badge ${badgeCls}">${escapeHTML(methodKey)}</span></span>
          <span class="method-status ${status}">${statusIcon} ${statusLabel}</span>
        </div>
        <div class="card-metrics">
          <div class="metric">
            <span class="metric-label">Root</span>
            <span class="metric-value root-value">${formatNumber(r.root)}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Iterations</span>
            <span class="metric-value">${r.iterations != null ? r.iterations : '—'}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Time</span>
            <span class="metric-value">${formatTime(r.execution_time_ms)}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Error</span>
            <span class="metric-value">${formatScientific(r.error)}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Space</span>
            <span class="metric-value">${r.space_complexity || 'O(1)'}</span>
          </div>
          <div class="metric">
            <span class="metric-label">f(root)</span>
            <span class="metric-value">${formatScientific(r.f_root)}</span>
          </div>
        </div>
        <div class="error-indicator">
          <div class="error-fill" style="width: ${errWidth}%"></div>
        </div>
        <div class="method-explanation">
          ${escapeHTML(data.method_explanations ? data.method_explanations[methodKey] : '')}
        </div>`;
      dom.resultsGrid.appendChild(card);
    });
  }

  // ---------- Render: Comparison Table ----------

  function renderComparisonTable(data) {
    const results = data.results || [];
    dom.comparisonTableBody.innerHTML = '';

    // Sort by: converged first, then by error ascending
    const sorted = [...results].sort((a, b) => {
      if (a.converged && !b.converged) return -1;
      if (!a.converged && b.converged) return 1;
      return Math.abs(a.error || Infinity) - Math.abs(b.error || Infinity);
    });

    sorted.forEach((r, i) => {
      const rank = i + 1;
      const label = METHOD_LABELS[r.method] || r.method;
      const status = r.converged ? 'Converged' : (r.stagnated ? 'Stagnated' : 'Diverged');
      const statusCls = r.converged ? 'text-emerald' : (r.stagnated ? 'text-amber' : 'text-rose');
      const rankCls = rank <= 3 ? `rank-${rank}` : '';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="rank-cell ${rankCls}">#${rank}</td>
        <td>${escapeHTML(label)}</td>
        <td class="text-mono">${formatNumber(r.root, 12)}</td>
        <td class="text-mono">${r.iterations != null ? r.iterations : '—'}</td>
        <td class="text-mono">${r.execution_time_ms != null ? r.execution_time_ms.toFixed(3) : '—'}</td>
        <td class="text-mono">${formatScientific(r.error)}</td>
        <td class="${statusCls}">${status}</td>`;
      dom.comparisonTableBody.appendChild(tr);
    });
  }

  // ---------- Render: Comparison Charts (Bar) ----------

  function renderComparisonCharts(data) {
    const results = data.results || [];
    if (results.length === 0) return;

    const names = results.map(r => METHOD_LABELS[r.method] || r.method);
    const colors = results.map(r => METHOD_COLORS[r.method] || '#64748b');

    // Iterations chart
    Plotly.newPlot(dom.chartIterations, [{
      x: names,
      y: results.map(r => r.iterations || 0),
      type: 'bar',
      marker: {
        color: colors,
        line: { color: colors.map(c => c + '88'), width: 1 },
        opacity: 0.85,
      },
      hovertemplate: '%{x}<br>Iterations: %{y}<extra></extra>',
    }], {
      ...PLOTLY_LAYOUT_BASE,
      xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, title: '' },
      yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, title: 'Iterations' },
    }, PLOTLY_CONFIG);

    // Time chart
    Plotly.newPlot(dom.chartTime, [{
      x: names,
      y: results.map(r => r.execution_time_ms || 0),
      type: 'bar',
      marker: {
        color: colors,
        line: { color: colors.map(c => c + '88'), width: 1 },
        opacity: 0.85,
      },
      hovertemplate: '%{x}<br>Time: %{y:.4f} ms<extra></extra>',
    }], {
      ...PLOTLY_LAYOUT_BASE,
      xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, title: '' },
      yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, title: 'Time (ms)' },
    }, PLOTLY_CONFIG);
  }

  // ---------- Render: Convergence Chart ----------

  function renderConvergenceChart(data) {
    const results = data.results || [];
    const traces = [];

    results.forEach(r => {
      const history = r.iteration_history || r.convergence_history || r.steps || [];
      if (history.length === 0) return;

      const xVals = history.map((_, i) => i + 1);
      const yVals = history.map(h => h.x != null ? h.x : (h.approximation != null ? h.approximation : h));

      traces.push({
        x: xVals,
        y: yVals,
        mode: 'lines+markers',
        name: METHOD_LABELS[r.method] || r.method,
        line: { color: METHOD_COLORS[r.method] || '#64748b', width: 2 },
        marker: { size: 4 },
        hovertemplate: `${METHOD_LABELS[r.method] || r.method}<br>Iter: %{x}<br>x = %{y:.10f}<extra></extra>`,
      });
    });

    // Add true root line if available
    const trueRoot = data.true_root;
    if (trueRoot != null && traces.length > 0) {
      const maxIter = Math.max(...traces.map(t => Math.max(...t.x)));
      traces.push({
        x: [1, maxIter],
        y: [trueRoot, trueRoot],
        mode: 'lines',
        name: 'True Root',
        line: { color: '#f8fafc', width: 1.5, dash: 'dash' },
        hovertemplate: 'True Root: %{y:.10f}<extra></extra>',
      });
    }

    if (traces.length === 0) return;

    Plotly.newPlot(dom.chartConvergence, traces, {
      ...PLOTLY_LAYOUT_BASE,
      xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, title: 'Iteration' },
      yaxis: { ...PLOTLY_LAYOUT_BASE.yaxis, title: 'Approximation (x)' },
      showlegend: true,
    }, PLOTLY_CONFIG);
  }

  // ---------- Render: Error Decay Chart ----------

  function renderErrorDecayChart(data) {
    const results = data.results || [];
    const traces = [];

    results.forEach(r => {
      const history = r.iteration_history || r.convergence_history || r.steps || [];
      if (history.length === 0) return;

      const xVals = history.map((_, i) => i + 1);
      const yVals = history.map(h => {
        const err = h.error != null ? Math.abs(h.error) : (h.fx != null ? Math.abs(h.fx) : null);
        return err != null && err > 0 ? err : null;
      });

      traces.push({
        x: xVals,
        y: yVals,
        mode: 'lines+markers',
        name: METHOD_LABELS[r.method] || r.method,
        line: { color: METHOD_COLORS[r.method] || '#64748b', width: 2 },
        marker: { size: 4 },
        connectgaps: true,
        hovertemplate: `${METHOD_LABELS[r.method] || r.method}<br>Iter: %{x}<br>|error| = %{y:.4e}<extra></extra>`,
      });
    });

    if (traces.length === 0) return;

    Plotly.newPlot(dom.chartErrorDecay, traces, {
      ...PLOTLY_LAYOUT_BASE,
      xaxis: { ...PLOTLY_LAYOUT_BASE.xaxis, title: 'Iteration' },
      yaxis: {
        ...PLOTLY_LAYOUT_BASE.yaxis,
        title: '|Error|',
        type: 'log',
        exponentformat: 'e',
      },
      showlegend: true,
    }, PLOTLY_CONFIG);
  }

  // ---------- Render: Reasoning ----------

  function renderReasoning(data) {
    const reasoning = data.reasoning || [];
    dom.reasoningItems.innerHTML = '';

    if (reasoning.length === 0) {
      dom.reasoningItems.innerHTML = `
        <div class="empty-state" style="padding:32px;">
          <p class="text-dim">No analytical reasoning generated.</p>
        </div>`;
      return;
    }

    reasoning.forEach((text, i) => {
      const item = document.createElement('div');
      item.className = 'reasoning-item';
      item.style.animationDelay = `${i * 0.08}s`;
      item.innerHTML = `
        <span class="reasoning-icon">💡</span>
        <span class="reasoning-text">${escapeHTML(text)}</span>`;
      dom.reasoningItems.appendChild(item);
    });
  }

  // ---------- Render: Patterns ----------

  function renderPatterns(data) {
    const patterns = data.patterns || [];
    dom.patternItems.innerHTML = '';

    if (patterns.length === 0) {
      dom.patternItems.innerHTML = `
        <div class="empty-state" style="padding:32px;">
          <p class="text-dim">No patterns detected.</p>
        </div>`;
      return;
    }

    patterns.forEach((text, i) => {
      const item = document.createElement('div');
      item.className = 'pattern-item';
      item.style.animationDelay = `${i * 0.08}s`;
      item.innerHTML = `
        <span class="pattern-icon">🔍</span>
        <span class="pattern-text">${escapeHTML(text)}</span>`;
      dom.patternItems.appendChild(item);
    });
  }

  // ---------- Render: Function Properties ----------

  function renderFunctionProperties(data) {
    const props = data.function_properties || data.properties || null;
    if (!props) {
      dom.functionPropsCard.style.display = 'none';
      return;
    }

    dom.functionPropsCard.style.display = '';
    dom.functionPropsGrid.innerHTML = '';

    const entries = Object.entries(props);
    entries.forEach(([key, val]) => {
      const item = document.createElement('div');
      item.className = 'prop-item';
      const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      item.innerHTML = `
        <span class="prop-label">${escapeHTML(label)}</span>
        <span class="prop-value">${escapeHTML(String(val))}</span>`;
      dom.functionPropsGrid.appendChild(item);
    });
  }

  // ---------- Render: Error Log ----------

  function renderErrorLog(errors) {
    if (!errors || errors.length === 0) return;

    errors.forEach(err => {
      const msg = typeof err === 'string' ? err : (err.message || JSON.stringify(err));
      addErrorEntry(msg);
    });
  }

  // ---------- Event Listeners ----------

  function init() {
    // Run Analysis
    dom.btnRun.addEventListener('click', runAnalysis);

    // Load Demo
    dom.btnDemo.addEventListener('click', loadDemo);

    // Tab navigation
    dom.tabNav.addEventListener('click', (e) => {
      const btn = e.target.closest('.tab-btn');
      if (!btn) return;
      switchTab(btn.dataset.tab);
    });

    // Select All / Deselect All
    dom.selectAll.addEventListener('click', () => {
      $$('input[name="method"]').forEach(cb => cb.checked = true);
    });
    dom.deselectAll.addEventListener('click', () => {
      $$('input[name="method"]').forEach(cb => cb.checked = false);
    });

    // Error log toggle
    dom.errorLogHeader.addEventListener('click', () => {
      dom.errorLogBody.classList.toggle('open');
      dom.errorToggleIcon.classList.toggle('open');
    });

    // Keyboard shortcut: Ctrl+Enter to run
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runAnalysis();
      }
    });

    // Load demos on startup
    loadDemos();
  }

  // ---------- Bootstrap ----------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
