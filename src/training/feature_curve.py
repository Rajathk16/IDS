"""Feature evaluation curve comparing selector performance across varying k values.

CLI: python -m src.training.feature_curve [--seeds 1 2 3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from src.algorithms.baselines import AllFeaturesSelector, EstablishedKBestSelector
from src.algorithms.feature_selector import DEFAULT_COST, FEATURE_COST, LRRCSFeatureSelector
from src.core.logging_config import get_logger
from src.data.build_dataset import load_dataset_pool
from src.training.run_experiments import extract_features_and_labels

logger = get_logger("feature_curve")


def compute_avg_cost(selected_features: List[str]) -> float:
    """Calculate mean feature extraction cost."""
    if not selected_features:
        return 0.0
    costs = [FEATURE_COST.get(f, DEFAULT_COST) for f in selected_features]
    return float(np.mean(costs))


def run_feature_curve(
    processed_dir: Path = Path("data/processed"),
    results_dir: Path = Path("results"),
    seeds: List[int] = [1, 2, 3],
    n_estimators: int = 50
) -> int:
    """Execute feature curve evaluation."""
    processed_dir = Path(processed_dir)
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    train_exists = (processed_dir / "train_pool.parquet").exists() or (processed_dir / "train_pool.csv").exists()
    test_exists = (processed_dir / "test_pool.parquet").exists() or (processed_dir / "test_pool.csv").exists()

    if not (train_exists and test_exists):
        print(f"[feature_curve] Note: Processed dataset pools not found in '{processed_dir}'. Exiting gracefully.")
        return 0

    logger.info(f"Loading data pools from {processed_dir}...")
    df_train = load_dataset_pool(processed_dir / "train_pool")
    df_test = load_dataset_pool(processed_dir / "test_pool")

    # Extract binary features
    X_train_raw, y_train_raw = extract_features_and_labels(df_train, task_type="binary")
    X_test_raw, y_test_raw = extract_features_and_labels(df_test, task_type="binary")

    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train_raw)
    X_test_imp = imputer.transform(X_test_raw)

    scaler = StandardScaler()
    X_train_scale = scaler.fit_transform(X_train_imp)
    X_test_scale = scaler.transform(X_test_imp)

    all_feat_names = list(X_train_raw.columns)
    df_X_train = pd.DataFrame(X_train_scale, columns=all_feat_names)
    df_X_test = pd.DataFrame(X_test_scale, columns=all_feat_names)

    le = LabelEncoder()
    y_train = le.fit_transform(y_train_raw)
    y_test = le.transform(y_test_raw)

    max_features = len(all_feat_names)
    k_values = [5, 8, 10, 15, 20, 25, min(39, max_features)]
    k_values = sorted(list(set(k for k in k_values if k <= max_features)))

    curve_rows: List[Dict[str, Any]] = []
    lrrc_selections: List[List[str]] = []
    kbest_selections: List[List[str]] = []
    k15_selections: Dict[str, List[str]] = {}

    for k in k_values:
        logger.info(f"--- Evaluating feature subset k={k} ---")

        selectors_to_run = ["select_k_best", "lrrc_stability"]
        if k == max(k_values):
            selectors_to_run.append("all_features")
        selectors_to_run.append("variance_threshold")

        for sel_name in selectors_to_run:
            for seed in seeds:
                if sel_name == "all_features":
                    selector = AllFeaturesSelector()
                    X_tr = selector.fit_transform(df_X_train, y_train)
                    X_te = selector.transform(df_X_test)
                    chosen_features = all_feat_names
                elif sel_name == "variance_threshold":
                    # Compute feature variances and pick top k
                    variances = df_X_train.var().to_dict()
                    sorted_by_var = sorted(variances.keys(), key=lambda f: variances[f], reverse=True)
                    chosen_features = sorted_by_var[:k]
                    X_tr = df_X_train[chosen_features].to_numpy()
                    X_te = df_X_test[chosen_features].to_numpy()
                elif sel_name == "select_k_best":
                    selector = EstablishedKBestSelector(k=k)
                    X_tr = selector.fit_transform(df_X_train, y_train)
                    X_te = selector.transform(df_X_test)
                    chosen_features = selector.selected_features_
                    if k == 15 and seed == seeds[0]:
                        k15_selections["select_k_best"] = list(chosen_features)
                    if k == 15:
                        kbest_selections.append(list(chosen_features))
                elif sel_name == "lrrc_stability":
                    selector = LRRCSFeatureSelector(n_features_to_select=k, random_state=seed)
                    X_tr = selector.fit_transform(df_X_train, y_train, use_stability=True, n_bootstrap=5)
                    X_te = selector.transform(df_X_test)
                    chosen_features = selector.selected_features_
                    if k == 15 and seed == seeds[0]:
                        k15_selections["lrrc_stability"] = list(chosen_features)
                    if k == 15:
                        lrrc_selections.append(list(chosen_features))
                else:
                    continue

                avg_cost = compute_avg_cost(chosen_features)

                # Train RF
                clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=12, min_samples_leaf=2, random_state=seed, n_jobs=-1)
                clf.fit(X_tr, y_train)
                preds = clf.predict(X_te)

                acc = accuracy_score(y_test, preds)
                macro_f1 = f1_score(y_test, preds, average="macro", zero_division=0)

                curve_rows.append({
                    "k": k,
                    "selector": sel_name,
                    "seed": seed,
                    "macro_f1": round(float(macro_f1), 4),
                    "accuracy": round(float(acc), 4),
                    "avg_cost": round(float(avg_cost), 4)
                })

    df_curve = pd.DataFrame(curve_rows)
    csv_curve_path = results_dir / "accuracy_vs_features.csv"
    df_curve.to_csv(csv_curve_path, index=False)
    logger.info(f"Saved accuracy vs features data to {csv_curve_path}")

    # Plot Accuracy and Macro F1 vs k
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=120)
    for sel, grp in df_curve.groupby("selector"):
        means = grp.groupby("k")[["macro_f1", "accuracy"]].mean()
        ax1.plot(means.index, means["macro_f1"], marker="o", label=sel)
        ax2.plot(means.index, means["accuracy"], marker="s", label=sel)

    ax1.set_title("Macro F1 vs. Number of Features (k)", fontweight="bold", fontsize=11)
    ax1.set_xlabel("Number of Features (k)")
    ax1.set_ylabel("Macro F1")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="lower right")

    ax2.set_title("Accuracy vs. Number of Features (k)", fontweight="bold", fontsize=11)
    ax2.set_xlabel("Number of Features (k)")
    ax2.set_ylabel("Accuracy")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="lower right")

    plt.tight_layout()
    plot_path = results_dir / "accuracy_vs_features.png"
    fig.savefig(plot_path)
    plt.close(fig)
    logger.info(f"Saved feature curve plot to {plot_path}")

    # Feature selection frequency across seeds for k=15
    stability_records: List[Dict[str, Any]] = []
    total_seeds = len(seeds)
    for feat in all_feat_names:
        lrrc_cnt = sum(1 for sel_list in lrrc_selections if feat in sel_list)
        kbest_cnt = sum(1 for sel_list in kbest_selections if feat in sel_list)
        stability_records.append({
            "feature": feat,
            "lrrc_selection_freq": round(lrrc_cnt / total_seeds, 4) if total_seeds > 0 else 0.0,
            "selectkbest_selection_freq": round(kbest_cnt / total_seeds, 4) if total_seeds > 0 else 0.0
        })

    df_stab = pd.DataFrame(stability_records)
    stab_path = results_dir / "feature_stability.csv"
    df_stab.to_csv(stab_path, index=False)
    logger.info(f"Saved feature stability table to {stab_path}")

    # Selected features by method for k=15
    method_features_rows = []
    for method, feats in k15_selections.items():
        for rank, f in enumerate(feats, 1):
            method_features_rows.append({
                "method": method,
                "rank": rank,
                "feature": f,
                "cost": FEATURE_COST.get(f, DEFAULT_COST)
            })

    df_methods = pd.DataFrame(method_features_rows)
    methods_path = results_dir / "selected_features_by_method.csv"
    df_methods.to_csv(methods_path, index=False)
    logger.info(f"Saved selected features by method to {methods_path}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate accuracy vs features curves.")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--processed-dir", type=str, default="data/processed")
    parser.add_argument("--results-dir", type=str, default="results")
    args = parser.parse_args()

    return run_feature_curve(
        processed_dir=Path(args.processed_dir),
        results_dir=Path(args.results_dir),
        seeds=args.seeds
    )


if __name__ == "__main__":
    sys.exit(main())
