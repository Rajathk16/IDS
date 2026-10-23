"""Unit tests for synthetic dataset generation, data loading, and dataset audit."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.data.synthetic import generate_synthetic_dataset
from src.data.loader import discover_csv_files, inspect_schema, load_dataset, is_synthetic_file
from src.data.audit import audit_dataset
from src.data.taxonomy import map_to_binary, map_to_category, CICIOT2023_FEATURE_NAMES


def test_taxonomy_mappings():
    assert map_to_binary("BenignTraffic") == "BENIGN"
    assert map_to_binary("benign") == "BENIGN"
    assert map_to_binary("DDoS-UDP_Flood") == "ATTACK"
    assert map_to_binary("Mirai-udpplain") == "ATTACK"

    assert map_to_category("BenignTraffic") == "Benign"
    assert map_to_category("DDoS-UDP_Flood") == "DDoS"
    assert map_to_category("DoS-TCP_Flood") == "DoS"
    assert map_to_category("Mirai-greeth_flood") == "Mirai"
    assert map_to_category("Recon-PortScan") == "Recon"
    assert map_to_category("SqlInjection") == "Web"
    assert map_to_category("DictionaryBruteForce") == "BruteForce"
    assert map_to_category("MITM-ArpSpoofing") == "Spoofing"


def test_synthetic_generation_and_metadata(tmp_path: Path):
    out_csv = tmp_path / "synthetic_test.csv"
    generated_path = generate_synthetic_dataset(
        output_path=out_csv,
        n_samples=500,
        random_seed=123,
        include_anomalous_values=True
    )

    assert generated_path.exists()
    assert is_synthetic_file(generated_path) is True

    # Check columns
    df = pd.read_csv(generated_path)
    assert len(df) == 500
    assert "label" in df.columns
    for feat in CICIOT2023_FEATURE_NAMES:
        assert feat in df.columns

    # Verify anomalous values were injected
    has_nan = df.isna().any().any()
    has_inf = np.isinf(df.select_dtypes(include=[np.number]).to_numpy()).any()
    assert bool(has_nan) is True
    assert bool(has_inf) is True


def test_data_loader_and_sample_limit(tmp_path: Path):
    out_csv = tmp_path / "synth_loader.csv"
    generate_synthetic_dataset(output_path=out_csv, n_samples=300, random_seed=42)

    # Test discovery
    discovered = discover_csv_files(tmp_path)
    assert len(discovered) == 1
    assert discovered[0].name == "synth_loader.csv"

    # Test inspect schema
    cols, tgt = inspect_schema(out_csv)
    assert tgt == "label"
    assert len(cols) == 47  # 46 features + 1 label

    # Test load with sample_limit
    df_sample, is_synth, files = load_dataset(out_csv, sample_limit=150)
    assert len(df_sample) == 150
    assert is_synth is True
    assert len(files) == 1


def test_data_loader_missing_target_error(tmp_path: Path):
    bad_csv = tmp_path / "bad_schema.csv"
    bad_df = pd.DataFrame({"feat_a": [1, 2, 3], "feat_b": [4, 5, 6]})
    bad_df.to_csv(bad_csv, index=False)

    with pytest.raises(ValueError, match="Could not identify target label column"):
        load_dataset(bad_csv)


def test_dataset_audit(tmp_path: Path):
    out_csv = tmp_path / "synth_audit.csv"
    generate_synthetic_dataset(
        output_path=out_csv,
        n_samples=400,
        random_seed=99,
        include_anomalous_values=True
    )

    audit_result = audit_dataset(out_csv, max_rows_for_audit=500)
    assert audit_result.file_count == 1
    assert audit_result.total_rows == 400
    assert audit_result.target_column == "label"
    assert audit_result.is_synthetic is True
    assert audit_result.missing_value_count > 0
    assert audit_result.infinite_value_count > 0
    assert "BenignTraffic" in audit_result.class_distribution
    assert audit_result.schema_valid is True

    # Verify audit report file was generated
    settings_dir = Path("results/reports")
    reports = list(settings_dir.glob("audit_report_*.md"))
    assert len(reports) > 0
