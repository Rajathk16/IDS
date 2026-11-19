# Frontend State & Progress

## Current Architecture
- Structure restored to complete feature-rich 4-view dashboard:
  - **Dashboard**: Live telemetry, Threat family distribution, Confusion Matrix visualizer (supporting both Binary TP/TN/FP/FN and Multiclass N×N matrix), Active model & partition counters.
  - **Flow Inspection**: Live evaluation of flows across any dataset partition, calibrated threshold application, prediction latency, confidence distribution, and CSV export.
  - **ML Lab & Models**: Interactive training across multiple architectures (Random Forest, Decision Tree, Extra Trees, HistGradientBoosting) with 4-term LRRC-FS feature selection, dataset resampling, and historical run tracking.
  - **Alerts & Defense**: Active defense policy cards (`POL-001` through `POL-007`), severity filtering, and real-time detection event streams.
- **Color Scheme & Gradients**:
  - Adopted the Sentinel AI dark cybersecurity aesthetic:
  - Deep obsidian base: `#080c0a`
  - Subtle dark surfaces: `#0e1412` with emerald/obsidian borders `#1a2620`
  - High-contrast text: `#ffffff` primary, `#9ca3af` secondary
  - Vivid accent: `#00e676` / `#10b981`
  - Attack/Malicious accent: `#f59e0b` / `#ef4444`
- **Integrity**:
  - Zero backend code or API changes.
  - All real backend data fields preserved and accurately displayed.
