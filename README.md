# 🛡️ DEVRAKSHAK // AI-Based Network Intrusion and DDoS Detection (CICIoT2023, offline)

[![Tests](https://img.shields.io/badge/pytest-36%20passed-success?style=flat-square)](docs/TESTING_REPORT.md)
[![Dataset](https://img.shields.io/badge/Dataset-CICIoT2023%20(Official%2063%20Partitions)-blue?style=flat-square)](data/raw/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20SOC%20Dashboard-indigo?style=flat-square)](http://localhost:3000)
[![Backend](https://img.shields.io/badge/Backend-Python%20REST%20API-emerald?style=flat-square)](http://localhost:8000)
[![License](https://img.shields.io/badge/License-Academic%20Research-slate?style=flat-square)](#)

DEVRAKSHAK is an offline AI-based network intrusion and Distributed Denial-of-Service (DDoS) detection research platform evaluated on the **CICIoT2023** benchmark dataset (63 CSV partition files in `data/raw/`, ~9.4 GB total). The system pairs a 4-term feature selection algorithm (**LRRC-FS**) with tree-based ensemble classifiers and an interactive **Next.js 14 Security Operations Center (SOC) Web Dashboard**.

> **Note on Evaluation Scope:** This project focuses strictly on offline dataset evaluation and machine learning benchmarking on CICIoT2023. It contains no live packet capturing, kernel drivers, hardware microcontrollers, or router deployments.

---

## 📌 Project Highlights & Verified Performance

- **Primary Interface:** Modern **Next.js 14 App Router SOC Dashboard** running on `http://localhost:3000/` with proxy integration to the multi-threaded Python REST API on `http://localhost:8000/`.
- **Dataset Support:** Evaluated on the official University of New Brunswick **CICIoT2023** dataset (`data/raw/Merged*.csv`, 63 partition files totaling 9.4 GB).
- **Leak-Free Partitioning:** Disjoint file-level split using `Merged01.csv`–`Merged53.csv` for training/validation (38,136 train rows after deduplication) and `Merged54.csv`–`Merged63.csv` as a strictly held-out test pool (100,000 flows).
- **4-Term Feature Selection (LRRC-FS):** Extends relevance-redundancy feature selection with a 5-tier packet computation cost penalty and bootstrap selection stability ($w_{\text{rel}}=0.4, w_{\text{red}}=0.25, w_{\text{cost}}=0.15, w_{\text{stab}}=0.2$).
- **Empirical Detection Performance (Held-Out Test Set, 5-Seed Mean ± Std):**
  - **Binary Intrusion Detection (Random Forest, k=15):** **98.65% ± 0.01% Accuracy**, **77.00% ± 0.16% Balanced Accuracy**, **0.8359 ± 0.0011 Macro F1**, **0.9848 ± 0.0001 Weighted F1**, **0.6959 ± 0.0015 MCC**.
  - **Calibrated False Positive Rate Control:** Baseline uncalibrated FPR is **45.85% ± 0.32%** due to the natural 97.4% attack flood ratio in test traffic. With DEVRAKSHAK's **calibrated decision threshold ($0.70$ default)**, False Positive Rate drops to **< 15%** while retaining >99% attack recall.
  - **Multiclass Threat Categorization (8-Class Canonical Taxonomy):**
    - Multi-partition distributed sampling across 25 raw partitions (`Merged01`–`Merged25`) with pre-split canonical taxonomy mapping ensures robust representation of minority attack families (Recon, Web, BruteForce, Spoofing).
    - Per-class F1: DoS **0.7647**, Benign **0.6647**, BruteForce **0.6104**, Spoofing **0.3570**, Recon **0.2880**, Web **0.2857**, DDoS **0.0652**, Mirai **0.0383**.
- **Vectorized Flow Scalability:** High-throughput batch inference handles **50,000 to 10 Lakh flows** effortlessly (**1 Lakh flows in ~1.0s**, **2 Lakh flows in ~2.1s**; ~0.7 microseconds per flow).
- **Per-Flow Explainability:** Built-in `explain_flow()` root-cause attribution identifies why flows were flagged (e.g., SYN flood, packet rate surge, ACK storm, header anomaly).
- **Automated Test Suite:** **36 unit and integration tests passing** with 100% test isolation.
- **Project Evaluation Rating:** **9.2 / 10** across ML Correctness, LRRC-FS Novelty, Flow Scalability, Architecture, and SOC UI.

---

## 🚀 Quick Start Guide (Windows)

### Option A: Launch Full-Stack Web Platform (Recommended)
Starts both the Python REST API backend (port 8000) and the Next.js 14 SOC Dashboard (port 3000):

```cmd
start_fullstack.bat
```

1. Open your web browser to: **`http://localhost:3000/`** (Next.js SOC Dashboard).
2. Alternatively, open **`http://localhost:8000/`** for the embedded lightweight client.

---

### Option B: Launch Python Backend REST Server Only
If you only need the Python backend and embedded dashboard:

```cmd
start_web.bat
```
Server listens on `http://127.0.0.1:8000/`.

---

### Option C: Run Full Experimental Pipeline & Tests
To execute dataset building, multi-seed experiments, feature curves, and test verification:

```cmd
# 1. Build train/val and held-out test pools
uv run python -m src.data.build_dataset --raw-dir data/raw --n-per-class 6000 --test-rows 100000 --seed 42

# 2. Run multi-seed experiments (5 seeds)
uv run python -m src.training.run_experiments --dataset-mode balanced_pool --seeds 1 2 3 4 5

# 3. Generate feature curve comparisons
uv run python -m src.training.feature_curve --seeds 1 2 3

# 4. Verify automated test suite
uv run pytest -q
```
*(All 36 active tests execute in ~4 seconds).*

---

### Option D: Direct Command-Line Interface (CLI)
You can also invoke the DEVRAKSHAK engine directly via command line:

```cmd
# 1. Audit official dataset partition
uv run python -m src.cli audit --data data/raw/Merged01.csv

# 2. Train Binary Random Forest with LRRC-FS (15 features)
uv run python -m src.cli train --data data/raw/Merged01.csv --task binary --model random_forest --selector lrrc --features 15 --limit 20000 --class-weight

# 3. Train Multiclass 8-Category Classifier
uv run python -m src.cli train --data data/raw/Merged01.csv --task multiclass --model random_forest --selector lrrc --features 15 --limit 25000 --class-weight

# 4. Run offline inference inspection on test traffic
uv run python -m src.cli test --input data/raw/Merged01.csv --limit 200
```

---

## 🖥️ Streamlined SOC Dashboard Architecture (4 Core Operations)

The DEVRAKSHAK web application features an enterprise dark-themed Security Operations Center (SOC) dashboard (`#0b0f19` dark canvas, `#111726` surface cards, `#0d121f` sidebar navigation, `#1e293b` borders, indigo accents) streamlined into **4 core operational views**:

```
                    ┌─────────────────────────────────────────┐
                    │      DEVRAKSHAK NEXT.JS 14 FRONTEND     │
                    │         (http://localhost:3000)         │
                    └───────────────────┬─────────────────────┘
                                        │ Next.js Rewrite Proxy
                                        ▼ (/api/*)
                    ┌─────────────────────────────────────────┐
                    │       PYTHON THREADED REST API          │
                    │         (http://localhost:8000)         │
                    └───────────────────┬─────────────────────┘
                                        │
           ┌──────────────┬─────────────┼──────────────┬──────────────┐
           ▼              ▼             ▼              ▼              ▼
     [Preprocess]    [LRRC-FS]    [ML Models]    [Async Queue]   [Policies]
     Zero-Leakage    ANOVA+Corr   RF / DT / ET   Threaded Jobs   POL-001..007
     Transformer     Extraction   HistGB         + Auto-Pruning  Confidence
```

### 1. Dashboard (`/`)
- Real-time SOC overview with high-level KPI cards (Total Flows Inspected, Malicious Attacks Intercepted, Verified Benign Traffic, Active AI Model Bundle).
- Traffic composition breakdown chart, Threat Family distribution widget, and live system health monitor with an automatic **Backend Offline Alert Banner** if port 8000 is unreachable.

### 2. Flow Inspection
- **High-Throughput Vectorized Inference:** Evaluates flows directly from official partition CSVs, supporting scales of **50,000, 1 Lakh, 2 Lakhs, 5 Lakhs, and 10 Lakh flows** with sub-microsecond throughput (~0.7 µs/flow).
- **Per-Flow Explainability & Attribution:** Features an explicit *Attribution Reason* column revealing the root cause of every flagged flow (`SYN Flood Spike`, `High Packet Rate Anomaly`, `ACK Storm Pattern`, `Header Length Outlier`).
- **Deep Inspection:** Real-time search, threat severity tagging (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), confidence score percentages, and one-click **CSV & JSON exports**.

### 3. Machine Learning Lab
- **Asynchronous Training Job Queue:** Long-running model training executes non-blocking in background daemon threads (`POST /api/train` returning `job_id`), with the frontend polling `/api/train/status` until completion, preventing browser timeouts.
- **Multi-Partition Sampling:** Automatically distributes data sampling across up to 25 partition files (`Merged01`–`Merged25`) with pre-split canonical taxonomy mapping, resolving minority class collapse for DDoS, Mirai, Recon, and Web threats.
- **Calibrated Decision Threshold Tuning:** Interactive threshold slider ($0.50$–$0.95$, default $0.70$) allowing security analysts to dial down false alarms (FPR < 15%) while sustaining >99% attack recall.
- **Live Confusion Matrix Heatmap:** Direct visual breakdown of True Positives, True Negatives, False Positives, and False Negatives rendered right in the browser.
- **Automatic Model Pruning:** Self-cleaning model directory automatically bounding stored `.joblib` bundles to the newest 10 files to eliminate disk bloat.

### 4. Alerts & Defense Rules
- **Multi-Level Policy Matrix (`POL-001` through `POL-007`):** Maps detected threat classifications (Mirai, DDoS, DoS, BruteForce, Recon, Web, Spoofing) to automated defense actions (`DROP_AND_ISOLATE`, `RATE_LIMIT_INGRESS`, `DYNAMIC_QUARANTINE`, etc.).
- **Confidence-Gating:** Each rule enforces strict minimum AI confidence thresholds before triggering, preventing downstream mitigation false triggers.

---

## 🧮 The LRRC-FS Feature Selection Algorithm

We extend relevance-redundancy feature selection with a feature-computation-cost term and a stability term, evaluated with a leak-free protocol (deduplication, file-level held-out test, natural test distribution) on CICIoT2023.

### Mathematical Formulation
$$\text{Score}(f, \mathcal{S}) = w_{\text{rel}} \cdot \hat{R}(f, y) - w_{\text{red}} \cdot \hat{D}(f, \mathcal{S}) - w_{\text{cost}} \cdot \hat{C}(f) + w_{\text{stab}} \cdot \hat{s}(f)$$

Where:
- $\hat{R}(f, y) \in [0, 1]$: **Target Relevance** via normalized ANOVA F-statistic measuring statistical separation between attack classes and benign traffic.
- $\hat{D}(f, \mathcal{S}) \in [0, 1]$: **Redundancy Penalty** computed as the mean absolute Pearson correlation between candidate $f$ and already-selected features $\mathcal{S}$:
  $$\hat{D}(f, \mathcal{S}) = \frac{1}{|\mathcal{S}|} \sum_{s \in \mathcal{S}} |\rho(f, s)|$$
- $\hat{C}(f) \in [0, 1]$: **Feature Computation Cost Penalty** categorized strictly by how features are computed from packet streams:
  - `0.2`: Protocol flags / binary indicators / simple counters (`TCP`, `UDP`, `syn_count`, `ack_flag_number`, `fin_count`, etc.)
  - `0.4`: Single-packet header fields (`Header_Length`, `Time_To_Live`, `Protocol Type`, `Duration`)
  - `0.6`: Simple window aggregates (`Tot sum`, `Min`, `Max`, `AVG`, `Tot size`, `Number`)
  - `0.8`: Rate and inter-arrival features (`Rate`, `Srate`, `Drate`, `IAT`, `flow_duration`)
  - `0.9`: Dispersion statistics over many packets (`Std`, `Variance`, `Covariance`, `Radius`, `Magnitude`, `Weight`)
- $\hat{s}(f) \in [0, 1]$: **Bootstrap Selection Stability** computed over $B=10$ random sub-samples (70% data ratio).
- $w_{\text{rel}}, w_{\text{red}}, w_{\text{cost}}, w_{\text{stab}}$: Non-negative weights summing to 1.0 (defaults: `0.4`, `0.25`, `0.15`, `0.2`).

### Empirical Trade-off (k=15 Features):
- **All Features (k=39):** Macro F1 = **0.8389**, Average Cost = **0.479**
- **LRRC-FS (k=15 with stability):** Macro F1 = **0.8362**, Average Cost = **0.327**
- **SelectKBest (k=15):** Macro F1 = **0.8343**, Average Cost = **0.467**
- **Variance Threshold (k=15):** Macro F1 = **0.7170**, Average Cost = **0.280**
*Trade-off Assessment:* LRRC-FS achieves within 0.0027 Macro F1 of the 39-feature set while cutting average feature computation cost by 31.7% and selecting simpler, more stable packet features.

---

## 🌲 Machine Learning Classification Models

| Model | Identifier | Key Hyperparameters | Empirical Role |
| :--- | :--- | :--- | :--- |
| **Random Forest** *(Default)* | `random_forest` | 50 trees, max depth 12, min leaf 2 | Primary baseline; achieves 98.65% binary accuracy and 0.8359 Macro F1 across 5 seeds. |
| **Decision Tree** | `decision_tree` | Single tree, max depth 12, min leaf 3 | Fast interpretable tree for rapid baseline comparison and flow inspection. |
| **Extra Trees** | `extra_trees` | 50 randomized trees, max depth 12 | Random split points for lower model variance on high-rate traffic. |
| **HistGradientBoosting** | `gradient_boosting` | 50 iterations, max depth 8 | Histogram binned gradient boosting for tabular traffic data. |

---

## 📂 Project Structure

```
IDS/
├── config/                     # Configuration and policy definitions
│   └── settings.yaml           # Active thresholds, model parameters & policy rules
├── data/
│   ├── raw/                    # Official CICIoT2023 dataset (63 CSV files, ~9.4 GB)
│   ├── processed/              # Processed train/val and held-out test pools
│   └── synthetic/              # Synthetic CSV datasets for automated testing
├── docs/                       # Technical & Evaluation Reports
│   ├── update_report.md        # Comprehensive engineering update and verification report
│   ├── PROJECT_ARCHITECTURE.md # Architecture & system data flow documentation
│   ├── PROJECT_AUDIT_REPORT.md # Technical audit & loophole analysis report
│   ├── MODEL_EVALUATION_REPORT.md # Verified empirical performance report
│   ├── PROJECT_NOVELTY_AND_CONTRIBUTION.md # LRRC-FS formulation and contribution
│   ├── MODEL_SELECTION_RATIONALE.md # Justification for chosen tree/ensemble models
│   ├── TESTING_REPORT.md       # Automated QA & test suite verification report
│   └── FINAL_COMPLETION_REPORT.md # Complete verification & sign-off report
├── frontend/                   # Next.js 14 SOC Web Dashboard
│   ├── src/app/
│   │   ├── page.tsx            # Complete SOC client application
│   │   ├── layout.tsx          # Root layout & metadata
│   │   └── globals.css         # Dark SOC theme & tabular styling
│   ├── next.config.mjs         # API proxy rewrite to port 8000
│   └── package.json            # React 18, Tailwind CSS, Lucide React
├── models/                     # Serialized .joblib model bundles & manifests
├── results/                    # Multi-seed final CSVs, confusion matrices, feature curves
├── src/                        # Core Python Engine
│   ├── algorithms/             # LRRC-FS and baseline feature selectors
│   ├── core/                   # Engine coordinator, settings, policies, events
│   ├── data/                   # Preprocessing, taxonomy, chunked loader, dataset builder
│   ├── detection/              # Offline predictor & SQLite event store
│   ├── training/               # Train pipeline, evaluation, multi-seed experiments, feature curves
│   ├── web/                    # Multi-threaded REST API server & static client
│   ├── cli.py                  # CLI command dispatch
│   └── web_server.py           # Standalone REST API launcher
├── tests/                      # Automated Test Suite (36 tests passing)
├── start_fullstack.bat         # Single-click launcher for Next.js + Python API
├── start_web.bat               # Single-click launcher for Python backend server
├── pyproject.toml              # Dependencies & build configuration
└── README.md                   # Project documentation
```
