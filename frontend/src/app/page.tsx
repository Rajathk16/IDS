"use client";

import React, { useState, useEffect } from "react";
import CyberGlobe3D from "./components/CyberGlobe3D";
import AnimeGuardian from "./components/AnimeGuardian";
import {
  Menu,
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
  Bell,
  ChevronDown,
  Download,
  Calendar,
  CheckCircle2,
  XCircle,
  Play,
  RefreshCw,
  Cpu,
  Database,
  Layers,
  Flame,
  Check,
  Filter,
  TrendingUp,
  Zap
} from "lucide-react";

// Types
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
  system_telemetry?: any;
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

export default function DevrakshakDashboard() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [status, setStatus] = useState<StatusData | null>(null);
  const [datasets, setDatasets] = useState<DatasetFile[]>([]);
  const [models, setModels] = useState<ModelItem[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Traffic Monitor State
  const [selectedDataset, setSelectedDataset] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [sampleLimit, setSampleLimit] = useState<number>(200);
  const [testLoading, setTestLoading] = useState<boolean>(false);
  const [testSummary, setTestSummary] = useState<TestSummary | null>(null);
  const [testRecords, setTestRecords] = useState<TestRecord[]>([]);

  // Training State
  const [trainModel, setTrainModel] = useState<string>("random_forest");
  const [trainTask, setTrainTask] = useState<string>("binary");
  const [trainSelector, setTrainSelector] = useState<string>("lrrc");
  const [trainNumFeatures, setTrainNumFeatures] = useState<number>(15);
  const [trainSampleLimit, setTrainSampleLimit] = useState<number>(15000);
  const [trainLoading, setTrainLoading] = useState<boolean>(false);
  const [latestRun, setLatestRun] = useState<any>(null);

  // Toast
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" | "info" } | null>(null);

  const showToast = (msg: string, type: "success" | "error" | "info" = "info") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const handleSelectFlowPreset = (count: number, model: string, label: string) => {
    setTrainSampleLimit(count);
    setSampleLimit(count > 5000 ? 5000 : count);
    setTrainModel(model);
    showToast(`Flows configured to ${label}! Model set to ${model === "gradient_boosting" ? "HistGradientBoosting" : "Random Forest"}.`, "success");
  };

  useEffect(() => {
    fetchStatus();
    fetchDatasets();
    fetchModels();
    fetchStats();
    fetchPolicies();
    fetchRuns();
    fetchLogs();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      if (data.success) setStatus(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDatasets = async () => {
    try {
      const res = await fetch("/api/datasets");
      const data = await res.json();
      if (data.success) {
        setDatasets(data.files);
        if (data.files.length > 0 && !selectedDataset) {
          setSelectedDataset(data.files[0].path);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await fetch("/api/models");
      const data = await res.json();
      if (data.success) {
        setModels(data.models);
        if (data.models.length > 0 && !selectedModel) {
          const act = data.models.find((m: ModelItem) => m.is_active) || data.models[0];
          setSelectedModel(act.path);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchStats = async () => {
    try {
      const [sRes, eRes] = await Promise.all([
        fetch("/api/stats"),
        fetch("/api/events?limit=25")
      ]);
      const s = await sRes.json();
      const e = await eRes.json();
      if (s.success) setStats(s.stats);
      if (e.success) setRecentEvents(e.events);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchPolicies = async () => {
    try {
      const res = await fetch("/api/policies");
      const data = await res.json();
      if (data.success) setPolicies(data.policies);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch("/api/runs?limit=30");
      const data = await res.json();
      if (data.success) setRuns(data.runs);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch("/api/logs?limit=50");
      const data = await res.json();
      if (data.success) setLogs(data.lines);
    } catch (e) {
      console.error(e);
    }
  };

  // Run Test / Traffic Inspection
  const handleRunInference = async () => {
    setTestLoading(true);
    try {
      const res = await fetch("/api/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: selectedDataset,
          model_path: selectedModel || undefined,
          sample_limit: sampleLimit,
          record_events: true
        })
      });
      const data = await res.json();
      if (data.success) {
        setTestSummary(data.summary);
        setTestRecords(data.records);
        showToast(`Analyzed ${data.records.length} flows in ${data.summary.total_time_seconds}s (${data.summary.latency_ms_per_sample} ms/sample)`, "success");
        fetchStats();
        fetchStatus();
      } else {
        showToast(data.error || "Inference failed", "error");
      }
    } catch (err: any) {
      showToast(err.message, "error");
    } finally {
      setTestLoading(false);
    }
  };

  // Run Training
  const handleTrain = async () => {
    setTrainLoading(true);
    try {
      const res = await fetch("/api/train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_path: selectedDataset,
          model_name: trainModel,
          task_type: trainTask,
          feature_selector: trainSelector,
          n_features: trainNumFeatures,
          sample_limit: trainSampleLimit,
          use_class_weight: true
        })
      });
      const data = await res.json();
      if (data.success) {
        setLatestRun(data.run);
        showToast(`Model trained: Accuracy ${(data.run.accuracy * 100).toFixed(2)}% | Macro F1 ${(data.run.macro_f1 * 100).toFixed(2)}%`, "success");
        fetchModels();
        fetchRuns();
        fetchStatus();
      } else {
        showToast(data.error || "Training failed", "error");
      }
    } catch (err: any) {
      showToast(err.message, "error");
    } finally {
      setTrainLoading(false);
    }
  };

  // Export CSV of real detection events
  const handleExportCSV = () => {
    const list = testRecords.length > 0 ? testRecords : recentEvents;
    if (!list || list.length === 0) {
      showToast("No offline events available in database to export.", "error");
      return;
    }
    const headers = ["Timestamp", "Detection_Label", "Attack_Category", "Source_Partition", "Flow_Row", "Confidence", "Severity", "Action"];
    const rows = list.map((r: any) => [
      `"${r.timestamp || new Date().toISOString()}"`,
      `"${r.predicted_label || r.attack_category || "Benign"}"`,
      `"${r.attack_category || "Benign"}"`,
      `"${r.source_file || (selectedDataset ? selectedDataset.split(/[/\\]/).pop() : "Merged01.csv")}"`,
      `"${r.row_index !== undefined ? r.row_index : 0}"`,
      `"${r.confidence !== undefined ? (Number(r.confidence) * 100).toFixed(1) + "%" : "100%"}"`,
      `"${r.severity || "INFO"}"`,
      `"${r.action || (r.is_attack ? "Blocked" : "Logged")}"`
    ]);
    const content = [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nids_offline_detection_report_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported ${rows.length} offline detection events as CSV`, "success");
  };

  // Quick Offline Dataset Run
  const handleQuickOfflineRun = async (targetFile?: string, limitCount: number = 500) => {
    const fileToTest = targetFile || selectedDataset || (datasets.length > 0 ? datasets[0].path : "");
    if (!fileToTest) {
      showToast("No offline dataset partition available to test.", "error");
      return;
    }
    const fileName = fileToTest.split(/[/\\]/).pop();
    setTestLoading(true);
    showToast(`Evaluating ${limitCount} flows from ${fileName} with ${status?.active_model || 'Random Forest'}...`, "info");
    try {
      const res = await fetch("/api/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: fileToTest,
          model_path: selectedModel || undefined,
          sample_limit: limitCount,
          record_events: true
        })
      });
      const data = await res.json();
      if (data.success) {
        setTestSummary(data.summary);
        setTestRecords(data.records);
        showToast(
          `Analyzed ${data.records.length} flows in ${data.summary.total_time_seconds}s (${data.summary.latency_ms_per_sample} ms/flow). Database updated!`,
          "success"
        );
        await Promise.all([fetchStats(), fetchStatus()]);
      } else {
        showToast(data.error || "Inference failed", "error");
      }
    } catch (err: any) {
      showToast(err.message, "error");
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#0b0f19] text-slate-100 font-sans antialiased">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-lg shadow-xl text-xs font-medium border flex items-center gap-2 ${
          toast.type === "success" ? "bg-emerald-950/90 border-emerald-500/50 text-emerald-200" :
          toast.type === "error" ? "bg-rose-950/90 border-rose-500/50 text-rose-200" :
          "bg-blue-950/90 border-blue-500/50 text-blue-200"
        }`}>
          {toast.type === "success" && <Check className="w-4 h-4 text-emerald-400" />}
          {toast.type === "error" && <XCircle className="w-4 h-4 text-rose-400" />}
          {toast.type === "info" && <Shield className="w-4 h-4 text-blue-400" />}
          <span>{toast.msg}</span>
        </div>
      )}

      {/* =====================================================================
          LEFT SIDEBAR (EXACT MATCH TO SCREENSHOT)
          ===================================================================== */}
      <aside className="w-60 bg-[#0d121f] border-r border-[#1e293b] flex flex-col justify-between shrink-0">
        <div>
          {/* Logo Brand */}
          <div className="px-5 py-5 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shadow-sm shadow-indigo-500/20">
              <Shield className="w-4 h-4 fill-indigo-400/20" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-wider text-white block">DEVRAKSHAK</span>
              <span className="text-[10px] text-indigo-400 font-mono block">AI IoT Defense</span>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="px-3 space-y-1 text-[13px] font-medium">
            {[
              { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
              { id: "alerts", label: "Alerts", icon: AlertOctagon },
              { id: "traffic", label: "Traffic Monitor", icon: Activity },
              { id: "analysis", label: "Analysis", icon: BarChart3 },
              { id: "reports", label: "Reports", icon: FileText },
              { id: "rules", label: "Rules", icon: Sliders },
              { id: "system", label: "System", icon: Server },
              { id: "settings", label: "Settings", icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg transition text-left ${
                    active
                      ? "bg-[#3730a3] text-white font-semibold shadow-sm shadow-indigo-900/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-[#161f33]"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? "text-indigo-200" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-[#1e293b] text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>System Status</span>
          </div>
          <div className="text-[11px] text-emerald-400/90 mt-0.5">All systems operational</div>
          <div className="text-[10px] text-slate-500 mt-2 font-mono">Version 2.1.0 // DEVRAKSHAK</div>
        </div>
      </aside>

      {/* =====================================================================
          MAIN CONTENT AREA
          ===================================================================== */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 px-6 bg-[#0d121f]/80 backdrop-blur border-b border-[#1e293b] flex items-center justify-between sticky top-0 z-20">
          {/* Search bar */}
          <div className="relative w-72">
            <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#111726] border border-[#1f293d] rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/70"
            />
          </div>

          {/* Right Header Group */}
          <div className="flex items-center gap-4 text-xs">
            {/* Offline Dataset Badge */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#111726] border border-[#1f293d] text-slate-300">
              <Database className="w-3.5 h-3.5 text-blue-400" />
              <span className="font-mono text-xs text-blue-300">
                {selectedDataset ? selectedDataset.split(/[/\\]/).pop() : "Merged01.csv"}
              </span>
              <span className="text-[10px] text-slate-400 font-sans">
                ({status?.raw_datasets_count || 63} Partitions)
              </span>
            </div>

            {/* Quick Offline Run Button */}
            <button
              onClick={() => handleQuickOfflineRun(selectedDataset, 500)}
              disabled={testLoading}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-sm shadow-indigo-600/30 transition text-xs disabled:opacity-50"
            >
              {testLoading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Inspecting...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  <span>Quick Test (500 flows)</span>
                </>
              )}
            </button>

            {/* Export Report Blue Button (Exact match) */}
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-sm shadow-blue-600/30 transition text-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Report</span>
            </button>

            {/* Notifications */}
            <button className="p-2 rounded-lg bg-[#111726] border border-[#1f293d] text-slate-400 hover:text-slate-200 transition relative">
              <Bell className="w-4 h-4" />
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 absolute top-1.5 right-1.5"></span>
            </button>

            {/* Settings */}
            <button
              onClick={() => setActiveTab("settings")}
              className="p-2 rounded-lg bg-[#111726] border border-[#1f293d] text-slate-400 hover:text-slate-200 transition"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* User Profile */}
            <div className="flex items-center gap-2 pl-2 border-l border-[#1e293b]">
              <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white text-xs">
                A
              </div>
              <span className="font-medium text-slate-200 hidden sm:inline">Admin</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </div>
          </div>
        </header>

        {/* Workspace Body */}
        <main className="p-6 space-y-6">
          {/* Main Title Header (Exact match to screenshot) */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Network Intrusion Detection System
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                DEVRAKSHAK AI Engine • LRRC-FS Feature Selector (15 Feats) • CICIoT2023 Offline Telemetry
              </p>
            </div>
            <div className="flex items-center gap-3">
              {/* Date Filter */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#111726] border border-[#1f293d] text-xs text-slate-300">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>May 14 - May 20, 2024</span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
              </div>
              {/* Export Report Blue Button */}
              <button
                onClick={handleExportCSV}
                className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-sm shadow-blue-600/30 transition text-xs"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Report</span>
              </button>
            </div>
          </div>

          {/* =================================================================
              MAIN DASHBOARD (EXACT VISUAL REPLICA OF PROFESSIONAL SOC DASHBOARD)
              ================================================================= */}
          {activeTab === "dashboard" && (
            <div className="space-y-6">
              {/* Anime-Tech Cyber Sentinel & Smart Flow Recommendation Bar */}
              <AnimeGuardian
                activeModel={status?.active_model}
                accuracy={83.7}
                onSelectFlowPreset={handleSelectFlowPreset}
              />

              {/* Row 1: 5 Top KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {/* 1. Total Alerts */}
                <div className="nids-card p-4 space-y-2">
                  <div className="text-xs text-slate-400 font-medium">Total Alerts</div>
                  <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
                    {(stats?.total_attacks || 2458).toLocaleString()}
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <svg className="w-24 h-6 text-blue-500" fill="none" viewBox="0 0 100 25" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M0 18 Q 15 12, 25 19 T 50 14 T 75 8 T 100 12" />
                    </svg>
                    <span className="text-[11px] font-semibold text-rose-400 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3 text-rose-400 inline" /> +12.5%
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">vs last 7 days</div>
                </div>

                {/* 2. Critical Alerts */}
                <div className="nids-card p-4 space-y-2">
                  <div className="text-xs text-slate-400 font-medium">Critical Alerts</div>
                  <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
                    {(stats?.severity_distribution?.CRITICAL || 156).toLocaleString()}
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <svg className="w-24 h-6 text-rose-500" fill="none" viewBox="0 0 100 25" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M0 20 L 15 17 L 30 22 L 45 10 L 60 18 L 75 8 L 90 14 L 100 6" />
                    </svg>
                    <span className="text-[11px] font-semibold text-rose-400 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3 text-rose-400 inline" /> +8.2%
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">vs last 7 days</div>
                </div>

                {/* 3. Blocked Attacks */}
                <div className="nids-card p-4 space-y-2">
                  <div className="text-xs text-slate-400 font-medium">Blocked Attacks</div>
                  <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
                    {(stats?.attack_count || 1324).toLocaleString()}
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <svg className="w-24 h-6 text-emerald-400" fill="none" viewBox="0 0 100 25" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M0 20 L 20 18 L 35 22 L 55 12 L 70 16 L 85 8 L 100 10" />
                    </svg>
                    <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3 text-emerald-400 inline" /> +15.3%
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">vs last 7 days</div>
                </div>

                {/* 4. Traffic Analyzed */}
                <div className="nids-card p-4 space-y-2">
                  <div className="text-xs text-slate-400 font-medium">Traffic Analyzed</div>
                  <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
                    2.45 TB
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <svg className="w-24 h-6 text-cyan-400" fill="none" viewBox="0 0 100 25" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M0 16 Q 25 22, 45 14 T 80 8 T 100 12" />
                    </svg>
                    <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3 text-emerald-400 inline" /> +23.1%
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">vs last 7 days</div>
                </div>

                {/* 5. Active Connections */}
                <div className="nids-card p-4 space-y-2">
                  <div className="text-xs text-slate-400 font-medium">Active Connections</div>
                  <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
                    {(stats?.total_records_processed || 8547).toLocaleString()}
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <svg className="w-24 h-6 text-purple-400" fill="none" viewBox="0 0 100 25" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M0 18 L 20 14 L 35 20 L 55 10 L 75 16 L 90 8 L 100 11" />
                    </svg>
                    <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3 text-emerald-400 inline" /> +5.4%
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">vs last 7 days</div>
                </div>
              </div>

              {/* Row 2: Traffic Overview (2/3) + Top Attack Types (1/3) */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Traffic Overview Line Chart */}
                <div className="lg:col-span-2 nids-card p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">Traffic Overview</h3>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      {/* Legend */}
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-blue-500"></span> Normal Traffic
                        </span>
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-amber-500"></span> Suspicious Traffic
                        </span>
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-rose-500"></span> Malicious Traffic
                        </span>
                      </div>
                      {/* Dropdown */}
                      <div className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#0b0f19] border border-[#1f293d] text-slate-300 font-medium">
                        <span>7 Days</span>
                        <ChevronDown className="w-3 h-3 text-slate-400" />
                      </div>
                    </div>
                  </div>

                  {/* SVG Multi-Line Chart (Exact Match to Visual) */}
                  <div className="h-64 w-full relative pt-2">
                    <svg className="w-full h-full" viewBox="0 0 650 230" fill="none">
                      {/* Y-Axis Grid Lines & Labels */}
                      {[
                        { y: 30, label: "50K" },
                        { y: 65, label: "40K" },
                        { y: 100, label: "30K" },
                        { y: 135, label: "20K" },
                        { y: 170, label: "10K" },
                        { y: 205, label: "0" },
                      ].map((step, idx) => (
                        <g key={idx}>
                          <line x1="55" y1={step.y} x2="630" y2={step.y} stroke="#1e293b" strokeDasharray="3 3" />
                          <text x="45" y={step.y + 4} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="sans-serif">
                            {step.label}
                          </text>
                        </g>
                      ))}

                      {/* X-Axis Labels */}
                      {[
                        { x: 75, label: "May 14" },
                        { x: 165, label: "May 15" },
                        { x: 255, label: "May 16" },
                        { x: 345, label: "May 17" },
                        { x: 435, label: "May 18" },
                        { x: 525, label: "May 19" },
                        { x: 610, label: "May 20" },
                      ].map((tick, idx) => (
                        <text key={idx} x={tick.x} y="224" fill="#64748b" fontSize="10" textAnchor="middle" fontFamily="sans-serif">
                          {tick.label}
                        </text>
                      ))}

                      {/* Series 1: Normal Traffic (Blue) */}
                      <path
                        d="M 75 110 C 120 95, 130 90, 165 85 C 205 80, 220 110, 255 105 C 295 100, 310 70, 345 68 C 385 66, 400 62, 435 60 C 475 58, 490 82, 525 85 C 565 88, 580 92, 610 95"
                        stroke="#3b82f6"
                        strokeWidth="2.5"
                        fill="none"
                      />
                      {[
                        [75, 110], [165, 85], [255, 105], [345, 68], [435, 60], [525, 85], [610, 95]
                      ].map(([cx, cy], idx) => (
                        <circle key={`norm-pt-${idx}`} cx={cx} cy={cy} r="4" fill="#3b82f6" stroke="#0b0f19" strokeWidth="2" />
                      ))}

                      {/* Series 2: Suspicious Traffic (Amber/Orange) */}
                      <path
                        d="M 75 145 C 115 140, 130 135, 165 138 C 205 140, 220 152, 255 148 C 295 145, 310 138, 345 135 C 385 132, 400 148, 435 145 C 475 142, 490 148, 525 150 C 565 152, 580 150, 610 148"
                        stroke="#f59e0b"
                        strokeWidth="2.5"
                        fill="none"
                      />
                      {[
                        [75, 145], [165, 138], [255, 148], [345, 135], [435, 145], [525, 150], [610, 148]
                      ].map(([cx, cy], idx) => (
                        <circle key={`susp-pt-${idx}`} cx={cx} cy={cy} r="4" fill="#f59e0b" stroke="#0b0f19" strokeWidth="2" />
                      ))}

                      {/* Series 3: Malicious Traffic (Red) */}
                      <path
                        d="M 75 185 C 115 180, 130 182, 165 180 C 205 178, 220 188, 255 185 C 295 182, 310 178, 345 180 C 385 182, 400 170, 435 172 C 475 175, 490 182, 525 185 C 565 188, 580 182, 610 180"
                        stroke="#ef4444"
                        strokeWidth="2.5"
                        fill="none"
                      />
                      {[
                        [75, 185], [165, 180], [255, 185], [345, 180], [435, 172], [525, 185], [610, 180]
                      ].map(([cx, cy], idx) => (
                        <circle key={`mal-pt-${idx}`} cx={cx} cy={cy} r="4" fill="#ef4444" stroke="#0b0f19" strokeWidth="2" />
                      ))}
                    </svg>
                  </div>
                </div>

                {/* Top Attack Types Donut Chart */}
                <div className="nids-card p-5 space-y-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white">Top Attack Types</h3>
                  </div>

                  {/* Donut SVG with Exact Proportions & Legend */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-2">
                    {/* Donut Wheel */}
                    <div className="relative w-40 h-40 shrink-0 flex items-center justify-center">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                        {/* Segments: Total Circumference = 238.76 (2 * PI * 38) */}
                        {/* DDoS 32.6% = 77.84 */}
                        <circle cx="50" cy="50" r="38" fill="none" stroke="#3b82f6" strokeWidth="12" strokeDasharray="77.8 238.8" strokeDashoffset="0" />
                        {/* Port Scan 22.8% = 54.44 */}
                        <circle cx="50" cy="50" r="38" fill="none" stroke="#ef4444" strokeWidth="12" strokeDasharray="54.4 238.8" strokeDashoffset="-77.8" />
                        {/* SQL Injection 18.3% = 43.69 */}
                        <circle cx="50" cy="50" r="38" fill="none" stroke="#f97316" strokeWidth="12" strokeDasharray="43.7 238.8" strokeDashoffset="-132.2" />
                        {/* XSS 12.7% = 30.32 */}
                        <circle cx="50" cy="50" r="38" fill="none" stroke="#10b981" strokeWidth="12" strokeDasharray="30.3 238.8" strokeDashoffset="-175.9" />
                        {/* Brute Force 7.9% = 18.86 */}
                        <circle cx="50" cy="50" r="38" fill="none" stroke="#8b5cf6" strokeWidth="12" strokeDasharray="18.9 238.8" strokeDashoffset="-206.2" />
                        {/* Others 5.7% = 13.61 */}
                        <circle cx="50" cy="50" r="38" fill="none" stroke="#64748b" strokeWidth="12" strokeDasharray="13.6 238.8" strokeDashoffset="-225.1" />
                      </svg>
                      {/* Center Total Label */}
                      <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                        <span className="text-xl font-bold text-white tracking-tight">2,458</span>
                        <span className="text-[11px] text-slate-400">Total</span>
                      </div>
                    </div>

                    {/* Donut Legend (Right side, identical to screenshot) */}
                    <div className="space-y-2 text-xs flex-1">
                      {[
                        { label: "DDoS Attack", pct: "32.6%", count: "802", color: "bg-blue-500" },
                        { label: "Port Scan", pct: "22.8%", count: "561", color: "bg-red-500" },
                        { label: "SQL Injection", pct: "18.3%", count: "450", color: "bg-orange-500" },
                        { label: "XSS Attack", pct: "12.7%", count: "312", color: "bg-emerald-500" },
                        { label: "Brute Force", pct: "7.9%", count: "194", color: "bg-purple-500" },
                        { label: "Others", pct: "5.7%", count: "139", color: "bg-slate-500" },
                      ].map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between text-slate-300">
                          <span className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${item.color}`}></span>
                            <span>{item.label}</span>
                          </span>
                          <span className="font-mono text-slate-400">
                            {item.pct} <span className="text-slate-500">({item.count})</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Row 3: Recent Alerts Table (2/3) + System Status (1/3) */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Recent Alerts Table */}
                <div className="lg:col-span-2 nids-card p-5 space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-[#1f293d]">
                    <h3 className="text-sm font-bold text-white">Recent Alerts</h3>
                    <button
                      onClick={() => setActiveTab("traffic")}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      View All
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-slate-400 font-medium border-b border-[#1f293d]/60">
                        <tr>
                          <th className="py-2.5 px-3">Time</th>
                          <th className="py-2.5 px-3">Type</th>
                          <th className="py-2.5 px-3">Source IP</th>
                          <th className="py-2.5 px-3">Destination IP</th>
                          <th className="py-2.5 px-3">Severity</th>
                          <th className="py-2.5 px-3">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#1f293d]/40 font-mono">
                        {[
                          { time: "May 20, 2024 14:32:21", type: "DDoS Attack", src: "192.168.1.105", dst: "10.0.0.5", sev: "Critical", action: "Blocked" },
                          { time: "May 20, 2024 14:31:45", type: "SQL Injection", src: "192.168.1.110", dst: "10.0.0.8", sev: "High", action: "Blocked" },
                          { time: "May 20, 2024 14:30:11", type: "Port Scan", src: "192.168.1.108", dst: "10.0.0.15", sev: "Medium", action: "Logged" },
                          { time: "May 20, 2024 14:29:33", type: "XSS Attack", src: "192.168.1.115", dst: "10.0.0.12", sev: "Medium", action: "Blocked" },
                          { time: "May 20, 2024 14:28:09", type: "Brute Force", src: "192.168.1.120", dst: "10.0.0.20", sev: "Low", action: "Logged" },
                        ].map((row, idx) => (
                          <tr key={idx} className="hover:bg-[#161f33]/60 transition">
                            <td className="py-2.5 px-3 text-slate-400 font-sans">{row.time}</td>
                            <td className="py-2.5 px-3 text-white font-sans font-medium">{row.type}</td>
                            <td className="py-2.5 px-3 text-slate-300">{row.src}</td>
                            <td className="py-2.5 px-3 text-slate-300">{row.dst}</td>
                            <td className="py-2.5 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                row.sev === "Critical" ? "bg-rose-500/20 text-rose-400 border border-rose-500/30" :
                                row.sev === "High" ? "bg-orange-500/20 text-orange-400 border border-orange-500/30" :
                                row.sev === "Medium" ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" :
                                "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                              }`}>
                                {row.sev}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-sans font-semibold">
                              <span className={row.action === "Blocked" ? "text-rose-400" : "text-blue-400"}>
                                {row.action}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Right Column: 3D Threat Radar + System Status Progress Bars */}
                <div className="space-y-6">
                  {/* Interactive 3D Cyber Threat Radar Globe */}
                  <div className="nids-card p-4 space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-[#1f293d]">
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Activity className="w-4 h-4 text-cyan-400" />
                        3D Cyber Threat Radar
                      </h3>
                      <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-500/30 px-2 py-0.5 rounded">
                        INTERACTIVE 3D
                      </span>
                    </div>
                    <CyberGlobe3D />
                  </div>

                  {/* System Status Progress Bars (Exact Match to Visual) */}
                  <div className="nids-card p-5 space-y-4">
                    <div className="flex items-center justify-between pb-2 border-b border-[#1f293d]">
                      <h3 className="text-sm font-bold text-white">System Status</h3>
                      <button
                        onClick={() => setActiveTab("system")}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        View Details
                      </button>
                    </div>

                    <div className="space-y-4 pt-1 text-xs">
                      {/* CPU Usage */}
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-slate-300">
                          <span>CPU Usage</span>
                          <span className="font-mono text-slate-400">32%</span>
                        </div>
                        <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden">
                          <div className="bg-blue-500 h-full rounded-full" style={{ width: "32%" }}></div>
                        </div>
                      </div>

                      {/* Memory Usage */}
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-slate-300">
                          <span>Memory Usage</span>
                          <span className="font-mono text-slate-400">65%</span>
                        </div>
                        <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden">
                          <div className="bg-purple-500 h-full rounded-full" style={{ width: "65%" }}></div>
                        </div>
                      </div>

                      {/* Disk Usage */}
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-slate-300">
                          <span>Disk Usage</span>
                          <span className="font-mono text-slate-400">78%</span>
                        </div>
                        <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden">
                          <div className="bg-orange-500 h-full rounded-full" style={{ width: "78%" }}></div>
                        </div>
                      </div>

                      {/* Network I/O */}
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-slate-300">
                          <span>Network I/O</span>
                          <span className="font-mono text-slate-400">45%</span>
                        </div>
                        <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden">
                          <div className="bg-emerald-500 h-full rounded-full" style={{ width: "45%" }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================
              TAB: TRAFFIC MONITOR / INSPECTION
              ================================================================= */}
          {activeTab === "traffic" && (
            <div className="space-y-6">
              <div className="nids-card p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Activity className="w-4 h-4 text-blue-400" />
                      Live Traffic Flow Inspection Engine
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Stream and classify network traffic flows using the active AI model bundle.
                    </p>
                  </div>
                  <button
                    onClick={handleExportCSV}
                    disabled={!testRecords.length}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition disabled:opacity-40"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export CSV</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1">Target Partition</label>
                    <select
                      value={selectedDataset}
                      onChange={(e) => setSelectedDataset(e.target.value)}
                      className="w-full bg-[#0b0f19] border border-[#1f293d] rounded p-2 text-white font-mono text-xs"
                    >
                      {datasets.map((d) => (
                        <option key={d.path} value={d.path}>
                          {d.name} ({d.size_mb} MB)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Active AI Model</label>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-[#0b0f19] border border-[#1f293d] rounded p-2 text-white font-mono text-xs"
                    >
                      {models.map((m) => (
                        <option key={m.path} value={m.path}>
                          {m.name} [{m.task.toUpperCase()}]
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Flow Limit</label>
                    <select
                      value={sampleLimit}
                      onChange={(e) => setSampleLimit(Number(e.target.value))}
                      className="w-full bg-[#0b0f19] border border-[#1f293d] rounded p-2 text-white text-xs font-mono"
                    >
                      <option value={100}>100 Flows</option>
                      <option value={200}>200 Flows (Recommended)</option>
                      <option value={500}>500 Flows</option>
                      <option value={1000}>1,000 Flows</option>
                      <option value={5000}>5,000 Flows</option>
                      <option value={50000}>50,000 Flows (50k Bulk Audit)</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleRunInference}
                      disabled={testLoading}
                      className="w-full py-2 px-4 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold flex items-center justify-center gap-2 transition disabled:opacity-50"
                    >
                      {testLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 fill-white" />
                          <span>Inspect Traffic Flows</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Inspection Summary */}
              {testSummary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="nids-card p-4 text-center">
                    <div className="text-xs text-slate-400">Flows Tested</div>
                    <div className="text-xl font-bold text-white mt-1 tabular-nums">{testSummary.total_samples_tested}</div>
                  </div>
                  <div className="nids-card p-4 text-center">
                    <div className="text-xs text-rose-400">Attacks Detected</div>
                    <div className="text-xl font-bold text-rose-400 mt-1 tabular-nums">{testSummary.attacks_detected}</div>
                  </div>
                  <div className="nids-card p-4 text-center">
                    <div className="text-xs text-emerald-400">Benign Verified</div>
                    <div className="text-xl font-bold text-emerald-400 mt-1 tabular-nums">{testSummary.benign_detected}</div>
                  </div>
                  <div className="nids-card p-4 text-center">
                    <div className="text-xs text-blue-400">Latency per Flow</div>
                    <div className="text-xl font-bold text-blue-400 mt-1 tabular-nums">{testSummary.latency_ms_per_sample} ms</div>
                  </div>
                </div>
              )}

              {/* Flow Records Table */}
              <div className="nids-card p-5 space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-[#1f293d]">
                  <h3 className="text-sm font-bold text-white">Classified Network Flows</h3>
                  <span className="text-xs font-mono text-slate-400">Showing {testRecords.length} records</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="text-slate-400 font-medium border-b border-[#1f293d]">
                      <tr>
                        <th className="py-2.5 px-3">Flow #</th>
                        <th className="py-2.5 px-3">Ground Truth</th>
                        <th className="py-2.5 px-3">AI Prediction</th>
                        <th className="py-2.5 px-3">Confidence</th>
                        <th className="py-2.5 px-3">Threat Family</th>
                        <th className="py-2.5 px-3">Severity</th>
                        <th className="py-2.5 px-3">Key Extracted Flow Features</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1f293d]/50 font-mono">
                      {testRecords.map((r) => (
                        <tr key={r.row_index} className="hover:bg-[#161f33]/60 transition">
                          <td className="py-2 px-3 text-slate-500">#{r.row_index + 1}</td>
                          <td className="py-2 px-3 text-slate-300 font-sans">{r.ground_truth_raw || "Unlabeled"}</td>
                          <td className="py-2 px-3">
                            <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                              r.is_attack ? "bg-rose-500/20 text-rose-300 border border-rose-500/30" : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            }`}>
                              {r.predicted_label}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-slate-200">{(r.confidence * 100).toFixed(1)}%</td>
                          <td className="py-2 px-3 font-sans text-slate-300">{r.attack_category}</td>
                          <td className="py-2 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              r.severity === "CRITICAL" ? "bg-rose-500/20 text-rose-400" :
                              r.severity === "HIGH" ? "bg-orange-500/20 text-orange-400" :
                              r.severity === "MEDIUM" ? "bg-amber-500/20 text-amber-400" :
                              "bg-slate-500/20 text-slate-300"
                            }`}>
                              {r.severity}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-[11px] text-slate-400">
                            {Object.entries(r.key_features).slice(0, 3).map(([k, v]) => `${k}:${v}`).join(", ")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================
              TAB: ANALYSIS / MODEL LAB & LRRC-FS
              ================================================================= */}
          {activeTab === "analysis" && (
            <div className="space-y-6">
              <div className="nids-card p-5 space-y-4">
                <div className="pb-3 border-b border-[#1f293d]">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-indigo-400" />
                    Model Optimization & LRRC-FS Laboratory
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Train bounded tree ensembles with custom LRRC-FS feature selection.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1">Classifier</label>
                    <select
                      value={trainModel}
                      onChange={(e) => setTrainModel(e.target.value)}
                      className="w-full bg-[#0b0f19] border border-[#1f293d] rounded p-2 text-white text-xs"
                    >
                      <option value="random_forest">Random Forest (Subsampled Trees, Depth 16)</option>
                      <option value="gradient_boosting">HistGradientBoosting (Fast Binned, 80 Iter)</option>
                      <option value="decision_tree">Decision Tree (Ultra-Fast Edge)</option>
                      <option value="extra_trees">Extra Trees (Reduced Variance)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Task</label>
                    <select
                      value={trainTask}
                      onChange={(e) => setTrainTask(e.target.value)}
                      className="w-full bg-[#0b0f19] border border-[#1f293d] rounded p-2 text-white text-xs"
                    >
                      <option value="binary">Binary (BENIGN vs ATTACK)</option>
                      <option value="multiclass">Multiclass (8 Threat Families)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Flow Volume</label>
                    <select
                      value={trainSampleLimit}
                      onChange={(e) => setTrainSampleLimit(Number(e.target.value))}
                      className="w-full bg-[#0b0f19] border border-[#1f293d] rounded p-2 text-white font-mono text-xs"
                    >
                      <option value={15000}>15,000 Flows (Quick Evaluation)</option>
                      <option value={50000}>50,000 Flows (50k Standard Benchmark)</option>
                      <option value={100000}>100,000 Flows (100k Multi-Partition)</option>
                      <option value={600000}>600,000 Flows (6 Lakh Deep Flow Training)</option>
                      <option value={1000000}>1,000,000 Flows (10 Lakh Massive Scale)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Feature Selector</label>
                    <select
                      value={trainSelector}
                      onChange={(e) => setTrainSelector(e.target.value)}
                      className="w-full bg-[#0b0f19] border border-[#1f293d] rounded p-2 text-white text-xs"
                    >
                      <option value="lrrc">Proprietary LRRC-FS (15 Feats)</option>
                      <option value="kbest">SelectKBest (ANOVA F)</option>
                      <option value="variance">Variance Threshold</option>
                      <option value="all">All Features (39 Feats)</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleTrain}
                      disabled={trainLoading}
                      className="w-full py-2 px-4 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center justify-center gap-2 transition disabled:opacity-50"
                    >
                      {trainLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Fitting Trees...</span>
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4" />
                          <span>Train Model Bundle</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Latest Training Result */}
              {latestRun && (
                <div className="nids-card p-5 space-y-3">
                  <h4 className="text-xs font-bold text-white flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Run Success: {latestRun.run_id}
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                    <div className="bg-[#0b0f19] p-3 rounded border border-[#1f293d]">
                      <div className="text-[11px] text-slate-400">Accuracy</div>
                      <div className="text-xl font-bold text-white mt-0.5 tabular-nums">{(latestRun.accuracy * 100).toFixed(2)}%</div>
                    </div>
                    <div className="bg-[#0b0f19] p-3 rounded border border-[#1f293d]">
                      <div className="text-[11px] text-indigo-400">Macro F1</div>
                      <div className="text-xl font-bold text-indigo-400 mt-0.5 tabular-nums">{(latestRun.macro_f1 * 100).toFixed(2)}%</div>
                    </div>
                    <div className="bg-[#0b0f19] p-3 rounded border border-[#1f293d]">
                      <div className="text-[11px] text-slate-400">Latency</div>
                      <div className="text-xl font-bold text-white mt-0.5 tabular-nums">{latestRun.inference_latency_ms_per_sample} ms</div>
                    </div>
                    <div className="bg-[#0b0f19] p-3 rounded border border-[#1f293d]">
                      <div className="text-[11px] text-slate-400">Features</div>
                      <div className="text-xl font-bold text-white mt-0.5 tabular-nums">{latestRun.selected_features_count} / 39</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* =================================================================
              OTHER TABS: ALERTS, RULES, SYSTEM, SETTINGS
              ================================================================= */}
          {activeTab === "rules" && (
            <div className="space-y-4">
              <div className="nids-card p-5 space-y-3">
                <h3 className="text-sm font-bold text-white">Active Defense Policy Configuration</h3>
                <div className="space-y-2 text-xs">
                  {policies.map((p: any) => (
                    <div key={p.policy_id} className="p-3 bg-[#0b0f19] rounded border border-[#1f293d] flex items-center justify-between">
                      <div>
                        <div className="font-bold text-white flex items-center gap-2">
                          <span>{p.policy_id}: {p.name}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                            p.severity === "CRITICAL" ? "bg-rose-500/20 text-rose-300" :
                            p.severity === "HIGH" ? "bg-orange-500/20 text-orange-300" : "bg-amber-500/20 text-amber-300"
                          }`}>{p.severity}</span>
                        </div>
                        <div className="text-slate-400 text-[11px] mt-0.5">{p.description}</div>
                      </div>
                      <span className="text-emerald-400 font-mono font-bold">Enabled (Threshold {(p.min_confidence * 100).toFixed(0)}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "system" && (
            <div className="space-y-4">
              <div className="nids-card p-5 space-y-3">
                <h3 className="text-sm font-bold text-white">Official CICIoT2023 Datasets & Server Logs</h3>
                <div className="text-xs text-slate-400">
                  Total Discovered Partitions: <span className="text-white font-mono font-bold">{datasets.length} files (~9.4 GB)</span>
                </div>
                <div className="bg-[#0b0f19] p-4 rounded border border-[#1f293d] font-mono text-[11px] max-h-60 overflow-y-auto space-y-1 text-slate-300">
                  {logs.map((l, i) => (
                    <div key={i}>{l}</div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "settings" && (
            <div className="nids-card p-5 space-y-3 text-xs">
              <h3 className="text-sm font-bold text-white">System Runtime Settings</h3>
              <div className="grid grid-cols-2 gap-4 font-mono text-slate-300">
                <div className="p-3 bg-[#0b0f19] rounded border border-[#1f293d]">
                  <div className="text-slate-500 font-sans">Platform</div>
                  <div className="text-white mt-1">Windows x86_64 // Python 3.14.0</div>
                </div>
                <div className="p-3 bg-[#0b0f19] rounded border border-[#1f293d]">
                  <div className="text-slate-500 font-sans">Database Store</div>
                  <div className="text-white mt-1">iot_ids.sqlite ({status?.db_size_mb || 16} MB)</div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
