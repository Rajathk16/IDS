"""Unit and regression tests for FPR calculation and /api/test model resolution."""

import numpy as np
import pytest
from src.core.engine import IDSEngine
from src.detection.predictor import OfflinePredictor
from src.training.evaluate import evaluate_predictions
from src.web.server import DevRakshakAPIHandler


class MockHandler(DevRakshakAPIHandler):
    """Socketless mock handler for testing request handling."""
    def __init__(self):
        self.sent_json = None
        self.sent_status = None

    def _send_json(self, data, status=200):
        self.sent_json = data
        self.sent_status = status

    def _send_error_json(self, message, status=400, details=None):
        self.sent_json = {"success": False, "error": message, "details": details}
        self.sent_status = status


def test_binary_fpr_calculation():
    """Verify binary FPR formula: FP / (FP + TN)."""
    # 100 true Benign (1), 200 true Attack (0)
    # Predictions: 90 TN, 10 FP -> FPR = 10 / 100 = 0.10
    y_true = np.array([1] * 100 + [0] * 200)
    y_pred = np.array([1] * 90 + [0] * 10 + [0] * 190 + [1] * 10)
    report = evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        labels=["ATTACK", "BENIGN"],
        task_type="binary",
        model_name="dt",
        feature_selector="none",
        training_duration_seconds=0.1,
        inference_latency_ms=0.01,
    )
    assert report.false_positive_rate == 0.1
    assert report.per_class_metrics["BENIGN"]["false_positive_rate"] == 0.1


def test_multiclass_macro_fpr_calculation():
    """Verify multiclass one-vs-rest macro FPR calculation."""
    y_true = np.array([0] * 50 + [1] * 50 + [2] * 50)
    y_pred = np.array([0] * 45 + [1] * 5 + [1] * 40 + [0] * 10 + [2] * 48 + [0] * 2)
    report = evaluate_predictions(
        y_true=y_true,
        y_pred=y_pred,
        labels=["ClassA", "ClassB", "ClassC"],
        task_type="multiclass",
        model_name="rf",
        feature_selector="none",
        training_duration_seconds=0.1,
        inference_latency_ms=0.01,
    )
    assert report.false_positive_rate is not None
    assert 0.0 <= report.false_positive_rate <= 1.0
    for c in ["ClassA", "ClassB", "ClassC"]:
        assert "false_positive_rate" in report.per_class_metrics[c]


def test_api_test_uses_active_model_bundle_without_type_error():
    """Verify /api/test does not throw TypeError when engine.active_model_bundle is a TrainedModelBundle."""
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    # Train a quick model to populate engine.active_model_bundle
    bundle, run = engine.train(
        data_path=data_file,
        task_type="binary",
        model_name="decision_tree",
        sample_limit=200,
    )
    assert engine.active_model_bundle is not None
    assert not isinstance(engine.active_model_bundle, (str, bytes))

    # Test /api/test via MockHandler
    handler = MockHandler()
    body = {
        "file_path": str(data_file),
        "sample_limit": 50,
        "record_events": False,
    }
    handler._handle_api_post("/api/test", body)

    assert handler.sent_status == 200
    assert handler.sent_json["success"] is True
    summary = handler.sent_json["summary"]
    assert summary["model_task"] == "binary"
    assert "false_positive_rate" in summary
    assert "fpr_percentage" in summary
    assert "confusion_matrix" in summary


def test_api_test_missing_model_returns_404():
    """Verify that requesting an invalid model path returns clean 404 error instead of server crash."""
    engine = IDSEngine()
    discovered = engine.discover_datasets()
    data_file = discovered["synthetic"][0] if discovered["synthetic"] else discovered["raw"][0]

    handler = MockHandler()
    body = {
        "file_path": str(data_file),
        "model_path": "non_existent_model_xyz.joblib",
        "sample_limit": 50,
    }
    handler._handle_api_post("/api/test", body)

    assert handler.sent_status == 404
    assert handler.sent_json["success"] is False
    assert "could not be found" in handler.sent_json["error"].lower()
