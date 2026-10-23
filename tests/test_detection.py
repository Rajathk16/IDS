"""Unit tests for offline detection, policy alert triggering, and SQLite persistence."""

from pathlib import Path
import pandas as pd
import pytest
from src.data.synthetic import generate_synthetic_dataset
from src.detection.event_store import EventStore
from src.detection.predictor import OfflinePredictor
from src.training.train import train_model


@pytest.fixture
def trained_binary_model(tmp_path: Path):
    train_csv = tmp_path / "train_synth.csv"
    generate_synthetic_dataset(train_csv, n_samples=250, random_seed=42)
    bundle, run = train_model(
        data_path=train_csv,
        task_type="binary",
        model_name="decision_tree",
        feature_selector="lrrc",
        n_features=6,
        sample_limit=200,
        random_seed=42
    )
    return bundle, train_csv


def test_offline_predictor(trained_binary_model, tmp_path: Path):
    bundle, data_csv = trained_binary_model
    predictor = OfflinePredictor(bundle)

    # Test inference on a small test batch
    test_csv = tmp_path / "test_unseen.csv"
    generate_synthetic_dataset(test_csv, n_samples=50, random_seed=99)

    df_out, events = predictor.predict_csv_file(test_csv, sample_limit=50, record_events=True)

    assert len(df_out) == 50
    assert "predicted_label" in df_out.columns
    assert "prediction_confidence" in df_out.columns
    assert "is_attack" in df_out.columns
    assert "alert_severity" in df_out.columns

    assert len(events) == 50
    assert all(e.predicted_label in ("BENIGN", "ATTACK") for e in events)


def test_event_store_query_and_summary(tmp_path: Path, trained_binary_model):
    bundle, data_csv = trained_binary_model
    db_file = tmp_path / "test_events.sqlite"
    store = EventStore(db_path=db_file)

    # Initially empty
    summary_empty = store.get_detection_summary()
    assert summary_empty["total_records_processed"] == 0

    # Run inference and persist
    predictor = OfflinePredictor(bundle)
    predictor.event_store = store
    df_out, events = predictor.predict_csv_file(data_csv, sample_limit=30, record_events=True)

    # Verify persisted in store
    retrieved = store.list_detection_events(limit=50)
    assert len(retrieved) == 30

    summary = store.get_detection_summary()
    assert summary["total_records_processed"] == 30
    assert summary["benign_count"] + summary["attack_count"] == 30


def test_invalid_model_bundle_loading(tmp_path: Path):
    bad_model = tmp_path / "corrupted_model.joblib"
    with open(bad_model, "w") as f:
        f.write("not a joblib file")

    with pytest.raises(ValueError, match="Failed to load model file"):
        OfflinePredictor(bad_model)
