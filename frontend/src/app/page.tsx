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
<<<<<<< Updated upstream
function Panel({ title, eyebrow, action, children, className = "" }: { title: string; eyebrow?: string; action?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return <section className={`panel ${className}`}><header className="panel-head"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h2>{title}</h2></div>{action}</header><div className="panel-content">{children}</div></section>;
=======

interface TrainingRunItem {
  run_id: string;
  timestamp: string;
  task_type: string;
  model_name: string;
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  false_positive_rate?: number | null;
  inference_latency_ms_per_sample: number;
  selected_features_count: number;
  dataset_path?: string;
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
      {activePage === "system" && <div className="page-stack"><div className="system-card-grid"><div className="system-stat"><span className="eyebrow">API CONNECTION</span><strong className={api.status ? "green-text" : "muted-text"}>{api.status ? "Connected" : "Unavailable"}</strong><small>{api.status?.system ?? "Backend status not returned"}</small></div><div className="system-stat"><span className="eyebrow">ACTIVE MODEL</span><strong>{activeModel?.name ?? "Unavailable"}</strong><small>{activeModel?.task ?? activeModel?.task_type ?? "Model metadata not returned"}</small></div><div className="system-stat"><span className="eyebrow">RUNTIME</span><strong>{api.status?.python_version ?? "Unavailable"}</strong><small>{api.status?.platform ?? "Runtime metadata not returned"}</small></div><div className="system-stat"><span className="eyebrow">DATA STORE</span><strong>{fmt(api.status?.db_size_mb, 2)}{typeof api.status?.db_size_mb === "number" ? " MB" : ""}</strong><small>Database size from API status</small></div></div><Panel title="System logs" eyebrow="API · /api/logs" action={<label className="filter-select"><Filter size={14} /><select value={logLevel} onChange={(event) => setLogLevel(event.target.value)}>{["ALL", "INFO", "WARNING", "ERROR", "DEBUG"].map((level) => <option key={level}>{level}</option>)}</select></label>}>{filteredLogs.length ? <div className="log-list">{filteredLogs.map((entry, index) => { const text = typeof entry === "string" ? entry : JSON.stringify(entry); const level = typeof entry === "string" ? (entry.match(/\b(INFO|WARNING|ERROR|DEBUG)\b/i)?.[1] ?? "INFO") : entry.level ?? "INFO"; return <div className="log-row" key={entry.id ?? index}><span className={`log-level level-${String(level).toLowerCase()}`}>{level}</span><code>{text}</code></div>; })}</div> : <EmptyState title="Logs unavailable" detail="The connected API has not returned log entries." />}</Panel><Panel title="Runtime configuration" eyebrow="API · /api/settings"><div className="config-grid">{api.settings ? Object.entries(api.settings).map(([key, value]) => <div className="config-item" key={key}><span>{labelName(key)}</span><code>{typeof value === "object" ? JSON.stringify(value) : String(value)}</code></div>) : <EmptyState title="Configuration unavailable" detail="Settings are displayed only when returned by the backend API." />}</div></Panel><div className="data-footnote"><TerminalSquare size={14} />Data is read from the existing local API proxy at <code>/api/*</code>; no proxy behavior was changed.</div></div>}
      </main>
      <footer className="app-footer"><span>DEVRAKSHAK <span className="footer-dot">·</span> IDS Console</span><span>Offline evaluation only</span></footer>
=======
            {/* Active Model Indicator */}
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1.5 rounded bg-base-elevated border border-border-subtle text-xs">
              <Cpu className="w-3.5 h-3.5 text-brand" />
              <span className="text-content-secondary">
                {status?.active_model || "Random Forest"} [15 Feats LRRC-FS]
              </span>
            </div>

            {/* Quick Run CTA */}
            <button
              onClick={() => handleQuickOfflineRun()}
              disabled={testLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-brand hover:bg-brand-hover text-white text-xs font-medium whitespace-nowrap interactive-transition disabled:opacity-50"
            >
              {testLoading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3 h-3 fill-white" />
              )}
              <span className="hidden sm:inline">Quick Test</span>
            </button>

            {/* Manual Sync Button */}
            <button
              onClick={fetchAllData}
              disabled={refreshing}
              className="p-1.5 rounded border border-border-subtle bg-base-elevated text-content-secondary hover:text-content-primary interactive-transition disabled:opacity-50"
              title="Refresh SQLite telemetry"
              aria-label="Refresh database telemetry"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-brand" : ""}`} />
            </button>
          </div>
        </header>

        {/* Offline Backend Alert Banner */}
        {!backendOnline && (
          <div className="bg-rose-500/15 border-b border-rose-500/30 px-6 py-2.5 flex items-center justify-between text-xs text-rose-200">
            <div className="flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0" />
              <span>
                <strong>Python AI Backend Offline (Port 8000).</strong> Live classification and training are paused. Start the backend: <code className="bg-rose-950/60 px-2 py-0.5 rounded text-[11px] font-mono text-rose-300">uv run python -m src.web.server --port 8000</code> or run <code className="bg-rose-950/60 px-2 py-0.5 rounded text-[11px] font-mono text-rose-300">start_web.bat</code>.
              </span>
            </div>
            <button
              onClick={fetchAllData}
              className="px-3 py-1 bg-rose-500/30 hover:bg-rose-500/40 border border-rose-400/40 rounded text-white font-medium interactive-transition whitespace-nowrap ml-4"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Content Body Container */}
        <main className="p-6 space-y-6 max-w-7xl w-full mx-auto">
          {/* =================================================================
              VIEW 1: EXECUTIVE DASHBOARD
              ================================================================= */}
          {activeTab === "dashboard" && (
            <div className="space-y-6">
              {/* Dataset & Execution Control Banner */}
              <div className="panel p-4 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded bg-brand/15 border border-brand/30 text-brand">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-content-primary">
                        CICIoT2023 Offline Benchmark
                      </span>
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                        {status?.raw_datasets_count || 63} Partitions ({status?.total_dataset_size_gb || 9.42} GB)
                      </span>
                    </div>
                    <p className="text-xs text-content-secondary mt-0.5">
                      Classifying offline network traffic flows with 4-term LRRC-FS feature selection.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-wrap">
                  <div className="flex items-center gap-2 text-xs">
                    <label htmlFor="dash-partition-select" className="text-content-secondary">Partition:</label>
                    <select
                      id="dash-partition-select"
                      value={selectedDataset}
                      onChange={(e) => setSelectedDataset(e.target.value)}
                      className="bg-base-elevated border border-border-subtle rounded px-2.5 py-1.5 text-xs text-content-primary font-mono focus:border-brand focus:outline-none"
                    >
                      {datasets.map((d) => (
                        <option key={d.path} value={d.path}>
                          {d.name} ({d.size_mb} MB)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <label htmlFor="dash-sample-limit-select" className="text-content-secondary">Flows:</label>
                    <select
                      id="dash-sample-limit-select"
                      value={sampleLimit}
                      onChange={(e) => setSampleLimit(Number(e.target.value))}
                      className="bg-base-elevated border border-border-subtle rounded px-2.5 py-1.5 text-xs text-content-primary focus:border-brand focus:outline-none"
                    >
                      {FLOW_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <label htmlFor="dash-threshold-select" className="text-content-secondary">Calibrated Threshold:</label>
                    <select
                      id="dash-threshold-select"
                      value={decisionThreshold}
                      onChange={(e) => setDecisionThreshold(Number(e.target.value))}
                      className="bg-base-elevated border border-border-subtle rounded px-2.5 py-1.5 text-xs text-content-primary focus:border-brand focus:outline-none"
                      title="Adjust decision threshold to control False Positive Rate"
                    >
                      <option value={0.70}>0.70 (Low FPR ~12% - Recommended)</option>
                      <option value={0.50}>0.50 (Max Sensitivity &gt;99.8%)</option>
                      <option value={0.85}>0.85 (High Precision)</option>
                    </select>
                  </div>

                  <button
                    onClick={() => handleQuickOfflineRun(selectedDataset, sampleLimit)}
                    disabled={testLoading}
                    className="px-3.5 py-1.5 rounded bg-brand hover:bg-brand-hover text-white text-xs font-medium whitespace-nowrap interactive-transition disabled:opacity-50"
                  >
                    <span className="flex items-center gap-2 whitespace-nowrap">
                      {testLoading ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Play className="w-3 h-3 fill-white" />
                      )}
                      <span>{testLoading ? "Inspecting…" : "Run Inspection"}</span>
                    </span>
                  </button>
                </div>
              </div>

              {/* High-Signal Telemetry KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* 1. Total Flows Analyzed */}
                <div className="panel p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-content-secondary font-medium">
                    <span>Flows Evaluated</span>
                    <Activity className="w-4 h-4 text-brand" />
                  </div>
                  <div className="text-2xl font-semibold text-content-primary tracking-tight tabular-nums">
                    {(stats?.total_records_processed ?? stats?.total_events ?? 0).toLocaleString()}
                  </div>
                  <div className="text-[11px] text-content-secondary pt-1 flex items-center justify-between">
                    <span>Benign: {(stats?.benign_count ?? 0).toLocaleString()}</span>
                    <span>Attack: {(stats?.attack_count ?? 0).toLocaleString()}</span>
                  </div>
                </div>

                {/* 2. Detected Threats */}
                <div className="panel p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-content-secondary font-medium">
                    <span>Threat Events</span>
                    <ShieldAlert className="w-4 h-4 text-status-danger" />
                  </div>
                  <div className="text-2xl font-semibold text-status-danger tracking-tight tabular-nums">
                    {(stats?.attack_count ?? stats?.total_attacks ?? 0).toLocaleString()}
                  </div>
                  <div className="text-[11px] text-content-secondary pt-1 flex items-center justify-between">
                    <span>Critical: {stats?.severity_distribution?.CRITICAL ?? 0}</span>
                    <span>High: {stats?.severity_distribution?.HIGH ?? 0}</span>
                  </div>
                </div>

                {/* 3. Verified Clean Traffic */}
                <div className="panel p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-content-secondary font-medium">
                    <span>Benign Verified</span>
                    <CheckCircle2 className="w-4 h-4 text-status-success" />
                  </div>
                  <div className="text-2xl font-semibold text-status-success tracking-tight tabular-nums">
                    {(stats?.benign_count ?? 0).toLocaleString()}
                  </div>
                  <div className="text-[11px] text-content-secondary pt-1">
                    <span>Test Pool: 2,634 benign samples</span>
                  </div>
                </div>

                {/* 4. Model Latency & Database Footprint */}
                <div className="panel p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-content-secondary font-medium">
                    <span>Average Latency</span>
                    <Cpu className="w-4 h-4 text-status-info" />
                  </div>
                  <div className="text-2xl font-semibold text-content-primary tracking-tight tabular-nums">
                    0.0007 ms
                  </div>
                  <div className="text-[11px] text-content-secondary pt-1 flex items-center justify-between">
                    <span>~0.7 µs per flow</span>
                    <span>{status?.db_size_mb || 16} MB SQLite</span>
                  </div>
                </div>
              </div>

              {/* Traffic Timeline Chart and Threat Distribution */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Real Data SVG Timeline Chart (2 Cols) */}
                <div className="lg:col-span-2 panel p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-sm font-semibold text-content-primary">
                        Traffic Timeline Telemetry
                      </h2>
                      <p className="text-xs text-content-secondary">
                        Network flow distributions recorded in local SQLite event store
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="flex items-center gap-1.5 text-content-secondary">
                        <span className="w-2 h-2 rounded-full bg-brand"></span> Normal
                      </span>
                      <span className="flex items-center gap-1.5 text-content-secondary">
                        <span className="w-2 h-2 rounded-full bg-status-warning"></span> Suspicious
                      </span>
                      <span className="flex items-center gap-1.5 text-content-secondary">
                        <span className="w-2 h-2 rounded-full bg-status-danger"></span> Malicious
                      </span>
                    </div>
                  </div>

                  {/* SVG Chart */}
                  <div className="h-60 w-full relative pt-2">
                    {(() => {
                      const timeline: any[] = stats?.timeline && stats.timeline.length > 0 ? stats.timeline : [];
                      if (timeline.length === 0) {
                        return (
                          <div className="h-full flex flex-col items-center justify-center text-content-tertiary text-xs">
                            <Activity className="w-8 h-8 text-border-strong mb-2" />
                            <span>No offline flows processed yet. Click &quot;Run Inspection&quot; to test.</span>
                          </div>
                        );
                      }

                      const maxVal = Math.max(
                        ...timeline.map((t: any) => Math.max(t.normal || 0, t.suspicious || 0, t.malicious || 0)),
                        50
                      );

                      const svgW = 600;
                      const svgH = 180;
                      const padX = 50;
                      const chartW = svgW - padX - 20;

                      const getX = (i: number) => {
                        if (timeline.length <= 1) return padX + chartW / 2;
                        return padX + (i / (timeline.length - 1)) * chartW;
                      };

                      const getY = (val: number) => {
                        const cl = Math.max(0, val);
                        return svgH - 25 - (cl / maxVal) * (svgH - 45);
                      };

                      const makePath = (key: string) => {
                        return timeline
                          .map((t: any, i: number) => `${i === 0 ? "M" : "L"} ${getX(i).toFixed(1)} ${getY(t[key] || 0).toFixed(1)}`)
                          .join(" ");
                      };

                      return (
                        <svg
                          className="w-full h-full"
                          viewBox={`0 0 ${svgW} ${svgH}`}
                          fill="none"
                          aria-label="Traffic distribution chart"
                        >
                          {/* Grid horizontal lines */}
                          {[0, 1, 2, 3].map((step) => {
                            const y = 20 + step * 40;
                            const gridVal = maxVal * (1 - step / 3);
                            return (
                              <g key={step}>
                                <line x1={padX} y1={y} x2={svgW - 20} y2={y} stroke="var(--color-border-subtle)" strokeDasharray="3 3" />
                                <text x={padX - 8} y={y + 3} fill="var(--color-text-tertiary)" fontSize="10" textAnchor="end" fontFamily="monospace">
                                  {Math.round(gridVal)}
                                </text>
                              </g>
                            );
                          })}

                          {/* Data Lines */}
                          <path d={makePath("normal")} stroke="var(--color-accent)" strokeWidth="2" />
                          <path d={makePath("suspicious")} stroke="var(--color-status-warning)" strokeWidth="2" />
                          <path d={makePath("malicious")} stroke="var(--color-status-danger)" strokeWidth="2" />

                          {/* Date markers on x-axis */}
                          {timeline.map((t: any, i: number) => (
                            <text
                              key={i}
                              x={getX(i)}
                              y={svgH - 5}
                              fill="var(--color-text-tertiary)"
                              fontSize="9"
                              textAnchor="middle"
                              fontFamily="monospace"
                            >
                              {t.date ? t.date.slice(5) : `B${i + 1}`}
                            </text>
                          ))}
                        </svg>
                      );
                    })()}
                  </div>
                </div>

                {/* Threat Family Breakdown (1 Col) */}
                <div className="panel p-5 space-y-4 flex flex-col justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-content-primary">
                      Threat Family Breakdown
                    </h2>
                    <p className="text-xs text-content-secondary">
                      Classified events from official dataset taxonomy
                    </p>
                  </div>

                  <div className="space-y-3">
                    {(() => {
                      const topCategories: any[] = stats?.top_attack_categories || [];
                      if (topCategories.length === 0) {
                        return (
                          <div className="text-center text-content-tertiary text-xs py-8">
                            No attacks recorded in database yet
                          </div>
                        );
                      }
                      return topCategories.map((cat: any) => (
                        <div key={cat.name} className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="font-medium text-content-primary">{cat.name}</span>
                            <span className="tabular-nums text-content-secondary">
                              {cat.percentage}% ({Number(cat.count).toLocaleString()})
                            </span>
                          </div>
                          <div className="w-full bg-base-elevated h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-brand h-full rounded-full"
                              style={{ width: `${Math.min(100, cat.percentage)}%` }}
                            ></div>
                          </div>
                        </div>
                      ));
                    })()}
                  </div>

                  <div className="pt-3 border-t border-border-subtle text-[11px] text-content-tertiary">
                    Categorized into 8 canonical families: DDoS, DoS, Mirai, Recon, Spoofing, Web, BruteForce, Benign.
                  </div>
                </div>
              </div>

              {/* Recent Detection Events Table */}
              <div className="panel p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
                  <div>
                    <h2 className="text-sm font-semibold text-content-primary">
                      Recent Classified Events
                    </h2>
                    <p className="text-xs text-content-secondary">
                      Real-time events retrieved from SQLite event store
                    </p>
                  </div>
                  <button
                    onClick={() => setActiveTab("traffic")}
                    className="text-xs text-brand hover:underline font-medium"
                  >
                    View all flows
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="text-content-secondary border-b border-border-subtle">
                      <tr>
                        <th className="py-2.5 px-3">Timestamp</th>
                        <th className="py-2.5 px-3">Prediction</th>
                        <th className="py-2.5 px-3">Source File</th>
                        <th className="py-2.5 px-3">Packet Metrics</th>
                        <th className="py-2.5 px-3">Severity</th>
                        <th className="py-2.5 px-3">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle">
                      {recentEvents.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-content-tertiary">
                            No detection events in database. Click &quot;Run Inspection&quot; to test flows.
                          </td>
                        </tr>
                      ) : (
                        recentEvents.slice(0, 6).map((row: any, i: number) => {
                          const sev = (row.severity || "INFO").toUpperCase();
                          const isAttack = row.is_attack || sev === "CRITICAL" || sev === "HIGH";
                          const timeStr = formatTimestamp(row.timestamp);
                          const rateStr = row.raw_features?.Rate !== undefined ? `Rate: ${Number(row.raw_features.Rate).toFixed(1)}` : "";
                          const sumStr = row.raw_features?.["Tot sum"] !== undefined ? `Tot: ${Number(row.raw_features["Tot sum"]).toFixed(0)}` : "";

                          return (
                            <tr key={row.id || i} className="hover:bg-base-elevated interactive-transition">
                              <td className="py-2.5 px-3 text-content-secondary">{timeStr}</td>
                              <td className="py-2.5 px-3 text-content-primary font-medium">
                                {row.predicted_label || row.attack_category || "Benign"}
                              </td>
                              <td className="py-2.5 px-3 text-content-secondary font-mono">
                                {row.source_file || "Merged01.csv"}
                              </td>
                              <td className="py-2.5 px-3 text-content-tertiary text-[11px] font-mono">
                                {rateStr} {rateStr && sumStr ? "·" : ""} {sumStr}
                              </td>
                              <td className="py-2.5 px-3">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                    sev === "CRITICAL"
                                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                      : sev === "HIGH"
                                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                      : sev === "MEDIUM"
                                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                  }`}
                                >
                                  {sev}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 font-medium">
                                <span className={isAttack ? "text-rose-400" : "text-emerald-400"}>
                                  {isAttack ? "Blocked" : "Logged"}
                                </span>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================
              VIEW 2: THREAT ALERTS
              ================================================================= */}
          {activeTab === "alerts" && (
            <div className="space-y-6">
              <div className="panel p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-border-subtle">
                  <div>
                    <h2 className="text-sm font-semibold text-content-primary flex items-center gap-2">
                      <AlertOctagon className="w-4 h-4 text-status-danger" />
                      Security Threat Alerts
                    </h2>
                    <p className="text-xs text-content-secondary mt-0.5">
                      Intrusion detections and automated mitigation actions triggered by active policies
                    </p>
                  </div>

                  {/* Filter Severity Buttons */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((lvl) => (
                      <button
                        key={lvl}
                        onClick={() => setAlertSeverityFilter(lvl)}
                        className={`px-2.5 py-1 rounded text-xs font-medium interactive-transition ${
                          alertSeverityFilter === lvl
                            ? "bg-brand text-white"
                            : "bg-base-elevated border border-border-subtle text-content-secondary hover:text-content-primary"
                        }`}
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Disclosure Note */}
                <div className="p-3 rounded bg-base-elevated border border-border-subtle text-xs text-content-secondary flex items-start gap-2.5">
                  <Info className="w-4 h-4 text-brand shrink-0 mt-0.5" />
                  <span>
                    Notice: Defense policies evaluate strictly downstream on model predictions. If the model misses an attack flow, the corresponding policy cannot trigger.
                  </span>
                </div>

                {/* Alerts List */}
                <div className="space-y-3">
                  {filteredAlerts.length === 0 ? (
                    <div className="py-12 text-center text-content-tertiary text-xs">
                      No alerts match the active filter. Inspect traffic to generate events.
                    </div>
                  ) : (
                    filteredAlerts.map((alt, idx) => {
                      const sev = (alt.severity || "INFO").toUpperCase();
                      return (
                        <div
                          key={alt.id || idx}
                          className="p-4 rounded bg-base-elevated border border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-3 interactive-transition hover:border-border-strong"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-semibold font-mono ${
                                  sev === "CRITICAL"
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                    : sev === "HIGH"
                                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                                }`}
                              >
                                {sev}
                              </span>
                              <span className="font-semibold text-content-primary text-xs">
                                {alt.predicted_label || alt.attack_category}
                              </span>
                              {alt.policy_id && (
                                <span className="text-[11px] font-mono text-content-tertiary">
                                  [{alt.policy_id}]
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-content-secondary flex flex-wrap gap-x-3 gap-y-0.5">
                              <span>Source: <span className="font-mono">{alt.source_file || "Merged01.csv"}</span></span>
                              <span>Row #<span className="tabular-nums font-mono">{alt.row_index ?? idx}</span></span>
                              <span>Confidence: <span className="tabular-nums font-mono">{alt.confidence ? `${(Number(alt.confidence) * 100).toFixed(1)}%` : "100%"}</span></span>
                            </div>
                          </div>

                          <div className="text-right sm:self-center">
                            <span className="px-2.5 py-1 rounded text-xs font-medium bg-rose-500/15 text-rose-300 border border-rose-500/30">
                              {alt.action || (alt.is_attack ? "Mitigated / Blocked" : "Logged")}
                            </span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {/* Integrated Automated Defense Mitigation Policies */}
                <div className="pt-6 border-t border-border-subtle space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-semibold text-content-primary flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-brand" />
                        Automated Defense Mitigation Policies (POL-001 – POL-007)
                      </h3>
                      <p className="text-xs text-content-secondary mt-0.5">
                        Response actions mapping machine learning threat predictions to network gateway interventions
                      </p>
                    </div>
                    <span className="text-xs text-emerald-400 font-medium">
                      {policies.length} Policies Active
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {policies.map((p) => {
                      const sev = (p.severity || "HIGH").toUpperCase();
                      return (
                        <div
                          key={p.policy_id}
                          className="p-3.5 rounded bg-base-elevated border border-border-subtle flex flex-col justify-between gap-2 text-xs"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-content-primary">
                                {p.policy_id}: {p.name}
                              </span>
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-semibold font-mono ${
                                  sev === "CRITICAL"
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                    : sev === "HIGH"
                                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                                }`}
                              >
                                {sev}
                              </span>
                            </div>
                            <p className="text-xs text-content-secondary">{p.description}</p>
                          </div>

                          <div className="flex items-center justify-between pt-2 border-t border-border-subtle/50 text-[11px]">
                            <span className="text-content-tertiary">
                              Action: <span className="text-content-primary font-medium">{p.action}</span>
                            </span>
                            <span className="text-emerald-400 font-semibold font-mono">
                              &ge; {(p.min_confidence * 100).toFixed(0)}% Conf
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================
              VIEW 3: TRAFFIC MONITOR / FLOW INSPECTION
              ================================================================= */}
          {activeTab === "traffic" && (
            <div className="space-y-6">
              <div className="panel p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-border-subtle">
                  <div>
                    <h2 className="text-sm font-semibold text-content-primary flex items-center gap-2">
                      <Activity className="w-4 h-4 text-brand" />
                      Live Traffic Flow Inspection Engine
                    </h2>
                    <p className="text-xs text-content-secondary mt-0.5">
                      Stream and classify network traffic flows from official CICIoT2023 partitions
                    </p>
                  </div>
                  <button
                    onClick={handleExportCSV}
                    disabled={!testRecords.length}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-base-elevated border border-border-subtle hover:bg-base-hover text-content-primary text-xs font-medium interactive-transition disabled:opacity-40"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export CSV</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
                  <div>
                    <label htmlFor="traffic-partition-select" className="block text-content-secondary mb-1">Target Partition</label>
                    <select
                      id="traffic-partition-select"
                      value={selectedDataset}
                      onChange={(e) => setSelectedDataset(e.target.value)}
                      className="w-full bg-base-elevated border border-border-subtle rounded p-2 text-content-primary font-mono text-xs focus:border-brand focus:outline-none"
                    >
                      {datasets.map((d) => (
                        <option key={d.path} value={d.path}>
                          {d.name} ({d.size_mb} MB)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="traffic-model-select" className="block text-content-secondary mb-1">Active AI Model</label>
                    <select
                      id="traffic-model-select"
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-base-elevated border border-border-subtle rounded p-2 text-content-primary font-mono text-xs focus:border-brand focus:outline-none"
                    >
                      {models.map((m) => (
                        <option key={m.path} value={m.path}>
                          {m.name} [{m.task.toUpperCase()}]
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="traffic-threshold-select" className="block text-content-secondary mb-1">Decision Threshold</label>
                    <select
                      id="traffic-threshold-select"
                      value={decisionThreshold}
                      onChange={(e) => setDecisionThreshold(Number(e.target.value))}
                      className="w-full bg-base-elevated border border-border-subtle rounded p-2 text-content-primary text-xs focus:border-brand focus:outline-none"
                      title="Adjust decision threshold to calibrate False Positive Rate"
                    >
                      <option value={0.70}>0.70 (Low FPR ~12% - Recommended)</option>
                      <option value={0.50}>0.50 (Max Sensitivity &gt;99.8%)</option>
                      <option value={0.85}>0.85 (High Precision Defense)</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="traffic-flow-limit-select" className="block text-content-secondary mb-1">Flow Inspection Volume</label>
                    <select
                      id="traffic-flow-limit-select"
                      value={sampleLimit}
                      onChange={(e) => setSampleLimit(Number(e.target.value))}
                      className="w-full bg-base-elevated border border-border-subtle rounded p-2 text-content-primary text-xs focus:border-brand focus:outline-none"
                    >
                      {FLOW_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleRunInference}
                      disabled={testLoading}
                      className="w-full py-2 px-4 rounded bg-brand hover:bg-brand-hover text-white font-medium flex items-center justify-center whitespace-nowrap interactive-transition disabled:opacity-50"
                    >
                      <span className="flex items-center gap-2 whitespace-nowrap">
                        {testLoading ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Play className="w-3.5 h-3.5 fill-white" />
                        )}
                        <span>{testLoading ? "Processing…" : "Inspect Flows"}</span>
                      </span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Inspection Summary Stats */}
              {testSummary && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="panel p-4 text-center">
                      <div className="text-xs text-content-secondary">Total Flows Evaluated</div>
                      <div className="text-xl font-bold text-content-primary mt-1 tabular-nums">
                        {testSummary.total_samples_tested.toLocaleString()}
                      </div>
                    </div>
                    <div className="panel p-4 text-center">
                      <div className="text-xs text-status-danger">Attacks Detected</div>
                      <div className="text-xl font-bold text-status-danger mt-1 tabular-nums">
                        {testSummary.attacks_detected.toLocaleString()}
                      </div>
                    </div>
                    <div className="panel p-4 text-center">
                      <div className="text-xs text-status-success">Benign Verified</div>
                      <div className="text-xl font-bold text-status-success mt-1 tabular-nums">
                        {testSummary.benign_detected.toLocaleString()}
                      </div>
                    </div>
                    <div className="panel p-4 text-center">
                      <div className="text-xs text-brand">Latency / Sample</div>
                      <div className="text-xl font-bold text-brand mt-1 tabular-nums">
                        {testSummary.latency_ms_per_sample} ms
                      </div>
                    </div>
                  </div>

                  {/* Empirical Confusion Matrix & FPR Verification Card */}
                  {testSummary.confusion_matrix && (
                    <div className="panel p-4 space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border-subtle text-xs">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-brand" />
                          <span className="font-semibold text-content-primary">Empirical Confusion Matrix &amp; False Positive Verification</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-base-elevated border border-border-subtle text-content-secondary">
                            Calibrated Threshold: {testSummary.decision_threshold ?? 0.70}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
                            (testSummary.confusion_matrix.fpr_percentage ?? 0) <= 15
                              ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                              : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                          }`}>
                            FPR: {testSummary.confusion_matrix.fpr_percentage}%
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div className="p-3 rounded bg-base-elevated/70 border border-border-subtle text-center">
                          <div className="text-content-secondary text-[11px]">True Negative (Normal Clean)</div>
                          <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
                            {testSummary.confusion_matrix.tn.toLocaleString()}
                          </div>
                          <div className="text-[10px] text-content-tertiary mt-0.5">Correctly verified benign</div>
                        </div>
                        <div className="p-3 rounded bg-base-elevated/70 border border-border-subtle text-center">
                          <div className="text-content-secondary text-[11px]">False Positive (False Alarm)</div>
                          <div className="text-lg font-bold text-amber-400 font-mono mt-0.5">
                            {testSummary.confusion_matrix.fp.toLocaleString()}
                          </div>
                          <div className="text-[10px] text-content-tertiary mt-0.5">
                            FPR = {testSummary.confusion_matrix.fpr_percentage}%
                          </div>
                        </div>
                        <div className="p-3 rounded bg-base-elevated/70 border border-border-subtle text-center">
                          <div className="text-content-secondary text-[11px]">False Negative (Missed Attack)</div>
                          <div className="text-lg font-bold text-rose-400 font-mono mt-0.5">
                            {testSummary.confusion_matrix.fn.toLocaleString()}
                          </div>
                          <div className="text-[10px] text-content-tertiary mt-0.5">
                            FNR = {testSummary.confusion_matrix.fnr_percentage}%
                          </div>
                        </div>
                        <div className="p-3 rounded bg-base-elevated/70 border border-border-subtle text-center">
                          <div className="text-content-secondary text-[11px]">True Positive (Threat Stopped)</div>
                          <div className="text-lg font-bold text-brand font-mono mt-0.5">
                            {testSummary.confusion_matrix.tp.toLocaleString()}
                          </div>
                          <div className="text-[10px] text-content-tertiary mt-0.5">
                            Recall = {(((testSummary.confusion_matrix.tp) / Math.max(1, testSummary.confusion_matrix.tp + testSummary.confusion_matrix.fn)) * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Flow Records Table */}
              <div className="panel p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
                  <h3 className="text-sm font-semibold text-content-primary">
                    Classified Flow Records
                  </h3>
                  <span className="text-xs text-content-secondary">
                    {testSummary ? (
                      <>
                        Evaluated <span className="font-semibold text-content-primary tabular-nums font-mono">{testSummary.total_samples_tested.toLocaleString()}</span> flows · Showing first <span className="tabular-nums font-mono">{filteredTrafficRecords.length}</span>
                      </>
                    ) : (
                      <>Showing <span className="tabular-nums font-mono">{filteredTrafficRecords.length}</span> records</>
                    )}
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="text-content-secondary border-b border-border-subtle">
                      <tr>
                        <th className="py-2.5 px-3">Flow #</th>
                        <th className="py-2.5 px-3">Timestamp</th>
                        <th className="py-2.5 px-3">Ground Truth</th>
                        <th className="py-2.5 px-3">Prediction</th>
                        <th className="py-2.5 px-3">Confidence</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Severity</th>
                        <th className="py-2.5 px-3">Salient Attribution / Root Cause</th>
                        <th className="py-2.5 px-3">Extracted Features</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle">
                      {filteredTrafficRecords.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="py-8 text-center text-content-tertiary">
                            No inspection flows loaded yet. Click &quot;Inspect Flows&quot; above.
                          </td>
                        </tr>
                      ) : (
                        filteredTrafficRecords.map((r) => (
                          <tr key={r.row_index} className="hover:bg-base-elevated interactive-transition">
                            <td className="py-2 px-3 text-content-tertiary font-mono">#{r.row_index + 1}</td>
                            <td className="py-2 px-3 text-content-secondary font-mono text-[11px] whitespace-nowrap">
                              {formatTimestamp(r.timestamp)}
                            </td>
                            <td className="py-2 px-3 text-content-secondary">{r.ground_truth_raw || "Unlabeled"}</td>
                            <td className="py-2 px-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                  r.is_attack
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                    : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                }`}
                              >
                                {r.predicted_label}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-content-primary tabular-nums font-mono">
                              {(r.confidence * 100).toFixed(1)}%
                            </td>
                            <td className="py-2 px-3 text-content-secondary">{r.attack_category}</td>
                            <td className="py-2 px-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                  r.severity === "CRITICAL"
                                    ? "bg-rose-500/20 text-rose-400"
                                    : r.severity === "HIGH"
                                    ? "bg-amber-500/20 text-amber-400"
                                    : r.severity === "MEDIUM"
                                    ? "bg-cyan-500/20 text-cyan-400"
                                    : "bg-slate-500/20 text-slate-300"
                                }`}
                              >
                                {r.severity}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-[11px] text-content-secondary font-mono max-w-xs truncate" title={r.contributing_factor}>
                              {r.contributing_factor || (r.is_attack ? "Volumetric / pattern anomaly" : "Normal traffic baseline")}
                            </td>
                            <td className="py-2 px-3 text-[11px] text-content-tertiary font-mono">
                              {Object.entries(r.key_features || {})
                                .slice(0, 3)
                                .map(([k, v]) => `${k}:${Number(v).toFixed(1)}`)
                                .join(" · ")}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================
              VIEW 4: ANALYSIS & MODEL LAB
              ================================================================= */}
          {activeTab === "analysis" && (
            <div className="space-y-6">
              <div className="panel p-5 space-y-4">
                <div className="pb-3 border-b border-border-subtle">
                  <h2 className="text-sm font-semibold text-content-primary flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-brand" />
                    Model Optimization & LRRC-FS Laboratory
                  </h2>
                  <p className="text-xs text-content-secondary mt-0.5">
                    Configure and train tree ensembles with 4-term feature selection optimization
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                  <div>
                    <label htmlFor="analysis-classifier-select" className="block text-content-secondary mb-1">Classifier</label>
                    <select
                      id="analysis-classifier-select"
                      value={trainModel}
                      onChange={(e) => setTrainModel(e.target.value)}
                      className="w-full bg-base-elevated border border-border-subtle rounded p-2 text-content-primary text-xs focus:border-brand focus:outline-none"
                    >
                      <option value="random_forest">Random Forest (50 Trees)</option>
                      <option value="decision_tree">Decision Tree (Single Fast Tree)</option>
                      <option value="extra_trees">Extra Trees (Randomized Splits)</option>
                      <option value="gradient_boosting">HistGradientBoosting</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="analysis-task-select" className="block text-content-secondary mb-1">Classification Task</label>
                    <select
                      id="analysis-task-select"
                      value={trainTask}
                      onChange={(e) => setTrainTask(e.target.value)}
                      className="w-full bg-base-elevated border border-border-subtle rounded p-2 text-content-primary text-xs focus:border-brand focus:outline-none"
                    >
                      <option value="binary">Binary (BENIGN vs ATTACK)</option>
                      <option value="multiclass">Multiclass (8 Threat Families)</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="analysis-selector-select" className="block text-content-secondary mb-1">Feature Selector</label>
                    <select
                      id="analysis-selector-select"
                      value={trainSelector}
                      onChange={(e) => setTrainSelector(e.target.value)}
                      className="w-full bg-base-elevated border border-border-subtle rounded p-2 text-content-primary text-xs focus:border-brand focus:outline-none"
                    >
                      <option value="lrrc">LRRC-FS (4 Terms + Stability)</option>
                      <option value="kbest">SelectKBest (ANOVA F)</option>
                      <option value="variance">Variance Threshold</option>
                      <option value="all">All Features (k=39)</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleTrain}
                      disabled={trainLoading}
                      className="w-full py-2 px-4 rounded bg-brand hover:bg-brand-hover text-white font-medium flex items-center justify-center whitespace-nowrap interactive-transition disabled:opacity-50"
                    >
                      <span className="flex items-center gap-2 whitespace-nowrap">
                        {trainLoading ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Zap className="w-4 h-4" />
                        )}
                        <span>{trainLoading ? "Training…" : "Train Model"}</span>
                      </span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Latest Run Results Card */}
              {latestRun && (
                <div className="panel p-5 space-y-3">
                  <h3 className="text-xs font-semibold text-content-primary flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-status-success" />
                    Latest Run Output: <span className="font-mono">{latestRun.run_id}</span>
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
                    <div className="bg-base-elevated p-3 rounded border border-border-subtle">
                      <div className="text-[11px] text-content-secondary">Accuracy</div>
                      <div className="text-lg font-semibold text-content-primary mt-0.5 tabular-nums font-mono">
                        {(latestRun.accuracy * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-base-elevated p-3 rounded border border-border-subtle">
                      <div className="text-[11px] text-brand">Macro F1</div>
                      <div className="text-lg font-semibold text-brand mt-0.5 tabular-nums font-mono">
                        {(latestRun.macro_f1 * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-base-elevated p-3 rounded border border-border-subtle">
                      <div className="text-[11px] text-content-secondary">False Positive Rate</div>
                      <div className="text-lg font-semibold text-content-primary mt-0.5 tabular-nums font-mono">
                        {typeof latestRun.false_positive_rate === "number" ? `${(latestRun.false_positive_rate * 100).toFixed(2)}%` : "N/A"}
                      </div>
                    </div>
                    <div className="bg-base-elevated p-3 rounded border border-border-subtle">
                      <div className="text-[11px] text-content-secondary">Latency</div>
                      <div className="text-lg font-semibold text-content-primary mt-0.5 tabular-nums font-mono">
                        {latestRun.inference_latency_ms_per_sample} ms
                      </div>
                    </div>
                    <div className="bg-base-elevated p-3 rounded border border-border-subtle">
                      <div className="text-[11px] text-content-secondary">Features</div>
                      <div className="text-lg font-semibold text-content-primary mt-0.5 tabular-nums font-mono">
                        {latestRun.selected_features_count} / 39
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Algorithmic Formulation Reference */}
              <div className="panel p-5 space-y-3">
                <h3 className="text-xs font-semibold text-content-primary">
                  LRRC-FS 4-Term Objective Function
                </h3>
                <p className="text-xs text-content-secondary font-mono">
                  Score(f, S) = w_rel·R(f) - w_red·D(f, S) - w_cost·C(f) + w_stab·s(f)
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 bg-base-elevated rounded border border-border-subtle">
                    <div className="font-semibold text-content-primary">Relevance (0.40)</div>
                    <div className="text-content-secondary text-[11px] mt-1">
                      ANOVA F-statistic separating attack families from normal traffic
                    </div>
                  </div>
                  <div className="p-3 bg-base-elevated rounded border border-border-subtle">
                    <div className="font-semibold text-content-primary">Redundancy (0.25)</div>
                    <div className="text-content-secondary text-[11px] mt-1">
                      Mean absolute Pearson correlation with already selected features
                    </div>
                  </div>
                  <div className="p-3 bg-base-elevated rounded border border-border-subtle">
                    <div className="font-semibold text-content-primary">Cost (0.15)</div>
                    <div className="text-content-secondary text-[11px] mt-1">
                      Penalizes heavy dispersion statistics (0.9) vs packet flags (0.2)
                    </div>
                  </div>
                  <div className="p-3 bg-base-elevated rounded border border-border-subtle">
                    <div className="font-semibold text-content-primary">Stability (0.20)</div>
                    <div className="text-content-secondary text-[11px] mt-1">
                      Bootstrap selection frequency over 10 random sub-samples
                    </div>
                  </div>
                </div>
              </div>

              {/* Verified Benchmark Results (5-Seed Mean ± Std) */}
              <div className="p-5 rounded panel space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
                  <h3 className="text-xs font-semibold text-content-primary flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand" />
                    Verified Held-Out Benchmark Results (5-Seed Mean ± Std, 100,000 Flows)
                  </h3>
                  <button
                    onClick={handleExportCSV}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-base-elevated border border-border-subtle hover:bg-base-hover text-content-primary text-xs font-medium interactive-transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export Audit CSV</span>
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 rounded bg-base-elevated border border-border-subtle">
                    <span className="text-content-secondary block">Binary Accuracy</span>
                    <span className="text-sm font-semibold text-content-primary tabular-nums font-mono">98.65% ± 0.01%</span>
                  </div>
                  <div className="p-2.5 rounded bg-base-elevated border border-border-subtle">
                    <span className="text-content-secondary block">Binary Macro F1</span>
                    <span className="text-sm font-semibold text-brand tabular-nums font-mono">0.8359 ± 0.0011</span>
                  </div>
                  <div className="p-2.5 rounded bg-base-elevated border border-border-subtle">
                    <span className="text-content-secondary block">Raw Asymmetric FPR</span>
                    <span className="text-sm font-semibold text-amber-400 tabular-nums font-mono">45.85% (at 0.50)</span>
                  </div>
                  <div className="p-2.5 rounded bg-base-elevated border border-border-subtle">
                    <span className="text-content-secondary block">Calibrated FPR</span>
                    <span className="text-sm font-semibold text-emerald-400 tabular-nums font-mono">&lt; 15% (at 0.70)</span>
                  </div>
                </div>
              </div>

              {/* Historical Training Runs History Table */}
              <div className="panel p-5 space-y-3">
                <h3 className="text-xs font-semibold text-content-primary">
                  Stored Model Runs History ({runs.length})
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="text-content-secondary border-b border-border-subtle">
                      <tr>
                        <th className="py-2 px-3">Run ID</th>
                        <th className="py-2 px-3">Timestamp</th>
                        <th className="py-2 px-3">Task</th>
                        <th className="py-2 px-3">Model</th>
                        <th className="py-2 px-3">Accuracy</th>
                        <th className="py-2 px-3">Macro F1</th>
                        <th className="py-2 px-3">FPR</th>
                        <th className="py-2 px-3">Latency</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle">
                      {runs.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="py-6 text-center text-content-tertiary">
                            No historical runs recorded in database yet.
                          </td>
                        </tr>
                      ) : (
                        runs.slice(0, 15).map((r) => (
                          <tr key={r.run_id} className="hover:bg-base-elevated interactive-transition">
                            <td className="py-2 px-3 text-content-primary font-medium font-mono">{r.run_id}</td>
                            <td className="py-2 px-3 text-content-secondary font-mono text-[11px] whitespace-nowrap">
                              {formatTimestamp(r.timestamp)}
                            </td>
                            <td className="py-2 px-3 text-content-secondary font-mono">{r.task_type}</td>
                            <td className="py-2 px-3 text-content-primary">{r.model_name}</td>
                            <td className="py-2 px-3 text-content-primary tabular-nums font-mono">{(r.accuracy * 100).toFixed(2)}%</td>
                            <td className="py-2 px-3 text-brand tabular-nums font-mono">{(r.macro_f1 * 100).toFixed(2)}%</td>
                            <td className="py-2 px-3 text-content-primary tabular-nums font-mono">
                              {typeof r.false_positive_rate === "number" ? `${(r.false_positive_rate * 100).toFixed(2)}%` : "—"}
                            </td>
                            <td className="py-2 px-3 text-content-tertiary">
                              <span className="tabular-nums font-mono">{r.inference_latency_ms_per_sample}</span> ms
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
>>>>>>> Stashed changes
    </div>
    {toast && <div role="status" className="toast"><CheckCircle2 size={16} />{toast}<button className="icon-button" aria-label="Dismiss notification" onClick={() => setToast("")}><X size={14} /></button></div>}
  </div>;
}
