"use client";

import React, { useEffect, useRef } from "react";

interface Node3D {
  x: number;
  y: number;
  z: number;
  label?: string;
  isThreat?: boolean;
}

export default function CyberGlobe3D() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let angleX = 0.2;
    let angleY = 0;

    // Generate 3D sphere points (IoT nodes)
    const nodes: Node3D[] = [];
    const count = 48;
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(-1 + (2 * i) / count);
      const theta = Math.sqrt(count * Math.PI) * phi;
      const radius = 95;
      nodes.push({
        x: radius * Math.cos(theta) * Math.sin(phi),
        y: radius * Math.sin(theta) * Math.sin(phi),
        z: radius * Math.cos(phi),
        isThreat: i % 7 === 0,
      });
    }

    // Packet beams
    const beams: { from: number; to: number; progress: number; speed: number; isAttack: boolean }[] = [];
    for (let i = 0; i < 8; i++) {
      beams.push({
        from: Math.floor(Math.random() * count),
        to: Math.floor(Math.random() * count),
        progress: Math.random(),
        speed: 0.008 + Math.random() * 0.012,
        isAttack: Math.random() > 0.6,
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const fov = 260;

      angleY += 0.006;

      // Project 3D nodes
      const projected = nodes.map((node) => {
        // Rotate around Y
        const cosY = Math.cos(angleY);
        const sinY = Math.sin(angleY);
        const x1 = node.x * cosY - node.z * sinY;
        const z1 = node.x * sinY + node.z * cosY;

        // Rotate around X
        const cosX = Math.cos(angleX);
        const sinX = Math.sin(angleX);
        const y2 = node.y * cosX - z1 * sinX;
        const z2 = node.y * sinX + z1 * cosX;

        const scale = fov / (fov + z2);
        return {
          px: cx + x1 * scale,
          py: cy + y2 * scale,
          pz: z2,
          scale,
          isThreat: node.isThreat,
        };
      });

      // Draw latitude / longitude wireframe rings
      ctx.strokeStyle = "rgba(99, 102, 241, 0.12)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, 95, 0, Math.PI * 2);
      ctx.stroke();

      ctx.beginPath();
      ctx.ellipse(cx, cy, 95, 38, 0, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(6, 182, 212, 0.15)";
      ctx.stroke();

      // Connect nearby nodes with cyber mesh lines
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const dx = projected[i].px - projected[j].px;
          const dy = projected[i].py - projected[j].py;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 42 && projected[i].pz > -60 && projected[j].pz > -60) {
            const alpha = (1 - dist / 42) * 0.25;
            ctx.strokeStyle = projected[i].isThreat || projected[j].isThreat
              ? `rgba(244, 63, 94, ${alpha})`
              : `rgba(99, 102, 241, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(projected[i].px, projected[i].py);
            ctx.lineTo(projected[j].px, projected[j].py);
            ctx.stroke();
          }
        }
      }

      // Draw Animated Attack & Data Beams
      beams.forEach((beam) => {
        beam.progress += beam.speed;
        if (beam.progress > 1) {
          beam.progress = 0;
          beam.from = Math.floor(Math.random() * count);
          beam.to = Math.floor(Math.random() * count);
          beam.isAttack = Math.random() > 0.6;
        }

        const p1 = projected[beam.from];
        const p2 = projected[beam.to];
        if (p1.pz > -40 && p2.pz > -40) {
          const bx = p1.px + (p2.px - p1.px) * beam.progress;
          const by = p1.py + (p2.py - p1.py) * beam.progress;

          ctx.fillStyle = beam.isAttack ? "#ef4444" : "#00f3ff";
          ctx.shadowColor = beam.isAttack ? "#ef4444" : "#00f3ff";
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.arc(bx, by, beam.isAttack ? 3 : 2.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      // Draw Nodes
      projected.forEach((p) => {
        const alpha = Math.max(0.15, (p.pz + 100) / 200);
        const radius = Math.max(1.5, p.scale * 3);

        ctx.fillStyle = p.isThreat
          ? `rgba(239, 68, 68, ${alpha})`
          : `rgba(6, 182, 212, ${alpha})`;
        ctx.beginPath();
        ctx.arc(p.px, p.py, radius, 0, Math.PI * 2);
        ctx.fill();

        // Pulsing ring around threat nodes
        if (p.isThreat && p.pz > 0) {
          ctx.strokeStyle = `rgba(239, 68, 68, ${alpha * 0.7})`;
          ctx.beginPath();
          ctx.arc(p.px, p.py, radius + 3, 0, Math.PI * 2);
          ctx.stroke();
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="relative w-full h-56 flex items-center justify-center overflow-hidden rounded-xl bg-gradient-to-b from-[#0a0f1d] to-[#0f172a] border border-indigo-500/20">
      {/* 3D Canvas */}
      <canvas ref={canvasRef} width={340} height={220} className="relative z-10 cursor-grab active:cursor-grabbing" />

      {/* Cyber Overlay Tech Grid */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:16px_16px] opacity-15"></div>

      {/* Sci-Fi HUD Markers */}
      <div className="absolute top-2.5 left-3 text-[10px] font-mono text-cyan-400 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
        <span>GLOBAL 3D THREAT RADAR</span>
      </div>

      <div className="absolute bottom-2.5 left-3 text-[9px] font-mono text-slate-400">
        LAT: 37.77 • LON: -122.41 • FREQ: 2.4GHz
      </div>

      <div className="absolute top-2.5 right-3 text-[9px] font-mono text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded bg-indigo-950/40">
        48 ACTIVE IOT NODES
      </div>

      <div className="absolute bottom-2.5 right-3 text-[9px] font-mono text-emerald-400">
        MESH: CONNECTED [99.8%]
      </div>
    </div>
  );
}
