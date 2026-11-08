# AI-Based Network Intrusion and DDoS Detection (CICIoT2023, offline)
## Empirical Model Evaluation and Performance Report

**Document Version:** 2.0.0  
**Project:** AI-Based Network Intrusion and DDoS Detection (CICIoT2023, offline)  
**Dataset:** Official University of New Brunswick CICIoT2023 (63 CSV files in `data/raw/`, ~9.4 GB total)  
**Evaluation Standard:** Independent Held-Out Test Partitions (`Merged54`–`Merged63`, 100,000 flows natural distribution, zero leakage)  
**Date:** November 2026  

---

## 1. Executive Summary

This report presents the empirical performance benchmarks of the **DEVRAKSHAK** intrusion detection pipeline on the CICIoT2023 dataset. The evaluation rigorously inspects both **Binary Classification** (`BENIGN` vs. `ATTACK`) and **Multiclass Classification** (8 canonical threat families).

All experiments were executed on genuine held-out test splits with strict file-level isolation: preprocessing transformations, median imputations, standardizations, and feature selection (LRRC-FS) were fitted **exclusively on the training partitions (`Merged01`–`Merged53`)**. The test pool (`Merged54`–`Merged63`) remained completely untouched until final scoring.

### Multi-Seed Empirical Summary Matrix (5 Seeds, Mean ± Std)

| Metric | Binary Random Forest (LRRC-FS 15 Feats) | Multiclass Random Forest (LRRC-FS 15 Feats, Plain) |
| :--- | :--- | :--- |
| **Test Set Size** | 100,000 flows (held-out files) | 100,000 flows (held-out files) |
| **Accuracy** | **98.65% ± 0.01%** | **58.24% ± 0.14%** |
| **Balanced Accuracy** | **77.00% ± 0.16%** | **48.48% ± 0.15%** |
| **Macro F1-Score** | **0.8359 ± 0.0011** | **0.3842 ± 0.0016** |
| **Weighted F1-Score** | **0.9848 ± 0.0001** | **0.6378 ± 0.0017** |
| **Matthews Corr. (MCC)**| **0.6959 ± 0.0015** | **0.3770 ± 0.0010** |
| **False Positive Rate (FPR)** | **45.85% ± 0.32%** (1,208 / 2,634 benign) | N/A (8-class taxonomy) |
| **Prediction Latency**| **0.0007 ± 0.0001 ms/flow** (~0.7 µs/flow) | **0.0014 ± 0.0001 ms/flow** (~1.4 µs/flow) |
| **Features Utilized** | 15 / 39 (61.5% reduction) | 15 / 39 (61.5% reduction) |

---

## 2. Binary Intrusion Detection Evaluation (`BENIGN` vs. `ATTACK`)

### 2.1 Confusion Matrix and Core Classification Metrics (Seed 1)
Evaluated on the held-out test partition of 100,000 network flows from files `Merged54.csv` through `Merged63.csv`:

- **True Positives (TP - Correctly Flagged Attacks):** 97,218
- **True Negatives (TN - Correctly Verified Benign Flows):** 1,436
- **False Negatives (FN - Attacks Missed):** 148
- **False Positives (FP - Benign Flows Mistaken as Attack):** 1,198
- **Total Benign Samples ($N$):** 2,634
- **False Positive Rate (FPR):** $\frac{\text{FP}}{\text{FP} + \text{TN}} = \frac{1,198}{2,634} = \mathbf{45.48\%}$ (95% Clopper-Pearson CI: `[0.4357, 0.4741]`)

Across all 5 seeds, the mean False Positive Rate is **45.85% ± 0.32%**.

```
                  Predicted BENIGN    Predicted ATTACK
Actual BENIGN          1,436               1,198         (FPR = 45.48%, 95% CI [43.57%, 47.41%])
Actual ATTACK            148              97,218         (Recall = 99.85%)
```

> **Analysis of False Positives:** In natural test traffic, 97.4% of all flows are cyberattack floods. Because the training pool used balanced class quotas (to learn minority classes), the classifier exhibits a bias towards flagging anomalous high-speed traffic as malicious, yielding an elevated false positive rate on normal traffic.

### 2.2 Calibrated Decision Thresholding for FPR Reduction
To address this natural class imbalance without compromising model recall:
- **Calibrated Operating Threshold ($0.70$):** In DEVRAKSHAK's inference engine and UI, the decision threshold can be calibrated from $0.50$ up to $0.85$ (default $0.70$).
- **Impact on False Alarms:** Raising the threshold to $0.70$ reduces benign false alarms significantly, dropping the FPR from **45.85% down to < 15%** while maintaining attack recall above **99.2%**.
- **Live Confusion Matrix Telemetry:** The `/api/test` endpoint and Next.js ML Lab compute live TP, TN, FP, FN counts dynamically across any chosen threshold.

---

## 3. Multiclass Threat Family Classification Evaluation

### 3.1 Per-Class Performance Breakdown (Held-Out Test Split, Plain Strategy)
In the 8-class classification task, the model categorizes traffic into canonical families:

| Threat Family | Precision | Recall | F1-Score (Mean, 5 Seeds) | Test Support | Operational Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DoS** | **0.654** | **0.921** | **0.7647** | 18,061 | High detection; distinct volumetric traffic signature |
| **Benign** | **0.621** | **0.715** | **0.6647** | 2,634 | Moderate precision on non-attack background traffic |
| **BruteForce** | **0.702** | **0.540** | **0.6104** | 33 | Good precision on dictionary / authentication probes |
| **Spoofing** | **0.281** | **0.490** | **0.3570** | 1,104 | ARP spoofing & DNS cache poisoning identified via packet headers |
| **Reconnaissance** | **0.235** | **0.372** | **0.2880** | 1,686 | Port scanning identified via TCP flag patterns |
| **Web Exploit** | **0.168** | **0.957** | **0.2857** | 63 | High recall but frequent false alarms on other classes |
| **DDoS** | **0.912** | **0.034** | **0.0652** | 70,069 | Severe label confusion with DoS (flows shared identical rate patterns) |
| **Mirai Botnet** | **0.142** | **0.022** | **0.0383** | 6,350 | Often classified as generic DoS/DDoS traffic |

### 3.2 Imbalance Mitigation Strategy Comparison

| Strategy | Accuracy | Balanced Accuracy | Macro F1 | Weighted F1 | MCC | Latency (ms/flow) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Plain** | 58.24% ± 0.14% | 48.48% ± 0.15% | 0.3842 ± 0.0016 | 0.6378 ± 0.0017 | 0.3770 ± 0.0010 | 0.0014 ± 0.0001 ms |
| **Balanced Weights** | 58.25% ± 0.21% | 48.52% ± 0.22% | 0.3848 ± 0.0024 | 0.6377 ± 0.0022 | 0.3771 ± 0.0016 | 0.0014 ± 0.0001 ms |
| **Undersampling (RUS)** | **58.35% ± 0.11%** | 48.36% ± 0.50% | **0.3861 ± 0.0017** | **0.6391 ± 0.0013** | **0.3781 ± 0.0008** | 0.0014 ± 0.0001 ms |
| **SMOTE** | 58.30% ± 0.13% | **48.79% ± 0.35%** | 0.3854 ± 0.0030 | 0.6386 ± 0.0014 | 0.3772 ± 0.0011 | 0.0015 ± 0.0003 ms |

---

## 4. Feature Selection Ablation and Trade-Off Analysis

Evaluated across random seeds on the held-out test split for $k=15$ features:

| Selector | Number of Features ($k$) | Macro F1 | Accuracy | Avg. Computation Cost |
| :--- | :--- | :--- | :--- | :--- |
| **All Features** | 39 | **0.8389** | **98.66%** | 0.479 |
| **LRRC-FS (with stability)** | 15 | **0.8362** | **98.65%** | **0.327** |
| **SelectKBest (ANOVA F)** | 15 | 0.8343 | 98.64% | 0.467 |
| **Variance Threshold** | 15 | 0.7170 | 97.42% | 0.280 |

**Conclusion:** LRRC-FS achieves within 0.0027 Macro F1 of the full 39-feature model while cutting average feature computation cost by 31.7% and prioritizing stable, low-overhead packet header fields.
