"""
Diagnostic script: confirm which class index the decision threshold is applied to.
Run from project root:
  .venv\Scripts\python.exe scripts/diag_threshold.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from pathlib import Path
from src.training.train import TrainedModelBundle
from src.data.loader import load_dataset

# --- 1. Load most recent binary model bundle ---
model_dir = Path("models")
bundles = sorted(model_dir.glob("run_binary_*.joblib"), key=lambda p: p.stat().st_mtime, reverse=True)
if not bundles:
    print("No binary model bundles found in models/")
    sys.exit(1)

bundle_path = bundles[0]
print(f"\n=== Loading bundle: {bundle_path.name} ===")
bundle = TrainedModelBundle.load(bundle_path)

# --- 2. Print class information ---
print(f"\nTask type        : {bundle.task_type}")
print(f"Bundle labels    : {bundle.labels}")
clf_classes = getattr(bundle.classifier, 'classes_', None)
le_classes   = getattr(bundle.preprocessor.label_encoder_, 'classes_', None)
print(f"Classifier classes_ : {clf_classes}")
print(f"LabelEncoder classes_: {le_classes}")

# Identify ATTACK index
attack_indices = [i for i, lbl in enumerate(bundle.labels) if "attack" in str(lbl).lower()]
benign_indices = [i for i, lbl in enumerate(bundle.labels) if "benign" in str(lbl).lower()]
attack_idx = attack_indices[0] if attack_indices else None
benign_idx = benign_indices[0] if benign_indices else None
print(f"\nATTACK index in labels: {attack_idx}  (label: {bundle.labels[attack_idx] if attack_idx is not None else 'N/A'})")
print(f"BENIGN index in labels: {benign_idx}  (label: {bundle.labels[benign_idx] if benign_idx is not None else 'N/A'})")

# --- 3. Load a small sample from dataset ---
data_dir = Path("raw")
csv_files = list(data_dir.rglob("*.csv"))
if not csv_files:
    print("\nNo CSVs found in raw/. Generating synthetic test data instead.")
    # Generate synthetic data with both classes
    n = 200
    from src.data.taxonomy import CICIOT2023_FEATURE_NAMES
    feature_cols = CICIOT2023_FEATURE_NAMES[:39]
    rng = np.random.default_rng(42)
    df_test = pd.DataFrame(rng.random((n, len(feature_cols))), columns=feature_cols)
    half = n // 2
    df_test['label'] = ['BenignTraffic'] * half + ['DDoS-SYN_Flood'] * half
else:
    print(f"\nLoading sample from: {csv_files[0].name}")
    df_raw, _, _ = load_dataset(csv_files[0], sample_limit=400)
    # Take 200 rows with both classes for analysis
    target_col = 'label' if 'label' in df_raw.columns else 'Label'
    if target_col in df_raw.columns:
        benign_rows = df_raw[df_raw[target_col].str.lower().str.contains('benign', na=False)].head(100)
        attack_rows = df_raw[~df_raw[target_col].str.lower().str.contains('benign', na=False)].head(100)
        df_test = pd.concat([benign_rows, attack_rows], ignore_index=True)
    else:
        df_test = df_raw.head(200)
    target_col_found = target_col

print(f"Test sample size: {len(df_test)}")

# --- 4. Extract features and get raw probabilities ---
X_df, y_raw = bundle.preprocessor.extract_features_and_target(df_test)
probs = bundle.predict_proba(X_df)

print(f"\nprobs.shape: {probs.shape}")
print(f"probs[:5]:\n{np.round(probs[:5], 4)}")

# --- 5. Show first 10 rows with both class probabilities ---
print(f"\n{'Row':<4} {'True Label':<20} {'proba[:,0]':<12} {'proba[:,1]':<12} {'label[0]':<12} {'label[1]':<12}")
print("-" * 80)
for i in range(min(10, len(df_test))):
    true_lbl = str(y_raw.iloc[i]) if hasattr(y_raw, 'iloc') else str(y_raw[i])
    p0, p1 = float(probs[i, 0]), float(probs[i, 1])
    print(f"{i:<4} {true_lbl:<20} {p0:<12.4f} {p1:<12.4f} {bundle.labels[0]:<12} {bundle.labels[1]:<12}")

# --- 6. Compare FPR when threshold applied to index 0 vs index 1 ---
THRESHOLD = 0.70
print(f"\n=== Threshold = {THRESHOLD} comparison ===")

target_col_in_test = None
for cand in ['label', 'Label', 'LABEL']:
    if cand in df_test.columns:
        target_col_in_test = cand
        break

if target_col_in_test:
    from src.data.taxonomy import map_to_binary
    true_binary = df_test[target_col_in_test].astype(str).apply(map_to_binary).values
    n_benign_true = np.sum(true_binary == "BENIGN")
    n_attack_true = np.sum(true_binary == "ATTACK")
    print(f"True BENIGN: {n_benign_true}, True ATTACK: {n_attack_true}")

    for col_idx in [0, 1]:
        col_label = bundle.labels[col_idx]
        preds_attack = probs[:, col_idx] >= THRESHOLD
        fp = np.sum(preds_attack & (true_binary == "BENIGN"))
        tn = np.sum(~preds_attack & (true_binary == "BENIGN"))
        tp = np.sum(preds_attack & (true_binary == "ATTACK"))
        fn = np.sum(~preds_attack & (true_binary == "ATTACK"))
        fpr_val = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr_val = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        print(f"\n  Threshold applied to proba[:,{col_idx}] ('{col_label}' confidence):")
        print(f"    TP={tp}, TN={tn}, FP={fp}, FN={fn}")
        print(f"    FPR = {fpr_val:.4f} ({fpr_val*100:.2f}%)")
        print(f"    FNR = {fnr_val:.4f} ({fnr_val*100:.2f}%)")
        print(f"    Accuracy = {(tp+tn)/len(true_binary):.4f}")
else:
    print("No ground truth column found in test sample. Cannot compute FPR comparison.")

# --- 7. Verify predictor.py threshold direction ---
print(f"\n=== Current predictor.py behaviour ===")
print("In predictor.py lines 61-68:")
print("  attack_col_indices = [i for i, lbl in enumerate(bundle.labels) if 'attack' in str(lbl).lower()]")
print(f"  With bundle.labels={bundle.labels}")
attack_col_indices = [i for i, lbl in enumerate(bundle.labels) if "attack" in str(lbl).lower()]
atk_idx_pred = attack_col_indices[0] if attack_col_indices else 0
print(f"  -> atk_idx resolved to: {atk_idx_pred}  ('{bundle.labels[atk_idx_pred]}')")
print(f"  -> Threshold applied to proba[:, {atk_idx_pred}]  CORRECT={atk_idx_pred == attack_idx}")

print("\n=== DIAGNOSIS COMPLETE ===")
