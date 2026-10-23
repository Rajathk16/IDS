"""Empirical experiments comparing feature selection algorithms and class imbalance strategies."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from src.core.logging_config import get_logger
from src.core.settings import get_settings
from src.training.train import train_model

logger = get_logger("experiments")


def run_feature_selection_comparison(
    data_path: Path,
    task_type: str = "binary",
    model_name: str = "random_forest",
    n_features: int = 15,
    sample_limit: Optional[int] = 5000,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Empirically compare LRRC-FS against:
      1. All Features baseline
      2. Variance Threshold baseline
      3. Established SelectKBest (ANOVA F-statistic)
    
    Evaluates:
      - Feature count
      - Training duration (s)
      - Inference latency (ms/sample)
      - Accuracy
      - Macro F1-score
      - False Positive Rate (FPR)
    """
    settings = get_settings()
    data_path = Path(data_path)
    logger.info(f"Running Feature Selector Comparison Experiment on {data_path.name}...")

    selectors = ["all", "variance", "kbest", "lrrc"]
    results: List[Dict[str, Any]] = []

    for sel in selectors:
        logger.info(f"Testing selector: '{sel}'...")
        try:
            bundle, run = train_model(
                data_path=data_path,
                task_type=task_type,
                model_name=model_name,
                feature_selector=sel,
                n_features=n_features,
                sample_limit=sample_limit,
                random_seed=random_seed
            )
            results.append({
                "selector": sel,
                "feature_count": run.selected_features_count,
                "training_duration_s": run.training_duration_seconds,
                "inference_latency_ms": run.inference_latency_ms_per_sample,
                "accuracy": run.accuracy,
                "macro_f1": run.macro_f1,
                "weighted_f1": run.weighted_f1,
                "false_positive_rate": run.false_positive_rate,
                "status": "SUCCESS"
            })
        except Exception as exc:
            logger.error(f"Error testing selector '{sel}': {exc}")
            results.append({
                "selector": sel,
                "status": "FAILED",
                "error": str(exc)
            })

    # Summary analysis
    df_res = pd.DataFrame(results)
    
    # Save report
    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = settings.results_dir / "reports" / f"feature_selection_comparison_{ts_str}.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    md = [
        "# Empirical Feature Selection Comparison Report",
        f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}",
        f"**Dataset:** `{data_path.name}` | **Task:** `{task_type}` | **Model:** `{model_name}`",
        "",
        "## Performance Comparison Table",
        "| Feature Selector | Features Selected | Train Time (s) | Inference Latency (ms/sample) | Accuracy | Macro F1 | Weighted F1 | FPR |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in results:
        if r.get("status") == "SUCCESS":
            fpr_str = f"{r['false_positive_rate']:.4f}" if r.get("false_positive_rate") is not None else "N/A"
            md.append(
                f"| `{r['selector']}` | {r['feature_count']} | {r['training_duration_s']:.3f}s | "
                f"{r['inference_latency_ms']:.4f} ms | {r['accuracy']:.4f} | {r['macro_f1']:.4f} | "
                f"{r['weighted_f1']:.4f} | {fpr_str} |"
            )
        else:
            md.append(f"| `{r['selector']}` | FAILED | - | - | - | - | - | - |")

    md.extend([
        "",
        "## Technical Analysis",
        "- **Feature Reduction Efficiency:** LRRC-FS prunes redundant and high-cost features while maintaining statistical relevance to attack targets.",
        "- **Inference Overhead:** Evaluating whether reduced feature subsets lead to faster per-packet processing times.",
        "- **Trade-off Evaluation:** Quantifies whether LRRC-FS maintains comparable detection efficacy (Macro F1) to All Features while utilizing fewer network traffic metrics."
    ])

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return {
        "timestamp": ts_str,
        "results": results,
        "report_file": str(report_file)
    }


def run_class_imbalance_comparison(
    data_path: Path,
    task_type: str = "binary",
    model_name: str = "random_forest",
    sample_limit: Optional[int] = 5000,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Empirically compare methods for handling IoT class imbalance:
      1. Baseline: Unweighted learning
      2. Class Weighting: Cost-sensitive class_weight='balanced'
      3. Resampling: RandomUnderSampler on training split
      4. Resampling: SMOTE on training split
    """
    settings = get_settings()
    data_path = Path(data_path)
    logger.info(f"Running Class Imbalance Comparison Experiment on {data_path.name}...")

    configs = [
        ("None (Unweighted)", None, False),
        ("Class Weighted", None, True),
        ("Random Under-Sampling", "under_sample", False),
        ("SMOTE Oversampling", "smote", False),
    ]

    results: List[Dict[str, Any]] = []

    for name, strategy, use_cw in configs:
        logger.info(f"Testing imbalance strategy: '{name}'...")
        try:
            bundle, run = train_model(
                data_path=data_path,
                task_type=task_type,
                model_name=model_name,
                feature_selector="lrrc",
                n_features=15,
                sample_limit=sample_limit,
                resampling_strategy=strategy,
                use_class_weight=use_cw,
                random_seed=random_seed
            )
            results.append({
                "strategy": name,
                "accuracy": run.accuracy,
                "precision": run.precision,
                "recall": run.recall,
                "macro_f1": run.macro_f1,
                "weighted_f1": run.weighted_f1,
                "false_positive_rate": run.false_positive_rate,
                "status": "SUCCESS"
            })
        except Exception as exc:
            logger.error(f"Error testing imbalance strategy '{name}': {exc}")
            results.append({
                "strategy": name,
                "status": "FAILED",
                "error": str(exc)
            })

    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = settings.results_dir / "reports" / f"class_imbalance_comparison_{ts_str}.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    md = [
        "# Class Imbalance Comparison Report",
        f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}",
        f"**Dataset:** `{data_path.name}` | **Task:** `{task_type}` | **Model:** `{model_name}`",
        "",
        "## Imbalance Handling Performance",
        "| Strategy | Accuracy | Precision | Recall | Macro F1 | Weighted F1 | FPR |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in results:
        if r.get("status") == "SUCCESS":
            fpr_str = f"{r['false_positive_rate']:.4f}" if r.get("false_positive_rate") is not None else "N/A"
            md.append(
                f"| `{r['strategy']}` | {r['accuracy']:.4f} | {r['precision']:.4f} | "
                f"{r['recall']:.4f} | {r['macro_f1']:.4f} | {r['weighted_f1']:.4f} | {fpr_str} |"
            )
        else:
            md.append(f"| `{r['strategy']}` | FAILED | - | - | - | - | - |")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return {
        "timestamp": ts_str,
        "results": results,
        "report_file": str(report_file)
    }
