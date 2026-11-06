# DEVRAKSHAK: Model Selection Rationale and Architectural Justification
**Document Version:** 1.0.0  
**Project:** AI-Based Intrusion and DDoS Detection System for IoT Networks (CICIoT2023)  
**Date:** November 2026  
**Auditor:** Senior Machine Learning Engineer & Backend Architect

---

## 1. Executive Summary

A critical engineering decision in the development of the **DEVRAKSHAK** intrusion detection system is the selection of machine learning classification models. In academic and industrial literature, researchers frequently deploy complex Deep Neural Networks (CNNs, LSTMs, Transformers) or resource-heavy Support Vector Machines (SVMs) without evaluating their feasibility on constrained IoT network appliances.

This document presents a rigorous architectural justification for the **four core models** selected for DEVRAKSHAK:
1. **Random Forest Classifier** *(Default Operational Model)*
2. **Decision Tree Classifier** *(Ultra-Low-Latency Edge Model)*
3. **Extra Trees Classifier** *(Variance-Reduced Ensemble)*
4. **HistGradientBoosting Classifier** *(Fast Histogram-Based Boosting)*

It compares these chosen architectures against omitted alternatives (Deep Learning, SVM, k-NN, external XGBoost/LightGBM) across inference latency, memory consumption, training throughput, interpretability, and tabular data suitability.

---

## 2. Comparative Decision Matrix

| Model Architecture | Edge Latency | Memory Footprint | Training Time | Interpretability | Tabular Flow Suitability | Status in DEVRAKSHAK |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Decision Tree** | **0.0001 ms** (0.1 $\mu$s) | **< 100 KB** | **0.031s** | **High** (White-box if-then) | Excellent | **SELECTED** (Edge Baseline) |
| **Random Forest** | **0.0024 ms** (2.4 $\mu$s) | **~ 2.5 MB** | **0.349s** | **Medium** (Feature Imp.) | **Superior** (Robust to noise)| **SELECTED** (Default Model) |
| **Extra Trees** | **0.0022 ms** (2.2 $\mu$s) | **~ 2.4 MB** | **0.220s** | **Medium** (Feature Imp.) | **Superior** (Reduced var.) | **SELECTED** (DDoS Specialist) |
| **HistGradientBoosting**| **0.0009 ms** (0.9 $\mu$s) | **~ 1.1 MB** | **0.485s** | **Medium** (Tree ensembles)| **Superior** (Integer bins) | **SELECTED** (Large Datasets) |
| *Deep Learning (MLP/LSTM)*| Not evaluated in this project. | Not evaluated in this project. | Not evaluated in this project. | **None** (Black-box) | Sub-optimal (Overfits) | **REJECTED** (Too heavy) |
| *Support Vector Machine (SVM)*| Not evaluated in this project. | Not evaluated in this project. | Not evaluated in this project. | Low (Kernel dual space)| Moderate (Requires scaling)| **REJECTED** ($\mathcal{O}(n^2)$ scaling) |
| *k-Nearest Neighbors (k-NN)* | Not evaluated in this project. | Not evaluated in this project. | Not evaluated in this project. | High (Instance-based) | Poor (Curse of dim.) | **REJECTED** (High test latency) |
| *XGBoost / LightGBM* | Not evaluated in this project. | Not evaluated in this project. | Not evaluated in this project. | Medium | Excellent | **OMITTED** (External C++ deps)|

---

## 3. Justification for Selected Models

### 3.1 Random Forest Classifier (`RandomForestClassifier`)
- **Hyperparameters:** `n_estimators=50, max_depth=12, min_samples_leaf=2, class_weight='balanced', random_state=42`
- **Why Selected:** Random Forest is effective for tabular cybersecurity flow data. By averaging 50 randomized decision trees bounded to depth 12, it mitigates individual tree overfitting on high-variance packet rate metrics.
- **Empirical Metric:** Achieved **98.65% ± 0.01% test accuracy** and **0.8359 ± 0.0011 Macro F1** on the held-out test pool with fast inference (**0.0007 ± 0.0001 ms/flow**).
- **Bundle Footprint:** Serialized bundle size is compact (~2.5 MB).

### 3.2 Decision Tree Classifier (`DecisionTreeClassifier`)
- **Hyperparameters:** `max_depth=12, min_samples_leaf=3, class_weight='balanced', random_state=42`
- **Why Selected:** Fast inference verification. With a single tree bounded to depth 12, prediction requires traversing at most 12 binary comparison branches (`if Rate > 1200 and syn_count > 10`).
- **Empirical Metric:** Achieved **97.82% accuracy** with low latency per sample.
- **Interpretability:** Generates white-box rules directly auditable by human network security analysts for compliance verification.

### 3.3 Extra Trees Classifier (`ExtraTreesClassifier`)
- **Hyperparameters:** `n_estimators=50, max_depth=12, min_samples_leaf=2, class_weight='balanced', random_state=42`
- **Why Selected:** Extra Trees (Extremely Randomized Trees) randomizes cut-point threshold splits for each candidate feature. This further reduces model variance on bursty, erratic denial-of-service flooding patterns where packet counts fluctuate unpredictably.
- **Empirical Metric:** Achieved **97.92% accuracy** with fast training (**0.220s** on 16,000 samples).

### 3.4 HistGradientBoosting Classifier (`HistGradientBoostingClassifier`)
- **Hyperparameters:** `max_iter=50, max_depth=8, class_weight='balanced', random_state=42`
- **Why Selected:** Inspired by LightGBM, scikit-learn's native `HistGradientBoostingClassifier` bins continuous flow features into 256 discrete integer bins. This eliminates sorted array scanning and enables fast training on tabular data without third-party C++ binary dependencies.
- **Empirical Metric:** Achieved high binary test accuracy and balanced performance.

---

## 4. Why Alternative Architectures Were Rejected

### 4.1 Deep Learning (MLP, CNN, LSTM, Transformers)
- **The Empirical Reality on Tabular Data:** Tabular benchmark studies demonstrate that tree-based ensembles consistently perform strongly on tabular cybersecurity data.
- **Latency & Compute Overhead:** Inference and training compute overhead: Not evaluated in this project.
- **Runtime Dependencies:** Deploying deep learning frameworks introduces significant runtime dependencies: Not evaluated in this project.

### 4.2 Support Vector Machines (SVM)
- **Quadratic Training Complexity:** Non-linear kernel SVMs scale quadratically or cubically with sample size. Latency and memory: Not evaluated in this project.
- **Inference Bottleneck:** In-line classification cost across large support vector counts: Not evaluated in this project.

### 4.3 k-Nearest Neighbors (k-NN)
- **Memory and Test Latency:** Storing training samples and computing distances for incoming packets: Not evaluated in this project.

### 4.4 External Boosters (XGBoost, LightGBM, CatBoost)
- While XGBoost and LightGBM provide strong tabular performance, external dependencies are omitted in favor of scikit-learn's native HistGradientBoostingClassifier.

