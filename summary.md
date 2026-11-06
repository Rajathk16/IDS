# AI-Based Network Intrusion and DDoS Detection (CICIoT2023, offline)
## Project Summary

**Codebase:** `DEVRAKSHAK` (Directory: `d:\MINIPROJECT_AIML\IDS`)  
**Dataset:** CICIoT2023 (63 partition files in `data/raw/`, ~9.4 GB total)  
**Evaluation Mode:** Offline dataset analysis (no live network capture, edge hardware, or router deployment)  
**Automated Tests:** 36 passed, 0 failed, 0 skipped (`uv run pytest`)

---

## 1. Overview

DEVRAKSHAK is an offline network intrusion and DDoS detection research project evaluated on the official University of New Brunswick **CICIoT2023** dataset. The pipeline pairs a 4-term feature selection method (**LRRC-FS**) with ensemble classifiers (Random Forest, Decision Tree, Extra Trees, HistGradientBoosting) and a Security Operations Center (SOC) dashboard.

The dataset pipeline uses a strict file-level split:
- **Train/Val pool:** Files `Merged01.csv` through `Merged53.csv` (38,136 train rows, 9,534 validation rows after deduplication).
- **Test pool:** Files `Merged54.csv` through `Merged63.csv` (100,000 rows with natural attack-flood distribution; 2,634 benign samples, 70,069 DDoS flows).

---

## 2. Web Dashboard Architecture

The system provides two web interface options:

1. **Next.js 14 SOC Dashboard (`IDS/frontend/`):**
   - **Framework:** Next.js 14 (App Router), React 18, TypeScript 5.6, Tailwind CSS 3.4, Lucide icons.
   - **Theme:** Dark mode theme defined in [`globals.css`](file:///d:/MINIPROJECT_AIML/IDS/frontend/src/app/globals.css) with `#0b0f19` main background, `#111726` surface cards, `#0d121f` sidebar, and `#f1f5f9` text.
   - **Proxy Integration:** Configured in `next.config.mjs` to proxy `/api/*` requests to the Python REST server at `http://127.0.0.1:8000/api/*`.
   - **Operational Views:**
     - *Dashboard:* Live KPI indicators, threat family counters, and active model telemetry.
     - *Traffic Monitor:* Evaluates network flows from any dataset partition, displaying true labels, predictions, confidence percentages, threat severities, and CSV/JSON export buttons.
     - *Model Laboratory:* In-browser training across binary and 8-class tasks with customizable feature counts and resampling strategies.
     - *Rules & Policies:* Automated alert and response rules (`POL-001` through `POL-007`) with sensitivity threshold sliders. Note: policies evaluate downstream on model outputs and cannot recover missed attack classes.
     - *System:* SQLite storage footprint, thread health, and log streams.

2. **Embedded HTML5 Dashboard (`IDS/src/web/static/`):**
   - Pure HTML5, CSS3, and ES6 JavaScript served directly by the Python backend on `http://localhost:8000/`.

---

## 3. LRRC-FS Feature Selection (4 Terms)

The *Lightweight Relevance-Redundancy-Cost Feature Selector* selects $k$ features greedily using four terms:

$$\text{Score}(f, \mathcal{S}) = w_{\text{rel}} \cdot R(f) - w_{\text{red}} \cdot D(f, \mathcal{S}) - w_{\text{cost}} \cdot C(f) + w_{\text{stab}} \cdot s(f)$$

* **Target Relevance $R(f)$:** Normalized ANOVA F-statistic measuring statistical separation between attack classes and benign traffic.
* **Redundancy Penalty $D(f, \mathcal{S})$:** Mean absolute Pearson correlation with already-selected features $\mathcal{S}$.
* **Feature Computation Cost $C(f)$:** Categorized by how features are calculated from packets:
  - `0.2` (Flags & simple counters): `TCP`, `UDP`, `ICMP`, `HTTP`, `HTTPS`, `DNS`, `syn_count`, `ack_flag_number`, etc.
  - `0.4` (Single-packet header fields): `Header_Length`, `Protocol Type`, `Time_To_Live`, `Duration`.
  - `0.6` (Simple window aggregates): `Tot sum`, `Min`, `Max`, `AVG`, `Tot size`, `Number`.
  - `0.8` (Rate / inter-arrival metrics): `Rate`, `Srate`, `Drate`, `IAT`, `flow_duration`.
  - `0.9` (Multi-packet dispersion statistics): `Std`, `Variance`, `Covariance`, `Radius`, `Magnitude`, `Weight`.
  - Default: `0.5` for any unmapped feature.
* **Selection Stability $s(f)$:** Bootstrap selection frequency over 10 random sub-samples (70% data).
* **Weights:** $w_{\text{rel}}=0.4$, $w_{\text{red}}=0.25$, $w_{\text{cost}}=0.15$, $w_{\text{stab}}=0.2$ (sum = 1.0).

---

## 4. Measured Experimental Results

All numbers below are calculated from 5-seed runs on the held-out test pool (files `Merged54`–`Merged63`, 100,000 flows) and read from `results/final_results.csv`:

### Binary Classification (Random Forest + LRRC-FS, k=15):
- **Accuracy:** **98.65% ± 0.01%**
- **Balanced Accuracy:** **77.00% ± 0.16%**
- **Macro F1:** **0.8359 ± 0.0011**
- **Weighted F1:** **0.9848 ± 0.0001**
- **Matthews Correlation Coefficient (MCC):** **0.6959 ± 0.0015**
- **Average Prediction Latency:** **0.0007 ± 0.0001 ms/flow** (~0.7 microseconds per flow on development CPU)
- **False Positive Rate (FPR):** **45.85% ± 0.32%** (1,208 / 2,634 benign samples misclassified; Seed 1: 1,198 / 2,634 benign, 95% Clopper-Pearson CI: `[0.4357, 0.4741]`).  
  *Note:* The high false positive rate reflects severe class imbalance in the natural test set (97.4% attack traffic).

### Multiclass Classification (8-Class Canonical Taxonomy, 5 Seeds):
- **Plain Strategy:** Accuracy **58.24% ± 0.14%**, Macro F1 **0.3842 ± 0.0016**, Weighted F1 **0.6378 ± 0.0017**
- **Balanced Class Weights:** Accuracy **58.25% ± 0.21%**, Macro F1 **0.3848 ± 0.0024**, Weighted F1 **0.6377 ± 0.0022**
- **Random Under-Sampling (RUS):** Accuracy **58.35% ± 0.11%**, Macro F1 **0.3861 ± 0.0017**, Weighted F1 **0.6391 ± 0.0013**
- **SMOTE:** Accuracy **58.30% ± 0.13%**, Macro F1 **0.3854 ± 0.0030**, Weighted F1 **0.6386 ± 0.0014**
- **Per-Class F1 (Plain Strategy):**
  - DoS: **0.7647**
  - Benign: **0.6647**
  - BruteForce: **0.6104**
  - Spoofing: **0.3570**
  - Recon: **0.2880**
  - Web: **0.2857**
  - DDoS: **0.0652**
  - Mirai: **0.0383**

### Feature Selection Comparison (k=15 Features, Held-out Test Set):
- **LRRC-FS (with stability):** Macro F1 = **0.8362**, Average Feature Computation Cost = **0.327**
- **SelectKBest (ANOVA F):** Macro F1 = **0.8343**, Average Feature Computation Cost = **0.467**
- **Variance Threshold:** Macro F1 = **0.7170**, Average Feature Computation Cost = **0.280**
- **All Features (k=39):** Macro F1 = **0.8389**, Average Feature Computation Cost = **0.479**
- **Trade-off:** LRRC-FS achieves within 0.0027 Macro F1 of the full 39-feature set while reducing feature dimension by 61.5% and lowering the average feature computation cost by 31.7% (from 0.479 to 0.327).

---

## 5. Execution Instructions

```cmd
cd d:\MINIPROJECT_AIML\IDS

# Build dataset pools (disjoint train/val and held-out test)
uv run python -m src.data.build_dataset --raw-dir data/raw --n-per-class 6000 --test-rows 100000 --seed 42

# Run 5-seed evaluation
uv run python -m src.training.run_experiments --dataset-mode balanced_pool --seeds 1 2 3 4 5

# Run feature curve ablation
uv run python -m src.training.feature_curve --seeds 1 2 3

# Run automated tests
uv run pytest -q
```
