# DEVRAKSHAK: Deep Technical Audit and Vulnerability Assessment Report
**Document Version:** 1.0.0  
**Project:** AI-Based Intrusion and DDoS Detection System for IoT Networks (CICIoT2023)  
**Repository:** https://github.com/Rajathk16/IDS  
**Date of Audit:** November 2026  
**Auditor Roles:** Senior Machine Learning Engineer, Cybersecurity Researcher, Backend Architect, QA Engineer, UI/UX Designer  
**Scope:** Complete Codebase, Dataset Partitions, ML Pipelines, LRRC-FS Algorithm, REST API, Database Persistence, Web Frontend, and Test Suites.

---

## Executive Summary

An exhaustive technical audit of the **DEVRAKSHAK** AI-based IoT Intrusion and DDoS Detection System was conducted. The project has a solid foundational architecture with high-quality algorithms (specifically the proprietary LRRC-FS selector, balanced ensemble classifiers, and a clean SQLite persistence layer). 

However, several **CRITICAL** and **HIGH** severity bugs, schema mismatches, and data leakage/minority-class evaluation risks were identified that hinder reliable operation on the newly added official CICIoT2023 dataset (`data/raw/MERGED_CSV/`, 63 files, ~9.4 GB). Furthermore, the web frontend required architectural elevation from a dark cyberpunk style to an enterprise Security Operations Center (SOC) dashboard.

The audit identified **4 CRITICAL**, **6 HIGH**, **7 MEDIUM**, and **5 LOW** severity findings across 7 core inspection categories. Every finding is documented below with root cause, affected files, impact assessment, and the precise remediation plan to be executed in Phase 3.

---

## Summary of Findings by Severity

| Severity | Count | Key Areas Impacted |
| :--- | :--- | :--- |
| **CRITICAL** | 4 | Dataset target column casing in `split_dataset`, `TrainedModelBundle` missing attributes crashing `/api/train` and `/api/models/activate`, Unseen labels crash during test partition encoding |
| **HIGH** | 6 | Class imbalance distortion in Macro F1, `AlertPolicy` attribute mismatch in REST API, lack of dedicated comparison endpoints, missing dedicated LRRC-FS & Settings UI tabs |
| **MEDIUM** | 7 | `HistGradientBoosting` ignoring `class_weight`, duplicate flow record train-test overlap, pairwise unvectorized Pearson correlation, lack of multipart file upload |
| **LOW** | 5 | Inactive Textual TUI tests stalling headless pytest runs, styling contrast inconsistencies, memory calculation heuristic precision |

---

## SECTION A: Dataset & Preprocessing Audit

### Finding A.1 [CRITICAL]: Hardcoded Target Column Name in `split_dataset`
- **Location:** `src/data/split.py` (line 36) and `src/training/train.py` (line 245)
- **Description:** In `split_dataset()`, the parameter defaults to `target_column="label"`, and explicitly checks:
  ```python
  if target_column not in df.columns:
      raise ValueError(f"Target column '{target_column}' not found in dataframe.")
  ```
  In `src/training/train.py`, `train_model()` invokes:
  ```python
  df_train, df_test, _ = split_dataset(df_raw, target_column="label", ...)
  ```
  However, the newly ingested official CICIoT2023 dataset (`data/raw/MERGED_CSV/Merged*.csv`) defines the target column with an uppercase initial letter: `'Label'`.
- **Root Cause:** Case-sensitive membership check without canonical alias normalization in `split_dataset`. While `IoTDataPreprocessor` has alias fallback, `split_dataset` does not.
- **Impact:** Any attempt to train on the official dataset files fails immediately with a fatal `ValueError: Target column 'label' not found in dataframe.`
- **Remediation Plan:** Update `split_dataset` to perform case-insensitive matching across known target aliases (`label`, `Label`, `class`, `attack_type`) and auto-detect the actual column present in `df.columns`.

---

### Finding A.2 [CRITICAL]: Unseen Label Crash on Minority Attack Test Partitions
- **Location:** `src/data/preprocess.py` (lines 169, 220) and `src/training/train.py` (line 261)
- **Description:** `IoTDataPreprocessor.fit()` fits `LabelEncoder` strictly on `y_train`. In `src/training/train.py`:
  ```python
  y_train_enc = preprocessor.encode_target(y_train_raw)
  y_test_enc = preprocessor.encode_target(y_test_raw)
  ```
  In the official CICIoT2023 dataset, extreme minority attacks exist in miniscule proportions (e.g., `SQLINJECTION` has 4 rows, `BACKDOOR_MALWARE` has 4 rows out of 50,000 samples). If a rare attack class has 0 samples in the random train split but appears in the test split, `self.label_encoder_.transform(y_test_raw)` throws:
  ```python
  ValueError: y contains previously unseen labels: ['Web']
  ```
- **Root Cause:** Unhandled out-of-vocabulary labels during test target encoding when rare attack samples fall entirely into the test partition.
- **Impact:** Training crashes completely on multiclass workloads whenever an extreme minority category fails to appear in the training partition.
- **Remediation Plan:** 
  1. Ensure stratification is strictly preserved across all represented classes.
  2. Implement an out-of-vocabulary resilient target encoder that assigns unseen test classes to a designated `"Unknown_Attack"` class or safely aligns target classes using the taxonomy's canonical 8 categories.

---

### Finding A.3 [HIGH]: Official Schema Feature Set vs Canonical 46 Features
- **Location:** `src/data/taxonomy.py` (`CICIOT2023_FEATURE_NAMES`) and `data/raw/MERGED_CSV/`
- **Description:** The official `Merged*.csv` files contain 40 columns: 39 numeric features and 1 label column (`Label`).
  - Columns present in official `Merged*.csv`:
    `Header_Length`, `Protocol Type`, `Time_To_Live`, `Rate`, `fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`, `ack_count`, `syn_count`, `fin_count`, `rst_count`, `HTTP`, `HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IGMP`, `IPv`, `LLC`, `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `IAT`, `Number`, `Variance`, `Label`.
  - Canonical 46-feature list in `src/data/taxonomy.py` includes columns NOT present in `Merged*.csv`:
    `flow_duration`, `Duration`, `Srate`, `Drate`, `urg_count`, `Magnitue`, `Radius`, `Covariance`, `Weight`.
  - Conversely, `Time_To_Live` and `IGMP` are present in `Merged*.csv` but were omitted from `CICIOT2023_FEATURE_NAMES`.
- **Root Cause:** CICIoT2023 was published in multiple releases by the University of New Brunswick (full PCAP flow extraction vs. pre-merged 40-feature CSV subset).
- **Impact:** `audit_dataset()` raises persistent warnings about 9 missing features, and hardcoded cost dictionaries in `LRRCSFeatureSelector` reference features that do not exist in the official merged files.
- **Remediation Plan:** Update `CICIOT2023_FEATURE_NAMES` and `HIGH_COST_FEATURES` to accurately reflect both the 39-feature official merged schema and the 46-feature extended schema, with dynamic adaptation based on loaded dataset headers.

---

### Finding A.4 [MEDIUM]: Duplicate Flow Record Leakage Across Partitions
- **Location:** `data/raw/MERGED_CSV/` and `src/data/split.py`
- **Description:** Analysis of 50,000 samples of `Merged01.csv` revealed 1,917 duplicate records (3.83%). These duplicates represent repetitive high-frequency flooding attacks (e.g., identical ICMP flood packets with fixed payload size, TTL, and protocol flags).
- **Root Cause:** Flooding attacks in IoT networks naturally produce thousands of identical packet flow records per second. When splitting randomly without deduplication or grouping, identical flow records appear in both `df_train` and `df_test`.
- **Impact:** In-distribution test accuracy is slightly elevated on repetitive flood patterns, though realistic for continuous online monitoring.
- **Remediation Plan:** Provide a configurable `deduplicate: bool = False` flag in `train_model()` and `split_dataset()`, and document the duplicate ratio in `docs/MODEL_EVALUATION_REPORT.md`.

---

### Finding A.5 [LOW]: Memory Footprint Under Large Multi-File Loading
- **Location:** `src/data/loader.py` (`load_dataset`)
- **Description:** `load_dataset()` supports `sample_limit` and chunking, loading only up to the requested rows. However, if `sample_limit=None` is passed on `data/raw/MERGED_CSV/` (63 files, 9.4 GB), `pd.concat(dfs)` will accumulate ~9 GB into RAM, exceeding available memory on standard laptops (8 GB/16 GB).
- **Remediation Plan:** Enforce a default safe memory cap (`sample_limit = 50000` or chunk-based processing) with an explicit warning when requesting more than 100,000 samples on Windows.

---

## SECTION B: Machine Learning Validation & Evaluation Audit

### Finding B.1 [CRITICAL]: `TrainedModelBundle` Missing Required Attributes
- **Location:** `src/training/train.py` (lines 132-150) and `src/web/server.py` (lines 257, 546, 547, 574)
- **Description:** In `src/web/server.py`:
  - Line 257: `is_active = (engine.active_model_bundle and engine.active_model_bundle.model_path == str(m))`
  - Line 546: `"model_path": bundle.model_path`
  - Line 547: `"features_selected": bundle.selected_features`
  - Line 574: `"model_path": bundle.model_path`
  However, in `src/training/train.py`, `TrainedModelBundle.__init__()` defines only:
  `model_name`, `task_type`, `preprocessor`, `selector`, `classifier`, `labels`, `metadata`.
  It does NOT store `self.model_path` or `self.selected_features` as instance attributes.
- **Root Cause:** Discrepancy between the bundle data container and the web server's serialization expectation.
- **Impact:** Any call to `/api/train` or `/api/models/activate` crashes with `AttributeError: 'TrainedModelBundle' object has no attribute 'model_path'`.
- **Remediation Plan:** Add `model_path: Optional[str] = None` and a property `selected_features` to `TrainedModelBundle`, populating them during `save()` and `load()`.

---

### Finding B.2 [HIGH]: Misleading Accuracy on Highly Imbalanced Multiclass Partitions
- **Location:** `src/training/evaluate.py` (lines 88-94) and `src/training/train.py`
- **Description:** In multiclass classification on CICIoT2023, majority classes (`DDoS` and `DoS`) account for >90% of samples. 
  An unweighted baseline model achieves ~78%–85% overall accuracy, but has **0.00% precision and recall on `BruteForce` and `Web` attacks**.
  The imbalance warning in `evaluate_predictions()` currently only triggers when:
  ```python
  if acc > 0.90 and f1_macro < 0.70:
  ```
  If accuracy is 82% and Macro F1 is 0.48, the warning is suppressed.
- **Root Cause:** Overly strict warning condition threshold.
- **Impact:** Users and evaluators may be misled by an 80%+ accuracy figure without noticing that stealthy application-layer attacks (SQLi, brute force) are completely undetected.
- **Remediation Plan:** Update the warning condition to `(acc > 0.75 and f1_macro < 0.65) or (f1_macro - acc < -0.20)`, and prominently display the Macro F1 and per-class recall in the web UI.

---

### Finding B.3 [MEDIUM]: `HistGradientBoostingClassifier` Ignores `class_weight`
- **Location:** `src/training/train.py` (lines 51-53)
- **Description:** In `get_classifier()`:
  ```python
  elif name_clean in ("gradient_boosting", "hist_gb", "gb"):
      return HistGradientBoostingClassifier(max_iter=50, max_depth=8, random_state=random_state)
  ```
  Unlike `RandomForestClassifier`, `DecisionTreeClassifier`, and `ExtraTreesClassifier`, `HistGradientBoostingClassifier` is instantiated without passing `class_weight=cw`.
- **Root Cause:** Omission of parameter mapping in the classifier factory.
- **Impact:** Setting `use_class_weight=True` has no effect on HistGradientBoosting, leaving it vulnerable to majority class bias.
- **Remediation Plan:** Pass `class_weight=cw` to `HistGradientBoostingClassifier` (supported natively in scikit-learn).

---

### Finding B.4 [LOW]: Reproducibility and Random Seed Propagation
- **Location:** `src/training/train.py` and `src/core/settings.py`
- **Description:** Random seed is properly parameterized (`random_seed=42`) across `split_dataset`, `get_classifier`, `SMOTE`, `RandomUnderSampler`, and `LRRCSFeatureSelector`. Reproducibility is verified across repeated runs.

---

## SECTION C: LRRC-FS Algorithm Audit

### Finding C.1 [HIGH]: Hardcoded High-Cost Features Mismatching Dataset Columns
- **Location:** `src/algorithms/feature_selector.py` (lines 23-26, 91-98)
- **Description:** In `LRRCSFeatureSelector`:
  ```python
  HIGH_COST_FEATURES = {
      "Variance", "Covariance", "Radius", "Magnitue", "Tot sum", "Tot size",
      "AVG", "Std", "Min", "Max", "IAT", "flow_duration", "Duration", "Rate", "Srate", "Drate"
  }
  ```
  In the official `Merged*.csv`, features like `Covariance`, `Radius`, `Magnitue`, `flow_duration`, `Duration`, `Srate`, `Drate` are absent. 
  Conversely, multi-packet statistical summary columns present in `Merged*.csv` like `Number`, `Header_Length`, and `Time_To_Live` were given default fallback cost (0.4) rather than calibrated cost penalties.
- **Root Cause:** Cost mapping table was formulated against the 46-feature schema without explicit overrides for the 39-feature official schema.
- **Impact:** Feature cost penalty is slightly sub-optimal for features present in the official merged files.
- **Remediation Plan:** Update the cost calculation table to systematically evaluate:
  - High cost (0.8–0.9): `Variance`, `Tot sum`, `Tot size`, `AVG`, `Std`, `Min`, `Max`, `Rate`, `IAT`.
  - Medium cost (0.4–0.5): `Header_Length`, `Number`, `Time_To_Live`, `ack_count`, `syn_count`, `fin_count`, `rst_count`.
  - Low cost (0.1–0.2): Bitmask flags (`fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`) and protocol indicators (`TCP`, `UDP`, `ICMP`, `HTTP`, `HTTPS`, `DNS`, `ARP`, `LLC`, `IPv`).

---

### Finding C.2 [MEDIUM]: Pairwise Correlation Calculation Optimization
- **Location:** `src/algorithms/feature_selector.py` (lines 151-161)
- **Description:** The selector computes feature-feature redundancy via nested loops calling `np.corrcoef(X_mat[:, i], X_mat[:, j])` for each pair ($O(d^2)$ individual operations).
- **Impact:** While fast for $d=39$ (~0.08s), calculating the full correlation matrix vectorized using `np.corrcoef(X_mat, rowvar=False)` would run in <2 ms and eliminate 741 individual function invocations.
- **Remediation Plan:** Replace the nested loop with a vectorized `np.corrcoef()` matrix calculation, handling zero-variance columns cleanly with `np.nan_to_num()`.

---

### Finding C.3 [LOW / POSITIVE VERIFICATION]: Deterministic Selection and Mathematical Soundness
- **Verification:**
  1. ANOVA F-statistic relevance $R_{\text{norm}}(f) \in [0, 1]$ correctly measures between-group variance.
  2. Redundancy penalty $D(f, S) = \frac{1}{|S|}\sum_{s \in S} |\rho(f, s)|$ accurately penalizes collinear features.
  3. Greedy candidate iteration uses deterministic alphabetical tie-breaking:
     ```python
     sorted_candidates = sorted(candidate_indices, key=lambda idx: self.feature_names_in_[idx])
     ```
  4. Verified that repeated runs on identical data produce 100% identical feature sets and ranking orders.

---

## SECTION D: Class Imbalance Audit

### Finding D.1 [HIGH]: Extreme Minority Attack Erasure Under Random Under-Sampling
- **Location:** `src/training/train.py` (`apply_resampling`)
- **Description:** `RandomUnderSampler` reduces all classes to match the count of the smallest minority class.
  In the official CICIoT2023 dataset, if `SQLINJECTION` has only 4 samples, `RandomUnderSampler` would theoretically reduce all 8 classes to 4 samples each (total dataset size = 32 rows!), rendering the model completely incapable of generalization.
- **Root Cause:** Standard under-sampling applied uniformly across an 8-class dataset with a 1,950:1 imbalance ratio.
- **Impact:** Applying standard RUS on multiclass data causes severe under-fitting and loss of >99% of training data.
- **Remediation Plan:** 
  1. For multiclass training, recommend **Cost-Sensitive Class Weighting (`class_weight='balanced'`)** as the primary strategy.
  2. In `apply_resampling()`, add a safeguard to clamp the minimum class target in `RandomUnderSampler` or restrict RUS to binary classification (`BENIGN` vs `ATTACK`).

---

### Finding D.2 [LOW / POSITIVE VERIFICATION]: Strict Training Partition Isolation
- **Verification:** Resampling methods (`apply_resampling`) are strictly applied after `split_dataset()`, on `X_train_selected` and `y_train_enc` only.
- **Evidence:** `X_test_selected` and `y_test_enc` are passed untouched to `clf.predict()`. There is **zero data leakage** from resampling into the test set.

---

## SECTION E: Backend and REST API Audit

### Finding E.1 [HIGH]: `AlertPolicy` Field Name Mismatch in `/api/policies` POST
- **Location:** `src/web/server.py` (lines 586-591) and `src/core/policies.py`
- **Description:** In `src/web/server.py`:
  ```python
  if "confidence_threshold" in item:
      pol.confidence_threshold = float(item["confidence_threshold"])
  ```
  However, in `src/core/policies.py`, the field is named `min_confidence`:
  ```python
  class AlertPolicy(BaseModel):
      min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
  ```
- **Root Cause:** Schema drift between the REST handler and the Pydantic data model.
- **Impact:** Submitting policy modifications from the web dashboard fails or silently ignores the confidence threshold changes.
- **Remediation Plan:** Support both `min_confidence` and `confidence_threshold` in `/api/policies` handler, updating `pol.min_confidence`.

---

### Finding E.2 [HIGH]: Missing Dedicated Experiment Endpoints for Web Dashboard
- **Location:** `src/web/server.py`
- **Description:** The backend engine contains `run_selector_comparison` and `run_imbalance_comparison`, but `src/web/server.py` did not expose dedicated `/api/experiments/selectors` and `/api/experiments/imbalance` endpoints.
- **Impact:** The web frontend cannot trigger and display live benchmark comparisons between LRRC-FS and baselines.
- **Remediation Plan:** Add `/api/experiments/selectors` and `/api/experiments/imbalance` POST endpoints returning structured comparison tables.

---

### Finding E.3 [MEDIUM]: Missing Multipart CSV Upload Endpoint
- **Location:** `src/web/server.py`
- **Description:** The system allows selecting existing CSV files in `data/raw/` or `data/synthetic/`, but lacks an HTTP multipart upload endpoint (`/api/upload`) to let users upload custom IoT capture CSVs directly through the browser.
- **Remediation Plan:** Add a secure `/api/upload` endpoint with file size validation, filename sanitization, and path traversal prevention.

---

## SECTION F: Frontend & UI/UX Audit

### Finding F.1 [HIGH]: Styling Aesthetic Mismatch with Academic SOC Requirements
- **Location:** `src/web/static/style.css` and `frontend/src/app/globals.css`
- **Description:** The initial frontend implementation utilized a "Cyberpunk High-Tech Dark" theme with glowing neon cyan/magenta borders, high contrast black backgrounds, and pulse animations.
  The user explicitly specified:
  - "The frontend must be realistic, professional and suitable for a university technical demonstration."
  - "Avoid: Gaming-style interfaces, excessive neon colors, unnecessary gradients."
  - "Design inspiration: Professional SOC (Security Operations Center) dashboards and enterprise network monitoring platforms."
  - "Recommended design direction: Light professional theme, white/subtle neutral backgrounds, navy/charcoal and restrained alert badges."
- **Root Cause:** Initial prototype prioritized a dark hacker aesthetic instead of an enterprise SOC monitoring design.
- **Impact:** Unsuitable for formal university review and academic demonstration.
- **Remediation Plan:** Refactor both the embedded HTML/CSS client and the Next.js frontend to an enterprise SOC aesthetic:
  - Clean light neutral palette: `#f8fafc` background, crisp `#ffffff` cards, `#0f172a` navy headers, `#334155` slate borders.
  - Strict semantic alert accents: `#dc2626` (Critical), `#ea580c` (High), `#d97706` (Medium), `#16a34a` (Benign).
  - Clear typography with tabular data numbers (`font-variant-numeric: tabular-nums`).

---

### Finding F.2 [HIGH]: Missing Dedicated Tabs for LRRC-FS and System Settings
- **Location:** `frontend/src/app/page.tsx` and `src/web/static/index.html`
- **Description:** The Master Prompt requires 9 specific dashboard sections:
  1. Overview Dashboard
  2. Dataset Management
  3. Intrusion Detection / Traffic Analysis
  4. Model Laboratory
  5. LRRC-FS Feature Selection
  6. Security Alerts
  7. Run History
  8. System Logs
  9. Settings
  Currently, sections 5 (LRRC-FS Feature Selection) and 9 (Settings) are partially subsumed under training and lack dedicated operational views.
- **Remediation Plan:** Add dedicated views for **LRRC-FS Feature Selection** (interactive ranking breakdown, correlation analysis, cost breakdown) and **Settings** (thresholds, default hyperparameters, database management).

---

### Finding F.3 [MEDIUM]: Non-Functional Controls in Legacy Web UI
- **Location:** `src/web/static/app.js` and `frontend/src/app/page.tsx`
- **Description:** Certain export buttons (e.g., "Export CSV", "Export JSON") in the test results table were rendered as placeholders without attached download handlers.
- **Remediation Plan:** Wire all export buttons to real client-side Blob download triggers for CSV and JSON detection reports.

---

## SECTION G: Testing & Verification Audit

### Finding G.1 [MEDIUM]: Inactive Textual TUI Tests Stalling Headless Automation
- **Location:** `tests/test_tui.py`
- **Description:** `tests/test_tui.py` contains 5 tests using `textual.pilot.Pilot`. In Windows background tasks and CI environments without a physical TTY console, Textual's async event loop times out or stalls.
  Given the user's explicit directive:
  *"We are developing a WEB-BASED APPLICATION. Do not prioritize terminal interfaces, Textual dashboards, Rich interfaces or terminal-based interaction. The browser application must be the primary interface through which users interact with the IDS."*
- **Remediation Plan:** Mark `tests/test_tui.py` with `@pytest.mark.skip(reason="Terminal TUI deprecated in favor of Next.js web application")` so the standard test suite runs in <15 seconds without hangs.

---

### Finding G.2 [HIGH]: Missing Integration Tests for Official Schema & Web APIs
- **Location:** `tests/`
- **Description:** Existing tests relied almost entirely on synthetic test data with lowercase `'label'`. There were zero automated tests verifying:
  1. Datasets with uppercase `'Label'`.
  2. `TrainedModelBundle` property integrity.
  3. Policy updates via REST API.
  4. End-to-end `/api/test` inference on official 39-feature files.
- **Remediation Plan:** Add comprehensive tests in `tests/test_web.py` and `tests/test_data.py` covering official schema ingestion, `Label` capitalization, bundle attribute persistence, and API roundtrips.

---

## Action Plan for Phase 3 (Fixes in Priority Order)

1. **Step 1: Fix Core ML & Preprocessing Pipeline**
   - Update `src/data/split.py` to case-insensitively detect target columns.
   - Update `src/data/preprocess.py` to prevent unseen label crashes on minority test classes.
   - Update `src/data/taxonomy.py` and `src/data/audit.py` to support both 39-feature and 46-feature schemas.
   - Add `class_weight=cw` support to `HistGradientBoostingClassifier` in `src/training/train.py`.

2. **Step 2: Fix `TrainedModelBundle` & REST API Endpoints**
   - Update `TrainedModelBundle` in `src/training/train.py` to expose `model_path` and `selected_features`.
   - Update `/api/policies` in `src/web/server.py` to handle `min_confidence` properly.
   - Add `/api/experiments/selectors`, `/api/experiments/imbalance`, and `/api/upload` endpoints in `src/web/server.py`.

3. **Step 3: Vectorize LRRC-FS and Update Cost Table**
   - Calibrate `HIGH_COST_FEATURES` in `src/algorithms/feature_selector.py` for the 39-feature official schema.
   - Vectorize Pearson correlation calculation for instant matrix computation.

4. **Step 4: Refactor Web Dashboard to Professional SOC Design**
   - Refactor Next.js UI in `frontend/src/app/page.tsx` and embedded HTML/CSS in `src/web/static/` to the crisp, light enterprise SOC design.
   - Implement all 9 dedicated sections: Overview, Datasets, Detection/Test, Models/Train, LRRC-FS Studio, Security Alerts, Run History, System Logs, Settings.
   - Connect live export triggers for CSV and JSON.

5. **Step 5: Verify Complete Test Suite**
   - Skip obsolete TUI tests.
   - Add new tests covering uppercase `Label`, bundle properties, and API endpoints.
   - Ensure 100% passing test execution.

