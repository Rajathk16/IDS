"""Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS).

An original, transparent, greedy feature-selection algorithm designed for IoT
network intrusion detection. Balances statistical target relevance, inter-feature
redundancy penalty, and computational extraction/inference cost.
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

# Estimated/calibrated extraction cost penalties for IoT flow features
# Summary dispersion and floating-point statistical metrics incur higher computational cost
# than simple fixed bitmask header flags.
HIGH_COST_FEATURES = {
    "Variance", "Covariance", "Radius", "Magnitue", "Tot sum", "Tot size",
    "AVG", "Std", "Min", "Max", "IAT", "flow_duration", "Duration", "Rate", "Srate", "Drate"
}


class LRRCSFeatureSelector(BaseEstimator, TransformerMixin):
    """
    Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS).
    
    Mathematical Formulation:
      Score(f) = w_rel * R_norm(f) - w_red * D(f, S) - w_cost * C_norm(f)
    
    Where:
      - R_norm(f) in [0, 1]: Target relevance via normalized ANOVA F-statistic or Mutual Information.
      - D(f, S) in [0, 1]: Mean absolute Pearson correlation between candidate f and already selected features S.
      - C_norm(f) in [0, 1]: Computational extraction/inference cost penalty.
      - w_rel, w_red, w_cost: User-configurable non-negative weights.
    
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
        self.selection_history_: List[Dict[str, Union[str, float, int]]] = []
        self.fit_time_seconds_: float = 0.0

    def _compute_relevance(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Compute statistical relevance between candidate features and target."""
        if self.relevance_metric == "mutual_info":
            # Mutual information classification
            scores = mutual_info_classif(X, y, random_state=self.random_state)
        else:
            # Default: ANOVA F-statistic (fast, robust for continuous network flow metrics)
            f_scores, _ = f_classif(X, y)
            scores = np.nan_to_num(f_scores, nan=0.0, posinf=1e6, neginf=0.0)
        return scores

    def _compute_costs(self, feature_names: List[str]) -> np.ndarray:
        """
        Assign normalized computational extraction cost.
        Flags and discrete protocol indicators have low cost (0.1 - 0.3);
        Multi-packet aggregate statistics have higher cost (0.7 - 1.0).
        """
        costs = np.zeros(len(feature_names), dtype=np.float64)
        for i, feat in enumerate(feature_names):
            if feat in HIGH_COST_FEATURES:
                costs[i] = 0.9
            elif "count" in feat:
                costs[i] = 0.5
            elif "flag" in feat or feat in ("TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS"):
                costs[i] = 0.2
            else:
                costs[i] = 0.4
        return costs

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: np.ndarray) -> LRRCSFeatureSelector:
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
            self.feature_names_in_ = [f"feat_{i}" for i in range(X_mat.shape[1])]

        n_samples, n_features = X_mat.shape
        k = min(self.n_features_to_select, n_features)

        # Resilient fallback: ensure no NaNs in selector input
        if np.isnan(X_mat).any():
            col_medians = np.nanmedian(X_mat, axis=0)
            inds = np.where(np.isnan(X_mat))
            X_mat[inds] = np.take(np.nan_to_num(col_medians, nan=0.0), inds[1])

        logger.info(
            f"Fitting LRRC-FS: selecting {k} of {n_features} features "
            f"(w_rel={self.relevance_weight}, w_red={self.redundancy_weight}, w_cost={self.cost_weight})"
        )

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

        # 3. Compute absolute correlation matrix for redundancy penalty
        # Handle zero-variance columns safely
        std_devs = np.std(X_mat, axis=0)
        valid_cols = std_devs > 1e-9

        # Clip values to avoid runtime warnings in correlation
        corr_matrix = np.zeros((n_features, n_features), dtype=np.float64)
        for i in range(n_features):
            for j in range(i, n_features):
                if valid_cols[i] and valid_cols[j]:
                    c = np.corrcoef(X_mat[:, i], X_mat[:, j])[0, 1]
                    corr_val = 0.0 if np.isnan(c) else abs(float(c))
                else:
                    corr_val = 0.0
                corr_matrix[i, j] = corr_val
                corr_matrix[j, i] = corr_val

        # 4. Greedy Selection Procedure
        selected_indices: List[int] = []
        selected_names: List[str] = []
        candidate_indices = set(range(n_features))
        self.selection_history_ = []

        for step in range(1, k + 1):
            best_idx = -1
            best_score = -float("inf")
            best_metrics: Dict[str, float] = {}

            # Sort candidate indices for deterministic tie-breaking (by feature name)
            sorted_candidates = sorted(candidate_indices, key=lambda idx: self.feature_names_in_[idx])

            for idx in sorted_candidates:
                rel = norm_relevance[idx]
                cost = costs[idx]

                # Redundancy penalty with already selected features
                if len(selected_indices) == 0:
                    red = 0.0
                else:
                    red = float(np.mean([corr_matrix[idx, s] for s in selected_indices]))

                score = (
                    (self.relevance_weight * rel)
                    - (self.redundancy_weight * red)
                    - (self.cost_weight * cost)
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

            if best_idx != -1:
                selected_indices.append(best_idx)
                feat_name = self.feature_names_in_[best_idx]
                selected_names.append(feat_name)
                candidate_indices.remove(best_idx)

                self.selection_history_.append({
                    "step": step,
                    "feature": feat_name,
                    "index": best_idx,
                    **best_metrics
                })

        self.selected_indices_ = selected_indices
        self.selected_features_ = selected_names
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
            # Extract by column name
            return X[self.selected_features_].to_numpy(dtype=np.float64)
        else:
            X_mat = np.asarray(X)
            return X_mat[:, self.selected_indices_]

    def fit_transform(self, X: Union[pd.DataFrame, np.ndarray], y: np.ndarray) -> np.ndarray:
        return self.fit(X, y).transform(X)

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
