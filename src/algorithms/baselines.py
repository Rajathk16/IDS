"""Baseline feature selectors for empirical comparison against LRRC-FS."""

from __future__ import annotations

import time
from typing import List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif
from src.core.logging_config import get_logger

logger = get_logger("baseline_selectors")


class AllFeaturesSelector(BaseEstimator, TransformerMixin):
    """Pass-through baseline preserving all eligible features."""

    def __init__(self):
        self.feature_names_in_: List[str] = []
        self.selected_features_: List[str] = []
        self.fit_time_seconds_: float = 0.0

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[np.ndarray] = None) -> AllFeaturesSelector:
        t0 = time.perf_counter()
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = list(X.columns)
        else:
            self.feature_names_in_ = [f"feat_{i}" for i in range(X.shape[1])]
        self.selected_features_ = list(self.feature_names_in_)
        self.fit_time_seconds_ = time.perf_counter() - t0
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            return X.to_numpy(dtype=np.float64)
        return np.asarray(X, dtype=np.float64)

    def fit_transform(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[np.ndarray] = None) -> np.ndarray:
        return self.fit(X, y).transform(X)


class VarianceThresholdSelector(BaseEstimator, TransformerMixin):
    """Baseline removing near-zero variance features."""

    def __init__(self, threshold: float = 0.01):
        self.threshold = threshold
        self.selector_ = VarianceThreshold(threshold=threshold)
        self.feature_names_in_: List[str] = []
        self.selected_features_: List[str] = []
        self.selected_indices_: List[int] = []
        self.fit_time_seconds_: float = 0.0

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[np.ndarray] = None) -> VarianceThresholdSelector:
        t0 = time.perf_counter()
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = list(X.columns)
            X_mat = X.to_numpy(dtype=np.float64)
        else:
            X_mat = np.asarray(X, dtype=np.float64)
            self.feature_names_in_ = [f"feat_{i}" for i in range(X_mat.shape[1])]

        self.selector_.fit(X_mat)
        mask = self.selector_.get_support()
        self.selected_indices_ = [i for i, val in enumerate(mask) if val]
        self.selected_features_ = [self.feature_names_in_[i] for i in self.selected_indices_]
        self.fit_time_seconds_ = time.perf_counter() - t0
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            return X[self.selected_features_].to_numpy(dtype=np.float64)
        X_mat = np.asarray(X, dtype=np.float64)
        return X_mat[:, self.selected_indices_]

    def fit_transform(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[np.ndarray] = None) -> np.ndarray:
        return self.fit(X, y).transform(X)


class EstablishedKBestSelector(BaseEstimator, TransformerMixin):
    """Standard ANOVA F-score ranking (SelectKBest) without redundancy penalty."""

    def __init__(self, k: int = 15):
        self.k = k
        self.selector_ = SelectKBest(score_func=f_classif, k=k)
        self.feature_names_in_: List[str] = []
        self.selected_features_: List[str] = []
        self.selected_indices_: List[int] = []
        self.fit_time_seconds_: float = 0.0

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: np.ndarray) -> EstablishedKBestSelector:
        t0 = time.perf_counter()
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = list(X.columns)
            X_mat = X.to_numpy(dtype=np.float64)
        else:
            X_mat = np.asarray(X, dtype=np.float64)
            self.feature_names_in_ = [f"feat_{i}" for i in range(X_mat.shape[1])]

        if np.isnan(X_mat).any():
            col_medians = np.nanmedian(X_mat, axis=0)
            inds = np.where(np.isnan(X_mat))
            X_mat[inds] = np.take(np.nan_to_num(col_medians, nan=0.0), inds[1])

        k_adj = min(self.k, X_mat.shape[1])
        self.selector_.set_params(k=k_adj)
        self.selector_.fit(X_mat, y)
        mask = self.selector_.get_support()
        self.selected_indices_ = [i for i, val in enumerate(mask) if val]
        self.selected_features_ = [self.feature_names_in_[i] for i in self.selected_indices_]
        self.fit_time_seconds_ = time.perf_counter() - t0
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            return X[self.selected_features_].to_numpy(dtype=np.float64)
        X_mat = np.asarray(X, dtype=np.float64)
        return X_mat[:, self.selected_indices_]

    def fit_transform(self, X: Union[pd.DataFrame, np.ndarray], y: np.ndarray) -> np.ndarray:
        return self.fit(X, y).transform(X)
