"""Additional tests for threshold calibration, preprocessing consistency, label mapping, and confusion matrix."""

import numpy as np
import pandas as pd
import pytest

from src.core.engine import IDSEngine
from src.data.taxonomy import map_to_binary
from src.training.calibrate import calibrate_decision_threshold, SWEEP_THRESHOLDS, TARGET_FPRS
from src.training.evaluate import evaluate_predictions
from src.web.server import DevRakshakAPIHandler


class MockHandler(DevRakshakAPIHandler):
    """Socketless mock handler for testing."""
    def __init__(self):
        self.sent_json = None
        self.sent_status = None

    def _send_json(self, data, status=200):
        self.sent_json = data
        self.sent_status = status

    def _send_error_json(self, message, status=400, details=None):
        self.sent_json = {"success": False, "error": message, "details": details}
        self.sent_status = status


# ---------------------------------------------------------------------------
# 1. Label mapping tests
# ---------------------------------------------------------------------------

def test_binary_label_mapping_benign():
    """BENIGN variants must map to 'BENIGN', not 'ATTACK'."""
    benign_inputs = ["BenignTraffic", "benign", "BENIGN", "normal", "0"]
    for lbl in benign_inputs:
        result = map_to_binary(lbl)
        assert result == "BENIGN", f"Expected BENIGN for '{lbl}', got '{result}'"


def test_binary_label_mapping_attack():
    """Attack labels must map to 'ATTACK'."""
    attack_inputs = ["DDoS-SYN_Flood", "DoS-UDP_Flood", "Mirai-greip_flood", "SqlInjection", "1"]
    for lbl in attack_inputs:
        result = map_to_binary(lbl)
        assert result == "ATTACK", f"Expected ATTACK for '{lbl}', got '{result}'"


# ---------------------------------------------------------------------------
# 2. Label encoder ordering confirmation
# ---------------------------------------------------------------------------

def test_label_encoder_alphabetical_order():
    """
    LabelEncoder sorts classes alphabetically: ATTACK < BENIGN.
    So ATTACK = index 0, BENIGN = index 1.
    predictor.py must apply threshold to proba[:, 0] (ATTACK index).
    """
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    le.fit(["BENIGN", "ATTACK"])
    classes = list(le.classes_)
    assert classes[0] == "ATTACK", f"Expected ATTACK at index 0, got {classes[0]}"
    assert classes[1] == "BENIGN", f"Expected BENIGN at index 1, got {classes[1]}"


def test_predictor_threshold_applied_to_attack_index():
    """
    Verify predictor.py applies decision_threshold to ATTACK probability (index 0),
    not BENIGN probability (index 1).
    """
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    bundle, _ = engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=200,
    )
    assert bundle is not None

    # Confirm labels order
    attack_indices = [i for i, lbl in enumerate(bundle.labels) if "attack" in str(lbl).lower()]
    assert len(attack_indices) > 0, f"No ATTACK label found in bundle.labels={bundle.labels}"
    atk_idx = attack_indices[0]

    # The predictor source code resolves attack index by searching for 'attack' in label name.
    # Verify it matches the actual label_encoder classes_ ordering.
    le_classes = list(bundle.preprocessor.label_encoder_.classes_)
    le_attack_idx = le_classes.index("ATTACK") if "ATTACK" in le_classes else None
    if le_attack_idx is not None:
        assert atk_idx == le_attack_idx, (
            f"predictor attack_idx={atk_idx} does not match "
            f"label_encoder ATTACK index={le_attack_idx}. "
            f"Threshold would be applied to wrong class!"
        )


# ---------------------------------------------------------------------------
# 3. Preprocessing consistency: training pipeline == inference pipeline
# ---------------------------------------------------------------------------

def test_preprocessing_consistency_training_vs_inference():
    """
    Predictions from the training pipeline (clf.predict on X_test_selected)
    must match predictions from the full inference pipeline (bundle.predict(X_test_raw)).
    Uses the same 200-row synthetic dataset.
    """
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    bundle, _ = engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=300,
    )

    # Load the same dataset and run full inference via bundle.predict
    df_raw = pd.read_csv(data_file, nrows=100)
    X_df, y_raw = bundle.preprocessor.extract_features_and_target(df_raw)
    preds_inference = bundle.predict(X_df)

    # Training pipeline: transform → selector → classifier.predict → decode
    X_trans = bundle.preprocessor.transform(X_df)
    X_sel = bundle.selector.transform(pd.DataFrame(X_trans, columns=bundle.preprocessor.feature_names_))
    preds_encoded = bundle.classifier.predict(X_sel)
    preds_training = bundle.preprocessor.decode_target(preds_encoded)

    # Predictions must be identical
    n_matching = np.sum(preds_inference == preds_training)
    total = len(preds_inference)
    assert n_matching == total, (
        f"Inference vs training pipeline mismatch: "
        f"{total - n_matching}/{total} rows differ. "
        f"Preprocessing inconsistency detected!"
    )


# ---------------------------------------------------------------------------
# 4. Threshold calibration tests
# ---------------------------------------------------------------------------

def test_threshold_calibration_returns_valid_structure():
    """calibrate_decision_threshold must return a dict with expected keys."""
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    bundle, _ = engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=300,
    )

    df_val = pd.read_csv(data_file, nrows=100)
    X_val, y_val = bundle.preprocessor.extract_features_and_target(df_val)

    cal = calibrate_decision_threshold(bundle, X_val, y_val)

    assert "sweep" in cal
    assert "recommended" in cal
    assert "targets" in cal
    assert "note" in cal
    assert isinstance(cal["recommended"], float)
    assert 0.0 <= cal["recommended"] <= 1.0

    # Sweep must contain entries for all threshold steps
    if cal["sweep"]:
        assert len(cal["sweep"]) == len(SWEEP_THRESHOLDS)
        for entry in cal["sweep"]:
            for key in ("threshold", "tp", "tn", "fp", "fn", "fpr", "fnr", "precision", "recall", "f1"):
                assert key in entry, f"Missing key '{key}' in sweep entry"
            assert 0.0 <= entry["fpr"] <= 1.0
            assert 0.0 <= entry["fnr"] <= 1.0


def test_threshold_calibration_recommended_within_range():
    """The recommended threshold must be a valid probability in [0.30, 0.95]."""
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    bundle, _ = engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=300,
    )

    df_val = pd.read_csv(data_file, nrows=100)
    X_val, y_val = bundle.preprocessor.extract_features_and_target(df_val)

    cal = calibrate_decision_threshold(bundle, X_val, y_val)
    rec = cal["recommended"]

    # Must be from the sweep set or the fallback 0.50
    valid_thresholds = set(SWEEP_THRESHOLDS) | {0.50}
    assert rec in valid_thresholds, f"Recommended threshold {rec} not in sweep set"


def test_threshold_calibration_stored_in_bundle_metadata():
    """After training, bundle.metadata must contain calibration dict."""
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    bundle, _ = engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=300,
    )

    assert "calibration" in bundle.metadata, "bundle.metadata missing 'calibration' key"
    assert "calibrated_threshold" in bundle.metadata, "bundle.metadata missing 'calibrated_threshold'"
    assert isinstance(bundle.metadata["calibrated_threshold"], float)


# ---------------------------------------------------------------------------
# 5. Confusion matrix calculations
# ---------------------------------------------------------------------------

def test_confusion_matrix_fpr_formula():
    """
    FPR = FP / (FP + TN) with zero-denominator safety.
    
    Label encoding (alphabetical): ATTACK=0, BENIGN=1
    We want 50 actual BENIGN (y_true=1), 50 actual ATTACK (y_true=0).
    Predictions: 40 of 50 BENIGN correctly classified (TN), 10 misclassified as ATTACK (FP).
    FPR = 10 / (10 + 40) = 0.20
    """
    # 50 ATTACK (0), 50 BENIGN (1)
    y_true = np.array([0] * 50 + [1] * 50)
    # 50 ATTACK all predicted ATTACK (TP=50), 40 BENIGN predicted BENIGN (TN=40), 10 BENIGN predicted ATTACK (FP=10)
    y_pred = np.array([0] * 50 + [1] * 40 + [0] * 10)

    report = evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        labels=["ATTACK", "BENIGN"],
        task_type="binary",
        model_name="dt",
        feature_selector="none",
        training_duration_seconds=0.0,
        inference_latency_ms=0.0,
    )
    # BENIGN is the negative class (benign_idx=1 since "BENIGN" > "ATTACK" alphabetically)
    # TN = cm[1,1] = 40, FP = cm[1,0] = 10, FPR = 10/(10+40) = 0.20
    assert report.false_positive_rate is not None
    assert abs(report.false_positive_rate - 0.20) < 0.01, (
        f"Expected FPR ~0.20, got {report.false_positive_rate}. "
        f"CM: {report.confusion_matrix}"
    )


def test_confusion_matrix_zero_denominator_handled():
    """FPR = 0 when there are no actual negatives (all ATTACK)."""
    y_true = np.array([0] * 100)   # all ATTACK
    y_pred = np.array([0] * 90 + [1] * 10)

    report = evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        labels=["ATTACK", "BENIGN"],
        task_type="binary",
        model_name="dt",
        feature_selector="none",
        training_duration_seconds=0.0,
        inference_latency_ms=0.0,
    )
    # FPR = FP / (FP + TN). With no BENIGN samples, FP + TN = 0 → safe 0.0
    assert report.false_positive_rate == 0.0


# ---------------------------------------------------------------------------
# 6. /api/test response includes new metrics
# ---------------------------------------------------------------------------

def test_api_test_summary_includes_fnr_precision_recall_f1():
    """
    /api/test summary must include fnr_percentage, precision_percentage,
    recall_percentage, f1_percentage when ground truth is available.
    """
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    # Train a fresh model
    engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=300,
    )

    handler = MockHandler()
    body = {
        "file_path": str(data_file),
        "sample_limit": 100,
        "record_events": False,
    }
    handler._handle_api_post("/api/test", body)

    assert handler.sent_status == 200, f"Expected 200, got {handler.sent_status}: {handler.sent_json}"
    summary = handler.sent_json["summary"]

    # Ground truth is available in synthetic datasets
    if summary.get("has_ground_truth"):
        assert "fnr_percentage" in summary, "Missing fnr_percentage in summary"
        assert "precision_percentage" in summary, "Missing precision_percentage in summary"
        assert "recall_percentage" in summary, "Missing recall_percentage in summary"
        assert "f1_percentage" in summary, "Missing f1_percentage in summary"
        assert "predicted_attack_rate" in summary
        # Verify values are in plausible range
        cm = summary.get("confusion_matrix", {})
        if cm:
            assert "tp" in cm and "tn" in cm and "fp" in cm and "fn" in cm
    else:
        # No ground truth: check the note is present
        assert "ground_truth_note" in summary
        assert summary["ground_truth_note"] is not None
        assert "predicted_attack_rate" in summary


def test_api_test_summary_includes_calibration_info():
    """
    /api/test summary must include calibrated_threshold when model has calibration metadata.
    """
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=300,
    )

    handler = MockHandler()
    body = {
        "file_path": str(data_file),
        "sample_limit": 50,
        "record_events": False,
    }
    handler._handle_api_post("/api/test", body)

    assert handler.sent_status == 200
    summary = handler.sent_json["summary"]
    # calibrated_threshold may be None for old bundles, but key must exist
    assert "calibrated_threshold" in summary
    assert "calibration_note" in summary
