"""Unit tests for preprocessing, data splitting, and the LRRC-FS algorithm."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.data.synthetic import generate_synthetic_dataset
from src.data.preprocess import IoTDataPreprocessor, PreprocessingManifest
from src.data.split import split_dataset
from src.algorithms.feature_selector import LRRCSFeatureSelector
from src.algorithms.baselines import AllFeaturesSelector, VarianceThresholdSelector, EstablishedKBestSelector


@pytest.fixture
def sample_traffic_df(tmp_path: Path) -> pd.DataFrame:
    csv_path = tmp_path / "traffic_sample.csv"
    generate_synthetic_dataset(csv_path, n_samples=300, random_seed=42, include_anomalous_values=True)
    return pd.read_csv(csv_path)


def test_preprocessor_fit_transform_manifest(sample_traffic_df: pd.DataFrame, tmp_path: Path):
    preprocessor = IoTDataPreprocessor(task_type="binary", target_column="label")
    X, y = preprocessor.extract_features_and_target(sample_traffic_df)
    
    assert "label" not in X.columns
    assert y is not None
    assert set(np.unique(y)).issubset({"BENIGN", "ATTACK"})

    X_trans = preprocessor.fit_transform(X, y)
    assert X_trans.shape == X.shape
    # Check no NaNs or Infs remain after transform
    assert not np.isnan(X_trans).any()
    assert not np.isinf(X_trans).any()

    # Manifest verification
    manifest = preprocessor.manifest_
    assert manifest is not None
    assert len(manifest.input_features) == X.shape[1]
    assert manifest.task_type == "binary"

    # Save and reload manifest
    manifest_file = tmp_path / "manifest.json"
    manifest.save(manifest_file)
    assert manifest_file.exists()
    loaded_manifest = PreprocessingManifest.load(manifest_file)
    assert loaded_manifest.task_type == "binary"
    assert loaded_manifest.classes == manifest.classes


def test_split_dataset_stratification_and_ratios(sample_traffic_df: pd.DataFrame):
    df_train, df_test, df_val = split_dataset(
        sample_traffic_df,
        target_column="label",
        test_size=0.2,
        val_size=0.1,
        random_seed=42,
        stratify=True
    )

    total = len(sample_traffic_df)
    assert len(df_train) + len(df_test) + len(df_val) == total
    assert len(df_test) == int(total * 0.2)
    assert df_val is not None
    assert len(df_val) > 0


def test_lrrc_fs_selection_and_determinism(sample_traffic_df: pd.DataFrame):
    preprocessor = IoTDataPreprocessor(task_type="binary")
    X, y = preprocessor.extract_features_and_target(sample_traffic_df)
    X_clean = preprocessor.fit_transform(X, y)
    df_clean = pd.DataFrame(X_clean, columns=X.columns)
    y_encoded = preprocessor.encode_target(y)

    # Initialize LRRC-FS to select 8 features
    selector = LRRCSFeatureSelector(
        n_features_to_select=8,
        relevance_weight=0.5,
        redundancy_weight=0.3,
        cost_weight=0.2,
        random_state=42
    )

    selector.fit(df_clean, y_encoded)
    assert len(selector.selected_features_) == 8
    assert len(selector.selected_indices_) == 8

    # Verify explain_selection structure
    df_expl = selector.explain_selection()
    assert len(df_expl) == 8
    assert "relevance" in df_expl.columns
    assert "redundancy" in df_expl.columns
    assert "cost" in df_expl.columns
    assert "final_score" in df_expl.columns

    # Verify transform produces expected shape
    X_sub = selector.transform(df_clean)
    assert X_sub.shape == (len(df_clean), 8)

    # Verify deterministic execution (same inputs yield exact same feature order)
    selector2 = LRRCSFeatureSelector(
        n_features_to_select=8,
        relevance_weight=0.5,
        redundancy_weight=0.3,
        cost_weight=0.2,
        random_state=42
    )
    selector2.fit(df_clean, y_encoded)
    assert selector.selected_features_ == selector2.selected_features_


def test_baselines(sample_traffic_df: pd.DataFrame):
    preprocessor = IoTDataPreprocessor(task_type="binary")
    X, y = preprocessor.extract_features_and_target(sample_traffic_df)
    X_clean = preprocessor.fit_transform(X, y)
    df_clean = pd.DataFrame(X_clean, columns=X.columns)
    y_encoded = preprocessor.encode_target(y)

    # Baseline 1: AllFeatures
    all_sel = AllFeaturesSelector().fit(df_clean, y_encoded)
    assert len(all_sel.selected_features_) == df_clean.shape[1]
    assert all_sel.transform(df_clean).shape == df_clean.shape

    # Baseline 2: Variance
    var_sel = VarianceThresholdSelector(threshold=0.0).fit(df_clean, y_encoded)
    assert len(var_sel.selected_features_) > 0

    # Baseline 3: SelectKBest
    kbest_sel = EstablishedKBestSelector(k=10).fit(df_clean, y_encoded)
    assert len(kbest_sel.selected_features_) == 10
    assert kbest_sel.transform(df_clean).shape == (len(df_clean), 10)
