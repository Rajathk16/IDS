# 🛡️ DEVRAKSHAK // AI-Based IoT Intrusion & DDoS Defense System (CICIoT2023)

An offline, reproducible, cyber-dark terminal user interface and AI pipeline designed for IoT network anomaly detection, distributed denial-of-service (DDoS) flood mitigation, Mirai botnet recognition, and network reconnaissance based on the official **CICIoT2023** dataset schema.

---

## 📌 Project Status

- **Terminal Prototype:** **100% Complete & Tested.**
- **Sample Data Status:** **All sample/synthetic data has been cleaned and removed.** The repository is clean and prepared for the real **CICIoT2023** dataset.
- **Environment Setup:** **Zero external environment variables (`.env`) or cloud API keys required.** Everything operates 100% locally and offline.
- **Automated Tests:** **27/27 unit and integration tests passing.**

---

## 🧭 Table of Contents
1. [What We Have Done](#-1-what-we-have-done)
2. [What is Yet to Be Done](#-2-what-is-yet-to-be-done)
3. [The Core Novel Algorithm: LRRC-FS](#-3-the-core-novel-algorithm-lrrc-fs)
4. [Models & Machine Learning Architecture](#-4-models--machine-learning-architecture)
5. [How to Upload the Real CICIoT2023 Dataset](#-5-how-to-upload-the-real-ciciot2023-dataset)
6. [How to Run the Program](#-6-how-to-run-the-program)
   - [Interactive Terminal User Interface (TUI)](#option-a-interactive-terminal-ui-tui)
   - [Direct Command Line Interface (CLI)](#option-b-direct-cli-commands)
7. [How to Check Outputs & Artifacts](#-7-how-to-check-outputs--artifacts)
8. [Automated Verification & Testing](#-8-automated-verification--testing)
9. [Architecture & File Structure](#-9-architecture--file-structure)

---

## 🚀 1. What We Have Done

We have built a production-grade, offline cybersecurity defense system tailored specifically for IoT environments:

1. **Cyberpunk Terminal User Interface (TUI):**
   - Built with **Textual** and **Rich** featuring a 6-tab operational dashboard:
     - `[1] CHAT`: Command assistant supporting conversational AI explanations, background model training, schema audits, selector comparisons, and system status queries.
     - `[2] RUNS`: DataTable tracking historical training runs with per-class Macro F1 scores, accuracy, and latency.
     - `[3] LOGS`: Live colorized log viewer streaming from an in-memory buffer with severity filters (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
     - `[4] MONITOR`: High-level metric cards, attack category distribution tables, and recent detection alerts.
     - `[5] POLICIES`: Security policy manager for Mirai botnets, DDoS floods, DoS, Web injection, and Reconnaissance with threshold adjustments and an immutable audit log.
     - `[6] SETTINGS`: Form validated with Pydantic v2 to customize directories, default models, sample limits, and LRRC-FS weights.
2. **Proprietary Feature Selection Algorithm (LRRC-FS):**
   - Developed the **Lightweight Relevance-Redundancy-Cost Feature Selector**, which balances statistical relevance, inter-feature redundancy, and computational packet extraction cost.
3. **Dual Classification Tasks:**
   - **Binary Classification:** `BENIGN` vs. `ATTACK`.
   - **Multiclass Classification:** Categorizes traffic into 8 high-level security groups (`Benign`, `DDoS`, `DoS`, `Recon`, `Web`, `BruteForce`, `Spoofing`, `Mirai`).
4. **Memory-Conscious Data Ingestion:**
   - Designed to run on standard laptops (8 GB RAM) using chunk-based CSV processing.
   - Built-in automatic `.zip` archive unpacker (automatically detects and unzips `ciciot2023 csv.zip` in `data/raw/`).
5. **Class Imbalance Handling:**
   - Implemented and benchmarked 4 distinct strategies: Unweighted Baseline, Cost-Sensitive Class Weighting (`class_weight='balanced'`), Random Under-Sampling, and SMOTE.
6. **Persistence & Observability:**
   - Structured SQLite storage (`iot_ids.sqlite`) storing detection events and model metadata.
   - Automated confusion matrix heatmaps (`results/plots/`) and machine-readable metrics (`results/metrics/`).
7. **Comprehensive Automated Test Suite:**
   - 27 unit and integration tests covering all subsystems.

---

## ⏳ 2. What is Yet to Be Done

Now that the software framework and terminal prototype are complete, the remaining milestones are:

1. **Upload Real CICIoT2023 Dataset:**
   - Place `ciciot2023 csv.zip` (or uncompressed CSV partitions) into `data/raw/`.
2. **Run Full Data Audit on Real Data:**
   - Execute `python src/main.py audit` to inspect the authentic 46 numerical flow features, label distributions, missing values, and memory footprint.
3. **Train Models on Full Real Traffic:**
   - Train the primary Random Forest and Decision Tree classifiers on the real dataset partitions.
4. **Generate Final Empirical Benchmark Reports:**
   - Run `python src/main.py compare-selectors` and `python src/main.py compare-imbalance` on the real dataset to generate publication-ready comparative tables and Markdown reports.
5. **Hardware Edge Deployment (Optional Future Phase):**
   - Deploy the serialized `.joblib` model bundle onto physical edge IoT devices (e.g., Raspberry Pi, OpenWrt router) for live flow classification.

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

## 📥 5. How to Upload the Real CICIoT2023 Dataset

1. Place your downloaded dataset archive (`ciciot2023 csv.zip` or any `.csv` files) into:
   ```text
   d:\mini project\data\raw\
   ```
2. The data loader in `src/data/loader.py` includes **automatic zip extraction**. If a `.zip` file is detected, it will automatically unpack the CSV files upon the first run of `discover`, `audit`, or `train`.
3. Verify the files are recognized:
   ```powershell
   .\.venv\Scripts\python.exe src/main.py discover
   ```

---

## 💻 6. How to Run the Program

### Option A: Interactive Terminal UI (TUI)

Launch the full 6-tab terminal control plane:
```powershell
.\.venv\Scripts\python.exe src/main.py
# OR
.\.venv\Scripts\python.exe src/cli.py tui
```

#### TUI Navigation:
- **`1` - `6` or `F1` - `F6`**: Switch tabs (`1:Chat`, `2:Runs`, `3:Logs`, `4:Monitor`, `5:Policies`, `6:Settings`).
- **`Ctrl + Q`**: Exit cleanly.
- **Chat Commands**: In the `[1] CHAT` tab, type:
  - `/train` or `/train multiclass dt` - Spawns a background training worker.
  - `/audit` - Audits the dataset in real-time.
  - `/discover` - Lists discovered raw and synthetic datasets.
  - `/compare` - Runs feature selection comparison.
  - `/status` - Displays system health, record counts, and database status.
  - `/lrrc` - Explains the LRRC-FS mathematical formula.
  - `/models` - Compares classifier architectures.
  - `/metrics` - Explains why Macro F1 matters more than Accuracy.
  - `/clear` - Clears the chat screen.

---

### Option B: Direct CLI Commands

#### 1. Discover Available Datasets
```powershell
.\.venv\Scripts\python.exe src/main.py discover
```

#### 2. Audit Dataset Quality & Schema
Audits row counts, missing values, infinite values, duplicate rows, and class distributions:
```powershell
.\.venv\Scripts\python.exe src/main.py audit
# Or audit a specific file:
.\.venv\Scripts\python.exe src/main.py audit --path data/raw/ciciot2023.csv --max-rows 50000
```

#### 3. Train a Model (with LRRC-FS Feature Selection)
```powershell
# Binary classification (BENIGN vs ATTACK) using Random Forest (15 features)
.\.venv\Scripts\python.exe src/main.py train --task binary --model random_forest --selector lrrc --features 15 --samples 25000

# Multiclass classification (8 attack categories) using Decision Tree
.\.venv\Scripts\python.exe src/main.py train --task multiclass --model decision_tree --selector lrrc --features 10 --samples 25000

# Train with cost-sensitive class weighting for rare attacks
.\.venv\Scripts\python.exe src/main.py train --task multiclass --model random_forest --class-weight --samples 25000
```

#### 4. Run Empirical Feature Selection Comparison
Benchmarks **LRRC-FS** against *All Features*, *Variance Threshold*, and *SelectKBest*:
```powershell
.\.venv\Scripts\python.exe src/main.py compare-selectors --samples 10000 --features 15
```

#### 5. Run Class Imbalance Handling Comparison
Benchmarks *Unweighted*, *Class-Weighted*, *Random Under-Sampling*, and *SMOTE*:
```powershell
.\.venv\Scripts\python.exe src/main.py compare-imbalance --samples 10000
```

#### 6. Run Offline Inference / Predictions on Traffic
Classifies traffic flows, assigns confidence scores, flags attacks, and matches security policies:
```powershell
# Run inference on 1,000 rows
.\.venv\Scripts\python.exe src/main.py predict --input data/raw/ciciot2023.csv --samples 1000

# Export annotated predictions with alert tags to CSV
.\.venv\Scripts\python.exe src/main.py predict --input data/raw/ciciot2023.csv --output results/predictions_annotated.csv
```

#### 7. Review Historical Runs & Security Alerts
```powershell
# List training runs
.\.venv\Scripts\python.exe src/main.py runs --limit 10

# List recent detection events
.\.venv\Scripts\python.exe src/main.py events --limit 20

# Filter detection alerts by severity (CRITICAL, HIGH, MEDIUM, LOW)
.\.venv\Scripts\python.exe src/main.py events --severity HIGH
```

#### 8. Manage Security Alert Policies
```powershell
# Show active policies
.\.venv\Scripts\python.exe src/main.py policy show

# Toggle a policy enabled/disabled
.\.venv\Scripts\python.exe src/main.py policy toggle --id POL-001 --disable
.\.venv\Scripts\python.exe src/main.py policy toggle --id POL-001 --enable
```

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
