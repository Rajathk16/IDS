"""Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS).

A transparent, greedy feature-selection algorithm for tabular network intrusion detection.
Balances statistical target relevance, inter-feature redundancy penalty, computational
extraction/computation cost, and empirical selection stability.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import f_classif, mutual_info_classif
from src.core.logging_config import get_logger

logger = get_logger("lrrc_feature_selector")

# Feature extraction/computation cost dictionary
FEATURE_COST = {
    # 0.2: Protocol flags / binary indicators / simple counters
    "TCP": 0.2, "UDP": 0.2, "ICMP": 0.2, "HTTP": 0.2, "HTTPS": 0.2,
    "DNS": 0.2, "Telnet": 0.2, "SMTP": 0.2, "SSH": 0.2, "IRC": 0.2,
    "DHCP": 0.2, "ARP": 0.2, "IPv": 0.2, "LLC": 0.2, "IGMP": 0.2,
    "syn_flag_number": 0.2, "ack_flag_number": 0.2, "fin_flag_number": 0.2,
    "rst_flag_number": 0.2, "psh_flag_number": 0.2, "urg_flag_number": 0.2,
    "ece_flag_number": 0.2, "cwr_flag_number": 0.2,
    "syn_count": 0.2, "ack_count": 0.2, "fin_count": 0.2, "urg_count": 0.2, "rst_count": 0.2,
    # 0.4: Single-packet header fields  
    "Header_Length": 0.4, "Protocol Type": 0.4, "Time_To_Live": 0.4,
    "Duration": 0.4,
    # 0.6: Simple window aggregates
    "Tot sum": 0.6, "Min": 0.6, "Max": 0.6, "AVG": 0.6, "Tot size": 0.6,
    "Number": 0.6, "Pkt_SIZE": 0.6,
    # 0.8: Rate / inter-arrival features
    "Rate": 0.8, "Srate": 0.8, "Drate": 0.8,
    "flow_duration": 0.8, "IAT": 0.8,
    # 0.9: Dispersion statistics
    "Std": 0.9, "Variance": 0.9, "Covariance": 0.9, "Radius": 0.9,
    "Magnitude": 0.9, "Magnitue": 0.9, "Weight": 0.9,
}
DEFAULT_COST = 0.5


class LRRCSFeatureSelector(BaseEstimator, TransformerMixin):
    """
    Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS).
    
    Mathematical Formulation:
      Score(f) = w_rel * R_norm(f) - w_red * D(f, S) - w_cost * C_norm(f) + w_stab * s(f)
    
    Where:
      - R_norm(f) in [0, 1]: Target relevance via normalized ANOVA F-statistic or Mutual Information.
      - D(f, S) in [0, 1]: Mean absolute Pearson correlation between candidate f and already selected features S.
      - C_norm(f) in [0, 1]: Computational feature extraction/computation cost.
      - s(f) in [0, 1]: Empirical selection stability score across bootstrap subsamples.
      - w_rel, w_red, w_cost, w_stab: Configurable non-negative weights.
    
    Greedy Selection:
      Iteratively selects the candidate feature maximizing Score(f) with deterministic tie-breaking.
    """

    def __init__(
        self,
        n_features_to_select: int = 15,
        relevance_weight: float = 0.5,
        redundancy_weight: float = 0.3,
        cost_weight: float = 0.2,
        relevance_metric: str = "f_classif",  # "f_classif" or "mutual_info"
        random_state: int = 42
    ):
        self.n_features_to_select = n_features_to_select
        self.relevance_weight = relevance_weight
        self.redundancy_weight = redundancy_weight
        self.cost_weight = cost_weight
        self.relevance_metric = relevance_metric
        self.random_state = random_state

        # Fitted state
        self.feature_names_in_: List[str] = []
        self.selected_features_: List[str] = []
        self.selected_indices_: List[int] = []
        self.relevance_scores_: Dict[str, float] = {}
        self.normalized_relevance_: Dict[str, float] = {}
        self.cost_scores_: Dict[str, float] = {}
        self.stability_scores_: Dict[str, float] = {}
        self.selection_history_: List[Dict[str, Union[str, float, int]]] = []
        self.fit_time_seconds_: float = 0.0

    def _compute_relevance(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Compute statistical relevance between candidate features and target."""
        if self.relevance_metric == "mutual_info":
            scores = mutual_info_classif(X, y, random_state=self.random_state)
        else:
            f_scores, _ = f_classif(X, y)
            scores = np.nan_to_num(f_scores, nan=0.0, posinf=1e6, neginf=0.0)
        return scores

    def _compute_costs(self, feature_names: List[str]) -> np.ndarray:
        """Assign normalized computational cost using FEATURE_COST dictionary."""
        costs = np.zeros(len(feature_names), dtype=np.float64)
        for i, feat in enumerate(feature_names):
            if feat in FEATURE_COST:
                costs[i] = FEATURE_COST[feat]
            else:
                # Case-insensitive lookup fallback
                found = False
                for k, v in FEATURE_COST.items():
                    if k.lower() == feat.lower():
                        costs[i] = v
                        found = True
                        break
                if not found:
                    costs[i] = DEFAULT_COST
        return costs

    def _greedy_select(
        self,
        norm_relevance: np.ndarray,
        costs: np.ndarray,
        corr_matrix: np.ndarray,
        feature_names: List[str],
        k: int,
        w_rel: float,
        w_red: float,
        w_cost: float,
        w_stab: float = 0.0,
        stability_scores: Optional[Dict[str, float]] = None
    ) -> Tuple[List[int], List[str], List[Dict[str, Union[str, float, int]]]]:
        """Run deterministic greedy selection with given weights."""
        n_features = len(feature_names)
        selected_indices: List[int] = []
        selected_names: List[str] = []
        candidate_indices = set(range(n_features))
        history: List[Dict[str, Union[str, float, int]]] = []

        for step in range(1, k + 1):
            best_idx = -1
            best_score = -float("inf")
            best_metrics: Dict[str, float] = {}

            # Sort candidate indices for deterministic tie-breaking (by feature name)
            sorted_candidates = sorted(candidate_indices, key=lambda idx: feature_names[idx])

            for idx in sorted_candidates:
                rel = norm_relevance[idx]
                cost = costs[idx]
                feat_name = feature_names[idx]

                if len(selected_indices) == 0:
                    red = 0.0
                else:
                    red = float(np.mean([corr_matrix[idx, s] for s in selected_indices]))

                stab = float(stability_scores.get(feat_name, 0.0)) if stability_scores else 0.0

                score = (
                    (w_rel * rel)
                    - (w_red * red)
                    - (w_cost * cost)
                    + (w_stab * stab)
                )

                if score > best_score:
                    best_score = score
                    best_idx = idx
                    best_metrics = {
                        "relevance": float(rel),
                        "redundancy": float(red),
                        "cost": float(cost),
                        "final_score": float(score)
                    }
                    if stability_scores is not None:
                        best_metrics["stability"] = float(stab)

            if best_idx != -1:
                selected_indices.append(best_idx)
                chosen_name = feature_names[best_idx]
                selected_names.append(chosen_name)
                candidate_indices.remove(best_idx)

                history.append({
                    "step": step,
                    "feature": chosen_name,
                    "index": best_idx,
                    **best_metrics
                })

        return selected_indices, selected_names, history

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        use_stability: bool = False,
        n_bootstrap: int = 10,
        bootstrap_frac: float = 0.7
    ) -> LRRCSFeatureSelector:
        """
        Execute greedy LRRC-FS selection.
        Fit strictly on the training partition to prevent information leakage.
        """
        t0 = time.perf_counter()

        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = list(X.columns)
            X_mat = X.to_numpy(dtype=np.float64)
        else:
            X_mat = np.asarray(X, dtype=np.float64)
            if feature_names is not None:
                self.feature_names_in_ = list(feature_names)
            else:
                self.feature_names_in_ = [f"feat_{i}" for i in range(X_mat.shape[1])]

        n_samples, n_features = X_mat.shape
        k = min(self.n_features_to_select, n_features)

        # Impute any residual NaNs for safety
        if np.isnan(X_mat).any():
            col_medians = np.nanmedian(X_mat, axis=0)
            inds = np.where(np.isnan(X_mat))
            X_mat[inds] = np.take(np.nan_to_num(col_medians, nan=0.0), inds[1])

        # 1. Compute and normalize relevance
        raw_relevance = self._compute_relevance(X_mat, y)
        min_rel = np.min(raw_relevance)
        max_rel = np.max(raw_relevance)
        denom = (max_rel - min_rel) if (max_rel - min_rel) > 1e-9 else 1.0
        norm_relevance = (raw_relevance - min_rel) / denom

        for i, name in enumerate(self.feature_names_in_):
            self.relevance_scores_[name] = float(raw_relevance[i])
            self.normalized_relevance_[name] = float(norm_relevance[i])

        # 2. Compute normalized costs
        costs = self._compute_costs(self.feature_names_in_)
        for i, name in enumerate(self.feature_names_in_):
            self.cost_scores_[name] = float(costs[i])

        # 3. Vectorized absolute correlation matrix
        with np.errstate(all="ignore"):
            corr_raw = np.corrcoef(X_mat, rowvar=False)
        corr_matrix = np.nan_to_num(np.abs(corr_raw), nan=0.0, posinf=0.0, neginf=0.0)

        # 4. Optional Stability Estimation via Bootstrap Sub-sampling
        if use_stability and n_samples > 10:
            logger.info(f"Computing LRRC-FS stability with {n_bootstrap} bootstrap subsamples (frac={bootstrap_frac})...")
            rng = np.random.RandomState(self.random_state)
            subsample_size = max(5, int(n_samples * bootstrap_frac))
            selection_counts = {name: 0 for name in self.feature_names_in_}

            for b in range(n_bootstrap):
                sub_idx = rng.choice(n_samples, size=subsample_size, replace=False)
                X_sub = X_mat[sub_idx]
                y_sub = y[sub_idx]

                if len(np.unique(y_sub)) < 2:
                    X_sub, y_sub = X_mat, y

                raw_rel_b = self._compute_relevance(X_sub, y_sub)
                min_b, max_b = np.min(raw_rel_b), np.max(raw_rel_b)
                denom_b = (max_b - min_b) if (max_b - min_b) > 1e-9 else 1.0
                norm_rel_b = (raw_rel_b - min_b) / denom_b

                with np.errstate(all="ignore"):
                    corr_b = np.nan_to_num(np.abs(np.corrcoef(X_sub, rowvar=False)), nan=0.0, posinf=0.0, neginf=0.0)

                b_selected, _, _ = self._greedy_select(
                    norm_rel_b, costs, corr_b, self.feature_names_in_, k,
                    w_rel=0.5, w_red=0.3, w_cost=0.2, w_stab=0.0
                )
                for s_idx in b_selected:
                    selection_counts[self.feature_names_in_[s_idx]] += 1

            self.stability_scores_ = {name: count / n_bootstrap for name, count in selection_counts.items()}
            w_rel = 0.4
            w_red = 0.25
            w_cost = 0.15
            w_stab = 0.2
            stability_dict = self.stability_scores_
        else:
            self.stability_scores_ = {}
            w_rel = self.relevance_weight
            w_red = self.redundancy_weight
            w_cost = self.cost_weight
            w_stab = 0.0
            stability_dict = None

        logger.info(
            f"Fitting LRRC-FS: selecting {k} of {n_features} features "
            f"(w_rel={w_rel}, w_red={w_red}, w_cost={w_cost}, w_stab={w_stab})"
        )

        # 5. Greedy Selection
        selected_indices, selected_names, history = self._greedy_select(
            norm_relevance, costs, corr_matrix, self.feature_names_in_, k,
            w_rel=w_rel, w_red=w_red, w_cost=w_cost, w_stab=w_stab,
            stability_scores=stability_dict
        )

        self.selected_indices_ = selected_indices
        self.selected_features_ = selected_names
        self.selection_history_ = history
        self.fit_time_seconds_ = time.perf_counter() - t0

        logger.info(
            f"LRRC-FS completed in {self.fit_time_seconds_:.3f}s. "
            f"Selected {len(self.selected_features_)} features: {self.selected_features_[:5]}..."
        )
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Project input feature matrix onto the selected feature subset."""
        if not self.selected_indices_:
            raise RuntimeError("LRRC-FS must be fitted before calling transform().")

        if isinstance(X, pd.DataFrame):
            return X[self.selected_features_].to_numpy(dtype=np.float64)
        else:
            X_mat = np.asarray(X)
            return X_mat[:, self.selected_indices_]

    def fit_transform(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        use_stability: bool = False,
        n_bootstrap: int = 10,
        bootstrap_frac: float = 0.7
    ) -> np.ndarray:
        return self.fit(
            X, y,
            feature_names=feature_names,
            use_stability=use_stability,
            n_bootstrap=n_bootstrap,
            bootstrap_frac=bootstrap_frac
        ).transform(X)

    def get_support(self, indices: bool = False) -> Union[List[bool], List[int]]:
        """Return boolean mask or integer indices of selected features."""
        if indices:
            return list(self.selected_indices_)
        mask = [False] * len(self.feature_names_in_)
        for idx in self.selected_indices_:
            mask[idx] = True
        return mask

    def explain_selection(self) -> pd.DataFrame:
        """Return a structured DataFrame documenting each step of the greedy selection."""
        return pd.DataFrame(self.selection_history_)
