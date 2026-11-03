/**
 * DEVRAKSHAK // Web Dashboard & Offline Telemetry Client Controller
 */

const API_BASE = "/api";

const state = {
  activeTab: "tab-monitor",
  status: {},
  datasets: [],
  models: [],
  policies: [],
  lastTestResults: null,
  pollTimer: null,
  testFilter: "all"
};

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initEventListeners();
  loadInitialData();
  
  // Auto-poll status and monitor telemetry every 10 seconds
  state.pollTimer = setInterval(pollTelemetry, 10000);
});

/* ==========================================================================
   Navigation
   ========================================================================== */
function initNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.target;
      switchTab(target);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll(".nav-tab").forEach(t => {
    t.classList.toggle("active", t.dataset.target === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach(p => {
    p.classList.toggle("active", p.id === tabId);
  });

  // Lazy-load data depending on tab
  if (tabId === "tab-monitor") loadMonitorStats();
  else if (tabId === "tab-test") populateTestForm();
  else if (tabId === "tab-datasets") loadDatasetsList();
  else if (tabId === "tab-train") populateTrainForm();
  else if (tabId === "tab-runs") loadRunsList();
  else if (tabId === "tab-policies") loadPoliciesList();
  else if (tabId === "tab-logs") loadLogs();
}

/* ==========================================================================
   Initial Data & Status Polling
   ========================================================================== */
async function loadInitialData() {
  await Promise.all([
    fetchStatus(),
    fetchDatasets(),
    fetchModels(),
    loadMonitorStats()
  ]);
  populateTestForm();
  populateTrainForm();
}

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/status`);
    const data = await res.json();
    if (data.success) {
      state.status = data;
      renderStatusHeader(data);
    }
  } catch (err) {
    console.error("Failed to fetch status:", err);
  }
}

function renderStatusHeader(data) {
  const modelBadge = document.getElementById("header-model-badge");
  const eventCounter = document.getElementById("header-event-counter");
  if (modelBadge) {
    modelBadge.innerHTML = `<span class="pulse-dot"></span> MODEL: <strong>${data.active_model}</strong> [${data.active_task.toUpperCase()}]`;
  }
  if (eventCounter) {
    eventCounter.textContent = `${data.total_detection_events} Events / ${data.total_attacks_detected} Attacks`;
  }
}

async function pollTelemetry() {
  await fetchStatus();
  if (state.activeTab === "tab-monitor") {
    loadMonitorStats();
  }
}

/* ==========================================================================
   Tab 1: Monitor / Live Telemetry
   ========================================================================== */
async function loadMonitorStats() {
  try {
    const [statsRes, eventsRes] = await Promise.all([
      fetch(`${API_BASE}/stats`),
      fetch(`${API_BASE}/events?limit=25`)
    ]);
    const statsData = await statsRes.json();
    const eventsData = await eventsRes.json();

    if (statsData.success) {
      const s = statsData.stats;
      document.getElementById("stat-total-events").textContent = (s.total_events || 0).toLocaleString();
      document.getElementById("stat-attacks").textContent = (s.total_attacks || 0).toLocaleString();
      document.getElementById("stat-benign").textContent = (s.total_benign || 0).toLocaleString();

      const sev = s.by_severity || {};
      document.getElementById("stat-critical").textContent = (sev.CRITICAL || 0).toLocaleString();
      document.getElementById("stat-high").textContent = (sev.HIGH || 0).toLocaleString();

      renderAttackCategoryChart(s.by_category || {});
    }

    if (eventsData.success) {
      renderRecentEventsTable(eventsData.events || []);
    }
  } catch (err) {
    console.error("Error loading monitor stats:", err);
  }
}

function renderAttackCategoryChart(categories) {
  const container = document.getElementById("attack-category-chart");
  if (!container) return;
  container.innerHTML = "";

  const total = Object.values(categories).reduce((a, b) => a + b, 0);
  if (total === 0) {
    container.innerHTML = `<div style="color: var(--text-dim); padding: 1rem 0; font-family: var(--font-mono); font-size: 0.8rem;">No attack events recorded yet. Run an inference test on official dataset to generate telemetry.</div>`;
    return;
  }

  const colors = {
    DDoS: "var(--neon-red)",
    Mirai: "#f43f5e",
    DoS: "var(--neon-amber)",
    Recon: "var(--neon-purple)",
    Spoofing: "#06b6d4",
    Web: "#ec4899",
    BruteForce: "#f97316",
    Benign: "var(--neon-green)",
    Attack: "var(--neon-red)"
  };

  const sorted = Object.entries(categories).sort((a, b) => b[1] - a[1]);
  sorted.forEach(([cat, count]) => {
    const pct = ((count / total) * 100).toFixed(1);
    const color = colors[cat] || "var(--neon-cyan)";

    const row = document.createElement("div");
    row.className = "chart-bar-row";
    row.innerHTML = `
      <div class="chart-bar-label" title="${cat}">${cat}</div>
      <div class="chart-bar-track">
        <div class="chart-bar-fill" style="width: ${pct}%; background: ${color}"></div>
      </div>
      <div class="chart-bar-val">${count} <span style="font-size: 0.65rem; color: var(--text-dim)">(${pct}%)</span></div>
    `;
    container.appendChild(row);
  });
}

function renderRecentEventsTable(events) {
  const tbody = document.getElementById("recent-events-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (events.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 2rem;">No detection events in database. Use the "Dataset Testing" tab to run inference.</td></tr>`;
    return;
  }

  events.forEach(e => {
    const tr = document.createElement("tr");
    const sevClass = `badge-${(e.severity || 'info').toLowerCase()}`;
    const typeClass = e.is_attack ? 'badge-attack' : 'badge-benign';

    tr.innerHTML = `
      <td style="color: var(--text-dim); font-size: 0.72rem;">${new Date(e.timestamp).toLocaleTimeString()}</td>
      <td style="font-weight: 600;">${e.source_file}</td>
      <td>#${e.row_index}</td>
      <td><span class="badge ${typeClass}">${e.predicted_label}</span></td>
      <td><strong>${(e.confidence * 100).toFixed(1)}%</strong></td>
      <td><span class="badge ${sevClass}">${e.severity}</span></td>
      <td style="color: var(--neon-cyan); font-size: 0.72rem;">${e.policy_triggered || "—"}</td>
    `;
    tbody.appendChild(tr);
  });
}

/* ==========================================================================
   Tab 2: Dataset Testing & Inference (PRIMARY FOCUS)
   ========================================================================== */
async function fetchDatasets() {
  try {
    const res = await fetch(`${API_BASE}/datasets`);
    const data = await res.json();
    if (data.success) {
      state.datasets = data.files;
    }
  } catch (err) {
    console.error("Failed to load datasets:", err);
  }
}

async function fetchModels() {
  try {
    const res = await fetch(`${API_BASE}/models`);
    const data = await res.json();
    if (data.success) {
      state.models = data.models;
    }
  } catch (err) {
    console.error("Failed to load models:", err);
  }
}

function populateTestForm() {
  const fileSelect = document.getElementById("test-dataset-select");
  const modelSelect = document.getElementById("test-model-select");
  if (!fileSelect || !modelSelect) return;

  // Clear options
  fileSelect.innerHTML = "";
  modelSelect.innerHTML = "";

  // Datasets options: prioritize the newly added official MERGED_CSV files!
  const mergedFiles = state.datasets.filter(d => d.name.toLowerCase().includes("merged"));
  const otherFiles = state.datasets.filter(d => !d.name.toLowerCase().includes("merged"));

  if (mergedFiles.length > 0) {
    const optGroupMerged = document.createElement("optgroup");
    optGroupMerged.label = `⭐ Newly Added Official CICIoT2023 (${mergedFiles.length} files)`;
    mergedFiles.forEach(f => {
      const opt = document.createElement("option");
      opt.value = f.path;
      opt.textContent = `${f.name} (${f.size_mb} MB)`;
      optGroupMerged.appendChild(opt);
    });
    fileSelect.appendChild(optGroupMerged);
  }

  if (otherFiles.length > 0) {
    const optGroupOther = document.createElement("optgroup");
    optGroupOther.label = "Other Datasets (Synthetic / Partition)";
    otherFiles.forEach(f => {
      const opt = document.createElement("option");
      opt.value = f.path;
      opt.textContent = `${f.name} (${f.size_mb} MB)`;
      optGroupOther.appendChild(opt);
    });
    fileSelect.appendChild(optGroupOther);
  }

  // Model options
  state.models.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m.path;
    opt.textContent = `${m.name} (${m.task.toUpperCase()} | ${m.algorithm}) ${m.is_active ? '★ ACTIVE' : ''}`;
    if (m.is_active) opt.selected = true;
    modelSelect.appendChild(opt);
  });
}

async function executeInferenceTest() {
  const fileSelect = document.getElementById("test-dataset-select");
  const modelSelect = document.getElementById("test-model-select");
  const sampleLimitInput = document.getElementById("test-sample-limit");
  const recordEventsCheckbox = document.getElementById("test-record-events");
  const runBtn = document.getElementById("btn-run-test");
  const spinner = document.getElementById("test-loading-spinner");
  const resultsContainer = document.getElementById("test-results-container");

  const filePath = fileSelect.value;
  const modelPath = modelSelect.value;
  const sampleLimit = parseInt(sampleLimitInput.value) || 100;
  const recordEvents = recordEventsCheckbox.checked;

  if (!filePath) {
    alert("Please select a dataset file to test.");
    return;
  }

  runBtn.disabled = true;
  spinner.style.display = "inline-flex";
  resultsContainer.style.display = "none";

  try {
    const res = await fetch(`${API_BASE}/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: filePath,
        model_path: modelPath,
        sample_limit: sampleLimit,
        record_events: recordEvents
      })
    });

    const data = await res.json();
    if (!data.success) {
      alert(`Testing error: ${data.error}\n${data.details || ''}`);
      return;
    }

    state.lastTestResults = data;
    renderTestResults(data);
    resultsContainer.style.display = "block";
    
    // Refresh stats and monitor
    pollTelemetry();
  } catch (err) {
    console.error("Test execution failed:", err);
    alert(`Failed to execute test: ${err.message}`);
  } finally {
    runBtn.disabled = false;
    spinner.style.display = "none";
  }
}

function renderTestResults(data) {
  const s = data.summary;
  document.getElementById("test-res-file").textContent = s.dataset_file;
  document.getElementById("test-res-samples").textContent = s.total_samples_tested;
  document.getElementById("test-res-attacks").textContent = s.attacks_detected;
  document.getElementById("test-res-benign").textContent = s.benign_detected;
  document.getElementById("test-res-latency").textContent = `${s.latency_ms_per_sample} ms`;
  document.getElementById("test-res-model").textContent = `${s.model_used} (${s.model_task})`;

  const accCard = document.getElementById("test-res-accuracy-card");
  const accVal = document.getElementById("test-res-accuracy");
  if (s.has_ground_truth) {
    accCard.style.display = "block";
    accVal.textContent = `${s.accuracy_percentage}%`;
    document.getElementById("test-res-correct").textContent = `${s.correct_predictions} / ${s.total_samples_tested}`;
    document.getElementById("test-res-misclassified").textContent = s.misclassified;
  } else {
    accCard.style.display = "none";
  }

  // Render Category Breakdown Bars
  const breakdownContainer = document.getElementById("test-category-breakdown");
  breakdownContainer.innerHTML = "";
  const predDist = s.predicted_distribution || {};
  Object.entries(predDist).forEach(([cat, cnt]) => {
    const pct = ((cnt / s.total_samples_tested) * 100).toFixed(1);
    const row = document.createElement("div");
    row.className = "chart-bar-row";
    row.innerHTML = `
      <div class="chart-bar-label">${cat}</div>
      <div class="chart-bar-track">
        <div class="chart-bar-fill" style="width: ${pct}%; background: var(--neon-cyan)"></div>
      </div>
      <div class="chart-bar-val">${cnt} (${pct}%)</div>
    `;
    breakdownContainer.appendChild(row);
  });

  // Render Detailed Records Table
  applyTestFilter("all");
}

function applyTestFilter(filterType) {
  state.testFilter = filterType;
  document.querySelectorAll(".test-filter-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.filter === filterType);
  });

  if (!state.lastTestResults) return;

  const records = state.lastTestResults.records || [];
  let filtered = records;

  if (filterType === "attacks") {
    filtered = records.filter(r => r.is_attack);
  } else if (filterType === "benign") {
    filtered = records.filter(r => !r.is_attack);
  } else if (filterType === "mismatches") {
    filtered = records.filter(r => r.is_match === false);
  } else if (filterType === "critical") {
    filtered = records.filter(r => r.severity === "CRITICAL" || r.severity === "HIGH");
  }

  const tbody = document.getElementById("test-records-tbody");
  tbody.innerHTML = "";

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 1.5rem;">No flow samples match filter "${filterType}".</td></tr>`;
    return;
  }

  filtered.forEach(r => {
    const tr = document.createElement("tr");
    const sevClass = `badge-${(r.severity || 'info').toLowerCase()}`;
    const typeClass = r.is_attack ? 'badge-attack' : 'badge-benign';

    let matchBadge = "";
    if (r.is_match === true) {
      matchBadge = `<span class="badge badge-match">MATCH</span>`;
    } else if (r.is_match === false) {
      matchBadge = `<span class="badge badge-mismatch">MISMATCH</span>`;
    } else {
      matchBadge = `<span style="color: var(--text-dim)">—</span>`;
    }

    // Key features string
    const featStr = Object.entries(r.key_features || {})
      .map(([k, v]) => `<span style="color: var(--text-dim)">${k}:</span> <span style="color: var(--neon-cyan)">${v}</span>`)
      .join(" | ");

    tr.innerHTML = `
      <td style="color: var(--text-dim);">#${r.row_index}</td>
      <td><strong>${r.ground_truth_raw || '—'}</strong> <span style="color: var(--text-dim); font-size: 0.7rem;">(${r.ground_truth_mapped})</span></td>
      <td><span class="badge ${typeClass}">${r.predicted_label}</span></td>
      <td>${matchBadge}</td>
      <td><strong>${(r.confidence * 100).toFixed(1)}%</strong></td>
      <td><span class="badge ${sevClass}">${r.severity}</span></td>
      <td style="color: var(--text-muted); font-size: 0.72rem;">${r.policy_triggered || "—"}</td>
      <td style="font-size: 0.7rem; font-family: var(--font-mono);">${featStr || "—"}</td>
    `;
    tbody.appendChild(tr);
  });
}

function exportTestResults(format = "csv") {
  if (!state.lastTestResults || !state.lastTestResults.records) {
    alert("No test results available to export.");
    return;
  }

  const records = state.lastTestResults.records;
  if (format === "json") {
    const blob = new Blob([JSON.stringify(state.lastTestResults, null, 2)], { type: "application/json" });
    downloadBlob(blob, `devrakshak_test_${Date.now()}.json`);
  } else {
    // CSV Export
    const headers = ["row_index", "ground_truth_raw", "ground_truth_mapped", "predicted_label", "is_match", "confidence", "is_attack", "attack_category", "severity", "policy_triggered"];
    const rows = records.map(r => [
      r.row_index,
      `"${r.ground_truth_raw || ''}"`,
      `"${r.ground_truth_mapped || ''}"`,
      `"${r.predicted_label}"`,
      r.is_match,
      r.confidence,
      r.is_attack,
      `"${r.attack_category}"`,
      r.severity,
      `"${r.policy_triggered || ''}"`
    ]);
    const csvContent = [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    downloadBlob(blob, `devrakshak_test_${Date.now()}.csv`);
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* ==========================================================================
   Tab 3: Datasets & Audit
   ========================================================================== */
async function loadDatasetsList() {
  await fetchDatasets();
  const tbody = document.getElementById("datasets-table-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  state.datasets.forEach(d => {
    const tr = document.createElement("tr");
    const isMerged = d.name.toLowerCase().includes("merged");
    const tag = isMerged ? '<span class="badge" style="background: rgba(0, 240, 255, 0.2); color: var(--neon-cyan)">OFFICIAL NEW</span>' : (d.is_synthetic ? '<span class="badge badge-info">SYNTHETIC</span>' : '<span class="badge badge-benign">RAW</span>');

    tr.innerHTML = `
      <td><strong>${d.name}</strong> ${tag}</td>
      <td>${d.type}</td>
      <td><strong>${d.size_mb} MB</strong></td>
      <td style="color: var(--text-dim); font-size: 0.72rem;">${d.relative_path}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="auditSingleFile('${d.path.replace(/\\/g, '\\\\')}', '${d.name}')">🔍 Audit File</button>
        <button class="btn btn-primary btn-sm" onclick="jumpToTestWithFile('${d.path.replace(/\\/g, '\\\\')}')">⚡ Run Test</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function jumpToTestWithFile(filePath) {
  switchTab("tab-test");
  const select = document.getElementById("test-dataset-select");
  if (select) {
    select.value = filePath;
  }
}

async function auditSingleFile(filePath, fileName) {
  const modal = document.getElementById("audit-modal");
  const modalTitle = document.getElementById("audit-modal-title");
  const modalBody = document.getElementById("audit-modal-body");
  
  modal.style.display = "flex";
  modalTitle.textContent = `Auditing: ${fileName}`;
  modalBody.innerHTML = `<div style="text-align: center; padding: 3rem;"><span class="pulse-dot"></span> Performing memory-conscious chunk audit...</div>`;

  try {
    const res = await fetch(`${API_BASE}/audit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: filePath, max_rows: 50000 })
    });
    const data = await res.json();
    if (!data.success) {
      modalBody.innerHTML = `<div style="color: var(--neon-red); padding: 2rem;">Audit failed: ${data.error}</div>`;
      return;
    }

    const a = data.audit;
    let classRows = "";
    const dist = a.class_distribution || {};
    const totalLabeled = Object.values(dist).reduce((acc, v) => acc + v, 0);

    Object.entries(dist).forEach(([cls, count]) => {
      const pct = totalLabeled > 0 ? ((count / totalLabeled) * 100).toFixed(1) : 0;
      classRows += `
        <tr>
          <td><strong>${cls}</strong></td>
          <td>${count.toLocaleString()}</td>
          <td>${pct}%</td>
        </tr>
      `;
    });

    modalBody.innerHTML = `
      <div class="grid-cols-4" style="margin-bottom: 1.5rem;">
        <div class="metric-card" style="--accent: var(--neon-cyan)">
          <div class="metric-label">Audited Rows</div>
          <div class="metric-value">${(a.total_rows || 0).toLocaleString()}</div>
        </div>
        <div class="metric-card" style="--accent: var(--neon-green)">
          <div class="metric-label">Columns</div>
          <div class="metric-value">${a.column_count}</div>
          <div class="metric-sub">Target: ${a.target_column || 'None'}</div>
        </div>
        <div class="metric-card" style="--accent: var(--neon-amber)">
          <div class="metric-label">Missing / Inf Values</div>
          <div class="metric-value">${a.missing_value_count + a.infinite_value_count}</div>
        </div>
        <div class="metric-card" style="--accent: var(--neon-purple)">
          <div class="metric-label">Duplicate Rows</div>
          <div class="metric-value">${(a.duplicate_row_count || 0).toLocaleString()}</div>
        </div>
      </div>

      <div class="card" style="margin-bottom: 1rem;">
        <div class="card-header"><span class="card-title">Class Distribution (First ${a.total_rows.toLocaleString()} Rows)</span></div>
        <div class="card-body" style="padding: 0;">
          <table class="data-table">
            <thead>
              <tr><th>Class Label</th><th>Count</th><th>Percentage</th></tr>
            </thead>
            <tbody>${classRows || '<tr><td colspan="3">No labels found.</td></tr>'}</tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div style="color: var(--neon-red)">Error: ${err.message}</div>`;
  }
}

function closeAuditModal() {
  document.getElementById("audit-modal").style.display = "none";
}

/* ==========================================================================
   Tab 4: Model Training Studio
   ========================================================================== */
function populateTrainForm() {
  const trainDatasetSelect = document.getElementById("train-dataset-select");
  if (!trainDatasetSelect) return;
  trainDatasetSelect.innerHTML = "";

  state.datasets.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.path;
    opt.textContent = `${d.name} (${d.size_mb} MB) [${d.type}]`;
    trainDatasetSelect.appendChild(opt);
  });
}

async function startModelTraining() {
  const datasetPath = document.getElementById("train-dataset-select").value;
  const taskType = document.getElementById("train-task-type").value;
  const modelName = document.getElementById("train-model-name").value;
  const featureSelector = document.getElementById("train-feature-selector").value;
  const nFeatures = parseInt(document.getElementById("train-n-features").value) || 15;
  const sampleLimit = parseInt(document.getElementById("train-sample-limit").value) || 10000;
  const resampling = document.getElementById("train-resampling").value;
  const useClassWeight = document.getElementById("train-class-weight").checked;

  const btn = document.getElementById("btn-start-training");
  const spinner = document.getElementById("train-loading-spinner");
  const resultCard = document.getElementById("train-result-card");

  btn.disabled = true;
  spinner.style.display = "inline-flex";
  resultCard.style.display = "none";

  try {
    const res = await fetch(`${API_BASE}/train`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_path: datasetPath,
        task_type: taskType,
        model_name: modelName,
        feature_selector: featureSelector,
        n_features: nFeatures,
        sample_limit: sampleLimit,
        resampling_strategy: resampling,
        use_class_weight: useClassWeight
      })
    });

    const data = await res.json();
    if (!data.success) {
      alert(`Training failed: ${data.error}`);
      return;
    }

    renderTrainingResults(data);
    resultCard.style.display = "block";
    await fetchModels();
    populateTestForm();
  } catch (err) {
    alert(`Training request failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    spinner.style.display = "none";
  }
}

function renderTrainingResults(data) {
  const r = data.run;
  document.getElementById("train-res-f1").textContent = (r.macro_f1 * 100).toFixed(2) + "%";
  document.getElementById("train-res-acc").textContent = (r.accuracy * 100).toFixed(2) + "%";
  document.getElementById("train-res-latency").textContent = `${r.inference_latency_ms_per_sample.toFixed(4)} ms`;
  document.getElementById("train-res-duration").textContent = `${r.training_duration_seconds.toFixed(2)}s`;
  document.getElementById("train-res-samples").textContent = `${r.train_samples} Train / ${r.test_samples} Test`;
  document.getElementById("train-res-path").textContent = data.model_path;

  // Selected features
  const featsContainer = document.getElementById("train-res-features");
  featsContainer.innerHTML = "";
  (data.features_selected || []).forEach(f => {
    const tag = document.createElement("span");
    tag.className = "badge";
    tag.style.background = "var(--neon-purple-dim)";
    tag.style.color = "var(--neon-purple)";
    tag.style.border = "1px solid rgba(168, 85, 247, 0.4)";
    tag.style.margin = "0.2rem";
    tag.textContent = f;
    featsContainer.appendChild(tag);
  });
}

/* ==========================================================================
   Tab 5: Historical Runs
   ========================================================================== */
async function loadRunsList() {
  const tbody = document.getElementById("runs-table-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/runs?limit=50`);
    const data = await res.json();
    if (!data.success || !data.runs || data.runs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 2rem;">No historical training runs found.</td></tr>`;
      return;
    }

    data.runs.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-weight: 700; color: var(--neon-cyan);">${r.run_id}</td>
        <td style="color: var(--text-dim); font-size: 0.72rem;">${new Date(r.timestamp).toLocaleString()}</td>
        <td><strong>${r.model_name}</strong> (${r.task_type})</td>
        <td><span class="badge" style="background: var(--bg-highlight);">${r.feature_selector.toUpperCase()} (${r.selected_features_count})</span></td>
        <td style="color: var(--neon-green); font-weight: 700;">${(r.macro_f1 * 100).toFixed(2)}%</td>
        <td><strong>${(r.accuracy * 100).toFixed(2)}%</strong></td>
        <td>${r.inference_latency_ms_per_sample.toFixed(4)} ms</td>
        <td style="color: var(--neon-green); font-size: 0.75rem;">${r.status}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load runs:", err);
  }
}

/* ==========================================================================
   Tab 6: Security Policies
   ========================================================================== */
async function loadPoliciesList() {
  const container = document.getElementById("policies-list-container");
  if (!container) return;
  container.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/policies`);
    const data = await res.json();
    if (!data.success) return;
    state.policies = data.policies;

    data.policies.forEach((p, idx) => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.marginBottom = "1rem";

      const isChecked = p.enabled ? "checked" : "";
      const sevClass = `badge-${p.severity.toLowerCase()}`;

      card.innerHTML = `
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <input type="checkbox" id="policy-enable-${idx}" ${isChecked} style="cursor: pointer; transform: scale(1.3);">
            <strong style="color: #ffffff;">${p.policy_id}: ${p.name}</strong>
            <span class="badge ${sevClass}">${p.severity}</span>
          </div>
          <span style="color: var(--neon-cyan); font-family: var(--font-mono); font-size: 0.8rem;">Action: ${p.action}</span>
        </div>
        <div class="card-body">
          <p style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.75rem;">${p.description}</p>
          <div style="display: flex; align-items: center; gap: 1rem;">
            <label class="form-label" style="margin: 0;">Confidence Threshold:</label>
            <input type="range" id="policy-thresh-${idx}" min="0.1" max="1.0" step="0.05" value="${p.confidence_threshold}" style="flex: 1;" oninput="document.getElementById('thresh-val-${idx}').textContent = Math.round(this.value * 100) + '%'">
            <span id="thresh-val-${idx}" style="font-family: var(--font-mono); font-weight: 700; width: 45px; text-align: right;">${Math.round(p.confidence_threshold * 100)}%</span>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load policies:", err);
  }
}

async function saveUpdatedPolicies() {
  if (!state.policies || state.policies.length === 0) return;

  const payload = state.policies.map((p, idx) => {
    const enabledInput = document.getElementById(`policy-enable-${idx}`);
    const threshInput = document.getElementById(`policy-thresh-${idx}`);
    return {
      policy_id: p.policy_id,
      enabled: enabledInput ? enabledInput.checked : p.enabled,
      confidence_threshold: threshInput ? parseFloat(threshInput.value) : p.confidence_threshold
    };
  });

  try {
    const res = await fetch(`${API_BASE}/policies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policies: payload })
    });
    const data = await res.json();
    if (data.success) {
      alert("✅ Security policies successfully saved and applied to defense engine!");
      loadPoliciesList();
    }
  } catch (err) {
    alert("Failed to save policies: " + err.message);
  }
}

/* ==========================================================================
   Tab 7: System Logs
   ========================================================================== */
async function loadLogs() {
  const terminal = document.getElementById("log-terminal-body");
  const sevSelect = document.getElementById("log-severity-filter");
  const sev = sevSelect ? sevSelect.value : "";

  try {
    const res = await fetch(`${API_BASE}/logs?limit=100&severity=${sev}`);
    const data = await res.json();
    if (!data.success) return;

    terminal.innerHTML = "";
    if (data.lines.length === 0) {
      terminal.innerHTML = `<div style="color: var(--text-dim)">No log records found matching filter.</div>`;
      return;
    }

    data.lines.forEach(l => {
      const lineDiv = document.createElement("div");
      let lineClass = "info";
      if (l.includes("ERROR") || l.includes("CRITICAL")) lineClass = "error";
      else if (l.includes("WARNING")) lineClass = "warning";
      else if (l.includes("DEBUG")) lineClass = "debug";

      lineDiv.className = `log-line ${lineClass}`;
      lineDiv.textContent = l;
      terminal.appendChild(lineDiv);
    });

    terminal.scrollTop = terminal.scrollHeight;
  } catch (err) {
    console.error("Failed to load logs:", err);
  }
}

function initEventListeners() {
  // Test execute button
  const runTestBtn = document.getElementById("btn-run-test");
  if (runTestBtn) runTestBtn.addEventListener("click", executeInferenceTest);

  // Train button
  const trainBtn = document.getElementById("btn-start-training");
  if (trainBtn) trainBtn.addEventListener("click", startModelTraining);

  // Save policies button
  const savePolBtn = document.getElementById("btn-save-policies");
  if (savePolBtn) savePolBtn.addEventListener("click", saveUpdatedPolicies);

  // Filter buttons for test results
  document.querySelectorAll(".test-filter-btn").forEach(btn => {
    btn.addEventListener("click", () => applyTestFilter(btn.dataset.filter));
  });
}

