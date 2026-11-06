# AI-Based Network Intrusion and DDoS Detection (CICIoT2023, offline)
## Research Contribution and Algorithmic Formulation Report
### Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS)

**Document Version:** 2.0.0  
**Project:** AI-Based Network Intrusion and DDoS Detection (CICIoT2023, offline)  
**Date:** November 2026  

---

## 1. Academic Contribution

We extend relevance-redundancy feature selection with a feature-computation-cost term and a stability term, evaluated with a leak-free protocol (deduplication, file-level held-out test, natural test distribution) on CICIoT2023.

### Core Formulation:
Conventional feature selection baselines (e.g., SelectKBest, Variance Threshold) evaluate statistical metrics in isolation without accounting for the packet-processing effort required to compute features from raw network traffic, nor the stability of selections across data subsamples.

**LRRC-FS** addresses this by optimizing a 4-term objective:
1. **Statistical Relevance:** Maximizing target class separation via normalized ANOVA F-statistics.
2. **Redundancy Penalty:** Minimizing inter-feature collinearity using mean absolute Pearson correlation.
3. **Feature Computation Cost:** Penalizing features requiring rolling-window floating-point dispersion calculations in favor of low-cost packet header flags.
4. **Bootstrap Stability:** Rewarding features that are consistently chosen across multiple random subsamples of the training data.

---

## 2. Mathematical Formulation

Let $\mathcal{F} = \{f_1, f_2, \dots, f_d\}$ represent the set of candidate network flow features, and let $y$ represent the ground-truth target vector. To select a subset $\mathcal{S}$ of cardinality $|\mathcal{S}| = k$, candidate features $f \in \mathcal{F} \setminus \mathcal{S}$ are evaluated iteratively via the scoring function:

$$\text{Score}(f, \mathcal{S}) = w_{\text{rel}} \cdot \hat{R}(f, y) - w_{\text{red}} \cdot \hat{D}(f, \mathcal{S}) - w_{\text{cost}} \cdot \hat{C}(f) + w_{\text{stab}} \cdot \hat{s}(f)$$

Subject to non-negative weights summing to 1.0:
$$w_{\text{rel}} + w_{\text{red}} + w_{\text{cost}} + w_{\text{stab}} = 1.0$$
*(Defaults: $w_{\text{rel}}=0.4, w_{\text{red}}=0.25, w_{\text{cost}}=0.15, w_{\text{stab}}=0.2$)*

### 2.1 Target Relevance: $\hat{R}(f, y)$
Computed as the min-max normalized ANOVA F-statistic between candidate $f$ and label vector $y$:
$$\hat{R}(f, y) = \frac{F(f, y) - \min_{f'} F(f', y)}{\max_{f'} F(f', y) - \min_{f'} F(f', y) + \epsilon}$$

### 2.2 Redundancy Penalty: $\hat{D}(f, \mathcal{S})$
Calculated as the average absolute Pearson correlation between candidate $f$ and already-selected features:
$$\hat{D}(f, \mathcal{S}) = \frac{1}{|\mathcal{S}|} \sum_{s \in \mathcal{S}} |\rho(f, s)|, \quad \hat{D}(f, \emptyset) = 0$$

### 2.3 Feature Computation Cost: $\hat{C}(f)$
Assigned via hierarchical tiers based strictly on how features are computed from network packet headers:
- **0.2 (Protocol Flags & Simple Counters):** `TCP`, `UDP`, `ICMP`, `HTTP`, `HTTPS`, `DNS`, `syn_count`, `ack_flag_number`, `fin_count`, etc.
- **0.4 (Single-Packet Header Fields):** `Header_Length`, `Time_To_Live`, `Protocol Type`, `Duration`.
- **0.6 (Simple Window Aggregates):** `Tot sum`, `Min`, `Max`, `AVG`, `Tot size`, `Number`.
- **0.8 (Rate & Inter-Arrival Metrics):** `Rate`, `Srate`, `Drate`, `IAT`, `flow_duration`.
- **0.9 (Multi-Packet Dispersion Statistics):** `Std`, `Variance`, `Covariance`, `Radius`, `Magnitude`, `Weight`.
- **0.5:** Default for any unmapped column.

### 2.4 Bootstrap Selection Stability: $\hat{s}(f)$
Estimated by executing greedy selection over $B=10$ random bootstrap subsamples (sampling ratio 0.70):
$$\hat{s}(f) = \frac{1}{B} \sum_{b=1}^B \mathbb{I}(f \in \mathcal{S}_b)$$

---

## 3. Empirical Results and Trade-Off Analysis

Evaluated on the held-out test pool (`Merged54`–`Merged63`, 100,000 flows) across 3 random seeds:

| Method | Number of Features ($k$) | Test Macro F1 | Test Accuracy | Avg. Computation Cost |
| :--- | :--- | :--- | :--- | :--- |
| **All Features** | 39 | **0.8389** | **98.66%** | 0.479 |
| **LRRC-FS (with stability)** | 15 | **0.8362** | **98.65%** | **0.327** |
| **SelectKBest (ANOVA F)** | 15 | 0.8343 | 98.64% | 0.467 |
| **Variance Threshold** | 15 | 0.7170 | 97.42% | 0.280 |

### Trade-Off Discussion:
- **Accuracy / F1 Comparison:** LRRC-FS achieves **0.8362 Macro F1** compared to **0.8389** for All 39 Features (a difference of only 0.0027) and outperforms SelectKBest (0.8343) and Variance Threshold (0.7170).
- **Cost Reduction:** The average feature computation cost of the selected 15 features is **0.327** under LRRC-FS, compared to **0.479** for the full feature set (a **31.7% cost reduction**).
- **Feature Profile:** LRRC-FS actively penalizes expensive dispersion statistics (`Std`, `Variance`, `Covariance`) and selects low-overhead packet bitflags and header fields, yielding simpler and more stable feature sets without sacrificing detection efficacy.
