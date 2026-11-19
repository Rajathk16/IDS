"""
Threshold calibration utilities.

Sweeps decision thresholds on a validation split to find the operating point
that meets a target FPR while maximising attack recall.

Usage (called from train_model after fitting the bundle):
    from src.training.calibrate import calibrate_decision_threshold
    calibration = calibrate_decision_threshold(bundle, X_val, y_val_binary)
    bundle.metadata["calibration"] = calibration
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Thresholds to sweep (0.30 → 0.95 in steps of 0.05)
SWEEP_THRESHOLDS: List[float] = [round(t, 2) for t in np.arange(0.30, 0.96, 0.05).tolist()]

# Canonical target FPR operating points
TARGET_FPRS: List[float] = [0.01, 0.05, 0.10]


def _confusion_at_threshold(
    attack_proba: np.ndarray,
    true_binary: np.ndarray,  # 0=benign, 1=attack
    threshold: float,
) -> Tuple[int, int, int, int]:
    """Return (TP, TN, FP, FN) for a given threshold applied to attack probability."""
    preds = (attack_proba >= threshold).astype(int)
    tp = int(np.sum((preds == 1) & (true_binary == 1)))
    tn = int(np.sum((preds == 0) & (true_binary == 0)))
    fp = int(np.sum((preds == 1) & (true_binary == 0)))
    fn = int(np.sum((preds == 0) & (true_binary == 1)))
    return tp, tn, fp, fn


def calibrate_decision_threshold(
    bundle: Any,  # TrainedModelBundle (avoid circular import)
    X_val: Any,   # pd.DataFrame with features (not yet transformed)
    y_val_raw: Any,  # array-like of raw string labels
) -> Dict[str, Any]:
    """
    Sweep decision thresholds on a held-out validation set and return a
    calibration report.

    Returns a dict with:
      - sweep: list of per-threshold metrics dicts
      - recommended: threshold chosen at default 5% FPR target
      - targets: best thresholds for 1%, 5%, 10% FPR targets
      - note: disclaimer about generalisation to unseen traffic
    """
    import pandas as pd
    from src.data.taxonomy import map_to_binary

    if bundle.task_type != "binary":
        # Calibration only meaningful for binary classification
        return {
            "sweep": [],
            "recommended": 0.50,
            "targets": {},
            "note": "Threshold calibration only supported for binary classification."
        }

    # Map raw labels to binary int (0=BENIGN, 1=ATTACK)
    if hasattr(y_val_raw, "tolist"):
        y_val_list = y_val_raw.tolist()
    else:
        y_val_list = list(y_val_raw)

    true_binary = np.array([
        0 if map_to_binary(str(lbl)) == "BENIGN" else 1
        for lbl in y_val_list
    ], dtype=int)

    n_benign = int(np.sum(true_binary == 0))
    n_attack = int(np.sum(true_binary == 1))

    if n_benign == 0 or n_attack == 0:
        return {
            "sweep": [],
            "recommended": 0.50,
            "targets": {},
            "note": (
                "Validation set contains only one class. "
                "Cannot calibrate threshold without both BENIGN and ATTACK samples."
            )
        }

    # Get attack probabilities from bundle
    # Identify attack class index from labels
    attack_idx = None
    for i, lbl in enumerate(bundle.labels):
        if "attack" in str(lbl).lower():
            attack_idx = i
            break
    if attack_idx is None:
        attack_idx = 0  # fallback

    if not isinstance(X_val, pd.DataFrame):
        try:
            X_val = pd.DataFrame(X_val)
        except Exception:
            pass

    proba_matrix = bundle.predict_proba(X_val)
    attack_proba = proba_matrix[:, attack_idx]

    # Sweep thresholds
    sweep: List[Dict[str, Any]] = []
    for t in SWEEP_THRESHOLDS:
        tp, tn, fp, fn = _confusion_at_threshold(attack_proba, true_binary, t)
        fpr_val = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr_val = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1   = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        acc  = (tp + tn) / len(true_binary) if len(true_binary) > 0 else 0.0
        sweep.append({
            "threshold": t,
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "fpr": round(fpr_val, 6),
            "fnr": round(fnr_val, 6),
            "precision": round(prec, 6),
            "recall": round(rec, 6),
            "f1": round(f1, 6),
            "accuracy": round(acc, 6),
        })

    # Find best threshold per target FPR:
    # For each target, pick the highest threshold whose FPR <= target
    # (highest threshold = fewest false alarms while maximising recall)
    targets: Dict[str, Any] = {}
    for target_fpr in TARGET_FPRS:
        candidates = [s for s in sweep if s["fpr"] <= target_fpr]
        if candidates:
            # Among candidates with FPR <= target, choose highest recall, break ties by highest threshold
            best = max(candidates, key=lambda s: (s["recall"], s["threshold"]))
        else:
            # No threshold achieves the target FPR on this validation set;
            # choose the threshold with lowest FPR overall
            best = min(sweep, key=lambda s: (s["fpr"], -s["threshold"]))
        key = f"fpr_{int(target_fpr * 100)}pct"
        targets[key] = {
            "target_fpr": target_fpr,
            "selected_threshold": best["threshold"],
            "validation_fpr": best["fpr"],
            "validation_recall": best["recall"],
            "validation_f1": best["f1"],
            "met_target": best["fpr"] <= target_fpr,
        }

    # Default recommendation: 5% FPR target
    recommended_threshold = targets.get("fpr_5pct", {}).get("selected_threshold", 0.50)

    return {
        "sweep": sweep,
        "recommended": recommended_threshold,
        "targets": targets,
        "attack_idx": attack_idx,
        "val_n_benign": n_benign,
        "val_n_attack": n_attack,
        "note": (
            "Threshold selected on held-out validation data only. "
            "Actual FPR on live traffic may differ due to distribution shift. "
            "Re-calibrate periodically with representative traffic samples."
        )
    }
