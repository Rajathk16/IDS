# 🛡️ DEVRAKSHAK // AI-Based Intrusion & DDoS Defense System (CICIoT2023)

An offline, reproducible, cyber-dark terminal user interface and AI pipeline designed for IoT network anomaly detection, distributed denial-of-service (DDoS) flood mitigation, Mirai botnet recognition, and network reconnaissance using the official **CICIoT2023** dataset schema.

---

## 📌 1. Project Overview & Objectives

Internet of Things (IoT) devices have constrained computing power, memory, and rudimentary firmware, making them prime targets for botnet enslavement and massive DDoS campaigns. This system provides:

1. **Dual Classification Tasks:**
   - **Binary Classification:** `BENIGN` vs. `ATTACK`.
   - **Multiclass Classification:** Categorizes traffic into 8 attack groups (`Benign`, `DDoS`, `DoS`, `Recon`, `Web`, `BruteForce`, `Spoofing`, `Mirai`).
2. **Data Quality & Audit Engine:** Chunked, memory-conscious CSV loading that detects missing values (NaNs), infinities, duplicates, and severe class imbalances on consumer laptops (8 GB RAM).
3. **Custom Feature-Selection Algorithm:** Features our proprietary **Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS)**, which jointly optimizes statistical target relevance, inter-feature redundancy penalty, and computational extraction cost.
4. **Resilience to Class Imbalance:** Compares unweighted learning, cost-sensitive class weighting (`class_weight='balanced'`), random under-sampling, and SMOTE on training partitions.
5. **Interactive Terminal User Interface (TUI):** A 6-screen terminal application built with **Textual** and **Rich** featuring conversational queries, training runs management, live log viewing, detection monitoring, security policies, and settings.
6. **Persistent Telemetry:** Stores historical runs and offline detection events across restarts in SQLite (`iot_ids.sqlite`).
7. **Strict Grounding:** Works 100% offline. Never claims live packet inspection or real-time network hardware blocking unless genuine physical adapters are configured.

---

## 🏗️ 2. Architecture & Directory Structure

```text
d:/mini project/
├── config/
│   ├── settings.json            # Pydantic-validated application settings
│   └── policies.json            # Security alert policies & audit history
├── data/
│   ├── raw/                     # Place official CICIoT2023 CSV files here
│   │   └── README.md            # Manual download instructions
│   ├── processed/               # Preprocessed feature manifests & aligned data
│   └── synthetic/               # Synthetic offline test datasets
├── models/                      # Versioned .joblib model bundles (preprocessor + selector + clf)
├── results/
│   ├── metrics/                 # Machine-readable JSON evaluation reports
│   ├── plots/                   # Saved confusion matrix figures (.png)
│   └── reports/                 # Markdown audit and experiment comparisons
├── src/
│   ├── main.py                  # Default application entrypoint (launches TUI or CLI)
│   ├── cli.py                   # Rich terminal CLI commands
│   ├── core/
│   │   ├── engine.py            # Unified domain orchestrator
│   │   ├── events.py            # Pydantic event and run data models
│   │   ├── policies.py          # Alert policy engine & audit log
│   │   ├── settings.py          # AppSettings configuration management
│   │   └── logging_config.py    # Rotating file logger & in-memory buffer
│   ├── data/
│   │   ├── loader.py            # Chunked CSV reader & schema inspector
│   │   ├── audit.py             # Data quality audit & report generator
│   │   ├── preprocess.py        # Imputation, scaling & PreprocessingManifest
│   │   ├── split.py             # Leakage-resistant stratified partitioner
│   │   ├── synthetic.py         # Synthetic CICIoT2023 generator for offline tests
│   │   └── taxonomy.py          # Official 46 features & 34-class label taxonomy
│   ├── algorithms/
│   │   ├── feature_selector.py  # Custom LRRC-FS greedy algorithm
│   │   └── baselines.py         # AllFeatures, Variance, and SelectKBest baselines
│   ├── training/
│   │   ├── train.py             # Model training engine & bundle serializer
│   │   ├── evaluate.py          # Accuracy, Macro F1, FPR, latency & plot generator
│   │   └── experiments.py       # Selector & class-imbalance empirical comparisons
│   ├── detection/
│   │   ├── predictor.py         # Offline batch/streaming inference engine
│   │   └── event_store.py       # SQLite database manager
│   └── tui/
│       ├── app.py               # Main Textual TUI Application
│       └── screens/             # CHAT, RUNS, LOGS, MONITOR, POLICIES, SETTINGS
├── tests/                       # 25 automated pytest tests
├── requirements.txt             # Pinned package versions
├── .gitignore                   # Ignores large datasets, models, and virtualenvs
└── README.md                    # Project documentation
```

---

## ⚙️ 3. Installation & Environment Setup

### Prerequisites
- Python 3.11, 3.12, 3.13, or 3.14.
- Windows, Linux, or macOS.

### Step 1: Clone / Navigate to Workspace
```bash
cd "d:/mini project"
```

### Step 2: Initialize Virtual Environment
Using Python's standard `venv` or `uv`:
```bash
# Using standard Python
python -m venv .venv

# Activate on Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Activate on Windows (CMD):
.venv\Scripts\activate.bat
# Activate on Linux/macOS:
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 📊 4. Dataset Acquisition (CICIoT2023)

The project is designed around the official **CICIoT2023** dataset released by the Canadian Institute for Cybersecurity (University of New Brunswick).

### Real Dataset Instructions:
1. Visit the official download portal:
   [https://www.unb.ca/cic/datasets/iotdataset-2023.html](https://www.unb.ca/cic/datasets/iotdataset-2023.html)
2. Download one or more CSV partition files (e.g. `part-00000-*.csv`).
3. Place the `.csv` file(s) into:
   ```text
   data/raw/
   ```

### Offline Synthetic Dataset Generator (No 20 GB Download Required):
If you do not have the multi-gigabyte dataset downloaded yet, use the included synthetic generator. It generates exact 46-feature CSV files matching the authentic schema:
```bash
python src/cli.py synthetic --samples 3000 --output synthetic_ciciot2023.csv
```
*Note: All synthetic files are tagged with `.meta.json` sidecars and explicitly marked as `SYNTHETIC` across all reports and UI screens.*

---

## 🧮 5. Custom Algorithm: LRRC-FS

The **Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS)** is an original, greedy feature-selection algorithm developed for IoT network intrusion detection.

### Mathematical Formulation
$$\text{Score}(f) = w_{\text{rel}} \cdot \hat{R}(f) - w_{\text{red}} \cdot \hat{D}(f, S) - w_{\text{cost}} \cdot \hat{C}(f)$$

Where:
- $\hat{R}(f) \in [0, 1]$: **Normalized Target Relevance** via ANOVA F-statistic ($F(f, y)$) or Mutual Information, normalized by min-max scaling across candidate features.
- $\hat{D}(f, S) \in [0, 1]$: **Redundancy Penalty** computed as the mean absolute Pearson correlation between candidate $f$ and already-selected features $S$:
  $$\hat{D}(f, S) = \begin{cases} 0 & \text{if } |S| = 0 \\ \frac{1}{|S|} \sum_{s \in S} |\rho(f, s)| & \text{if } |S| > 0 \end{cases}$$
- $\hat{C}(f) \in [0, 1]$: **Computational Cost Penalty**. In IoT micro-controllers and edge routers, multi-packet dispersion statistics (`Variance`, `Covariance`, `Radius`, `IAT`) require floating-point divisions and square roots, whereas header flags (`syn_flag_number`, `TCP`, `UDP`) require single-cycle bitwise checks. We penalize complex metrics to prioritize fast, low-overhead features.
- $w_{\text{rel}}, w_{\text{red}}, w_{\text{cost}}$: User-configurable non-negative weights (default: `0.5`, `0.3`, `0.2`).

### Greedy Selection & Complexity
1. First feature $f_1^* = \arg\max_{f} (\hat{R}(f) - w_{\text{cost}}\hat{C}(f))$ with deterministic tie-breaking by alphabetical feature name.
2. Iteratively append the candidate maximizing $\text{Score}(f)$ until $k$ features are selected.
3. Total Time Complexity: $\mathcal{O}(n \cdot m^2 + k^2 m)$, which runs in under **0.1 seconds** on 3,000 samples.

---

## 🖥️ 6. Interactive Terminal User Interface (TUI)

Launch the interactive Textual application with:
```bash
python src/main.py
# or
python src/cli.py tui
```

### The Six Operational Screens:
1. **💬 CHAT (Key: `1`):** Ask questions about the dataset, metrics, models, policies, or type `help`, `status`, `audit`, `lrrc`, `models`, `metrics`. Provides educational explanations with zero hallucination.
2. **🚀 RUNS (Key: `2`):** Interactive DataTable of historical training runs. Click **"Train Model"** to run training asynchronously in a background worker without freezing the UI. Select any row to inspect per-class metrics and confusion matrix paths.
3. **📜 LOGS (Key: `3`):** Live structured logging console streaming from an in-memory circular buffer. Filter by `DEBUG`, `INFO`, `WARNING`, `ERROR`.
4. **📡 MONITOR (Key: `4`):** Displays offline detection metrics, Benign vs. Attack count cards, attack-category distribution table, and recent detection events with policy severity tags.
5. **🛡️ POLICIES (Key: `5`):** View and adjust security alert thresholds (e.g. Critical Mirai, High DDoS). Toggle policies enabled/disabled and inspect the audit trail.
6. **⚙️ SETTINGS (Key: `6`):** Configure data paths, sample limits, default models, and LRRC-FS weights. Validated using Pydantic v2 and persisted to `config/settings.json`.

### Global Keybindings:
- `1` - `6`: Switch between screens.
- `Ctrl + Q`: Quit application safely.

---

## 💻 7. Command Line Interface (CLI) Guide

All domain operations can be run directly from the command line:

```bash
# 1. Discover available datasets
python src/cli.py discover

# 2. Generate synthetic test dataset
python src/cli.py synthetic --samples 3000 --output synthetic_ciciot2023.csv

# 3. Perform a dataset quality audit
python src/cli.py audit --max-rows 10000

# 4. Train a Binary Model with LRRC-FS
python src/cli.py train --task binary --model random_forest --selector lrrc --features 15 --samples 2500

# 5. Train a Multiclass Model with Class Weighting
python src/cli.py train --task multiclass --model extra_trees --selector lrrc --features 15 --class-weight

# 6. Empirically Compare Feature Selectors (All vs Variance vs KBest vs LRRC-FS)
python src/cli.py compare-selectors

# 7. Run Offline Predictions on a CSV file
python src/cli.py predict --input data/synthetic/synthetic_ciciot2023.csv --samples 100

# 8. List Historical Training Runs
python src/cli.py runs --limit 10

# 9. View Detection Event Log
python src/cli.py events --limit 20 --severity HIGH

# 10. Inspect Alert Policies
python src/cli.py policy show
```

---

## 🧪 8. Automated Testing & Reliability

The test suite contains **25 unit tests** across all subsystems:

```bash
pytest -v
```

### Test Coverage Highlights:
- **`tests/test_core.py`:** Pydantic settings validation, persistence, alert policy evaluation, and circular log buffers.
- **`tests/test_data.py`:** Synthetic data generation, label taxonomy mapping, schema inspection, chunked loading, and dataset audit report creation.
- **`tests/test_pipeline.py`:** NaN/inf imputation, standardization, preprocessing manifest serialization, leakage-resistant stratification, LRRC-FS greedy determinism, and baselines.
- **`tests/test_training.py`:** Decision Tree, Random Forest, Extra Trees, Gradient Boosting, SMOTE/under-sampling, Macro F1, and False Positive Rate.
- **`tests/test_detection.py`:** Offline batch inference, policy triggers, and SQLite persistence.
- **`tests/test_cli.py`:** CLI subcommands and parameter parsing.
- **`tests/test_tui.py`:** Textual async runner testing mount, layout, and tab switching.

---

## ⚖️ 9. Academic Limitations & Ethical Boundaries

1. **Offline Traffic Analysis:** This prototype evaluates tabular flow records stored in CSV format. It does not perform live network sniffing (`pcap`) or socket packet interception.
2. **No Hardware Blocking:** Detection events flag security alerts according to policy thresholds. The system does not automatically modify iptables, route tables, or firewall rules.
3. **Random Splitting Disclaimer:** Standard train/test partitioning measures in-distribution classification accuracy. High performance on a given test partition does not guarantee generalization to unseen IoT device hardware or novel zero-day attack vectors.
4. **Synthetic Data Transparency:** Synthetic datasets are exclusively for testing when real dataset partitions cannot be downloaded. Synthetic metrics are clearly labeled in all tables and reports.
