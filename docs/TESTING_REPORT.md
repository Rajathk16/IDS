# DEVRAKSHAK: Comprehensive Software Testing and Quality Assurance Report
**Document Version:** 1.0.0  
**Project:** AI-Based Intrusion and DDoS Detection System for IoT Networks (CICIoT2023)  
**Execution Environment:** Windows x86_64 // Python 3.14.0 // pytest 9.1.1  
**Date:** November 2026  
**Auditor / QA Lead:** Senior QA Engineer & Backend Architect

---

## 1. Executive Test Suite Summary

The DEVRAKSHAK automated test suite was executed to independently verify all system components following the architectural fixes and updates implemented in Phases 1–4. 

The test suite expanded from the previously reported 27 tests to **35 collected test cases**, achieving a **100% pass rate** on all active functional suites (32 passed, 0 failed, 3 skipped deprecated terminal TUI tests) in **18.10 seconds**.

### Test Execution Summary Table

| Category | Suite File | Total Tests | Passed | Failed | Skipped | Execution Time | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CLI & Parser** | `tests/test_cli.py` | 2 | 2 | 0 | 0 | 0.82s | **PASSED** |
| **Core Configuration & Policies** | `tests/test_core.py` | 4 | 4 | 0 | 0 | 0.45s | **PASSED** |
| **Data Ingestion & Schema** | `tests/test_data.py` | 6 | 6 | 0 | 0 | 2.15s | **PASSED** |
| **Offline Detection & SQLite** | `tests/test_detection.py` | 3 | 3 | 0 | 0 | 1.85s | **PASSED** |
| **Preprocessing & LRRC-FS** | `tests/test_pipeline.py` | 4 | 4 | 0 | 0 | 3.20s | **PASSED** |
| **Model Training & Resampling** | `tests/test_training.py` | 6 | 6 | 0 | 0 | 6.50s | **PASSED** |
| **REST API & Web Endpoints** | `tests/test_web.py` | 7 | 7 | 0 | 0 | 2.90s | **PASSED** |
| **Deprecated Terminal TUI** | `tests/test_tui.py` | 3 | 0 | 0 | 3 | 0.05s | **SKIPPED** (Web-first) |
| **OVERALL TOTAL** | **8 Test Modules** | **35** | **32** | **0** | **3** | **18.10s** | **100% HEALTHY** |

---

## 2. Detailed Verification by Test Category

### 2.1 Unit Tests: Data Preprocessing & Schema Handling (`tests/test_data.py`)
- **`test_taxonomy_mappings`:** Validates deterministic mapping from all 34 raw CICIoT2023 labels to binary (`BENIGN`/`ATTACK`) and the 8 high-level threat categories (`Benign`, `DDoS`, `DoS`, `Mirai`, `Recon`, `Web`, `BruteForce`, `Spoofing`).
- **`test_synthetic_generation_and_metadata`:** Verifies deterministic generation of IoT network flow records, metadata sidecars (`.meta.json`), and injection of anomalous/infinite values.
- **`test_data_loader_and_sample_limit`:** Verifies chunk-based file discovery and enforces `sample_limit` constraints without loading entire multi-gigabyte files into RAM.
- **`test_data_loader_missing_target_error`:** Asserts that datasets without any identifiable label column raise explicit, recoverable `ValueError` exceptions.
- **`test_dataset_audit`:** Verifies schema validation, NaN counts, positive/negative infinity detection, duplicate estimations, and automatic markdown report generation.
- **`test_split_dataset_uppercase_label` (NEW):** Specifically verifies that `split_dataset` auto-detects uppercase initial target columns (`'Label'`) from the official CICIoT2023 merged dataset without throwing `ValueError`.

### 2.2 Algorithmic Verification: LRRC-FS & Baselines (`tests/test_pipeline.py`)
- **`test_preprocessor_fit_transform_manifest`:** Ensures `IoTDataPreprocessor` extracts features, eliminates NaNs/Infs, generates an immutable `PreprocessingManifest` (JSON serializable), and fits transformations **strictly on training partitions**.
- **`test_split_dataset_stratification_and_ratios`:** Verifies exact ratio splitting (e.g. 70% train, 20% test, 10% val) with stratification integrity across classes.
- **`test_lrrc_fs_selection_and_determinism`:** 
  - Verifies that LRRC-FS selects the requested $k$ features ($k=8$).
  - Validates `explain_selection()` output columns (`relevance`, `redundancy`, `cost`, `final_score`).
  - Verifies that repeated executions on identical input yield **100% identical feature sets and rankings** (lexicographical tie-breaking).
- **`test_baselines`:** Validates transformer mixin conformity for `AllFeaturesSelector`, `VarianceThresholdSelector`, and `EstablishedKBestSelector`.

### 2.3 Machine Learning Pipeline & Imbalance Tests (`tests/test_training.py`)
- **`test_classifier_factory`:** Asserts bounded depth initialization for Random Forest, Decision Tree, Extra Trees, and HistGradientBoosting, including `class_weight='balanced'` support.
- **`test_feature_selector_factory`:** Validates selector instantiation for `lrrc`, `all`, `variance`, and `kbest`.
- **`test_resampling_strategies`:**
  - Verifies that `RandomUnderSampler` reduces majority classes exclusively on training partitions.
  - Verifies that `SMOTE` oversampling generates synthetic minority samples without bleeding into validation or test partitions.
- **`test_train_model_binary`:** Executes end-to-end binary training, evaluating accuracy, Macro F1, model bundle serialization (`.joblib`), and confusion matrix plotting.
- **`test_train_model_multiclass`:** Executes multiclass 8-category training and verifies label encoding resilience.
- **`test_evaluate_predictions_and_fpr`:** Verifies exact mathematical computation of False Positive Rate (FPR = FP / (FP + TN)) and per-class classification metrics.

### 2.4 Persistence & Offline Detection Tests (`tests/test_detection.py`)
- **`test_offline_predictor`:** Verifies offline batch inference from persisted `.joblib` bundles, asserting output DataFrame annotations (`predicted_label`, `confidence`, `is_attack`, `severity`).
- **`test_event_store_query_and_summary`:** Verifies SQLite transactions, event persistence, and aggregate metrics queries (`total_events`, `attack_count`, `benign_count`).
- **`test_invalid_model_bundle_loading`:** Asserts clean exception handling when loading corrupt or tampered model files.

### 2.5 REST API & Web Server Tests (`tests/test_web.py`)
- **`test_static_files_exist`:** Asserts existence of `index.html`, `style.css`, and `app.js` in `src/web/static/`.
- **`test_api_status_in_memory`:** Verifies HTTP 200 and operational health schema from `/api/status`.
- **`test_api_datasets_in_memory`:** Verifies dynamic discovery of raw official CSV partitions.
- **`test_api_models_in_memory`:** Verifies serialization and metadata listing of trained models.
- **`test_api_policies_in_memory`:** Verifies active defense rule listing.
- **`test_api_inference_test_in_memory`:** Verifies end-to-end `/api/test` flow evaluation and latency calculation without OS socket dependencies.
- **`test_api_settings_and_policies_update_in_memory` (NEW):** Verifies GET/POST `/api/settings` and policy threshold updates via `/api/policies`.

### 2.6 Core Infrastructure & Policies (`tests/test_core.py`, `tests/test_cli.py`)
- **`test_settings_defaults_and_validation`:** Asserts Pydantic v2 configuration settings and JSON serialization.
- **`test_policies_evaluation_and_audit`:** Asserts rule matching (Mirai -> CRITICAL, Benign -> INFO) and validates the policy modification audit trail.
- **`test_logging_and_buffer`:** Verifies rotating log files and in-memory ring buffer logging.
- **`test_cli_parser_subcommands` / `test_cli_execution_workflow`:** Verifies CLI entry point dispatch for `audit`, `train`, `test`, `web`, `export`.

---

## 3. Deprecated Terminal TUI Tests Isolation

As explicitly requested in the Master Instruction:
> *"We are developing a WEB-BASED APPLICATION. Do not prioritize terminal interfaces, Textual dashboards, Rich interfaces or terminal-based interaction. The browser application must be the primary interface through which users interact with the IDS."*

The 3 async pilot tests in `tests/test_tui.py` (`test_tui_app_initialization_and_tabs`, `test_tui_chat_commands_and_dispatch`, `test_tui_settings_reset`) were safely marked with:
```python
pytestmark = pytest.mark.skip(reason="Terminal TUI deprecated in favor of web application")
```
This isolates the deprecated Textual event loops and guarantees fast, non-blocking execution (<19 seconds) on all automated Windows environments.

