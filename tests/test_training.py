"""Unit tests for model training, evaluation metrics, and model bundle persistence."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.data.synthetic import generate_synthetic_dataset
from src.training.train import (
    TrainedModelBundle,
    apply_resampling,
    get_classifier,
    get_feature_selector,
    train_model
)
from src.training.evaluate import evaluate_predictions, measure_inference_latency


@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    csv_file = tmp_path / "test_train_synth.csv"
    return generate_synthetic_dataset(csv_file, n_samples=300, random_seed=42)


def test_classifier_factory():
    dt = get_classifier("decision_tree", random_state=42)
    rf = get_classifier("random_forest", random_state=42, use_class_weight=True)
    et = get_classifier("extra_trees", random_state=42)
    gb = get_classifier("gradient_boosting", random_state=42)

    assert dt is not None
    assert rf.class_weight == "balanced"
    assert et is not None
    assert gb is not None

    with pytest.raises(ValueError, match="Unsupported model"):
        get_classifier("invalid_model")


def test_feature_selector_factory():
    lrrc = get_feature_selector("lrrc", n_features=8)
    all_f = get_feature_selector("all")
    var_f = get_feature_selector("variance")
    kbest = get_feature_selector("kbest", n_features=8)

    assert lrrc.n_features_to_select == 8
    assert all_f is not None
    assert var_f is not None
    assert kbest.k == 8


def test_resampling_strategies():
    X = np.random.randn(100, 5)
    # Imbalanced labels: 80 class 0, 20 class 1
    y = np.array([0] * 80 + [1] * 20)

    # 1. Under-sampling
    X_us, y_us, strat_us = apply_resampling(X, y, strategy="under_sample", random_state=42)
    assert len(X_us) == 40  # 20 of each
    assert "RandomUnderSampler" in strat_us

    # 2. SMOTE over-sampling
    X_sm, y_sm, strat_sm = apply_resampling(X, y, strategy="smote", random_state=42)
    assert len(X_sm) == 160  # 80 of each
    assert "SMOTE" in strat_sm


def test_train_model_binary(synthetic_csv: Path):
    bundle, run = train_model(
        data_path=synthetic_csv,
        task_type="binary",
        model_name="decision_tree",
        feature_selector="lrrc",
        n_features=8,
        sample_limit=250,
        random_seed=42
    )

    assert run.status == "SUCCESS"
    assert run.accuracy > 0.5
    assert run.macro_f1 > 0.5
    assert run.selected_features_count == 8
    assert Path(run.model_path).exists()
    assert Path(run.confusion_matrix_plot).exists()

    # Test reloading bundle
    loaded_bundle = TrainedModelBundle.load(Path(run.model_path))
    assert loaded_bundle.model_name == "decision_tree"
    assert loaded_bundle.task_type == "binary"
    assert len(loaded_bundle.labels) == 2


def test_train_model_multiclass(synthetic_csv: Path):
    bundle, run = train_model(
        data_path=synthetic_csv,
        task_type="multiclass",
        model_name="random_forest",
        feature_selector="kbest",
        n_features=10,
        sample_limit=250,
        random_seed=42
    )

    assert run.status == "SUCCESS"
    assert run.task_type == "multiclass"
    assert len(bundle.labels) >= 2


def test_evaluate_predictions_and_fpr():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_pred = np.array([0, 0, 1, 1, 1, 0])
    labels = ["BENIGN", "ATTACK"]

    report = evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        labels=labels,
        task_type="binary",
        model_name="test_model",
        feature_selector="test_selector",
        training_duration_seconds=0.05,
        inference_latency_ms=0.002
    )

    # 1 False Positive out of 3 actual Benign -> FPR = 1/3 = 0.3333
    assert report.false_positive_rate is not None
    assert round(report.false_positive_rate, 2) == 0.33
    assert report.macro_f1 > 0.0
