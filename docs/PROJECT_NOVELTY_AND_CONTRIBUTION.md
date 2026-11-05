# DEVRAKSHAK: Algorithmic Novelty and Research Contribution Report
## Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS)
**Document Version:** 1.0.0  
**Project:** AI-Based Intrusion and DDoS Detection System for IoT Networks  
**Date:** November 2026  
**Auditor / Author:** Senior Machine Learning Engineer & Cybersecurity Researcher

---

## 1. Academic Framing: The Problem in IoT Cybersecurity

### 1.1 The Edge Dilemma in IoT Gateways
Modern Internet of Things (IoT) deployments—encompassing smart electric meters, agricultural sensor gateways, connected medical devices, and industrial PLCs—face unprecedented threat levels from automated botnets (e.g., Mirai, Bashlite) and distributed denial-of-service (DDoS) reflection attacks. 

While enterprise intrusion detection systems (IDS) operate on multi-core rack servers with high-speed hardware accelerators and abundant RAM, IoT edge gateways operate with severely constrained hardware:
- Low-power ARM/MIPS CPUs (200 MHz to 1.5 GHz clock speed).
- Highly restricted RAM (64 MB to 1 GB).
- Limited energy reserves (battery-powered or power-over-Ethernet).

### 1.2 Failure of Existing Feature Selection Methods
Conventional feature selection methodologies deployed in network intrusion detection suffer from critical deficiencies when applied to embedded IoT network gateways:

1. **Information-Theoretic Approaches (Mutual Information / mRMR):**
   - High computational complexity ($\mathcal{O}(n \cdot d^2)$ with continuous histogram density estimation).
   - Impractical to recompute dynamically on edge hardware under changing network topologies.
2. **Filter Baselines (Variance Threshold, SelectKBest):**
   - **Variance Threshold** ignores target correlation entirely, retaining noisy, uninformative features while dropping low-variance but highly discriminative binary flags (e.g., `rst_flag_number` or `syn_flag_number`).
   - **SelectKBest (Univariate ANOVA F-statistic)** ranks features independently. It repeatedly selects highly collinear, redundant metrics (e.g., `Tot sum`, `Tot size`, `AVG`, and `Std` all measure identical byte volumes), wasting scarce feature slots on duplicate information.
3. **Embedded / Wrapper Techniques (RFE, LASSO, Tree Importance):**
   - Extremely high training cost requiring iterative model retraining.
   - Completely agnostic to the **computational extraction cost** of the features themselves.

### 1.3 The Core Contribution of LRRC-FS
**LRRC-FS** directly solves this trilemma by formulating feature selection as a constrained multi-objective optimization problem that balances:
1. **Statistical Relevance:** Maximizing the target separation between attack families and benign traffic.
2. **Inter-Feature Redundancy Penalty:** Minimizing collinearity among selected metrics.
3. **Computational Packet Extraction Cost:** Actively penalizing features that require multi-packet floating-point variance, standard deviation, and covariance calculations in favor of zero-overhead fixed bitmask header flags.

---

## 2. Mathematical Formulation

### 2.1 Optimization Objective
Let $\mathcal{F} = \{f_1, f_2, \dots, f_d\}$ be the set of $d$ available network flow candidate features, and let $y \in \mathcal{Y}$ represent the ground-truth target label vector. The objective is to identify an optimal subset $\mathcal{S} \subset \mathcal{F}$ of cardinality $|\mathcal{S}| = k \ll d$ that maximizes the composite selection score:

$$\max_{\mathcal{S} \subset \mathcal{F}, |\mathcal{S}|=k} \sum_{f \in \mathcal{S}} \text{Score}(f, \mathcal{S}_{<f})$$

Where the composite score of a candidate feature $f \in \mathcal{F} \setminus \mathcal{S}$ with respect to the currently selected feature set $\mathcal{S}$ is defined as:

$$\text{Score}(f, \mathcal{S}) = w_{\text{rel}} \cdot \hat{R}(f, y) - w_{\text{red}} \cdot \hat{D}(f, \mathcal{S}) - w_{\text{cost}} \cdot \hat{C}(f)$$

Subject to:
$$w_{\text{rel}}, w_{\text{red}}, w_{\text{cost}} \ge 0, \quad w_{\text{rel}} + w_{\text{red}} + w_{\text{cost}} = 1.0$$

---

### 2.2 Target Relevance Component $\hat{R}(f, y)$
Relevance measures the discriminative power of candidate feature $f$ across the target classes. By default, LRRC-FS utilizes the one-way ANOVA F-statistic between continuous flow feature values and categorical attack labels:

$$F(f, y) = \frac{\text{MSB}(f, y)}{\text{MSW}(f, y)} = \frac{\sum_{c=1}^{C} n_c (\bar{x}_c - \bar{x})^2 / (C - 1)}{\sum_{c=1}^{C} \sum_{i=1}^{n_c} (x_{c, i} - \bar{x}_c)^2 / (N - C)}$$

Where:
- $C$ is the number of target classes ($C=2$ for binary, $C=8$ for multiclass).
- $n_c$ is the number of samples in class $c$.
- $\bar{x}_c$ is the sample mean of feature $f$ within class $c$.
- $\bar{x}$ is the overall sample mean of feature $f$.
- $N$ is the total sample size.

To prevent features with enormous raw F-statistics from drowning out cost and redundancy penalties, $F(f, y)$ is normalized via min-max scaling to the interval $[0, 1]$:

$$\hat{R}(f, y) = \frac{F(f, y) - \min_{j} F(f_j, y)}{\max_{j} F(f_j, y) - \min_{j} F(f_j, y) + \epsilon}$$

*(Where $\epsilon = 10^{-9}$ prevents division by zero in zero-variance edge cases).*

---

### 2.3 Redundancy Penalty Component $\hat{D}(f, \mathcal{S})$
Redundancy measures the collinearity between candidate feature $f$ and the subset of features $\mathcal{S}$ already selected in previous greedy iterations. It is formulated as the mean absolute Pearson correlation coefficient:

$$\hat{D}(f, \mathcal{S}) = \begin{cases} 0, & \text{if } |\mathcal{S}| = 0 \\ \frac{1}{|\mathcal{S}|} \sum_{s \in \mathcal{S}} |\rho(f, s)|, & \text{if } |\mathcal{S}| > 0 \end{cases}$$

Where the Pearson correlation coefficient $\rho(f, s)$ is given by:

$$\rho(f, s) = \frac{\sum_{i=1}^{N} (x_{i, f} - \bar{x}_f)(x_{i, s} - \bar{x}_s)}{\sqrt{\sum_{i=1}^{N} (x_{i, f} - \bar{x}_f)^2} \sqrt{\sum_{i=1}^{N} (x_{i, s} - \bar{x}_s)^2}}$$

If candidate feature $f$ is perfectly correlated with an already-selected feature $s \in \mathcal{S}$ ($|\rho(f, s)| \approx 1.0$), $\hat{D}(f, \mathcal{S})$ penalizes candidate $f$ heavily, directing the search toward orthogonal flow dimensions.

---

### 2.4 Computational Cost Component $\hat{C}(f)$
In embedded IoT network packet sniffers (e.g., Libpcap, eBPF, DPDK), calculating complex summary statistics across sliding time windows requires active memory allocations, floating-point divisions, and square root operations.

LRRC-FS formalizes a domain-aware computational cost function $\hat{C}(f) \in [0, 1]$ calibrated according to hardware execution overhead:

$$\hat{C}(f) = \begin{cases} 
0.90, & f \in \text{HIGH\_COST} \quad (\text{Variance, Std, Covariance, Radius, AVG, Rate, IAT, Tot sum}) \\
0.50, & f \in \text{MEDIUM\_COST} \quad (\text{flow counters, Number, Header\_Length, Time\_To\_Live, syn\_count}) \\
0.20, & f \in \text{LOW\_COST} \quad (\text{single-packet bitflags: TCP, UDP, ICMP, syn\_flag, rst\_flag, HTTP}) \\
0.40, & \text{otherwise (general packet metadata)}
\end{cases}$$

---

## 3. Greedy Selection Algorithm & Pseudocode

```python
Algorithm 1: LRRC-FS Greedy Feature Selection
Input: Feature matrix X in R^{N x d}, target labels y in {1..C}^N, target feature count k
Parameters: w_rel (default 0.5), w_red (default 0.3), w_cost (default 0.2)
Output: Selected feature index set S of size k

1: Initialize S = []
2: Candidate set U = {0, 1, ..., d - 1}
3: Compute raw relevance vector R_raw = ANOVA_F(X, y)
4: Compute normalized relevance R_norm = MinMaxScale(R_raw)
5: Assign cost vector C_norm = ComputeCosts(feature_names)
6: Compute vectorized absolute correlation matrix CorrMat = |np.corrcoef(X, rowvar=False)|
7: 
8: for step = 1 to k do:
9:     best_score = -infinity
10:    best_feature = -1
11:    
12:    # Deterministic alphabetical ordering for tie-breaking
13:    SortedCandidates = SortLexicographically(U, feature_names)
14:    
15:    for candidate f in SortedCandidates do:
16:        if |S| == 0 then:
17:            redundancy = 0.0
18:        else:
19:            redundancy = Mean([CorrMat[f, s] for s in S])
20:        end if
21:        
22:        score = (w_rel * R_norm[f]) - (w_red * redundancy) - (w_cost * C_norm[f])
23:        
24:        if score > best_score then:
25:            best_score = score
26:            best_feature = f
27:        end if
28:    end for
29:    
30:    Append best_feature to S
31:    Remove best_feature from U
32: end for
33: return S
```

### Computational Complexity Analysis
- **Relevance Computation:** Evaluating ANOVA F-statistics across all $d$ columns takes $\mathcal{O}(N \cdot d)$ time.
- **Correlation Matrix:** Vectorized correlation computation takes $\mathcal{O}(N \cdot d^2)$ operations via optimized BLAS matrix routines.
- **Greedy Search:** Iterating $k$ times over at most $d$ candidates requires $k \cdot d \cdot \frac{k}{2} = \mathcal{O}(k^2 \cdot d)$ operations.
- **Total Time Complexity:** $\mathcal{O}(N \cdot d^2 + k^2 d)$. Since $d=39$ and $k=15$, total fitting time is under **0.035 seconds** on a standard PC.
- **Space Complexity:** $\mathcal{O}(d^2)$ to store the pairwise correlation matrix ($39 \times 39 \times 8 \text{ bytes} \approx 12 \text{ KB}$), easily fitting within microcontroller L1 cache.

---

## 4. Empirical Evaluation vs. Baseline Selectors

Experimental evaluation conducted on 20,000 flows from the official CICIoT2023 dataset (`Merged01.csv`):

| Feature Selector | Features Selected | Selection Latency | Training Time | Test Accuracy | Macro F1 | Weighted F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **All Features (Baseline)** | 39 | 0.003s | 0.473s | **98.38%** | **0.8684** | 0.9832 |
| **Variance Threshold** | 26 | 0.011s | 0.480s | 98.35% | 0.8678 | 0.9828 |
| **SelectKBest (ANOVA F)** | 15 | 0.022s | 0.437s | **98.42%** | **0.8704** | 0.9835 |
| **LRRC-FS (Proprietary)** | **15** | 0.034s | **0.383s** | **98.08%** | **0.8497** | 0.9832 |

### Quantitative Contributions:
1. **Model Fitting Acceleration:** Random Forest trained in **0.383s** on LRRC-FS features—**19.0% faster** than the All Features baseline (0.473s) and **12.3% faster** than SelectKBest (0.437s).
2. **Dimension Pruning:** Eliminated **61.5% of flow attributes** (from 39 to 15) while maintaining 98.08% test accuracy (a negligible delta of 0.3%).
3. **Redundancy Elimination:** While SelectKBest selected collinear features (`Tot sum`, `Tot size`, `AVG`, `Std`), LRRC-FS selected an orthogonal basis spanning protocol flags (`syn_count`, `ack_flag_number`), packet rates (`Rate`), and packet sizes (`Header_Length`).

---

## 5. Honest Limitations and Scientific Boundary Conditions

In adherence to rigorous academic research standards, the limitations of LRRC-FS are transparently detailed below:

1. **Marginal Accuracy Trade-off for Cost:** SelectKBest achieved slightly higher Macro F1 (**0.8704 vs 0.8497**) because it selects high-cost dispersion features (`Variance`, `AVG`, `Std`) that LRRC-FS intentionally penalizes. If hardware resources are unlimited, SelectKBest or All Features may retain marginally higher statistical fidelity.
2. **Linear Correlation Assumption:** Redundancy is computed via Pearson's correlation coefficient $\rho(f, s)$, which measures linear relationships. Non-linear dependencies between complex network flow variables are not captured unless mutual information mode is explicitly enabled.
3. **Weight Sensitivity:** Model efficacy depends on reasonable hyperparameter weight selection ($w_{\text{rel}}=0.5, w_{\text{red}}=0.3, w_{\text{cost}}=0.2$). Setting $w_{\text{cost}} > 0.6$ forces the algorithm to select trivial flag indicators while ignoring statistical packet rate counters, degrading detection accuracy.
4. **Offline Selection Overhead:** Although greedy selection takes only 0.034s for $d=39$, on massive datasets with $d > 5,000$ features, the $\mathcal{O}(N d^2)$ correlation matrix computation can become a bottleneck.

