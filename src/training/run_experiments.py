"""Rigorous multi-seed empirical evaluation on balanced train pools and natural test distributions.

CLI: python -m src.training.run_experiments [--dataset-mode balanced_pool] [--n-per-class 6000] [--seeds 1 2 3 4 5]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score
)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from src.algorithms.feature_selector import LRRCSFeatureSelector
from src.core.logging_config import get_logger
from src.data.build_dataset import load_dataset_pool
from src.data.taxonomy import get_supported_categories, map_to_binary, map_to_category
from src.training.stats_utils import clopper_pearson, fpr_with_ci

logger = get_logger("run_experiments")


def extract_features_and_labels(
    df: pd.DataFrame,
    task_type: str = "binary"
) -> Tuple[pd.DataFrame, np.ndarray]:
    """Separate numeric features from target labels."""
    df_clean = df.copy()
    target_col = None
    for cand in ["mapped_category", "label", "Label", "class", "Class"]:
        if cand in df_clean.columns:
            target_col = cand
            break

    if target_col is None:
        raise ValueError("Target label column not found in DataFrame.")

    raw_labels = df_clean[target_col].astype(str)
    if task_type == "binary":
        y = raw_labels.apply(map_to_binary).to_numpy()
    else:
        y = raw_labels.apply(map_to_category).to_numpy()

    cols_to_drop = [c for c in ["mapped_category", "label", "Label", "class", "Class", "attack_type"] if c in df_clean.columns]
    X = df_clean.drop(columns=cols_to_drop)

    # Coerce to numeric; replace inf/-inf with NaN so the imputer handles them
    for col in X.columns:
        if not np.issubdtype(X[col].dtype, np.number):
            X[col] = pd.to_numeric(X[col], errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan)

    return X, y


def plot_cm(cm: np.ndarray, labels: List[str], title: str, out_path: Path):
    """Plot and save confusion matrix figure."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(5, len(labels) * 0.9), max(4, len(labels) * 0.8)), dpi=120)
    cax = ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.85)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="left", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    thresh = cm.max() / 2.0 if cm.max() > 0 else 1.0
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = cm[i, j]
            color = "white" if val > thresh else "black"
            ax.text(j, i, f"{val:,}", ha="center", va="center", color=color, fontsize=8)

    ax.set_xlabel("Predicted", fontweight="bold")
    ax.set_ylabel("True", fontweight="bold")
    ax.set_title(title, pad=15, fontweight="bold", fontsize=10)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def run_all_experiments(
    processed_dir: Path = Path("data/processed"),
    results_dir: Path = Path("results"),
    seeds: List[int] = [1, 2, 3, 4, 5],
    n_estimators: int = 50,
    k_features: int = 15
) -> int:
    """Execute evaluation across multiple random seeds."""
    processed_dir = Path(processed_dir)
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Check that processed pool files exist
    train_exists = (processed_dir / "train_pool.parquet").exists() or (processed_dir / "train_pool.csv").exists()
    test_exists = (processed_dir / "test_pool.parquet").exists() or (processed_dir / "test_pool.csv").exists()

    if not (train_exists and test_exists):
        print(f"[run_experiments] ERROR: Processed dataset pools not found in '{processed_dir}'. Run build_dataset first.")
        return 1

    logger.info(f"Loading dataset pools from {processed_dir}...")
    df_train = load_dataset_pool(processed_dir / "train_pool")
    df_test = load_dataset_pool(processed_dir / "test_pool")

    logger.info(f"Loaded train_pool ({len(df_train):,} rows) and test_pool ({len(df_test):,} rows)")

    raw_results_rows: List[Dict[str, Any]] = []
    per_class_rows: List[Dict[str, Any]] = []

    # Evaluate for each seed
    for seed_idx, seed in enumerate(seeds, 1):
        logger.info(f"=== Running Seed {seed} ({seed_idx}/{len(seeds)}) ===")

        # ------------------- 1. BINARY TASK -------------------
        logger.info(f"[Seed {seed}] Evaluating Binary Task...")
        X_train_raw, y_train_bin = extract_features_and_labels(df_train, task_type="binary")
        X_test_raw, y_test_bin = extract_features_and_labels(df_test, task_type="binary")

        # Impute & Scale (fit strictly on train)
        imputer = SimpleImputer(strategy="median")
        X_train_imp = imputer.fit_transform(X_train_raw)
        X_test_imp = imputer.transform(X_test_raw)

        scaler = StandardScaler()
        X_train_scale = scaler.fit_transform(X_train_imp)
        X_test_scale = scaler.transform(X_test_imp)

        feature_names = list(X_train_raw.columns)
        df_X_train_scale = pd.DataFrame(X_train_scale, columns=feature_names)
        df_X_test_scale = pd.DataFrame(X_test_scale, columns=feature_names)

        le_bin = LabelEncoder()
        y_train_bin_enc = le_bin.fit_transform(y_train_bin)
        y_test_bin_enc = le_bin.transform(y_test_bin)

        # LRRC-FS
        selector_bin = LRRCSFeatureSelector(n_features_to_select=k_features, random_state=seed)
        X_train_sub = selector_bin.fit_transform(df_X_train_scale, y_train_bin_enc, use_stability=False)
        X_test_sub = selector_bin.transform(df_X_test_scale)

        # Train Random Forest
        rf_bin = RandomForestClassifier(n_estimators=n_estimators, max_depth=12, min_samples_leaf=2, random_state=seed, n_jobs=-1)
        rf_bin.fit(X_train_sub, y_train_bin_enc)

        # Measure prediction latency
        t0 = time.perf_counter()
        y_pred_bin_enc = rf_bin.predict(X_test_sub)
        pred_time = time.perf_counter() - t0
        latency_ms = (pred_time / len(X_test_sub)) * 1000.0

        # Evaluate binary metrics
        acc_b = accuracy_score(y_test_bin_enc, y_pred_bin_enc)
        bacc_b = balanced_accuracy_score(y_test_bin_enc, y_pred_bin_enc)
        macro_f1_b = f1_score(y_test_bin_enc, y_pred_bin_enc, average="macro", zero_division=0)
        weighted_f1_b = f1_score(y_test_bin_enc, y_pred_bin_enc, average="weighted", zero_division=0)
        mcc_b = matthews_corrcoef(y_test_bin_enc, y_pred_bin_enc)

        cm_b = confusion_matrix(y_test_bin_enc, y_pred_bin_enc, labels=[0, 1])
        # labels: sorted alphabetically by le_bin.classes_ (ATTACK=0, BENIGN=1)
        benign_cls_idx = list(le_bin.classes_).index("BENIGN") if "BENIGN" in le_bin.classes_ else 1
        attack_cls_idx = 1 - benign_cls_idx

        tn = int(cm_b[benign_cls_idx, benign_cls_idx])
        fp = int(cm_b[benign_cls_idx, attack_cls_idx])
        tp = int(cm_b[attack_cls_idx, attack_cls_idx])
        fn = int(cm_b[attack_cls_idx, benign_cls_idx])
        n_negatives = fp + tn

        fpr_str = fpr_with_ci(fp, n_negatives)
        fpr_lo, fpr_hi = clopper_pearson(fp, n_negatives)
        fpr_val = (fp / n_negatives) if n_negatives > 0 else 0.0

        if seed == seeds[0]:
            cm_bin_path = results_dir / "confusion_matrix_binary_s1.png"
            plot_cm(cm_b, list(le_bin.classes_), f"Binary Confusion Matrix (Seed {seed})", cm_bin_path)

        raw_results_rows.append({
            "task": "binary",
            "model": "random_forest",
            "strategy": "standard",
            "seed": seed,
            "accuracy": acc_b,
            "balanced_accuracy": bacc_b,
            "macro_f1": macro_f1_b,
            "weighted_f1": weighted_f1_b,
            "mcc": mcc_b,
            "latency_ms": latency_ms,
            "fp": fp,
            "tn": tn,
            "tp": tp,
            "fn": fn,
            "fpr": fpr_val,
            "fpr_ci_low": fpr_lo,
            "fpr_ci_high": fpr_hi,
            "fpr_display": fpr_str
        })

        # ------------------- 2. 8-CLASS TASK -------------------
        logger.info(f"[Seed {seed}] Evaluating 8-Class Multiclass Task...")
        X_train_raw_m, y_train_multi = extract_features_and_labels(df_train, task_type="multiclass")
        X_test_raw_m, y_test_multi = extract_features_and_labels(df_test, task_type="multiclass")

        # Encode classes canonically
        all_cats = get_supported_categories()
        le_multi = LabelEncoder()
        le_multi.fit(all_cats)
        y_train_multi_enc = le_multi.transform(y_train_multi)
        y_test_multi_enc = le_multi.transform(y_test_multi)

        # Impute & Scale
        imp_m = SimpleImputer(strategy="median")
        X_train_imp_m = imp_m.fit_transform(X_train_raw_m)
        X_test_imp_m = imp_m.transform(X_test_raw_m)

        sc_m = StandardScaler()
        X_train_scale_m = sc_m.fit_transform(X_train_imp_m)
        X_test_scale_m = sc_m.transform(X_test_imp_m)

        df_X_train_scale_m = pd.DataFrame(X_train_scale_m, columns=list(X_train_raw_m.columns))
        df_X_test_scale_m = pd.DataFrame(X_test_scale_m, columns=list(X_test_raw_m.columns))

        # LRRC-FS
        selector_multi = LRRCSFeatureSelector(n_features_to_select=k_features, random_state=seed)
        X_train_sub_m = selector_multi.fit_transform(df_X_train_scale_m, y_train_multi_enc, use_stability=False)
        X_test_sub_m = selector_multi.transform(df_X_test_scale_m)

        # Imbalance strategies for 8-class:
        # 1. Plain (unweighted)
        # 2. class_weight='balanced'
        # 3. RandomUnderSampler
        # 4. SMOTE
        strategies = [
            ("plain", None, False),
            ("class_weight_balanced", None, True),
            ("undersampling", "rus", False),
            ("smote", "smote", False)
        ]

        skip_smote = False

        for strat_name, resample_type, use_cw in strategies:
            if strat_name == "smote" and skip_smote:
                logger.info("Skipping SMOTE due to prior timeout flag.")
                continue

            X_tr, y_tr = X_train_sub_m, y_train_multi_enc
            if resample_type == "rus":
                rus = RandomUnderSampler(random_state=seed)
                X_tr, y_tr = rus.fit_resample(X_train_sub_m, y_train_multi_enc)
            elif resample_type == "smote":
                t_smote_0 = time.perf_counter()
                try:
                    # class count check
                    unique, counts = np.unique(y_tr, return_counts=True)
                    min_samples = int(np.min(counts))
                    if min_samples < 2:
                        logger.warning("SMOTE skipped: minority class < 2 samples.")
                        continue
                    k_nn = min(5, min_samples - 1)
                    smote = SMOTE(k_neighbors=k_nn, random_state=seed)
                    X_tr, y_tr = smote.fit_resample(X_train_sub_m, y_train_multi_enc)
                    smote_dur = time.perf_counter() - t_smote_0
                    if smote_dur > 180.0 and seed == seeds[0]:
                        logger.warning(f"SMOTE took {smote_dur:.1f}s (>3 min). Skipping for future seeds.")
                        skip_smote = True
                except Exception as exc:
                    logger.warning(f"SMOTE failed: {exc}. Skipping.")
                    continue

            cw = "balanced" if use_cw else None
            rf_m = RandomForestClassifier(n_estimators=n_estimators, max_depth=12, min_samples_leaf=2, class_weight=cw, random_state=seed, n_jobs=-1)
            rf_m.fit(X_tr, y_tr)

            t0 = time.perf_counter()
            y_pred_m = rf_m.predict(X_test_sub_m)
            lat_m = ((time.perf_counter() - t0) / len(X_test_sub_m)) * 1000.0

            acc_m = accuracy_score(y_test_multi_enc, y_pred_m)
            bacc_m = balanced_accuracy_score(y_test_multi_enc, y_pred_m)
            macro_f1_m = f1_score(y_test_multi_enc, y_pred_m, average="macro", zero_division=0)
            weighted_f1_m = f1_score(y_test_multi_enc, y_pred_m, average="weighted", zero_division=0)
            mcc_m = matthews_corrcoef(y_test_multi_enc, y_pred_m)

            if seed == seeds[0] and strat_name == "plain":
                cm_m = confusion_matrix(y_test_multi_enc, y_pred_m, labels=range(len(all_cats)))
                cm_8c_path = results_dir / "confusion_matrix_8class_s1.png"
                plot_cm(cm_m, all_cats, f"8-Class Confusion Matrix (Seed {seed})", cm_8c_path)

            raw_results_rows.append({
                "task": "8class",
                "model": "random_forest",
                "strategy": strat_name,
                "seed": seed,
                "accuracy": acc_m,
                "balanced_accuracy": bacc_m,
                "macro_f1": macro_f1_m,
                "weighted_f1": weighted_f1_m,
                "mcc": mcc_m,
                "latency_ms": lat_m,
                "fp": None,
                "tn": None,
                "tp": None,
                "fn": None,
                "fpr": None,
                "fpr_ci_low": None,
                "fpr_ci_high": None,
                "fpr_display": "N/A"
            })

            # Per-class metrics
            cr = classification_report(
                y_test_multi_enc,
                y_pred_m,
                labels=range(len(all_cats)),
                target_names=all_cats,
                output_dict=True,
                zero_division=0
            )
            for cname in all_cats:
                if cname in cr:
                    per_class_rows.append({
                        "task": "8class",
                        "strategy": strat_name,
                        "seed": seed,
                        "class_name": cname,
                        "precision": cr[cname]["precision"],
                        "recall": cr[cname]["recall"],
                        "f1_score": cr[cname]["f1-score"],
                        "support": cr[cname]["support"]
                    })

    # Save outputs
    df_raw_res = pd.DataFrame(raw_results_rows)
    df_per_class = pd.DataFrame(per_class_rows)

    df_raw_res.to_csv(results_dir / "final_results_raw.csv", index=False)
    df_per_class.to_csv(results_dir / "per_class_metrics.csv", index=False)

    # Aggregations (mean ± std)
    summary_rows: List[Dict[str, Any]] = []
    final_dict: Dict[str, Any] = {"seeds": seeds, "results": {}}

    metric_cols = ["accuracy", "balanced_accuracy", "macro_f1", "weighted_f1", "mcc", "latency_ms", "fpr"]

    grouped = df_raw_res.groupby(["task", "model", "strategy"])
    for (task, model, strategy), grp in grouped:
        key = f"{task}_{model}_{strategy}"
        final_dict["results"][key] = {}
        row = {"task": task, "model": model, "strategy": strategy, "n_seeds": len(grp)}

        for m in metric_cols:
            vals = grp[m].dropna()
            if len(vals) > 0:
                mean_v = float(vals.mean())
                std_v = float(vals.std()) if len(vals) > 1 else 0.0
                row[f"{m}_mean"] = round(mean_v, 4)
                row[f"{m}_std"] = round(std_v, 4)
                final_dict["results"][key][m] = {
                    "mean": round(mean_v, 4),
                    "std": round(std_v, 4)
                }

        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(results_dir / "final_results.csv", index=False)

    with open(results_dir / "final_results.json", "w", encoding="utf-8") as f:
        json.dump(final_dict, f, indent=2)

    logger.info(f"Experiments complete. Results saved to {results_dir / 'final_results.json'}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run multi-seed evaluation experiments.")
    parser.add_argument("--dataset-mode", type=str, default="balanced_pool")
    parser.add_argument("--n-per-class", type=int, default=6000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--processed-dir", type=str, default="data/processed")
    parser.add_argument("--results-dir", type=str, default="results")
    args = parser.parse_args()

    return run_all_experiments(
        processed_dir=Path(args.processed_dir),
        results_dir=Path(args.results_dir),
        seeds=args.seeds
    )


if __name__ == "__main__":
    sys.exit(main())
