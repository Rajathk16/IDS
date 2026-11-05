# 🛡️ DEVRAKSHAK // AI-Based IoT Network Intrusion & DDoS Defense System

[![Tests](https://img.shields.io/badge/pytest-32%20passed%20%2F%203%20skipped-success?style=flat-square)](docs/TESTING_REPORT.md)
[![Dataset](https://img.shields.io/badge/Dataset-CICIoT2023%20(Official%2063%20Partitions)-blue?style=flat-square)](data/raw/MERGED_CSV/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20SOC%20Dashboard-indigo?style=flat-square)](http://localhost:3000)
[![Backend](https://img.shields.io/badge/Backend-Python%20REST%20API-emerald?style=flat-square)](http://localhost:8000)
[![License](https://img.shields.io/badge/License-Academic%20Research-slate?style=flat-square)](#)

DEVRAKSHAK is an enterprise-grade, offline-capable AI Intrusion and Distributed Denial-of-Service (DDoS) Detection System designed specifically for resource-constrained Internet of Things (IoT) network gateways. Built upon the comprehensive **CICIoT2023** benchmark dataset (63 official partitions, ~9.4 GB), the system couples a novel, transparent feature selection algorithm (**LRRC-FS**) with high-throughput ensemble classifiers and a professional **Next.js 14 Security Operations Center (SOC) Web Dashboard**.

---

## 📌 Project Highlights & Verified Performance

- **Primary Interface:** Modern **Next.js 14 App Router SOC Dashboard** running on `http://localhost:3000/` with proxy integration to the multi-threaded Python REST API on `http://localhost:8000/`.
- **Dataset Support:** Evaluated on the official University of New Brunswick **CICIoT2023** dataset (`data/raw/MERGED_CSV/Merged*.csv`, 63 partition files totaling 9.4 GB).
- **Novel Feature Selection (LRRC-FS):** The *Lightweight Relevance-Redundancy-Cost Feature Selector* reduces flow feature dimensions by **61.5%** (from 39 to 15 features) and accelerates training by **19.0%** while preserving **98.08% test accuracy**.
- **Empirical Detection Performance (Held-Out Test Set):**
  - **Binary Intrusion Detection:** **98.08% Accuracy**, **0.8497 Macro F1**, **0.9832 Weighted F1**, **0.00% False Positive Rate (FPR)**.
  - **Multiclass Threat Categorization:** Categorizes traffic into 8 canonical families (`Benign`, `DDoS`, `DoS`, `Mirai`, `Recon`, `Spoofing`, `Web`, `BruteForce`) with **0.77 F1 on DDoS floods**.
- **Ultra-Low Latency:** Decision Tree reaches **0.0001 ms/sample** (0.1 microseconds); Random Forest operates at **0.0024 ms/sample** (2.4 microseconds), achieving over **416,000 packets/second** on a single CPU core.
- **Automated Test Suite:** **32/32 active unit and integration tests passing** with 100% test isolation.

---

## 🚀 Quick Start Guide (Windows)

### Option A: Launch Full-Stack Web Platform (Recommended)
Starts both the Python REST API backend (port 8000) and the Next.js 14 SOC Dashboard (port 3000):

```cmd
start_fullstack.bat
```

1. Open your web browser to: **`http://localhost:3000/`** (Enterprise Next.js SOC Dashboard).
2. Alternatively, open **`http://localhost:8000/`** for the embedded lightweight client.

---

### Option B: Launch Python Backend REST Server Only
If you only need the Python backend and embedded dashboard:

```cmd
start_web.bat
```
Server listens on `http://127.0.0.1:8000/`.

---

### Option C: Run Automated Test Suite
To verify the complete test suite across data loading, preprocessing, LRRC-FS, model bundles, and REST endpoints:

```cmd
uv run pytest
```
*(All 32 active tests execute in ~18 seconds. Deprecated terminal TUI tests are safely skipped).*

---

### Option D: Direct Command-Line Interface (CLI)
You can also invoke the DEVRAKSHAK engine directly via command line:

```cmd
# 1. Audit official dataset partition
uv run python -m src.cli audit --data data/raw/MERGED_CSV/MERGED_CSV/Merged01.csv

# 2. Train Binary Random Forest with LRRC-FS (15 features)
uv run python -m src.cli train --data data/raw/MERGED_CSV/MERGED_CSV/Merged01.csv --task binary --model random_forest --selector lrrc --features 15 --limit 20000 --class-weight

# 3. Train Multiclass 8-Category Classifier
uv run python -m src.cli train --data data/raw/MERGED_CSV/MERGED_CSV/Merged01.csv --task multiclass --model random_forest --selector lrrc --features 15 --limit 25000 --class-weight

# 4. Run offline inference inspection on test traffic
uv run python -m src.cli test --input data/raw/MERGED_CSV/MERGED_CSV/Merged01.csv --limit 200
```

---

## 🖥️ Web Dashboard Architecture (9 Operational Sections)

The DEVRAKSHAK web application is engineered around an enterprise Security Operations Center (SOC) aesthetic: clean light neutral backgrounds, navy/charcoal typography, restrained alert badges, and tabular numerical layouts.

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
     [Preprocess]    [LRRC-FS]    [ML Models]    [Event Store]   [Policies]
     Zero-Leakage    ANOVA+Corr   RF / DT / ET   SQLite Record   POL-001..007
     Transformer     Extraction   HistGB         Telemetry       Mitigation
```

### 1. Overview Dashboard (`/`)
Displays total flows inspected, attack breakdown, benign traffic verification, active model status, live detection telemetry, and recent security incident logs.

### 2. Dataset Management
Discovers all 63 official merged partitions in `data/raw/MERGED_CSV/`, supports direct in-browser CSV uploads, and executes memory-conscious schema audits (checking NaNs, Infs, duplicate records, and class distributions).

### 3. Intrusion Detection / Traffic Analysis
Evaluates network flows directly from official dataset partitions. Displays an interactive table with true labels, AI classifications, confidence scores, severity levels (CRITICAL, HIGH, MEDIUM, LOW), extracted packet features (`Rate`, `Header_Length`, `Time_To_Live`, `syn_count`), multi-dimensional search filters, and one-click **CSV/JSON report exports**.

### 4. Model Laboratory
Configurable training interface supporting Random Forest, Decision Tree, Extra Trees, and HistGradientBoosting across Binary and Multiclass tasks. Includes cost-sensitive class weighting (`class_weight='balanced'`), Random Under-Sampling (RUS), SMOTE, and one-click active bundle deployment.

### 5. LRRC-FS Feature Selection Studio
Interactive algorithm explorer for the custom feature selector. Allows configuring relevance, redundancy, and extraction cost weights, viewing the step-by-step ranking log, and running live benchmark comparisons against All Features, Variance Threshold, and SelectKBest.

### 6. Security Alerts & Policies
Real-time rule engine mapping AI predictions to defensive policy triggers (e.g., POL-001 for Mirai Botnets, POL-002 for High-Volume DDoS floods). Includes threshold sliders, severity controls, and an immutable policy audit log.

### 7. Run History
Persistent SQLite history table tracking every historical training run with Macro F1, Accuracy, training duration, inference latency, and selected feature references.

### 8. System Logs
Live streaming log viewer with level filtering (INFO, WARNING, ERROR) and auto-refresh telemetry.

### 9. System Settings & Runtime Environment
Inspects Python runtime environment, database disk footprint, default detection thresholds, and memory management options.

---

## 🧮 The Core Novel Algorithm: LRRC-FS

Standard feature selection algorithms (e.g. SelectKBest, PCA, Variance Threshold) evaluate statistical variance in isolation. However, in low-power IoT gateways and edge microcontrollers, calculating multi-packet dispersion statistics (`Variance`, `Covariance`, `Radius`, `Standard Deviation`) consumes massive CPU cycles and energy.

### Mathematical Formulation
$$\text{Score}(f, \mathcal{S}) = w_{\text{rel}} \cdot \hat{R}(f, y) - w_{\text{red}} \cdot \hat{D}(f, \mathcal{S}) - w_{\text{cost}} \cdot \hat{C}(f)$$

Where:
- $\hat{R}(f, y) \in [0, 1]$: **Target Relevance** via normalized ANOVA F-statistic measuring statistical separation between attack classes and benign traffic.
- $\hat{D}(f, \mathcal{S}) \in [0, 1]$: **Redundancy Penalty** computed as the mean absolute Pearson correlation between candidate $f$ and already-selected features $\mathcal{S}$:
  $$\hat{D}(f, \mathcal{S}) = \frac{1}{|\mathcal{S}|} \sum_{s \in \mathcal{S}} |\rho(f, s)|$$
- $\hat{C}(f) \in [0, 1]$: **Computational Cost Penalty**. Features requiring floating-point calculations and multi-packet window aggregation (`Variance`, `Covariance` = 0.9) are penalized in favor of zero-overhead packet bitflags (`TCP`, `UDP`, `syn_count`, `ack_flag_number` = 0.2).
- $w_{\text{rel}}, w_{\text{red}}, w_{\text{cost}}$: User-configurable non-negative weights (default: `0.5`, `0.3`, `0.2`).

Greedy selection executes deterministically in $\mathcal{O}(N \cdot d^2 + k^2 d)$ time using vectorized correlation matrix calculations in under **0.035 seconds**.

---

## 🌲 Machine Learning Classification Models

| Model | Identifier | Key Hyperparameters | Optimal IoT Use Case |
| :--- | :--- | :--- | :--- |
| **Random Forest** *(Default)* | `random_forest` | 50 trees, max depth 12, min leaf 2, balanced weights | Primary operational model; best balance of high Macro F1 (0.8497) and zero false alarm rate. |
| **Decision Tree** | `decision_tree` | Single tree, max depth 12, min leaf 3, balanced weights | Ultra-low-latency edge verification (< 0.1 microseconds per packet); white-box rule compliance. |
| **Extra Trees** | `extra_trees` | 50 randomized trees, max depth 12, balanced weights | High-volume DDoS flood mitigation; lower variance under bursty packet rates. |
| **HistGradientBoosting** | `gradient_boosting` | 50 iterations, max depth 8, balanced weights | Integer-binned tabular gradient boosting for multi-gigabyte dataset partitions. |

---

## 📂 Project Structure

```
IDS/
├── config/                     # Configuration and policy definitions
│   └── policies.json           # Active security alert rules & audit history
├── data/
│   ├── raw/
│   │   └── MERGED_CSV/         # Official CICIoT2023 dataset (63 CSV files, ~9.4 GB)
│   ├── synthetic/              # Deterministic synthetic test partitions
│   └── processed/              # Preprocessing manifests & feature lists
├── docs/                       # Comprehensive Academic & Technical Reports
│   ├── PROJECT_ARCHITECTURE.md # Architecture & system data flow documentation
│   ├── PROJECT_AUDIT_REPORT.md # Technical audit & loophole analysis report
│   ├── MODEL_EVALUATION_REPORT.md # Verified empirical performance report
│   ├── PROJECT_NOVELTY_AND_CONTRIBUTION.md # Formal LRRC-FS mathematical thesis
│   ├── MODEL_SELECTION_RATIONALE.md # Justification for chosen tree/ensemble models
│   ├── TESTING_REPORT.md       # Automated QA & test suite verification report
│   └── FINAL_COMPLETION_REPORT.md # Complete verification & sign-off report
├── frontend/                   # Professional Next.js 14 SOC Web Dashboard
│   ├── src/app/
│   │   ├── page.tsx            # Complete 9-section enterprise SOC client
│   │   ├── layout.tsx          # Root layout & metadata
│   │   └── globals.css         # Clean SOC light theme & tabular styling
│   ├── next.config.mjs         # API proxy rewrite to port 8000
│   └── package.json            # React 18, Tailwind CSS, Lucide React
├── models/                     # Serialized .joblib model bundles & manifests
├── results/                    # Generated confusion matrices, metrics JSON, reports
├── src/                        # Core Python Engine
│   ├── algorithms/             # LRRC-FS and baseline feature selectors
│   ├── core/                   # Engine coordinator, settings, policies, events
│   ├── data/                   # Preprocessing, taxonomy, chunked loader, split
│   ├── detection/              # Offline predictor & SQLite event store
│   ├── training/               # Train pipeline, evaluation, benchmarks
│   ├── web/                    # Multi-threaded REST API server & static client
│   ├── cli.py                  # CLI command dispatch
│   └── web_server.py           # Standalone REST API launcher
├── tests/                      # Automated Test Suite (35 tests, 100% healthy)
├── start_fullstack.bat         # Single-click launcher for Next.js + Python API
├── start_web.bat               # Single-click launcher for Python backend server
├── pyproject.toml              # Dependencies & build configuration
└── README.md                   # Project documentation
```

---

## ⚖️ Academic Integrity & Notice on Class Imbalance

In authentic network flow datasets like CICIoT2023, attack distributions exhibit extreme natural imbalance: denial-of-service floods constitute over 89% of recorded traffic, while application-layer exploits (`Web`, `BruteForce`) constitute less than 0.1% (a 1,950:1 ratio). 

DEVRAKSHAK maintains strict academic rigor:
1. **Zero Fabrication:** All metrics reported are genuine empirical figures evaluated on held-out test splits.
2. **Transparent Minority Reporting:** The system explicitly reports that while overall accuracy is **98.08%** on binary traffic and **78.05%** on weighted multiclass traffic, minority attacks (`BruteForce`, `Web`) achieve lower standalone F1 without aggressive resampling.
3. **Data Leakage Immunity:** Resampling (SMOTE, Random Under-Sampling) and feature selection are **strictly confined to training partitions**.
