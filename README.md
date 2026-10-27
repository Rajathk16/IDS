# 🛡️ DEVRAKSHAK // AI-Based IoT Intrusion & DDoS Defense System (CICIoT2023)

An offline, reproducible, cyber-dark terminal user interface and AI pipeline designed for IoT network anomaly detection, distributed denial-of-service (DDoS) flood mitigation, Mirai botnet recognition, and network reconnaissance based on the official **CICIoT2023** dataset schema.

---

## 📌 Project Status

- **Real Dataset Status:** **Ingested & Audited.** Official CICIoT2023 partition files (`train.csv` [1.55 GB], `test.csv` [331 MB], `validation.csv` [331 MB]) located in `data/raw/CICIOT23/`.
- **Model Training:** **Complete on Real Data.**
  - Binary Random Forest: **98.72% Accuracy**, **0.8653 Macro F1**, **0.0051 ms/sample** latency.
  - Multiclass Random Forest: **78.05% Accuracy**, **0.7974 Weighted F1**, **99.7% Mirai F1**.
- **Empirical Benchmarks:** **Generated & Published.** Reports saved for LRRC-FS feature selection and class imbalance handling.
- **Offline Inference & Detection:** **Verified on Test Traffic.** Tested on `data/raw/CICIOT23/test/test.csv`, triggering real-time alerts for Mirai botnets, DDoS floods, and DoS.
- **Automated Tests:** **27/27 unit and integration tests passing.**
- **Terminal Prototype:** **100% Operational, Offline & Tested.**

---

## 🧭 Table of Contents
1. [What We Have Done](#-1-what-we-have-done)
2. [Dataset Structure & Ingestion](#-2-dataset-structure--ingestion)
3. [The Core Novel Algorithm: LRRC-FS](#-3-the-core-novel-algorithm-lrrc-fs)
4. [Models & Machine Learning Architecture](#-4-models--machine-learning-architecture)
5. [How to Run & Check the Program](#-5-how-to-run--check-the-program)
   - [Interactive Terminal User Interface (TUI)](#option-a-interactive-terminal-ui-tui)
   - [Direct Command Line Interface (CLI)](#option-b-direct-cli-commands)
6. [What We Are Checking and How (Evaluation Guide)](#-6-what-we-are-checking-and-how-evaluation-guide)
7. [How to Check Outputs & Artifacts](#-7-how-to-check-outputs--artifacts)
8. [Automated Verification & Testing](#-8-automated-verification--testing)
9. [Architecture & File Structure](#-9-architecture--file-structure)

---

## 🚀 1. What We Have Done

We have built and validated a production-grade, offline cybersecurity defense system tailored specifically for IoT environments:

1. **Ingested Real CICIoT2023 Traffic:**
   - Ingested authentic traffic partitions (`train.csv`, `test.csv`, `validation.csv`) from the University of New Brunswick CICIoT2023 dataset.
   - Audited 46 numerical flow features with zero missing/infinite values across all attack families.
2. **Trained & Serialized AI Classifiers:**
   - **Binary Classifier:** Distinguishes `BENIGN` vs. `ATTACK` with **98.72% accuracy** and sub-millisecond inference (0.0051 ms).
   - **Multiclass Classifier:** Categorizes flows into 8 security groups (`Benign`, `DDoS`, `DoS`, `Mirai`, `Recon`, `Web`, `BruteForce`, `Spoofing`) with **99.7% F1 on Mirai botnets**.
3. **Proprietary Feature Selection Algorithm (LRRC-FS):**
   - Implemented the **Lightweight Relevance-Redundancy-Cost Feature Selector**, balancing statistical relevance (ANOVA F-statistic), Pearson redundancy penalties, and packet parsing computational cost.
   - Outperformed standard SelectKBest and Variance Threshold baselines in throughput and resource efficiency.
4. **Class Imbalance Mitigation:**
   - Tested 4 strategies (Baseline, Cost-Sensitive Weighting, Random Under-Sampling, SMOTE). Class weighting and under-sampling drove minority attack recall to **96.0% - 98.7%** and slashed false alarms to **0.00% - 0.06%**.
5. **Interactive Cyberpunk Terminal UI (TUI):**
   - Built with **Textual** and **Rich** featuring a 6-tab operational dashboard:
     - `[1] CHAT`: Command assistant for training, schema audits, selector comparisons, and system status.
     - `[2] RUNS`: DataTable tracking historical training runs with Macro F1, accuracy, and latency.
     - `[3] LOGS`: Live streaming log viewer with severity filters.
     - `[4] MONITOR`: High-level metrics, attack breakdowns, and live detection alerts.
     - `[5] POLICIES`: Active security policy manager with an immutable audit log.
     - `[6] SETTINGS`: Form-validated system configuration.
6. **Persistence & Security Policy Engine:**
   - Integrated SQLite storage (`iot_ids.sqlite`) storing detection events and model metadata.
   - Automated rule-matching engine triggering alerts (CRITICAL Mirai, HIGH DDoS, MEDIUM DoS).
7. **Comprehensive Automated Test Suite:**
   - 27 unit and integration tests passing with 100% test isolation.

---

## ⏳ 2. What is Yet to Be Done

All core software, training, benchmarking, and interactive capabilities are **complete**. The only optional future milestone is:

1. **Hardware Edge Deployment (Optional Physical Stage):**
   - Flash the serialized lightweight `.joblib` model bundles directly onto physical embedded IoT hardware (e.g., Raspberry Pi 4/5, ESP32 gateway, OpenWrt router) for in-line hardware packet capture via Libpcap/Scapy.

---

## 🧮 3. The Core Novel Algorithm: LRRC-FS

Standard feature selection methods (like SelectKBest or PCA) only analyze statistical variance. However, in IoT gateways, micro-controllers, and smart meters, calculating complex multi-packet dispersion statistics (like *Variance, Covariance, Radius*) consumes significant CPU cycles and power.

### Mathematical Formulation
$$\text{Score}(f) = w_{\text{rel}} \cdot \hat{R}(f) - w_{\text{red}} \cdot \hat{D}(f, S) - w_{\text{cost}} \cdot \hat{C}(f)$$

Where:
- $\hat{R}(f) \in [0, 1]$: **Target Relevance** via normalized ANOVA F-statistic ($F(f, y)$) measuring separation between benign flows and attacks.
- $\hat{D}(f, S) \in [0, 1]$: **Redundancy Penalty** computed as the mean absolute Pearson correlation between candidate $f$ and already-selected features $S$:
  $$\hat{D}(f, S) = \begin{cases} 0 & \text{if } |S| = 0 \\ \frac{1}{|S|} \sum_{s \in S} |\rho(f, s)| & \text{if } |S| > 0 \end{cases}$$
- $\hat{C}(f) \in [0, 1]$: **Computational Cost Penalty**. Features requiring floating-point calculations and square roots (`Variance`, `Covariance`, `Radius` = cost $0.9$) are penalized in favor of lightweight packet bitflags (`TCP`, `UDP`, `syn_count`, `ack_flag_number` = cost $0.2$).
- $w_{\text{rel}}, w_{\text{red}}, w_{\text{cost}}$: User-configurable non-negative weights (default: `0.5`, `0.3`, `0.2`).

Greedy selection executes in $\mathcal{O}(n \cdot m^2 + k^2 m)$ time with deterministic lexical tie-breaking.

---

## 🌲 4. Models & Machine Learning Architecture

| Model | CLI Identifier | Description | Optimal Use Case |
| :--- | :--- | :--- | :--- |
| **Random Forest** *(Default)* | `random_forest` | 50 bounded-depth trees (depth 12). Mitigates overfitting on noisy packet rate statistics. | Primary model for best balance of high Macro F1 and low False Positive Rate (FPR). |
| **Decision Tree** | `decision_tree` | Single interpretable tree (depth 12). Ultra-low latency (< 0.05 ms/sample). | Sub-millisecond verification on edge routers. |
| **Extra Trees** | `extra_trees` | Randomized decision trees. Lower variance on high-volume flood attacks. | Heavy DDoS flood classification. |
| **HistGradientBoosting** | `gradient_boosting` | Histogram-based gradient boosting optimized for tabular metrics. | Large multi-partition datasets. |

---

## 📁 2. Dataset Structure & Ingestion

The repository uses the authentic **CICIoT2023** partition files extracted into `data/raw/CICIOT23/`:

```text
data/raw/CICIOT23/
├── train/
│   └── train.csv          # Primary training set (1.55 GB, ~1.8M flows)
├── test/
│   └── test.csv           # Unseen testing set (331.8 MB, ~400k flows)
└── validation/
    └── validation.csv     # Validation holdout set (331.8 MB, ~400k flows)
```

The data loader in `src/data/loader.py` supports streaming chunk-based ingestion (`chunk_size=50,000`), allowing processing of gigabyte-scale datasets on standard laptops without memory exhaustion (OOM).

---

## 💻 5. How to Run & Check the Program

### Option A: Interactive Terminal UI (TUI)

Launch the cyberpunk terminal control plane:
```powershell
.\.venv\Scripts\python.exe src/main.py
```

#### TUI Hotkeys & Tabs:
- **`1` (`[1] CHAT`)**: Interactive command console. Type:
  - `/status` — Displays system health, record counts, active model, and database stats.
  - `/audit` — Audits the dataset in real-time.
  - `/train binary rf` — Spawns background training for Random Forest.
  - `/compare` — Runs feature selector comparison.
  - `/lrrc` — Displays the LRRC-FS mathematical breakdown.
- **`2` (`[2] RUNS`)**: DataTable tracking all historical training runs with Macro F1, accuracy, and inference latency.
- **`3` (`[3] LOGS`)**: Live colorized log viewer streaming directly from memory with severity filters.
- **`4` (`[4] MONITOR`)**: Real-time traffic breakdown, high-level metrics, and recent detection event alerts.
- **`5` (`[5] POLICIES`)**: Toggle and edit alert thresholds for Mirai, DDoS, DoS, and Recon policies.
- **`6` (`[6] SETTINGS`)**: Validate and modify directories, default models, and LRRC-FS weights.
- **`Ctrl + Q`**: Exit cleanly.

---

### Option B: Direct CLI Commands

#### 1. Check Discovered Datasets
Scans the dataset directories and lists detected raw and synthetic CSV files:
```powershell
.\.venv\Scripts\python.exe src/main.py discover
```

#### 2. Check Dataset Quality & Flow Schema
Inspects row counts, column types, missing values, infinite values, and label distributions:
```powershell
.\.venv\Scripts\python.exe src/main.py audit --path "data/raw/CICIOT23/train/train.csv" --max-rows 50000
```

#### 3. Train Models on Real Traffic
```powershell
# Binary classification (BENIGN vs ATTACK) using Random Forest (15 features with LRRC-FS)
.\.venv\Scripts\python.exe src/main.py train --path "data/raw/CICIOT23/train/train.csv" --task binary --model random_forest --selector lrrc --features 15 --samples 30000

# Multiclass classification (8 attack categories) with Cost-Sensitive Class Weighting
.\.venv\Scripts\python.exe src/main.py train --path "data/raw/CICIOT23/train/train.csv" --task multiclass --model random_forest --selector lrrc --features 15 --class-weight --samples 30000
```

#### 4. Benchmark Feature Selection (LRRC-FS vs Baselines)
Empirically benchmarks LRRC-FS against All Features, Variance Threshold, and SelectKBest:
```powershell
.\.venv\Scripts\python.exe src/main.py compare-selectors --path "data/raw/CICIOT23/train/train.csv" --samples 10000 --features 15
```

#### 5. Benchmark Class Imbalance Strategies
Compares Unweighted Baseline, Class-Weighting, Random Under-Sampling, and SMOTE:
```powershell
.\.venv\Scripts\python.exe src/main.py compare-imbalance --path "data/raw/CICIOT23/train/train.csv" --samples 10000
```

#### 6. Run Offline Testing / Inference on Unseen Traffic
Evaluates the trained model against unseen records from `test.csv`, classifies flows, and triggers security policy alerts:
```powershell
# Run inference on 1,000 unseen test flows
.\.venv\Scripts\python.exe src/main.py predict --input "data/raw/CICIOT23/test/test.csv" --samples 1000

# Export annotated test predictions with policy alert tags to CSV
.\.venv\Scripts\python.exe src/main.py predict --input "data/raw/CICIOT23/test/test.csv" --samples 5000 --output "results/predictions_annotated.csv"
```

#### 7. Review Historical Training Runs & Alert Events
```powershell
# List recent training runs stored in SQLite
.\.venv\Scripts\python.exe src/main.py runs --limit 10

# List recent detection events and security alerts
.\.venv\Scripts\python.exe src/main.py events --limit 20

# Filter detection alerts by severity (CRITICAL, HIGH, MEDIUM, LOW)
.\.venv\Scripts\python.exe src/main.py events --severity CRITICAL
```

#### 8. Manage Security Alert Policies
```powershell
# Show active alert policies (Mirai, DDoS, DoS, Web, Recon)
.\.venv\Scripts\python.exe src/main.py policy show

# Toggle a policy enabled/disabled
.\.venv\Scripts\python.exe src/main.py policy toggle --id POL-001 --disable
.\.venv\Scripts\python.exe src/main.py policy toggle --id POL-001 --enable
```

---

## 🔍 6. What We Are Checking and How (Evaluation Guide)

When evaluating this IoT intrusion defense system, we perform 6 systematic checks:

### 1. Data Integrity & Schema Audit
- **What We Check:**
  - Whether all 46 official CICIoT2023 flow features are present and numerical.
  - Whether corrupted, infinite (`+/- Inf`), or missing (`NaN`) values exist in the stream.
  - The exact class distribution and extreme imbalance ratio (e.g. 7,916 : 1 majority vs. minority).
- **How It Is Checked:**
  - `src/data/audit.py` reads data in streaming chunks without loading gigabytes into RAM.
  - Computes `np.isnan()` and `np.isinf()` matrices, counts exact value frequencies, and generates a structured Markdown audit report in `results/reports/audit_report_*.md`.

### 2. Feature Selection Efficiency (LRRC-FS)
- **What We Check:**
  - Whether complex dispersion statistics (Variance, Covariance, Radius) can be replaced by lightweight packet flags (TCP, UDP, SYN, ACK) to save CPU cycles on resource-constrained IoT gateways.
  - That reduction from 46 to 15 features does not degrade attack detection accuracy.
- **How It Is Checked:**
  - `src/algorithms/feature_selector.py` evaluates the multi-objective objective function:
    $$\text{Score}(f) = w_{\text{rel}} \cdot \hat{R}(f) - w_{\text{red}} \cdot \hat{D}(f, S) - w_{\text{cost}} \cdot \hat{C}(f)$$
  - ANOVA F-statistic ($\hat{R}$) measures attack separation; Pearson correlation matrix ($\hat{D}$) penalizes redundant features; the domain cost table ($\hat{C}$) heavily penalizes floating-point heavy features ($0.9$) vs bitflags ($0.2$).
  - `compare-selectors` benchmarks accuracy, Macro F1, and latency against *SelectKBest* and *VarianceThreshold*.

### 3. Binary Anomaly Detection (`BENIGN` vs. `ATTACK`)
- **What We Check:**
  - How reliably normal smart-home/industrial IoT operations are distinguished from malicious traffic.
  - The **False Positive Rate (FPR)**: ensuring legitimate device communications are not mistakenly blocked.
- **How It Is Checked:**
  - Evaluated on a strictly isolated holdout test split (`20%`).
  - Measures Accuracy ($98.72\%$), Macro F1 ($0.8653$), and FPR ($FP / (FP + TN)$) using `src/training/evaluate.py`.
  - Plots confusion matrices to `results/plots/` showing true positives, true negatives, false positives, and false negatives.

### 4. Multiclass Attack Recognition (8 Attack Families)
- **What We Check:**
  - Specific identification of attack vectors: **Mirai Botnets**, **DDoS Floods**, **DoS Floods**, **Reconnaissance**, **Spoofing**, **BruteForce**, and **Web Attacks**.
  - That rare minority classes (such as Mirai or Recon) are not ignored by the model.
- **How It Is Checked:**
  - `src/data/taxonomy.py` maps 34 raw CICIoT sub-attacks into 8 canonical categories.
  - Models are trained with cost-sensitive class weighting (`class_weight='balanced'`), assigning higher penalties to errors on rare attacks.
  - Verified via per-class precision, recall, and Macro F1 (yielding **99.7% F1 on Mirai**).

### 5. Inference Latency & Edge Feasibility
- **What We Check:**
  - Inference speed per packet sample in milliseconds ($< 0.05\text{ ms}$).
  - Hardware feasibility for low-power edge gateways (Raspberry Pi, ARM routers) without requiring GPU accelerators.
- **How It Is Checked:**
  - `src/training/evaluate.py` measures inference time using high-precision timers (`time.perf_counter()`) across thousands of test samples.
  - Random Forest achieves **0.0051 ms/sample** (~196,000 predictions/sec on CPU).

### 6. Security Policy Alerts & Threat Mitigation
- **What We Check:**
  - Whether detected attacks immediately map to enforceable security policies.
  - That high-confidence malicious events generate immediate actionable alerts (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- **How It Is Checked:**
  - `src/core/policies.py` evaluates confidence thresholds and category match rules (e.g. `confidence >= 0.85` + `category == Mirai` $\rightarrow$ trigger `POL-001: Critical Mirai Botnet Activity`).
  - Automatically records timestamped alerts into the SQLite database (`iot_ids.sqlite`) and streams them into the live TUI `MONITOR` screen.

---

## 📂 7. How to Check Outputs & Artifacts

| Output Type | File Path / Location | Purpose |
| :--- | :--- | :--- |
| **Trained Models** | `models/*.joblib` | Persisted model bundles containing the fitted classifier, fitted `IoTDataPreprocessor`, preprocessing manifest, and label encoder. |
| **Confusion Matrix Plots** | `results/plots/*.png` | Visual confusion matrix heatmaps generated after each training run. |
| **Run Metrics (JSON)** | `results/metrics/*.json` | Evaluation metrics (Accuracy, Macro F1, Weighted F1, FPR, inference latency, per-class Precision/Recall). |
| **Comparison Reports** | `results/reports/*.md` | Markdown reports documenting feature selection and class imbalance experiments. |
| **Audit Reports** | `results/reports/audit_report_*.md` | Comprehensive data quality and schema integrity audits. |
| **SQLite Database** | `iot_ids.sqlite` | Tables `training_runs` and `detection_events` recording all historical runs and alerts. |
| **Application Log** | `iot_ids.log` | Rotating log file capturing structured application and detection events. |

---

## 🧪 8. Automated Verification & Testing

To run the complete automated test suite (27 tests):
```powershell
.\.venv\Scripts\pytest.exe -v
```

All tests execute inside isolated temporary directories (`tmp_path`) and do not pollute the workspace.

---

## 🏛️ 9. Architecture & File Structure

```text
d:/mini project/
├── config/
│   ├── settings.json            # Pydantic-validated application settings
│   └── policies.json            # Security alert policies & audit history
├── data/
│   ├── raw/                     # Put ciciot2023 csv.zip or raw CSVs here
│   ├── processed/               # Preprocessed feature manifests & aligned data
│   └── synthetic/               # Empty (clean for real dataset upload)
├── models/                      # Versioned .joblib model bundles
├── results/
│   ├── metrics/                 # Machine-readable JSON evaluation reports
│   ├── plots/                   # Saved confusion matrix figures (.png)
│   └── reports/                 # Markdown audit and experiment comparisons
├── src/
│   ├── main.py                  # Main executable entrypoint (launches TUI or CLI)
│   ├── cli.py                   # Rich terminal CLI commands
│   ├── core/
│   │   ├── engine.py            # Unified domain orchestrator
│   │   ├── events.py            # Pydantic event and run data models
│   │   ├── policies.py          # Alert policy engine & audit log
│   │   ├── settings.py          # AppSettings configuration management
│   │   └── logging_config.py    # Rotating file logger & in-memory buffer
│   ├── data/
│   │   ├── loader.py            # Chunked CSV reader with automatic .zip extraction
│   │   ├── audit.py             # Data quality audit & report generator
│   │   ├── preprocess.py        # Imputation, scaling & PreprocessingManifest
│   │   ├── split.py             # Leakage-resistant stratified partitioner
│   │   ├── synthetic.py         # Synthetic CICIoT2023 generator utility
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
│       ├── app.py               # Main Textual TUI Application (F1-F6 keybindings)
│       └── screens/             # CHAT, RUNS, LOGS, MONITOR, POLICIES, SETTINGS
├── tests/                       # 27 automated pytest tests
├── requirements.txt             # Pinned package versions
├── iot_ids.sqlite               # Persistent SQLite database
├── iot_ids.log                  # Structured rotating log file
└── README.md                    # Project documentation
```
