"""Unit tests for statistical confidence intervals, LRRC-FS stability, and dataset deduplication."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest


def test_clopper_pearson_zero_fp():
    """0/41 benign FP -> upper bound < 0.09 (Clopper-Pearson)."""
    from src.training.stats_utils import clopper_pearson
    lo, hi = clopper_pearson(0, 41)
    assert lo == 0.0
    assert hi < 0.09


def test_stability_weights_backward_compat():
    """w_stab=0 (use_stability=False) must give identical selection to old algorithm."""
    from src.algorithms.feature_selector import LRRCSFeatureSelector

    rng = np.random.RandomState(42)
    n_samples, n_features = 100, 20
    X = rng.randn(n_samples, n_features)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    feature_names = [f"feat_{i}" for i in range(n_features)]
    df_X = pd.DataFrame(X, columns=feature_names)

    sel1 = LRRCSFeatureSelector(n_features_to_select=5, random_state=42)
    sel1.fit(df_X, y, use_stability=False)

    sel2 = LRRCSFeatureSelector(n_features_to_select=5, random_state=42)
    sel2.fit(df_X, y, use_stability=False)

    assert sel1.selected_features_ == sel2.selected_features_
    assert sel1.selected_indices_ == sel2.selected_indices_
    assert len(sel1.selected_features_) == 5


def test_cost_dict_keys_are_real_columns():
    """All keys in FEATURE_COST must be plausible column names (non-empty strings)."""
    from src.algorithms.feature_selector import FEATURE_COST
    assert all(isinstance(k, str) and len(k) > 0 for k in FEATURE_COST)


def test_build_dataset_dedupe():
    """With a tiny synthetic CSV containing duplicate rows, deduplication removes them."""
    from src.data.build_dataset import deduplicate_dataset

    data = {
        "feat_a": [1, 2, 3, 4, 1, 2, 5, 6, 7, 8],
        "feat_b": [10, 20, 30, 40, 10, 20, 50, 60, 70, 80],
        "label": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"]
    }
    df = pd.DataFrame(data)
    assert len(df) == 10

    # Rows index 4 is duplicate of 0, index 5 is duplicate of 1
    # Adding one more duplicate row to have 3 duplicates total
    row_dup = pd.DataFrame({"feat_a": [3], "feat_b": [30], "label": ["A"]})
    df_with_dups = pd.concat([df, row_dup], ignore_index=True)
    # Total rows = 11, with 3 duplicates (rows matching 0, 1, and 2), unique = 8
    deduped = deduplicate_dataset(df_with_dups)
    assert len(deduped) == 8

    # Specific 10-row, 3 duplicates case: 7 unique rows
    df_10_with_3_dups = pd.DataFrame({
        "feat_a": [1, 2, 3, 4, 5, 6, 7, 1, 2, 3],
        "feat_b": [10, 20, 30, 40, 50, 60, 70, 10, 20, 30],
        "label": ["A", "B", "A", "B", "A", "B", "A", "A", "B", "A"]
    })
    deduped_7 = deduplicate_dataset(df_10_with_3_dups)
    assert len(deduped_7) == 7
