"""Unit tests for core configuration, events, policies, and logging."""

import os
from pathlib import Path
from src.core.settings import AppSettings, get_settings
from src.core.events import DetectionEvent, TrainingRun, DatasetAuditResult
from src.core.policies import PolicyConfig, AlertPolicy, get_policies
from src.core.logging_config import setup_logging, get_logger, get_log_buffer


def test_settings_defaults_and_validation(tmp_path: Path):
    settings = AppSettings(
        log_level="DEBUG",
        default_task="binary",
        default_model="random_forest",
        lrrc_max_features=10,
    )
    assert settings.log_level == "DEBUG"
    assert settings.default_task == "binary"
    assert settings.default_model == "random_forest"
    assert settings.lrrc_max_features == 10

    # Test file persistence
    save_file = tmp_path / "test_settings.json"
    settings.save_to_file(save_file)
    assert save_file.exists()

    loaded = AppSettings.load_from_file(save_file)
    assert loaded.log_level == "DEBUG"
    assert loaded.lrrc_max_features == 10


def test_events_models():
    event = DetectionEvent(
        source_file="test.csv",
        row_index=42,
        predicted_label="DDoS-UDP_Flood",
        confidence=0.95,
        is_attack=True,
        attack_category="DDoS",
        severity="HIGH"
    )
    assert event.id is not None
    assert event.is_attack is True
    assert event.confidence == 0.95

    run = TrainingRun(
        dataset_name="ciciot_sample.csv",
        task_type="binary",
        model_name="decision_tree",
        feature_selector="lrrc",
        selected_features_count=10,
        selected_features=["f1", "f2"],
        train_samples=800,
        test_samples=200,
        training_duration_seconds=0.15,
        inference_latency_ms_per_sample=0.01,
        accuracy=0.98,
        precision=0.98,
        recall=0.98,
        macro_f1=0.98,
        weighted_f1=0.98,
        model_path="models/test.joblib"
    )
    assert run.accuracy == 0.98
    assert run.status == "SUCCESS"


def test_policies_evaluation_and_audit():
    policy_cfg = PolicyConfig.default_policies()
    assert len(policy_cfg.policies) >= 5

    # Mirai attack with confidence 0.9 should trigger CRITICAL
    sev, pol_name = policy_cfg.evaluate("Mirai", 0.95)
    assert sev == "CRITICAL"
    assert "Mirai" in pol_name

    # Benign should always be INFO and no policy alert
    sev_b, pol_b = policy_cfg.evaluate("Benign", 0.99)
    assert sev_b == "INFO"
    assert pol_b is None

    # Test toggle policy and audit logging
    initial_audits = len(policy_cfg.audit_log)
    policy_cfg.toggle_policy("POL-001", False)
    assert len(policy_cfg.audit_log) == initial_audits + 1
    assert policy_cfg.policies[0].enabled is False

    # After disabling POL-001, evaluate Mirai -> should drop to lower severity or fallback
    sev_disabled, _ = policy_cfg.evaluate("Mirai", 0.95)
    assert sev_disabled != "CRITICAL"


def test_logging_and_buffer(tmp_path: Path):
    test_log = tmp_path / "test.log"
    logger = setup_logging(log_level="DEBUG", log_file=test_log)
    logger.info("Test info message")
    logger.warning("Test warning message")

    buffer = get_log_buffer()
    records = buffer.get_records(limit=10)
    messages = [r.getMessage() for r in records]
    assert "Test info message" in messages
    assert "Test warning message" in messages
