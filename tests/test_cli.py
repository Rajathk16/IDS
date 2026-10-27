"""Unit tests for CLI commands and argument parser."""

from pathlib import Path
import pytest
from src.cli import build_parser, main
from src.core.engine import IDSEngine


def test_cli_parser_subcommands():
    parser = build_parser()

    # Synthetic command
    args_syn = parser.parse_args(["synthetic", "--samples", "100", "--output", "test_syn.csv"])
    assert args_syn.command == "synthetic"
    assert args_syn.samples == 100

    # Audit command
    args_aud = parser.parse_args(["audit", "--max-rows", "500"])
    assert args_aud.command == "audit"
    assert args_aud.max_rows == 500

    # Train command
    args_trn = parser.parse_args([
        "train", "--task", "binary", "--model", "decision_tree",
        "--selector", "lrrc", "--features", "8", "--samples", "200"
    ])
    assert args_trn.command == "train"
    assert args_trn.task == "binary"
    assert args_trn.model == "decision_tree"
    assert args_trn.features == 8

    # Policy command
    args_pol = parser.parse_args(["policy", "show"])
    assert args_pol.command == "policy"
    assert args_pol.action == "show"

    # Compare selectors command
    args_cmp = parser.parse_args(["compare-selectors", "--samples", "200", "--task", "binary", "--features", "6"])
    assert args_cmp.command == "compare-selectors"
    assert args_cmp.samples == 200
    assert args_cmp.features == 6

    # Compare imbalance command
    args_imb = parser.parse_args(["compare-imbalance", "--samples", "200", "--model", "decision_tree"])
    assert args_imb.command == "compare-imbalance"
    assert args_imb.samples == 200
    assert args_imb.model == "decision_tree"


def test_cli_execution_workflow(tmp_path: Path, monkeypatch):
    # Test synthetic generation via engine directly as invoked by CLI
    engine = IDSEngine()
    syn_file = engine.generate_synthetic(n_samples=100, output_name="cli_test.csv")
    assert syn_file.exists()

    # Test audit execution
    audit_res = engine.audit(target_path=syn_file, max_rows=100)
    assert audit_res.total_rows == 100

    # Test training execution
    bundle, run = engine.train(
        data_path=syn_file,
        task_type="binary",
        model_name="decision_tree",
        feature_selector="lrrc",
        n_features=6,
        sample_limit=100
    )
    assert run.status == "SUCCESS"
