"""Evaluation module for accuracy, macro/weighted F1, FPR, latency, and confusion matrix plotting."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless terminal & server environments
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)
from src.core.events import EvaluationReport
from src.core.logging_config import get_logger
from src.core.settings import get_settings

logger = get_logger("model_evaluation")


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: List[str],
    task_type: str,
    model_name: str,
    feature_selector: str,
    training_duration_seconds: float,
    inference_latency_ms: float
) -> EvaluationReport:
    """
    Compute rigorous evaluation metrics on test partition.
    
    Includes warning flag if class imbalance is severe enough that standard accuracy
    might be deceptive (e.g. high accuracy while minority attack classes have poor recall).
    """
    acc = float(accuracy_score(y_true, y_pred))
    prec_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=range(len(labels)))
    cm_list = [[int(val) for val in row] for row in cm]

    # Calculate False Positive Rate (FPR)
    # For binary classification where 0=BENIGN and 1=ATTACK:
    # FPR = FP / (FP + TN)
    fpr: Optional[float] = None
    if task_type == "binary" and len(labels) == 2:
        # Assuming label 0 is BENIGN and 1 is ATTACK
        benign_idx = 0 if "benign" in str(labels[0]).lower() else 1
        attack_idx = 1 - benign_idx
        tn = cm[benign_idx, benign_idx]
        fp = cm[benign_idx, attack_idx]
        denom = fp + tn
        fpr = float(fp / denom) if denom > 0 else 0.0

    # Per-class metrics
    report_dict = classification_report(
        y_true,
        y_pred,
        labels=range(len(labels)),
        target_names=labels,
        output_dict=True,
        zero_division=0
    )

    per_class: Dict[str, Dict[str, float]] = {}
    for name in labels:
        if name in report_dict:
            per_class[name] = {
                "precision": float(report_dict[name]["precision"]),
                "recall": float(report_dict[name]["recall"]),
                "f1-score": float(report_dict[name]["f1-score"]),
                "support": float(report_dict[name]["support"])
            }

    # Imbalance warning check
    warning = None
    if acc > 0.90 and f1_macro < 0.70:
        warning = (
            "Caution: High overall accuracy (>{:.1f}%) with low Macro F1 ({:.2f}) "
            "indicates significant class imbalance. The classifier may be biased toward "
            "the majority class while missing minority attack patterns."
        ).format(acc * 100, f1_macro)

    return EvaluationReport(
        task_type=task_type,
        model_name=model_name,
        feature_selector=feature_selector,
        accuracy=round(acc, 4),
        precision=round(prec_macro, 4),
        recall=round(rec_macro, 4),
        macro_f1=round(f1_macro, 4),
        weighted_f1=round(f1_weighted, 4),
        false_positive_rate=round(fpr, 4) if fpr is not None else None,
        inference_latency_ms=round(inference_latency_ms, 4),
        training_duration_seconds=round(training_duration_seconds, 4),
        per_class_metrics=per_class,
        labels=labels,
        confusion_matrix=cm_list,
        warning=warning
    )


def measure_inference_latency(
    model_pipeline: Any,
    X_test: Union[np.ndarray, Any],
    n_repetitions: int = 3
) -> float:
    """Measure inference latency in milliseconds per sample on the test split."""
    n_samples = len(X_test)
    if n_samples == 0:
        return 0.0

    durations: List[float] = []
    # Warmup
    _ = model_pipeline.predict(X_test[:min(10, n_samples)])

    for _ in range(n_repetitions):
        t0 = time.perf_counter()
        _ = model_pipeline.predict(X_test)
        elapsed = time.perf_counter() - t0
        durations.append(elapsed)

    mean_sec = float(np.mean(durations))
    latency_ms_per_sample = (mean_sec / n_samples) * 1000.0
    return latency_ms_per_sample


def plot_and_save_confusion_matrix(
    cm: List[List[int]],
    labels: List[str],
    run_id: str,
    output_dir: Optional[Path] = None
) -> Path:
    """Generate and save confusion matrix figure."""
    settings = get_settings()
    out_dir = Path(output_dir or (settings.results_dir / "plots"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"confusion_matrix_{run_id}.png"

    cm_arr = np.array(cm, dtype=int)
    n_classes = len(labels)

    fig, ax = plt.subplots(figsize=(max(6, n_classes * 0.9), max(5, n_classes * 0.8)), dpi=120)
    cax = ax.matshow(cm_arr, cmap=plt.cm.Blues, alpha=0.85)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    # Label axes
    ax.set_xticks(range(n_classes))
    ax.set_yticks(range(n_classes))
    ax.set_xticklabels(labels, rotation=45, ha="left", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    # Annotate counts inside cells
    thresh = cm_arr.max() / 2.0 if cm_arr.max() > 0 else 1.0
    for i in range(n_classes):
        for j in range(n_classes):
            val = cm_arr[i, j]
            color = "white" if val > thresh else "black"
            ax.text(j, i, f"{val:,}", ha="center", va="center", color=color, fontsize=8)

    ax.set_xlabel("Predicted Label", fontweight="bold", labelpad=10)
    ax.set_ylabel("True Label", fontweight="bold", labelpad=10)
    ax.set_title(f"Confusion Matrix - Run {run_id}", pad=20, fontsize=11, fontweight="bold")
    plt.tight_layout()

    fig.savefig(out_path)
    plt.close(fig)
    logger.info(f"Saved confusion matrix chart to {out_path}")
    return out_path


def save_metrics_json(report: EvaluationReport, run_id: str) -> Path:
    """Save machine-readable evaluation report to JSON file."""
    settings = get_settings()
    metrics_dir = settings.results_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    out_path = metrics_dir / f"{run_id}_metrics.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2)

    return out_path
