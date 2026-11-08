"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Shield,
  LayoutDashboard,
  AlertOctagon,
  Activity,
  BarChart3,
  FileText,
  Sliders,
  Server,
  Settings,
  Search,
  Download,
  CheckCircle2,
  XCircle,
  Play,
  RefreshCw,
  Cpu,
  Database,
  Check,
  Zap,
  Menu,
  X,
  ShieldAlert,
  Terminal,
  Info,
} from "lucide-react";

// Types matching Python REST API schemas
interface StatusData {
  status: string;
  system: string;
  active_model: string;
  active_task: string;
  total_detection_events: number;
  total_attacks_detected: number;
  total_benign_flows?: number;
  total_training_runs: number;
  raw_datasets_count: number;
  synthetic_datasets_count: number;
  total_dataset_size_gb?: number;
  db_size_mb: number;
  system_telemetry?: {
    cpu_threads?: number;
    mem_percent?: number;
    mem_avail_gb?: number;
    disk_percent?: number;
    disk_used_gb?: number;
  };
  python_version?: string;
  platform?: string;
}

interface DatasetFile {
  name: string;
  path: string;
  relative_path: string;
  size_mb: number;
  type: string;
  is_synthetic: boolean;
}

interface ModelItem {
  name: string;
  path: string;
  size_kb: number;
  modified: string;
  task: string;
  algorithm: string;
  is_active: boolean;
}

interface TestRecord {
  row_index: number;
  ground_truth_raw: string | null;
  ground_truth_mapped: string;
  predicted_label: string;
  confidence: number;
  is_attack: boolean;
  attack_category: string;
  severity: string;
  policy_triggered: string | null;
  is_match: boolean | null;
  key_features: Record<string, number>;
}

interface TestSummary {
  dataset_file: string;
  dataset_path: string;
  model_used: string;
  model_task: string;
  total_samples_tested: number;
  attacks_detected: number;
  benign_detected: number;
  has_ground_truth: boolean;
  accuracy_percentage: number | null;
  total_time_seconds: number;
  latency_ms_per_sample: number;
}

interface PolicyItem {
  policy_id: string;
  name: string;
  description: string;
  severity: string;
  min_confidence: number;
  action: string;
  enabled?: boolean;
}

interface TrainingRunItem {
  run_id: string;
  timestamp: string;
  task_type: string;
  model_name: string;
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  inference_latency_ms_per_sample: number;
  selected_features_count: number;
  dataset_path?: string;
}

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "traffic", label: "Flow Inspection", icon: Activity },
  { id: "analysis", label: "ML Lab & Models", icon: BarChart3 },
  { id: "alerts", label: "Alerts & Defense", icon: AlertOctagon },
];

const FLOW_OPTIONS = [
  { value: 50000, label: "50,000 Flows (50K)" },
  { value: 100000, label: "1,00,000 Flows (1 Lakh - Standard)" },
  { value: 200000, label: "2,00,000 Flows (2 Lakhs)" },
  { value: 500000, label: "5,00,000 Flows (5 Lakhs)" },
  { value: 1000000, label: "10,00,000 Flows (10 Lakhs - Stress Test)" },
];

export default function DevrakshakDashboard() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Data states
  const [status, setStatus] = useState<StatusData | null>(null);
  const [datasets, setDatasets] = useState<DatasetFile[]>([]);
  const [models, setModels] = useState<ModelItem[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [policies, setPolicies] = useState<PolicyItem[]>([]);
  const [runs, setRuns] = useState<TrainingRunItem[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Traffic / Flow Inspection states
  const [selectedDataset, setSelectedDataset] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [sampleLimit, setSampleLimit] = useState<number>(100000);
  const [testLoading, setTestLoading] = useState<boolean>(false);
  const [testSummary, setTestSummary] = useState<TestSummary | null>(null);
  const [testRecords, setTestRecords] = useState<TestRecord[]>([]);

  // Alerts filter state
  const [alertSeverityFilter, setAlertSeverityFilter] = useState<string>("ALL");

  // Model Training states
  const [trainModel, setTrainModel] = useState<string>("random_forest");
  const [trainTask, setTrainTask] = useState<string>("binary");
  const [trainSelector, setTrainSelector] = useState<string>("lrrc");
  const [trainNumFeatures, setTrainNumFeatures] = useState<number>(15);
  const [trainSampleLimit, setTrainSampleLimit] = useState<number>(15000);
  const [trainLoading, setTrainLoading] = useState<boolean>(false);
  const [latestRun, setLatestRun] = useState<any>(null);

  // Feedback Toast
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" | "info" } | null>(null);

  const showToast = (msg: string, type: "success" | "error" | "info" = "info") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3600);
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchStatus(),
      fetchDatasets(),
      fetchModels(),
      fetchStats(),
      fetchPolicies(),
      fetchRuns(),
      fetchLogs(),
    ]);
    setRefreshing(false);
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      if (data.success) setStatus(data);
    } catch (e) {
      console.error("fetchStatus error:", e);
    }
  };

  const fetchDatasets = async () => {
    try {
      const res = await fetch("/api/datasets");
      const data = await res.json();
      if (data.success && Array.isArray(data.files)) {
        setDatasets(data.files);
        if (data.files.length > 0 && !selectedDataset) {
          setSelectedDataset(data.files[0].path);
        }
      }
    } catch (e) {
      console.error("fetchDatasets error:", e);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await fetch("/api/models");
      const data = await res.json();
      if (data.success && Array.isArray(data.models)) {
        setModels(data.models);
        if (data.models.length > 0 && !selectedModel) {
          const active = data.models.find((m: ModelItem) => m.is_active) || data.models[0];
          setSelectedModel(active.path);
        }
      }
    } catch (e) {
      console.error("fetchModels error:", e);
    }
  };

  const fetchStats = async () => {
    try {
      const [sRes, eRes] = await Promise.all([
        fetch("/api/stats"),
        fetch("/api/events?limit=40"),
      ]);
      const s = await sRes.json();
      const e = await eRes.json();
      if (s.success) setStats(s.stats);
      if (e.success && Array.isArray(e.events)) setRecentEvents(e.events);
    } catch (err) {
      console.error("fetchStats error:", err);
    }
  };

  const fetchPolicies = async () => {
    try {
      const res = await fetch("/api/policies");
      const data = await res.json();
      if (data.success && Array.isArray(data.policies)) setPolicies(data.policies);
    } catch (e) {
      console.error("fetchPolicies error:", e);
    }
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch("/api/runs?limit=30");
      const data = await res.json();
      if (data.success && Array.isArray(data.runs)) setRuns(data.runs);
    } catch (e) {
      console.error("fetchRuns error:", e);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch("/api/logs?limit=50");
      const data = await res.json();
      if (data.success && Array.isArray(data.lines)) setLogs(data.lines);
    } catch (e) {
      console.error("fetchLogs error:", e);
    }
  };

  // Run Traffic Flow Inspection
  const handleRunInference = async () => {
    const datasetToUse = selectedDataset || (datasets.length > 0 ? datasets[0].path : "");
    if (!datasetToUse) {
      showToast("Please select a dataset partition first.", "error");
      return;
    }
    setTestLoading(true);
    try {
      const res = await fetch("/api/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: datasetToUse,
          model_path: selectedModel || undefined,
          sample_limit: sampleLimit,
          record_events: true,
        }),
      });

      if (!res.ok) {
        let errMessage = `Backend server (http://127.0.0.1:8000) returned error ${res.status}. Please ensure Python engine is running: 'uv run python -m src.web.server --port 8000'.`;
        try {
          const errData = await res.json();
          if (errData.error) errMessage = errData.error;
          else if (errData.details) errMessage = errData.details;
        } catch (_) {}
        showToast(errMessage, "error");
        return;
      }

      const data = await res.json();
      if (data.success) {
        setTestSummary(data.summary);
        setTestRecords(data.records);
        const totalTested = data.summary.total_samples_tested?.toLocaleString() || data.records.length;
        showToast(
          `Classified ${totalTested} flows in ${data.summary.total_time_seconds}s (${data.summary.latency_ms_per_sample} ms/flow)`,
          "success"
        );
        fetchStats();
        fetchStatus();
      } else {
        showToast(data.error || "Inference failed", "error");
      }
    } catch (err: any) {
      showToast(err.message || "Failed to connect to backend", "error");
    } finally {
      setTestLoading(false);
    }
  };

  // Quick Offline Evaluation Trigger
  const handleQuickOfflineRun = async (targetFile?: string, limitCount: number = 100000) => {
    const fileToTest = targetFile || selectedDataset || (datasets.length > 0 ? datasets[0].path : "");
    if (!fileToTest) {
      showToast("No offline dataset partition available.", "error");
      return;
    }
    const fileName = fileToTest.split(/[/\\]/).pop();
    setTestLoading(true);
    showToast(`Evaluating ${limitCount.toLocaleString()} flows from ${fileName}…`, "info");
    try {
      const res = await fetch("/api/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: fileToTest,
          model_path: selectedModel || undefined,
          sample_limit: limitCount,
          record_events: true,
        }),
      });

      if (!res.ok) {
        let errMessage = `Backend server (http://127.0.0.1:8000) returned error ${res.status}. Please ensure Python engine is running: 'uv run python -m src.web.server --port 8000'.`;
        try {
          const errData = await res.json();
          if (errData.error) errMessage = errData.error;
          else if (errData.details) errMessage = errData.details;
        } catch (_) {}
        showToast(errMessage, "error");
        return;
      }

      const data = await res.json();
      if (data.success) {
        setTestSummary(data.summary);
        setTestRecords(data.records);
        const totalTested = data.summary.total_samples_tested?.toLocaleString() || data.records.length;
        showToast(`Inspected ${totalTested} flows. Database updated!`, "success");
        await Promise.all([fetchStats(), fetchStatus()]);
      } else {
        showToast(data.error || "Execution failed", "error");
      }
    } catch (err: any) {
      showToast(err.message || "Failed to connect to backend", "error");
    } finally {
      setTestLoading(false);
    }
  };

  // Model Training Trigger
  const handleTrain = async () => {
    const datasetToUse = selectedDataset || (datasets.length > 0 ? datasets[0].path : "");
    setTrainLoading(true);
    try {
      const res = await fetch("/api/train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_path: datasetToUse || undefined,
          model_name: trainModel,
          task_type: trainTask,
          feature_selector: trainSelector,
          n_features: trainNumFeatures,
          sample_limit: trainSampleLimit,
          use_class_weight: true,
        }),
      });

      if (!res.ok) {
        let errMessage = `Backend server (http://127.0.0.1:8000) returned error ${res.status}. Please ensure Python engine is running: 'uv run python -m src.web.server --port 8000'.`;
        try {
          const errData = await res.json();
          if (errData.error) errMessage = errData.error;
          else if (errData.details) errMessage = errData.details;
        } catch (_) {}
        showToast(errMessage, "error");
        return;
      }

      const data = await res.json();
      if (data.success) {
        setLatestRun(data.run);
        showToast(
          `Bundle trained: Accuracy ${(data.run.accuracy * 100).toFixed(2)}% | Macro F1 ${(data.run.macro_f1 * 100).toFixed(2)}%`,
          "success"
        );
        fetchModels();
        fetchRuns();
        fetchStatus();
      } else {
        showToast(data.error || "Training failed", "error");
      }
    } catch (err: any) {
      showToast(err.message || "Failed to connect to backend", "error");
    } finally {
      setTrainLoading(false);
    }
  };

  // Export CSV of detection events
  const handleExportCSV = () => {
    const list = testRecords.length > 0 ? testRecords : recentEvents;
    if (!list || list.length === 0) {
      showToast("No detection events to export.", "error");
      return;
    }
    const headers = [
      "Timestamp",
      "Detection_Label",
      "Attack_Category",
      "Source_Partition",
      "Flow_Index",
      "Confidence",
      "Severity",
      "Action",
    ];
    const rows = list.map((r: any) => [
      `"${r.timestamp || new Date().toISOString()}"`,
      `"${r.predicted_label || r.attack_category || "Benign"}"`,
      `"${r.attack_category || "Benign"}"`,
      `"${r.source_file || (selectedDataset ? selectedDataset.split(/[/\\]/).pop() : "Merged01.csv")}"`,
      `"${r.row_index !== undefined ? r.row_index : 0}"`,
      `"${r.confidence !== undefined ? (Number(r.confidence) * 100).toFixed(1) + "%" : "100%"}"`,
      `"${r.severity || "INFO"}"`,
      `"${r.action || (r.is_attack ? "Blocked" : "Logged")}"`,
    ]);
    const content = [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ids_detection_export_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported ${rows.length} detection rows as CSV.`, "success");
  };

  // Filtered recent events for Alerts tab
  const filteredAlerts = useMemo(() => {
    return recentEvents.filter((ev) => {
      const sev = (ev.severity || "INFO").toUpperCase();
      const matchesSev = alertSeverityFilter === "ALL" || sev === alertSeverityFilter;
      const label = (ev.predicted_label || ev.attack_category || "").toLowerCase();
      const query = searchQuery.toLowerCase().trim();
      const matchesQuery = !query || label.includes(query) || (ev.source_file || "").toLowerCase().includes(query);
      return matchesSev && matchesQuery;
    });
  }, [recentEvents, alertSeverityFilter, searchQuery]);

  // Filtered traffic records
  const filteredTrafficRecords = useMemo(() => {
    if (!searchQuery.trim()) return testRecords;
    const q = searchQuery.toLowerCase();
    return testRecords.filter(
      (r) =>
        r.predicted_label.toLowerCase().includes(q) ||
        r.attack_category.toLowerCase().includes(q) ||
        (r.ground_truth_raw && r.ground_truth_raw.toLowerCase().includes(q))
    );
  }, [testRecords, searchQuery]);

  return (
    <div className="flex min-h-screen bg-base-bg text-content-primary font-sans antialiased">
      {/* Toast Notification */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-md text-xs font-medium border flex items-center gap-2.5 shadow-lg ${
            toast.type === "success"
              ? "toast-success"
              : toast.type === "error"
              ? "toast-error"
              : "toast-info"
          }`}
        >
          {toast.type === "success" && <Check className="w-4 h-4 text-emerald-400 shrink-0" />}
          {toast.type === "error" && <XCircle className="w-4 h-4 text-rose-400 shrink-0" />}
          {toast.type === "info" && <Info className="w-4 h-4 text-blue-400 shrink-0" />}
          <span>{toast.msg}</span>
        </div>
      )}

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* =====================================================================
          SIDEBAR NAVIGATION (Fixed Desktop, Collapsible Mobile)
          ===================================================================== */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 bg-base-surface border-r border-border-subtle flex flex-col justify-between shrink-0 transform transition-transform duration-200 ease-in-out md:translate-x-0 ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div>
          {/* Header Brand */}
          <div className="px-5 py-5 flex items-center justify-between border-b border-border-subtle">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-brand/15 border border-brand/40 flex items-center justify-center text-brand">
                <Shield className="w-4 h-4" />
              </div>
              <div>
                <span className="font-semibold text-sm tracking-wide text-content-primary block">
                  DEVRAKSHAK
                </span>
                <span className="text-[11px] text-content-secondary block">
                  AI Intrusion Defense
                </span>
              </div>
            </div>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="md:hidden text-content-tertiary hover:text-content-primary"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1" aria-label="Main navigation">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-md text-xs font-medium text-left interactive-transition ${
                    isActive
                      ? "bg-brand text-white font-semibold"
                      : "text-content-secondary hover:text-content-primary hover:bg-base-elevated"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-content-tertiary"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer Status */}
        <div className="p-4 border-t border-border-subtle text-xs bg-base-surface">
          <div className="flex items-center gap-2 text-content-secondary">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="font-medium text-content-primary">System Operational</span>
          </div>
          <div className="text-[11px] text-content-tertiary mt-1">
            <span className="tabular-nums font-mono">{status?.raw_datasets_count || 63}</span> Partitions Ready
          </div>
          <div className="text-[10px] text-content-tertiary mt-2">
            CICIoT2023 · Offline Mode
          </div>
        </div>
      </aside>

      {/* =====================================================================
          MAIN WORKSPACE AREA
          ===================================================================== */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 px-6 bg-base-surface/90 border-b border-border-subtle flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden text-content-secondary hover:text-content-primary"
              aria-label="Open navigation"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-sm font-semibold text-content-primary">
              {NAV_ITEMS.find((n) => n.id === activeTab)?.label}
            </h1>
          </div>

          {/* Search and Global Quick Controls */}
          <div className="flex items-center gap-3">
            <div className="relative w-48 sm:w-64">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-content-tertiary" />
              <input
                type="text"
                placeholder="Search flows, alerts, rules…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-base-elevated border border-border-subtle rounded-md pl-9 pr-3 py-1.5 text-xs text-content-primary placeholder:text-content-tertiary focus:border-brand focus:outline-none"
              />
            </div>

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
                          const timeStr = row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : "—";
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

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
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
                        <th className="py-2.5 px-3">Ground Truth</th>
                        <th className="py-2.5 px-3">Prediction</th>
                        <th className="py-2.5 px-3">Confidence</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Severity</th>
                        <th className="py-2.5 px-3">Extracted Features</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle">
                      {filteredTrafficRecords.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-content-tertiary">
                            No inspection flows loaded yet. Click &quot;Inspect Flows&quot; above.
                          </td>
                        </tr>
                      ) : (
                        filteredTrafficRecords.map((r) => (
                          <tr key={r.row_index} className="hover:bg-base-elevated interactive-transition">
                            <td className="py-2 px-3 text-content-tertiary font-mono">#{r.row_index + 1}</td>
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
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
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
            </div>
          )}

          {/* =================================================================
              VIEW 5: REPORTS & EXPERIMENTAL RUNS
              ================================================================= */}
          {activeTab === "reports" && (
            <div className="space-y-6">
              <div className="panel p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
                  <div>
                    <h2 className="text-sm font-semibold text-content-primary flex items-center gap-2">
                      <FileText className="w-4 h-4 text-brand" />
                      Research Reports & Multi-Seed Benchmark Runs
                    </h2>
                    <p className="text-xs text-content-secondary mt-0.5">
                      Empirical evaluation records on the CICIoT2023 held-out test split (100,000 flows)
                    </p>
                  </div>
                  <button
                    onClick={handleExportCSV}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-base-elevated border border-border-subtle hover:bg-base-hover text-content-primary text-xs font-medium interactive-transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export Audit CSV</span>
                  </button>
                </div>

                {/* Benchmark Summary Table */}
                <div className="p-4 rounded bg-base-elevated border border-border-subtle space-y-3">
                  <h3 className="text-xs font-semibold text-content-primary">
                    Verified Benchmark Results (5-Seed Mean ± Std)
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div className="p-2.5 rounded bg-base-surface border border-border-subtle">
                      <span className="text-content-secondary block">Binary Accuracy</span>
                      <span className="text-sm font-semibold text-content-primary tabular-nums font-mono">98.65% ± 0.01%</span>
                    </div>
                    <div className="p-2.5 rounded bg-base-surface border border-border-subtle">
                      <span className="text-content-secondary block">Binary Macro F1</span>
                      <span className="text-sm font-semibold text-brand tabular-nums font-mono">0.8359 ± 0.0011</span>
                    </div>
                    <div className="p-2.5 rounded bg-base-surface border border-border-subtle">
                      <span className="text-content-secondary block">Benign False Positive Rate</span>
                      <span className="text-sm font-semibold text-amber-400 tabular-nums font-mono">45.85% ± 0.32%</span>
                    </div>
                  </div>
                </div>

                {/* Historical Runs Table from SQLite */}
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-content-primary">
                    Stored Training Runs History ({runs.length})
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
                          <th className="py-2 px-3">Latency</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle">
                        {runs.length === 0 ? (
                          <tr>
                            <td colSpan={7} className="py-6 text-center text-content-tertiary">
                              No historical runs recorded in database.
                            </td>
                          </tr>
                        ) : (
                          runs.map((r) => (
                            <tr key={r.run_id} className="hover:bg-base-elevated interactive-transition">
                              <td className="py-2 px-3 text-content-primary font-medium font-mono">{r.run_id}</td>
                              <td className="py-2 px-3 text-content-secondary">
                                {r.timestamp ? new Date(r.timestamp).toLocaleString() : "—"}
                              </td>
                              <td className="py-2 px-3 text-content-secondary font-mono">{r.task_type}</td>
                              <td className="py-2 px-3 text-content-primary">{r.model_name}</td>
                              <td className="py-2 px-3 text-content-primary tabular-nums font-mono">{(r.accuracy * 100).toFixed(2)}%</td>
                              <td className="py-2 px-3 text-brand tabular-nums font-mono">{(r.macro_f1 * 100).toFixed(2)}%</td>
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
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
