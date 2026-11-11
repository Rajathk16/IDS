"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, BarChart3, CheckCircle2, ChevronDown, ChevronLeft, ChevronRight,
  CircleHelp, ClipboardList, Database, Download, FileSearch, Filter, Gauge, History, LayoutDashboard,
  ListFilter, LoaderCircle, Menu, RefreshCw, Search, ServerCog, Settings2, Shield, SlidersHorizontal,
  TerminalSquare, X, XCircle, Zap,
} from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

type AnyRecord = Record<string, any>;
type ApiState = { status: AnyRecord | null; datasets: AnyRecord[]; models: AnyRecord[]; stats: AnyRecord | null; events: AnyRecord[]; policies: AnyRecord[]; runs: AnyRecord[]; logs: any[]; settings: AnyRecord | null };
type TestFlow = AnyRecord & { row_index?: number; ground_truth_mapped?: string; predicted_label?: string; confidence?: number; severity?: string; key_features?: Record<string, number> };

const NAV = [
  { group: "MONITORING & ANALYSIS", items: [{ id: "overview", label: "Overview", icon: LayoutDashboard }, { id: "traffic", label: "Traffic Analysis", icon: Activity }, { id: "alerts", label: "Security Alerts", icon: AlertTriangle }] },
  { group: "MACHINE LEARNING", items: [{ id: "models", label: "Model Laboratory", icon: BarChart3 }, { id: "features", label: "Feature Selection", icon: SlidersHorizontal }] },
  { group: "DATA & HISTORY", items: [{ id: "datasets", label: "Dataset Management", icon: Database }, { id: "runs", label: "Run History", icon: History }] },
  { group: "SYSTEM", items: [{ id: "system", label: "System Logs & Config", icon: ServerCog }] },
];
const PAGE_META: Record<string, { title: string; description: string }> = {
  overview: { title: "Overview", description: "Offline evaluation results and current analysis status." },
  traffic: { title: "Traffic Analysis", description: "Inspect classified flows returned by the offline test endpoint." },
  alerts: { title: "Security Alerts", description: "Review detections and the policy rules associated with each event." },
  models: { title: "Model Laboratory", description: "Compare recorded evaluation results and launch a training run." },
  features: { title: "Feature Selection", description: "LRRC-FS scoring terms, recorded feature curves, and selection stability." },
  datasets: { title: "Dataset Management", description: "Inspect available files, the recorded split, and run an audit." },
  runs: { title: "Run History", description: "Review training runs from the connected API and compare two runs." },
  system: { title: "System Logs & Config", description: "Review API logs, runtime configuration, and connection status." },
};
const CLASS_COLORS: Record<string, string> = { DDoS: "#991b1b", DoS: "#dc2626", Mirai: "#be123c", Recon: "#d97706", Spoofing: "#c2410c", Web: "#b91c1c", BruteForce: "#991b1b", Benign: "#15803d" };
const PIE_COLORS = ["#b91c1c", "#dc2626", "#be123c", "#d97706", "#c2410c", "#ef4444", "#991b1b", "#16a34a"];
const fmt = (value: unknown, digits = 0) => typeof value === "number" && Number.isFinite(value) ? value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits }) : "Unavailable";
const pct = (value: unknown, digits = 2) => typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(digits)}%` : "Unavailable";
const first = (...values: any[]) => values.find((value) => value !== null && value !== undefined && value !== "");
const labelName = (value: unknown) => String(value ?? "Unavailable").replaceAll("_", " ");

async function getJson(url: string) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}
function EmptyState({ title = "Unavailable", detail }: { title?: string; detail?: string }) {
  return <div className="empty-state"><div className="empty-icon"><CircleHelp size={18} /></div><strong>{title}</strong>{detail && <span>{detail}</span>}</div>;
}
function Panel({ title, eyebrow, action, children, className = "" }: { title: string; eyebrow?: string; action?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return <section className={`panel ${className}`}><header className="panel-head"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h2>{title}</h2></div>{action}</header><div className="panel-content">{children}</div></section>;
}
function Kpi({ label, value, caption, tone, icon: Icon }: { label: string; value: string; caption: string; tone: string; icon: any }) {
  return <article className="kpi-card"><div className="kpi-top"><span className="eyebrow">{label}</span><span className={`kpi-icon ${tone}`}><Icon size={17} /></span></div><div className={`kpi-value ${tone}`}>{value}</div><div className="kpi-caption">{caption}</div></article>;
}
function ClassBadge({ name }: { name: unknown }) {
  const cls = String(name ?? "Unavailable");
  const color = CLASS_COLORS[cls] || "#64748b";
  return <span className="class-badge" style={{ color, borderColor: `${color}44`, backgroundColor: `${color}12` }}>{cls}</span>;
}
function SeverityBadge({ value }: { value: unknown }) {
  const sev = String(value ?? "Unavailable").toUpperCase();
  const color = ["CRITICAL", "HIGH"].includes(sev) ? "danger" : sev === "MEDIUM" ? "warning" : sev === "LOW" ? "info" : "neutral";
  return <span className={`severity-badge ${color}`}>{sev}</span>;
}
function MetricCell({ value, isRate = false }: { value: unknown; isRate?: boolean }) {
  return <span className="mono">{typeof value === "number" ? isRate ? pct(value) : fmt(value, 4) : "Unavailable"}</span>;
}
function ExportButton({ data, disabled, formats = ["CSV", "JSON"] }: { data: any[]; disabled?: boolean; formats?: string[] }) {
  const [format, setFormat] = useState(formats[0]);
  const exportData = () => {
    if (disabled || !data.length) return;
    let body = "";
    let mime = "application/json";
    let ext = "json";
    if (format === "CSV") {
      const keys = Array.from(new Set(data.flatMap((row) => Object.keys(row ?? {}))));
      const esc = (value: any) => `"${String(typeof value === "object" ? JSON.stringify(value) : value ?? "").replaceAll('"', '""')}"`;
      body = [keys.map(esc).join(","), ...data.map((row) => keys.map((key) => esc(row?.[key])).join(","))].join("\n");
      mime = "text/csv"; ext = "csv";
    } else body = JSON.stringify(data, null, 2);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([body], { type: mime }));
    link.download = `devrakshak-export.${ext}`; link.click(); URL.revokeObjectURL(link.href);
  };
  return <div className="export-control"><select aria-label="Export format" value={format} onChange={(event) => setFormat(event.target.value)}>{formats.map((item) => <option key={item}>{item}</option>)}</select><button className="button button-primary" onClick={exportData} disabled={disabled || !data.length}><Download size={15} />Export</button></div>;
}

export default function DevrakshakConsole() {
  const [activePage, setActivePage] = useState("overview");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [api, setApi] = useState<ApiState>({ status: null, datasets: [], models: [], stats: null, events: [], policies: [], runs: [], logs: [], settings: null });
  const [evaluation, setEvaluation] = useState<AnyRecord | null>(null);
  const [datasetSummary, setDatasetSummary] = useState<AnyRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [flows, setFlows] = useState<TestFlow[]>([]);
  const [testSummary, setTestSummary] = useState<AnyRecord | null>(null);
  const [selectedDataset, setSelectedDataset] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [sampleLimit, setSampleLimit] = useState(200);
  const [testBusy, setTestBusy] = useState(false);
  const [trainBusy, setTrainBusy] = useState(false);
  const [trainResult, setTrainResult] = useState<AnyRecord | null>(null);
  const [auditBusy, setAuditBusy] = useState(false);
  const [auditResult, setAuditResult] = useState<AnyRecord | null>(null);
  const [query, setQuery] = useState("");
  const [classFilter, setClassFilter] = useState("All classes");
  const [severityFilter, setSeverityFilter] = useState("All severities");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [logLevel, setLogLevel] = useState("ALL");
  const [runA, setRunA] = useState("");
  const [runB, setRunB] = useState("");
  const [toast, setToast] = useState("");
  const [training, setTraining] = useState({ model_name: "random_forest", task_type: "binary", feature_selector: "lrrc", n_features: 15, sample_limit: 15000, strategy: "plain" });
  const notify = (message: string) => { setToast(message); window.setTimeout(() => setToast(""), 3600); };

  const refresh = useCallback(async () => {
    setRefreshing(true);
    const requests: [keyof ApiState, string, string][] = [
      ["status", "/api/status", "status"], ["datasets", "/api/datasets", "files"], ["models", "/api/models", "models"],
      ["stats", "/api/stats", "stats"], ["events", "/api/events?limit=100", "events"], ["policies", "/api/policies", "policies"],
      ["runs", "/api/runs?limit=100", "runs"], ["logs", "/api/logs?limit=100", "lines"], ["settings", "/api/settings", "settings"],
    ];
    const updates: Partial<ApiState> = {};
    await Promise.all(requests.map(async ([key, url, field]) => {
      try {
        const data = await getJson(url);
        if (data.success === false) return;
        const value = key === "status" ? data : key === "logs" ? (Array.isArray(data.lines) ? data.lines : []) : key === "datasets" || key === "models" || key === "events" || key === "runs" ? (Array.isArray(data[field]) ? data[field] : []) : (data[field] ?? data);
        (updates as any)[key] = value;
      } catch { /* API is optional while working offline; the UI shows explicit unavailable states. */ }
    }));
    setApi((current) => ({ ...current, ...updates }));
    if (Array.isArray(updates.datasets) && updates.datasets.length && !selectedDataset) setSelectedDataset(String(updates.datasets[0].path ?? ""));
    if (Array.isArray(updates.models) && updates.models.length && !selectedModel) {
      const active = updates.models.find((model: AnyRecord) => model.is_active) ?? updates.models[0];
      setSelectedModel(String(active.path ?? ""));
    }
    setRefreshing(false); setLoading(false);
  }, [selectedDataset, selectedModel]);

  useEffect(() => {
    void refresh();
    Promise.all([getJson("/data/evaluation.json").catch(() => null), getJson("/data/dataset-summary.json").catch(() => null)]).then(([evalData, datasetData]) => {
      if (evalData) setEvaluation(evalData);
      if (datasetData?.available && datasetData.data) setDatasetSummary({ ...datasetData.data, source: datasetData.source });
      else if (datasetData) setDatasetSummary(null);
    });
  }, [refresh]);

  const testFlows = async () => {
    if (!selectedDataset) { notify("Select an available dataset file first."); return; }
    setTestBusy(true);
    try {
      const response = await fetch("/api/test", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file_path: selectedDataset, model_path: selectedModel || undefined, sample_limit: sampleLimit, record_events: true }) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || `${response.status} ${response.statusText}`);
      setFlows(Array.isArray(data.records) ? data.records : []); setTestSummary(data.summary ?? null); notify(`Classified ${data.records?.length ?? 0} flows.`); void refresh();
    } catch (error: any) { notify(`Test failed: ${error.message}`); }
    finally { setTestBusy(false); }
  };
  const trainModel = async () => {
    if (!selectedDataset) { notify("Select a dataset file before training."); return; }
    setTrainBusy(true);
    try {
      const response = await fetch("/api/train", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataset_path: selectedDataset, model_name: training.model_name, task_type: training.task_type, feature_selector: training.feature_selector, n_features: Number(training.n_features), sample_limit: Number(training.sample_limit), use_class_weight: training.strategy === "class_weight", resampling_strategy: training.strategy === "undersampling" ? "rus" : training.strategy === "smote" ? "smote" : "none" }) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || `${response.status} ${response.statusText}`);
      setTrainResult(data.run ?? data); notify("Training completed and run recorded."); void refresh();
    } catch (error: any) { notify(`Training failed: ${error.message}`); }
    finally { setTrainBusy(false); }
  };
  const auditDataset = async () => {
    setAuditBusy(true); setAuditResult(null);
    try {
      const response = await fetch("/api/audit", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: selectedDataset || undefined, max_rows: 50000 }) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || `${response.status} ${response.statusText}`);
      setAuditResult(data.audit ?? data); notify("Dataset audit complete.");
    } catch (error: any) { notify(`Audit unavailable: ${error.message}`); }
    finally { setAuditBusy(false); }
  };

  const resultRows = useMemo(() => evaluation?.results && typeof evaluation.results === "object" && !Array.isArray(evaluation.results) ? Object.entries(evaluation.results).map(([key, value]: [string, any]) => ({ key, ...value })) : Array.isArray(evaluation?.results) ? evaluation.results : [], [evaluation]);
  const classDistribution = useMemo(() => Object.entries(datasetSummary?.test_class_distribution ?? {}).map(([name, value]) => ({ name, count: Number(value) })).filter((row) => Number.isFinite(row.count)), [datasetSummary]);
  const activeModel = api.models.find((model) => model.is_active) ?? api.models.find((model) => model.path === selectedModel) ?? (api.status?.active_model && api.status.active_model !== "None" ? { name: api.status.active_model, task: api.status.active_task } : null);
  const eventSeverities = api.events.reduce((acc: Record<string, number>, event) => { const severity = String(event.severity ?? "UNKNOWN").toUpperCase(); acc[severity] = (acc[severity] ?? 0) + 1; return acc; }, {});
  const latestSeverity = ["CRITICAL", "HIGH", "MEDIUM", "LOW"].find((severity) => eventSeverities[severity] > 0) ?? "Unavailable";
  const benignTestCount = datasetSummary?.test_class_distribution?.Benign;
  const binaryResult = resultRows.find((row) => String(row.key ?? "").startsWith("binary_"));
  const fprCountPresent = typeof binaryResult?.fpr_count === "number" && typeof binaryResult?.benign_count === "number" && Array.isArray(binaryResult?.fpr_ci_95);
  const pageTitle = PAGE_META[activePage];

  const filteredFlows = useMemo(() => flows.filter((row) => {
    const name = String(row.predicted_label ?? row.ground_truth_mapped ?? "");
    const severity = String(row.severity ?? "").toUpperCase();
    const text = `${row.row_index ?? ""} ${row.ground_truth_mapped ?? ""} ${row.predicted_label ?? ""} ${row.attack_category ?? ""} ${JSON.stringify(row.key_features ?? {})}`.toLowerCase();
    return (classFilter === "All classes" || name === classFilter || row.ground_truth_mapped === classFilter) && (severityFilter === "All severities" || severity === severityFilter.toUpperCase()) && (!query || text.includes(query.toLowerCase()));
  }), [flows, classFilter, severityFilter, query]);
  const pages = Math.max(1, Math.ceil(filteredFlows.length / pageSize));
  const visibleFlows = filteredFlows.slice((page - 1) * pageSize, page * pageSize);
  const visibleAlerts = api.events.filter((event) => severityFilter === "All severities" || String(event.severity ?? "").toUpperCase() === severityFilter.toUpperCase());
  const filteredLogs = api.logs.filter((entry) => logLevel === "ALL" || String(typeof entry === "string" ? entry : entry.level ?? "INFO").toUpperCase() === logLevel);
  const selectedRunA = api.runs.find((run) => String(run.run_id) === runA);
  const selectedRunB = api.runs.find((run) => String(run.run_id) === runB);

  const datasetOptions = api.datasets.map((item) => ({ path: String(item.path ?? ""), name: String(item.name ?? item.relative_path ?? item.path ?? "Unavailable") })).filter((item) => item.path);
  const exportRows = flows.map((record) => ({ ...record, source_file: record.source_file ?? selectedDataset.split(/[\\/]/).pop() }));

  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
      <div className="brand-lockup"><div className="brand-mark"><Shield size={19} strokeWidth={2.3} /></div><div><div className="brand-name">DEVRAKSHAK</div><div className="brand-subtitle">IDS Console</div></div><button className="icon-button sidebar-close" aria-label="Close menu" onClick={() => setMobileOpen(false)}><X size={18} /></button></div>
      <div className="sidebar-status"><span className={`status-dot ${api.status ? "online" : "offline"}`} /><span>{api.status ? "API CONNECTED" : "API UNAVAILABLE"}</span><span className="status-ping" /></div>
      <nav className="sidebar-nav" aria-label="Console navigation">{NAV.map((section) => <div className="nav-section" key={section.group}><div className="nav-label">{section.group}</div>{section.items.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${activePage === id ? "active" : ""}`} onClick={() => { setActivePage(id); setMobileOpen(false); }}><Icon size={16} /><span>{label}</span>{id === "alerts" && api.events.length > 0 && <span className="nav-count">{api.events.length}</span>}</button>)}</div>)}</nav>
      <div className="sidebar-bottom"><div className="offline-note"><span className="offline-note-dot" /><div><strong>OFFLINE EVALUATION</strong><small>CICIoT2023 benchmark</small></div></div><div className="sidebar-version">DEVRAKSHAK <span>•</span> IDS Console</div></div>
    </aside>
    {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <div className="main-column">
      <header className="topbar"><div className="topbar-left"><button className="icon-button menu-toggle" aria-label="Open menu" onClick={() => setMobileOpen(true)}><Menu size={19} /></button><div className="breadcrumb"><span>Console</span><span className="crumb-slash">/</span><strong>{pageTitle.title}</strong></div></div><div className="topbar-right"><span className={`top-chip pipeline ${api.status ? "" : "muted"}`}><span className="tiny-dot" />Pipeline {api.status ? "ready" : "unavailable"}</span><span className="top-chip model-chip"><span className="model-chip-dot" />{activeModel?.name ?? "Model unavailable"}</span><span className={`top-chip severity-chip ${latestSeverity === "Unavailable" ? "muted" : ""}`}><span className="severity-dot" />{latestSeverity}</span><button className="button button-light top-export" onClick={() => { if (!flows.length) { setActivePage("traffic"); notify("Run an offline flow test before exporting records."); return; } const blob = new Blob([JSON.stringify(flows, null, 2)], { type: "application/json" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "devrakshak-flow-export.json"; link.click(); URL.revokeObjectURL(link.href); }}><Download size={14} />Export</button><button className={`icon-button ${refreshing ? "spinning" : ""}`} aria-label="Refresh console data" onClick={() => void refresh()}><RefreshCw size={16} /></button></div></header>
      <main className="workspace"><div className="page-heading"><div><div className="eyebrow page-eyebrow">DEVRAKSHAK <span>/</span> OFFLINE ANALYTICS</div><h1>{pageTitle.title}</h1><p>{pageTitle.description}</p></div>{loading && <span className="loading-inline"><LoaderCircle size={15} className="spin" /> Loading source data</span>}</div>

      {activePage === "overview" && <div className="page-stack">
        <div className="source-banner"><div className="source-symbol"><Database size={18} /></div><div className="source-text"><strong>Offline evaluation results</strong><span>Research metrics are read from generated result files; live flow inspection uses the existing API.</span></div><span className="source-tag">CICIoT2023</span></div>
        <div className="kpi-grid">
          <Kpi label="TEST FLOWS" value={datasetSummary ? fmt(datasetSummary.n_test) : fmt(testSummary?.total_samples_tested)} caption={datasetSummary ? `Held-out split · ${datasetSummary.source ?? "data/processed/dataset_build_summary.json"}` : "Held-out count unavailable"} tone="blue" icon={Activity} />
          <Kpi label="BENIGN TEST FLOWS" value={fmt(benignTestCount)} caption="Count from held-out split summary" tone="green" icon={CheckCircle2} />
          <Kpi label="BINARY ACCURACY" value={pct(binaryResult?.accuracy?.mean)} caption={binaryResult ? `Recorded mean${binaryResult.accuracy?.std !== undefined ? ` · σ ${fmt(binaryResult.accuracy.std, 4)}` : ""}` : "Evaluation result unavailable"} tone="blue" icon={Gauge} />
          <Kpi label="MACRO-F1" value={pct(binaryResult?.macro_f1?.mean)} caption="Recorded binary evaluation mean" tone="blue" icon={BarChart3} />
          <Kpi label="BALANCED ACCURACY" value={pct(binaryResult?.balanced_accuracy?.mean)} caption="Recorded binary evaluation mean" tone="blue" icon={Activity} />
          <Kpi label="FPR · 95% CI" value={fprCountPresent ? `${fmt(binaryResult.fpr_count)} / ${fmt(binaryResult.benign_count)}` : "Unavailable"} caption={fprCountPresent ? `95% CI ${binaryResult.fpr_ci_95[0]}–${binaryResult.fpr_ci_95[1]}` : "Count and 95% interval not included in source"} tone="orange" icon={AlertTriangle} />
        </div>
        <div className="overview-grid"><Panel title="Held-out class distribution" eyebrow="TEST SPLIT" action={<span className="panel-source">dataset summary</span>} className="distribution-panel">{classDistribution.length ? <div className="chart-split"><div className="donut-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={classDistribution} dataKey="count" nameKey="name" innerRadius="66%" outerRadius="90%" paddingAngle={2} stroke="#fff" strokeWidth={2}>{classDistribution.map((item, index) => <Cell key={item.name} fill={CLASS_COLORS[item.name] ?? PIE_COLORS[index % PIE_COLORS.length]} />)}</Pie><Tooltip formatter={(value: any) => fmt(Number(value))} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>{fmt(datasetSummary?.n_test)}</strong><span>TEST FLOWS</span></div></div><div className="legend-list">{classDistribution.map((item) => <div className="legend-row" key={item.name}><span className="legend-dot" style={{ background: CLASS_COLORS[item.name] ?? "#64748b" }} /><span className="legend-name">{item.name}</span><strong className="mono">{fmt(item.count)}</strong></div>)}</div></div> : <EmptyState title="Unavailable" detail="The split summary does not contain test-class counts." />}</Panel>
          <Panel title="Active model" eyebrow="API STATUS" action={<span className={`state-label ${activeModel ? "state-green" : "state-muted"}`}><span />{activeModel ? "ACTIVE" : "UNAVAILABLE"}</span>} className="active-model-panel">{activeModel ? <div className="active-model-body"><div className="model-emblem"><Zap size={21} /></div><div><div className="model-title">{activeModel.name}</div><div className="model-kind">{activeModel.algorithm ?? activeModel.task ?? "Model metadata"}</div></div><div className="model-details"><div><span>Task</span><strong>{activeModel.task ?? activeModel.task_type ?? "Unavailable"}</strong></div><div><span>Model file</span><strong className="truncate">{activeModel.relative_path ?? activeModel.path ?? "Unavailable"}</strong></div><div><span>Evaluation mode</span><strong>Offline</strong></div></div></div> : <EmptyState title="No active model reported" detail="Connect the backend API to load model status." />}</Panel></div>
        <Panel title="Model comparison" eyebrow="RECORDED EVALUATIONS" action={<span className="panel-source">{evaluation?.source ?? "results unavailable"}</span>}>{resultRows.length ? <div className="table-scroll"><table><thead><tr><th>Evaluation</th><th>Accuracy</th><th>Balanced accuracy</th><th>Macro-F1</th><th>Weighted-F1</th><th>Latency · ms/flow</th></tr></thead><tbody>{resultRows.map((row, index) => <tr key={row.key ?? row.name ?? index}><td className="strong-cell">{labelName(row.key ?? row.name ?? row.model)}</td><td><MetricCell value={row.accuracy?.mean ?? row.accuracy} isRate /></td><td><MetricCell value={row.balanced_accuracy?.mean ?? row.balanced_accuracy} isRate /></td><td><MetricCell value={row.macro_f1?.mean ?? row.macro_f1} isRate /></td><td><MetricCell value={row.weighted_f1?.mean ?? row.weighted_f1} isRate /></td><td><MetricCell value={row.latency_ms?.mean ?? row.latency_ms} /></td></tr>)}</tbody></table></div> : <EmptyState title="Evaluation results unavailable" detail="Run node scripts/export-results.mjs after result files are available." />}</Panel>
        <div className="data-footnote"><FileSearch size={14} />Data source: <code>{evaluation?.source ?? "results/final_results.csv / results/final_results.json (unavailable)"}</code> · <code>{datasetSummary?.source ?? "data/processed/dataset_build_summary.json (unavailable)"}</code></div>
      </div>}

      {activePage === "traffic" && <div className="page-stack"><Panel title="Offline flow inspection" eyebrow="API · POST /api/test" action={<ExportButton data={exportRows} disabled={!flows.length} />}><div className="toolbar-grid"><label className="field"><span>Dataset file</span><select value={selectedDataset} onChange={(event) => setSelectedDataset(event.target.value)}><option value="">Select file</option>{datasetOptions.map((item) => <option key={item.path} value={item.path}>{item.name}</option>)}</select></label><label className="field"><span>Model</span><select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)}><option value="">API active model</option>{api.models.map((model, index) => <option key={model.path ?? index} value={model.path}>{model.name ?? model.path}</option>)}</select></label><label className="field"><span>Sample limit</span><select value={sampleLimit} onChange={(event) => setSampleLimit(Number(event.target.value))}>{[100, 200, 500, 1000, 5000].map((size) => <option key={size} value={size}>{fmt(size)} flows</option>)}</select></label><button className="button button-primary run-button" onClick={() => void testFlows()} disabled={testBusy || !selectedDataset}>{testBusy ? <LoaderCircle size={15} className="spin" /> : <Activity size={15} />}{testBusy ? "Inspecting…" : "Run test"}</button></div>{testSummary && <div className="result-strip"><span>Dataset <strong>{testSummary.dataset_file ?? "Unavailable"}</strong></span><span>Flows <strong className="mono">{fmt(testSummary.total_samples_tested)}</strong></span><span>Accuracy <strong>{pct(typeof testSummary.accuracy_percentage === "number" ? testSummary.accuracy_percentage / 100 : undefined)}</strong></span><span>Latency <strong className="mono">{fmt(testSummary.latency_ms_per_sample, 4)} ms per flow</strong></span></div>}
          <div className="filter-row"><label className="search-box"><Search size={15} /><input value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Search label, feature, row…" /></label><label className="filter-select"><ListFilter size={14} /><select value={classFilter} onChange={(event) => { setClassFilter(event.target.value); setPage(1); }}><option>All classes</option>{Array.from(new Set(flows.flatMap((row) => [row.predicted_label, row.ground_truth_mapped]).filter(Boolean))).map((item) => <option key={item}>{item}</option>)}</select></label><label className="filter-select"><Filter size={14} /><select value={severityFilter} onChange={(event) => { setSeverityFilter(event.target.value); setPage(1); }}><option>All severities</option>{["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].map((item) => <option key={item}>{item}</option>)}</select></label><span className="row-count">{fmt(filteredFlows.length)} flows</span></div>
          {visibleFlows.length ? <><div className="table-scroll"><table><thead><tr><th>ROW</th><th>TRUE LABEL</th><th>PREDICTION</th><th>CONFIDENCE</th><th>SEVERITY</th><th>KEY FEATURES</th></tr></thead><tbody>{visibleFlows.map((row, index) => <tr key={`${row.row_index ?? index}-${index}`}><td className="mono">{fmt(row.row_index)}</td><td><ClassBadge name={row.ground_truth_mapped ?? row.ground_truth_raw} /></td><td className="strong-cell"><ClassBadge name={row.predicted_label} /></td><td className="mono">{pct(row.confidence)}</td><td><SeverityBadge value={row.severity} /></td><td className="feature-cell">{row.key_features && Object.keys(row.key_features).length ? Object.entries(row.key_features).slice(0, 4).map(([key, value]) => <span key={key}><b>{key}</b> {typeof value === "number" ? value.toPrecision(4) : String(value)}</span>) : "Unavailable"}</td></tr>)}</tbody></table></div><div className="pagination"><span>Page {page} of {pages}</span><label>Rows <select value={pageSize} onChange={(event) => { setPageSize(Number(event.target.value)); setPage(1); }}><option value={10}>10</option><option value={25}>25</option><option value={50}>50</option></select></label><button className="icon-button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} aria-label="Previous page"><ChevronLeft size={17} /></button><button className="icon-button" disabled={page >= pages} onClick={() => setPage((value) => value + 1)} aria-label="Next page"><ChevronRight size={17} /></button></div></> : <EmptyState title={flows.length ? "No flows match these filters" : "No classified flows"} detail={flows.length ? "Adjust search or filters." : "Choose a dataset file and run the existing /api/test endpoint."} />}</Panel><div className="data-footnote"><FileSearch size={14} />Flow data source: <code>POST /api/test</code>. No fixture or demo records are displayed.</div></div>}

      {activePage === "alerts" && <div className="page-stack"><div className="severity-grid">{["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((severity) => <div className={`severity-card sev-${severity.toLowerCase()}`} key={severity}><span className="eyebrow">{severity}</span><strong>{api.events.length ? fmt(eventSeverities[severity] ?? 0) : "Unavailable"}</strong><small>API events</small></div>)}</div><Panel title="Detection events" eyebrow="API · /api/events" action={<span className="panel-source">Policy association only</span>}><div className="filter-row"><label className="filter-select"><Filter size={14} /><select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}><option>All severities</option>{["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].map((item) => <option key={item}>{item}</option>)}</select></label><span className="row-count">{api.events.length ? `${fmt(visibleAlerts.length)} events` : "Unavailable"}</span></div>{visibleAlerts.length ? <div className="table-scroll"><table><thead><tr><th>TIME</th><th>CLASS</th><th>SEVERITY</th><th>CONFIDENCE</th><th>POLICY</th><th>OUTCOME</th></tr></thead><tbody>{visibleAlerts.map((event, index) => <tr key={event.id ?? index}><td className="mono">{event.timestamp ? new Date(event.timestamp).toLocaleString() : "Unavailable"}</td><td><ClassBadge name={event.predicted_label ?? event.attack_category} /></td><td><SeverityBadge value={event.severity} /></td><td className="mono">{pct(event.confidence)}</td><td className="mono">{event.policy_id ?? event.policy_triggered ?? "Unavailable"}</td><td><span className={event.policy_id || event.policy_triggered ? "outcome-triggered" : "outcome-none"}>{event.policy_id || event.policy_triggered ? "Policy triggered" : "No policy"}</span></td></tr>)}</tbody></table></div> : <EmptyState title="No API detections available" detail="Connect the backend or run an offline flow inspection. No mitigation or quarantine outcomes are inferred." />}</Panel>{api.policies.length > 0 && <Panel title="Configured policies" eyebrow="API · /api/policies"><div className="table-scroll"><table><thead><tr><th>POLICY</th><th>NAME</th><th>SEVERITY</th><th>STATUS</th><th>DESCRIPTION</th></tr></thead><tbody>{api.policies.map((policy, index) => <tr key={policy.policy_id ?? index}><td className="mono">{policy.policy_id ?? "Unavailable"}</td><td className="strong-cell">{policy.name ?? "Unavailable"}</td><td><SeverityBadge value={policy.severity} /></td><td>{policy.enabled === false ? "Disabled" : policy.enabled === true ? "Enabled" : "Unavailable"}</td><td>{policy.description ?? "Unavailable"}</td></tr>)}</tbody></table></div></Panel>}</div>}

      {activePage === "models" && <div className="page-stack"><Panel title="Recorded model comparison" eyebrow="OFFLINE RESULTS" action={<span className="panel-source">{evaluation?.source ?? "source unavailable"}</span>}>{resultRows.length ? <div className="table-scroll"><table><thead><tr><th>MODEL / STRATEGY</th><th>ACCURACY</th><th>BALANCED ACC.</th><th>MACRO-F1</th><th>WEIGHTED-F1</th><th>MCC</th><th>MS / FLOW</th></tr></thead><tbody>{resultRows.map((row, index) => <tr key={row.key ?? index}><td className="strong-cell">{labelName(row.key ?? row.name)}</td><td><MetricCell value={row.accuracy?.mean ?? row.accuracy} isRate /></td><td><MetricCell value={row.balanced_accuracy?.mean ?? row.balanced_accuracy} isRate /></td><td><MetricCell value={row.macro_f1?.mean ?? row.macro_f1} isRate /></td><td><MetricCell value={row.weighted_f1?.mean ?? row.weighted_f1} isRate /></td><td><MetricCell value={row.mcc?.mean ?? row.mcc} /></td><td><MetricCell value={row.latency_ms?.mean ?? row.latency_ms} /></td></tr>)}</tbody></table></div> : <EmptyState title="Model metrics unavailable" detail="Metrics appear only when present in generated real result files." />}</Panel><div className="lab-grid"><Panel title="Binary confusion matrix" eyebrow="OFFLINE EVALUATION"><EmptyState title="Unavailable" detail="No confusion-matrix count source is available in the API or exported result data." /></Panel><Panel title="Per-class performance" eyebrow="PRECISION · RECALL · F1 · SUPPORT">{evaluation?.files?.perClassMetrics && evaluation.perClassMetrics?.length ? <div className="table-scroll"><table><thead><tr>{Object.keys(evaluation.perClassMetrics[0]).map((key: string) => <th key={key}>{key}</th>)}</tr></thead><tbody>{evaluation.perClassMetrics.map((row: AnyRecord, index: number) => <tr key={index}>{Object.values(row).map((value: any, cell: number) => <td key={cell}>{String(value)}</td>)}</tr>)}</tbody></table></div> : <EmptyState title="Per-class metrics unavailable" detail="results/per_class_metrics.csv was not present when the export ran." />}</Panel></div><Panel title="Train a model" eyebrow="API · POST /api/train"><div className="toolbar-grid training-fields"><label className="field"><span>Model</span><select value={training.model_name} onChange={(event) => setTraining({ ...training, model_name: event.target.value })}>{["random_forest", "decision_tree", "extra_trees", "gradient_boosting"].map((name) => <option key={name}>{name}</option>)}</select></label><label className="field"><span>Task</span><select value={training.task_type} onChange={(event) => setTraining({ ...training, task_type: event.target.value })}><option value="binary">Binary</option><option value="multiclass">Multiclass</option></select></label><label className="field"><span>Feature selector</span><select value={training.feature_selector} onChange={(event) => setTraining({ ...training, feature_selector: event.target.value })}>{["lrrc", "selectkbest", "variance", "all"].map((name) => <option key={name}>{name}</option>)}</select></label><label className="field"><span>Features (k)</span><input type="number" min="1" value={training.n_features} onChange={(event) => setTraining({ ...training, n_features: Number(event.target.value) })} /></label><label className="field"><span>Sample limit</span><input type="number" min="1" value={training.sample_limit} onChange={(event) => setTraining({ ...training, sample_limit: Number(event.target.value) })} /></label><label className="field"><span>Imbalance strategy</span><select value={training.strategy} onChange={(event) => setTraining({ ...training, strategy: event.target.value })}>{["plain", "class_weight", "undersampling", "smote"].map((name) => <option key={name}>{name}</option>)}</select></label><button className="button button-primary run-button" onClick={() => void trainModel()} disabled={trainBusy || !selectedDataset}>{trainBusy ? <LoaderCircle size={15} className="spin" /> : <Zap size={15} />}{trainBusy ? "Training…" : "Train model"}</button></div>{trainResult && <div className="result-strip"><span>Run <strong>{trainResult.run_id ?? "Recorded"}</strong></span><span>Accuracy <strong>{pct(trainResult.accuracy)}</strong></span><span>Macro-F1 <strong>{pct(trainResult.macro_f1)}</strong></span><span>Selected features <strong>{fmt(trainResult.selected_features_count)}</strong></span></div>}</Panel></div>}

      {activePage === "features" && <div className="page-stack"><Panel title="LRRC-FS scoring formulation" eyebrow="FOUR-TERM FEATURE RANKING"><div className="formula-box"><span className="formula">Score(f, S) = w<sub>rel</sub> · R̂(f,y) − w<sub>red</sub> · D̂(f,S) − w<sub>cost</sub> · Ĉ(f) + w<sub>stab</sub> · ŝ(f)</span><span className="formula-caption">Weights and component scores are shown only when reported by source data.</span></div><div className="term-grid"><div><strong>01 · Relevance</strong><span>Target association</span></div><div><strong>02 · Redundancy</strong><span>Correlation with selected features</span></div><div><strong>03 · Computation cost</strong><span>Feature extraction effort</span></div><div><strong>04 · Stability</strong><span>Repeat selection consistency</span></div></div></Panel><div className="lab-grid"><Panel title="Macro-F1 vs. k" eyebrow="FEATURE CURVE">{evaluation?.files?.accuracyVsFeatures && evaluation.featureCurve?.length ? <ResponsiveContainer width="100%" height={250}><LineChart data={evaluation.featureCurve}><CartesianGrid strokeDasharray="3 3" stroke="#e7ebf0" /><XAxis dataKey={Object.keys(evaluation.featureCurve[0]).find((key: string) => /feature|^k$/i.test(key))} /><YAxis /><Tooltip /><Legend />{Object.keys(evaluation.featureCurve[0]).slice(1).map((key: string, index: number) => <Line key={key} type="monotone" dataKey={key} stroke={PIE_COLORS[index % PIE_COLORS.length]} dot={false} />)}</LineChart></ResponsiveContainer> : <EmptyState title="Feature curve unavailable" detail="results/accuracy_vs_features.csv is missing or contains no rows." />}</Panel><Panel title="Selector comparison" eyebrow="MACRO-F1 & COST">{evaluation?.files?.accuracyVsFeatures && evaluation.featureCurve?.length ? <ResponsiveContainer width="100%" height={250}><BarChart data={evaluation.featureCurve}><CartesianGrid strokeDasharray="3 3" stroke="#e7ebf0" /><XAxis dataKey={Object.keys(evaluation.featureCurve[0])[0]} /><YAxis /><Tooltip /><Legend />{Object.keys(evaluation.featureCurve[0]).slice(1).map((key: string, index: number) => <Bar key={key} dataKey={key} fill={PIE_COLORS[index % PIE_COLORS.length]} radius={[4, 4, 0, 0]} />)}</BarChart></ResponsiveContainer> : <EmptyState title="Selector results unavailable" detail="Comparison values require the recorded feature-curve CSV." />}</Panel></div><div className="lab-grid"><Panel title="Selected features" eyebrow="SCORE COMPONENTS"><EmptyState title="Unavailable" detail="No selected-feature score-part table is included in the exported sources." /></Panel><Panel title="Feature stability" eyebrow="REPEAT SELECTION"><div className="table-scroll">{evaluation?.files?.featureStability && evaluation.featureStability?.length ? <table><thead><tr>{Object.keys(evaluation.featureStability[0]).map((key: string) => <th key={key}>{key}</th>)}</tr></thead><tbody>{evaluation.featureStability.map((row: AnyRecord, index: number) => <tr key={index}>{Object.values(row).map((value: any, cell: number) => <td key={cell}>{String(value)}</td>)}</tr>)}</tbody></table> : <EmptyState title="Feature stability unavailable" detail="results/feature_stability.csv is missing or contains no rows." />}</div></Panel></div></div>}

      {activePage === "datasets" && <div className="page-stack"><div className="dataset-split-grid">{[["TRAIN", datasetSummary?.n_train], ["VALIDATION", datasetSummary?.n_val], ["TEST", datasetSummary?.n_test]].map(([label, value]) => <div className="split-card" key={String(label)}><span className="eyebrow">{label} SPLIT</span><strong>{datasetSummary ? fmt(value) : "Unavailable"}</strong><small>flows in recorded summary</small></div>)}</div><div className="lab-grid"><Panel title="Partition class counts" eyebrow="TEST SET"><div className="table-scroll">{classDistribution.length ? <table><thead><tr><th>CLASS</th><th>FLOWS</th><th>SHARE</th></tr></thead><tbody>{classDistribution.map((item) => <tr key={item.name}><td><ClassBadge name={item.name} /></td><td className="mono">{fmt(item.count)}</td><td className="mono">{datasetSummary?.n_test ? pct(item.count / datasetSummary.n_test) : "Unavailable"}</td></tr>)}</tbody></table> : <EmptyState title="Split summary unavailable" detail="Run the exporter to read data/processed/dataset_build_summary.json." />}</div></Panel><Panel title="Split files" eyebrow="RECORDED PARTITION"><div className="split-file-group"><h3>TRAIN FILES <span>{fmt(datasetSummary?.train_files?.length)}</span></h3>{datasetSummary?.train_files?.length ? <div className="file-chips">{datasetSummary.train_files.map((file: string) => <code key={file}>{file}</code>)}</div> : <EmptyState title="Unavailable" />}</div><div className="split-file-group"><h3>TEST FILES <span>{fmt(datasetSummary?.test_files?.length)}</span></h3>{datasetSummary?.test_files?.length ? <div className="file-chips">{datasetSummary.test_files.map((file: string) => <code key={file}>{file}</code>)}</div> : <EmptyState title="Unavailable" />}</div></Panel></div><Panel title="Available dataset files" eyebrow="API · /api/datasets" action={<button className="button button-light" onClick={() => void auditDataset()} disabled={auditBusy}><FileSearch size={15} />{auditBusy ? "Auditing…" : "Audit selected"}</button>}>{api.datasets.length ? <div className="table-scroll"><table><thead><tr><th>FILE</th><th>PATH</th><th>SIZE · MB</th><th>TYPE</th><th>SELECTION</th></tr></thead><tbody>{api.datasets.map((file, index) => <tr key={file.path ?? index}><td className="strong-cell">{file.name ?? file.relative_path ?? "Unavailable"}</td><td className="mono path-cell">{file.relative_path ?? file.path ?? "Unavailable"}</td><td className="mono">{fmt(file.size_mb, 2)}</td><td>{file.type ?? (file.is_synthetic === true ? "Synthetic" : file.is_synthetic === false ? "Dataset" : "Unavailable")}</td><td><button className="text-button" onClick={() => setSelectedDataset(String(file.path ?? ""))}>{selectedDataset === file.path ? "Selected" : "Select"}</button></td></tr>)}</tbody></table></div> : <EmptyState title="Dataset files unavailable" detail="The backend did not return files from /api/datasets." />}{auditResult && <div className="audit-result"><div className="audit-result-title"><CheckCircle2 size={17} /> Audit result · {auditResult.target_path ?? "selected dataset"}</div><div className="audit-stat-grid">{Object.entries(auditResult).filter(([key, value]) => typeof value === "number" && !["timestamp"].includes(key)).map(([key, value]) => <div key={key}><span>{labelName(key)}</span><strong className="mono">{fmt(value)}</strong></div>)}</div><div className="audit-source">Audit fields are returned by the existing API endpoint.</div></div>}</Panel><div className="data-footnote"><FileSearch size={14} />Split source: <code>{datasetSummary?.source ?? "data/processed/dataset_build_summary.json (unavailable)"}</code></div></div>}

      {activePage === "runs" && <div className="page-stack"><Panel title="Training runs" eyebrow="API · /api/runs" action={<span className="panel-source">{api.runs.length ? `${fmt(api.runs.length)} runs` : "No run data"}</span>}>{api.runs.length ? <div className="table-scroll"><table><thead><tr><th>RUN ID</th><th>DATE</th><th>MODEL</th><th>TASK</th><th>ACCURACY</th><th>MACRO-F1</th><th>MS / FLOW</th><th>FEATURES</th></tr></thead><tbody>{api.runs.map((run, index) => <tr key={run.run_id ?? index}><td className="mono">{run.run_id ?? "Unavailable"}</td><td className="mono">{run.timestamp ? new Date(run.timestamp).toLocaleString() : "Unavailable"}</td><td>{run.model_name ?? "Unavailable"}</td><td>{run.task_type ?? "Unavailable"}</td><td><MetricCell value={run.accuracy} isRate /></td><td><MetricCell value={run.macro_f1} isRate /></td><td><MetricCell value={run.inference_latency_ms_per_sample} /></td><td className="mono">{fmt(run.selected_features_count)}</td></tr>)}</tbody></table></div> : <EmptyState title="Run history unavailable" detail="Training run records are provided by the existing /api/runs endpoint." />}</Panel><Panel title="Compare two runs" eyebrow="API RUN COMPARISON"><div className="toolbar-grid compare-fields"><label className="field"><span>Run A</span><select value={runA} onChange={(event) => setRunA(event.target.value)}><option value="">Select run</option>{api.runs.map((run, index) => <option key={run.run_id ?? index} value={run.run_id}>{run.run_id ?? `Run ${index + 1}`}</option>)}</select></label><label className="field"><span>Run B</span><select value={runB} onChange={(event) => setRunB(event.target.value)}><option value="">Select run</option>{api.runs.map((run, index) => <option key={run.run_id ?? index} value={run.run_id}>{run.run_id ?? `Run ${index + 1}`}</option>)}</select></label></div>{selectedRunA && selectedRunB ? <div className="table-scroll"><table><thead><tr><th>METRIC</th><th>RUN A</th><th>RUN B</th><th>DELTA · B − A</th></tr></thead><tbody>{[["Accuracy", "accuracy"], ["Macro-F1", "macro_f1"], ["Weighted-F1", "weighted_f1"], ["Latency · ms/flow", "inference_latency_ms_per_sample"], ["Selected features", "selected_features_count"]].map(([label, key]) => { const a = selectedRunA[key]; const b = selectedRunB[key]; return <tr key={key}><td>{label}</td><td className="mono">{typeof a === "number" ? key.includes("latency") ? fmt(a, 4) : key === "selected_features_count" ? fmt(a) : pct(a) : "Unavailable"}</td><td className="mono">{typeof b === "number" ? key.includes("latency") ? fmt(b, 4) : key === "selected_features_count" ? fmt(b) : pct(b) : "Unavailable"}</td><td className="mono">{typeof a === "number" && typeof b === "number" ? fmt(b - a, 4) : "Unavailable"}</td></tr>; })}</tbody></table></div> : <EmptyState title="Select two runs" detail="Comparison values appear only when both API run records are selected." />}</Panel></div>}

      {activePage === "system" && <div className="page-stack"><div className="system-card-grid"><div className="system-stat"><span className="eyebrow">API CONNECTION</span><strong className={api.status ? "green-text" : "muted-text"}>{api.status ? "Connected" : "Unavailable"}</strong><small>{api.status?.system ?? "Backend status not returned"}</small></div><div className="system-stat"><span className="eyebrow">ACTIVE MODEL</span><strong>{activeModel?.name ?? "Unavailable"}</strong><small>{activeModel?.task ?? activeModel?.task_type ?? "Model metadata not returned"}</small></div><div className="system-stat"><span className="eyebrow">RUNTIME</span><strong>{api.status?.python_version ?? "Unavailable"}</strong><small>{api.status?.platform ?? "Runtime metadata not returned"}</small></div><div className="system-stat"><span className="eyebrow">DATA STORE</span><strong>{fmt(api.status?.db_size_mb, 2)}{typeof api.status?.db_size_mb === "number" ? " MB" : ""}</strong><small>Database size from API status</small></div></div><Panel title="System logs" eyebrow="API · /api/logs" action={<label className="filter-select"><Filter size={14} /><select value={logLevel} onChange={(event) => setLogLevel(event.target.value)}>{["ALL", "INFO", "WARNING", "ERROR", "DEBUG"].map((level) => <option key={level}>{level}</option>)}</select></label>}>{filteredLogs.length ? <div className="log-list">{filteredLogs.map((entry, index) => { const text = typeof entry === "string" ? entry : JSON.stringify(entry); const level = typeof entry === "string" ? (entry.match(/\b(INFO|WARNING|ERROR|DEBUG)\b/i)?.[1] ?? "INFO") : entry.level ?? "INFO"; return <div className="log-row" key={entry.id ?? index}><span className={`log-level level-${String(level).toLowerCase()}`}>{level}</span><code>{text}</code></div>; })}</div> : <EmptyState title="Logs unavailable" detail="The connected API has not returned log entries." />}</Panel><Panel title="Runtime configuration" eyebrow="API · /api/settings"><div className="config-grid">{api.settings ? Object.entries(api.settings).map(([key, value]) => <div className="config-item" key={key}><span>{labelName(key)}</span><code>{typeof value === "object" ? JSON.stringify(value) : String(value)}</code></div>) : <EmptyState title="Configuration unavailable" detail="Settings are displayed only when returned by the backend API." />}</div></Panel><div className="data-footnote"><TerminalSquare size={14} />Data is read from the existing local API proxy at <code>/api/*</code>; no proxy behavior was changed.</div></div>}
      </main>
      <footer className="app-footer"><span>DEVRAKSHAK <span className="footer-dot">·</span> IDS Console</span><span>Offline evaluation only</span></footer>
    </div>
    {toast && <div role="status" className="toast"><CheckCircle2 size={16} />{toast}<button className="icon-button" aria-label="Dismiss notification" onClick={() => setToast("")}><X size={14} /></button></div>}
  </div>;
}
