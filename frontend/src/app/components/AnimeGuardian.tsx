"use client";

import React, { useState } from "react";
import { Shield, Sparkles, Zap, Flame, Terminal, Award } from "lucide-react";

interface AnimeGuardianProps {
  activeModel?: string;
  accuracy?: number;
  onSelectFlowPreset?: (count: number, model: string, label: string) => void;
}

export default function AnimeGuardian({
  activeModel = "Random Forest (LRRC-FS)",
  accuracy = 83.7,
  onSelectFlowPreset,
}: AnimeGuardianProps) {
  const [speech, setSpeech] = useState<string>(
    "Guardian Core online! For multiclass attack detection, I recommend 600,000 flows (6 Lakh) to catch rare Web & BruteForce attacks."
  );
  const [selectedPreset, setSelectedPreset] = useState<number>(600000);

  const presets = [
    {
      flows: 100000,
      label: "1 Lakh Flows (100K)",
      tag: "⚡ 1 Lakh Fast",
      model: "gradient_boosting",
      desc: "Fast inspection in ~3s. Perfect for partition checks.",
      tip: "1 Lakh flows configured! Rapid evaluation across 100,000 real flows.",
      color: "border-cyan-500/40 text-cyan-300 bg-cyan-950/30",
    },
    {
      flows: 200000,
      label: "2 Lakh Flows (200K)",
      tag: "🛡️ 2 Lakh Deep",
      model: "gradient_boosting",
      desc: "Evaluates 200,000 network flows in ~6s with high coverage.",
      tip: "2 Lakh flows active! Deep multi-threat attack inspection engaged.",
      color: "border-emerald-500/50 text-emerald-300 bg-emerald-950/30",
    },
    {
      flows: 600000,
      label: "6 Lakh Flows (600K)",
      tag: "⭐ Recommended",
      model: "gradient_boosting",
      desc: "Golden ratio for multiclass accuracy + rare attack detection.",
      tip: "600,000 flows (6 Lakh) active! Best balance between high accuracy and rare attack defense.",
      color: "border-indigo-500/60 text-indigo-300 bg-indigo-950/40 ring-1 ring-indigo-500/40",
    },
    {
      flows: 1000000,
      label: "10 Lakh Flows (1M)",
      tag: "🌐 10 Lakh Scale",
      model: "gradient_boosting",
      desc: "Massive scale 1,000,000 flow stress test (~156MB RAM).",
      tip: "1,000,000 flows (10 Lakh) engaged! HistGradientBoosting active for maximum enterprise throughput.",
      color: "border-fuchsia-500/40 text-fuchsia-300 bg-fuchsia-950/30",
    },
  ];

  const handlePresetClick = (p: typeof presets[0]) => {
    setSelectedPreset(p.flows);
    setSpeech(p.tip);
    if (onSelectFlowPreset) {
      onSelectFlowPreset(p.flows, p.model, p.label);
    }
  };

  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-[#0d1424] via-[#11192e] to-[#0c1322] border border-indigo-500/30 p-5 shadow-lg shadow-indigo-950/40 anime-card-3d">
      {/* Sci-Fi Top Accent Line */}
      <div className="cyber-scanline"></div>

      <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
        {/* Left: Anime Guardian Avatar & Cyber Persona */}
        <div className="flex items-center gap-4 shrink-0">
          {/* Cyber Avatar SVG with Anime Sci-Fi Visor */}
          <div className="relative w-20 h-20 shrink-0">
            {/* Outer Holographic Glow Rings */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-cyan-500/20 via-indigo-600/30 to-fuchsia-500/20 animate-pulse"></div>
            
            <div className="relative w-full h-full rounded-2xl bg-[#090d16] border border-cyan-400/50 flex items-center justify-center overflow-hidden cyber-glow-cyan">
              <svg viewBox="0 0 100 100" className="w-16 h-16">
                {/* Cyber Helmet / Hair Silhouette */}
                <path d="M 20 50 Q 20 20, 50 15 Q 80 20, 80 50 Q 80 80, 50 85 Q 20 80, 20 50 Z" fill="#1e1b4b" stroke="#6366f1" strokeWidth="2" />
                <path d="M 28 40 L 40 18 L 50 30 L 60 18 L 72 40 Z" fill="#312e81" />
                {/* Anime Face Plate */}
                <path d="M 32 46 Q 50 62, 68 46 L 64 68 Q 50 80, 36 68 Z" fill="#0f172a" stroke="#00f3ff" strokeWidth="1.5" />
                {/* Glowing Anime Cyber Visor (Eyes) */}
                <rect x="36" y="47" width="28" height="6" rx="2" fill="#00f3ff" className="animate-pulse" filter="drop-shadow(0 0 4px #00f3ff)" />
                <line x1="34" y1="50" x2="66" y2="50" stroke="#ffffff" strokeWidth="1" opacity="0.8" />
                {/* Cyber Marking */}
                <circle cx="50" cy="72" r="2.5" fill="#ec4899" />
                <path d="M 45 78 L 55 78" stroke="#ec4899" strokeWidth="1.5" />
              </svg>

              {/* Status Dot */}
              <span className="absolute bottom-1 right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#090d16]"></span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-300 to-fuchsia-400">
                DEVRAKSHAK // A.T. FIELD MK-III
              </span>
              <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                AI SENTINEL
              </span>
            </div>
            <div className="text-[11px] text-slate-300 font-mono mt-0.5 flex items-center gap-2">
              <span className="text-emerald-400">● SYNC RATE: 99.8%</span>
              <span className="text-slate-500">|</span>
              <span className="text-indigo-300">LRRC-FS DEFENSE ACTIVE</span>
            </div>

            {/* Speech Dialogue Bubble */}
            <div className="mt-2 text-xs bg-[#090d16]/90 border border-indigo-500/30 rounded-lg p-2.5 text-slate-200 max-w-md font-sans shadow-inner">
              <span className="text-cyan-400 font-bold mr-1">Sentinel:</span>
              &quot;{speech}&quot;
            </div>
          </div>
        </div>

        {/* Right: Flow Recommendation Presets */}
        <div className="w-full lg:w-auto flex flex-col gap-2">
          <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-indigo-300 font-bold">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              RECOMMENDED FLOW PRESETS:
            </span>
            <span className="text-[10px] text-slate-500">Click to Auto-Configure</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {presets.map((p) => {
              const isSelected = selectedPreset === p.flows;
              return (
                <button
                  key={p.flows}
                  onClick={() => handlePresetClick(p)}
                  className={`text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? `${p.color} shadow-md`
                      : "bg-[#0b101d] border-[#1e293b] text-slate-300 hover:border-slate-600 hover:bg-[#12192c]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-white">{p.label}</span>
                    <span className="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded bg-black/40 text-slate-300">
                      {p.tag}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1 leading-snug">{p.desc}</p>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

