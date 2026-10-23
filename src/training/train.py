"""Model training engine supporting binary/multiclass tasks, feature selection, and class imbalance handling."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from src.algorithms.baselines import AllFeaturesSelector, EstablishedKBestSelector, VarianceThresholdSelector
from src.algorithms.feature_selector import LRRCSFeatureSelector
from src.core.events import TrainingRun
from src.core.logging_config import get_logger
from src.core.settings import get_settings
from src.data.loader import is_synthetic_file, load_dataset
from src.data.preprocess import IoTDataPreprocessor
from src.data.split import split_dataset
from src.detection.event_store import EventStore
from src.training.evaluate import (
    evaluate_predictions,
    measure_inference_latency,
    plot_and_save_confusion_matrix,
    save_metrics_json
)

logger = get_logger("training_engine")


def get_classifier(
    model_name: str,
    random_state: int = 42,
    use_class_weight: bool = False
) -> BaseEstimator:
    """Instantiate a bounded-complexity scikit-learn classifier."""
    cw = "balanced" if use_class_weight else None
    name_clean = model_name.lower().strip()

    if name_clean in ("decision_tree", "dt"):
        return DecisionTreeClassifier(max_depth=12, min_samples_leaf=3, random_state=random_state, class_weight=cw)
    elif name_clean in ("random_forest", "rf"):
        return RandomForestClassifier(n_estimators=50, max_depth=12, min_samples_leaf=2, random_state=random_state, class_weight=cw, n_jobs=-1)
    elif name_clean in ("extra_trees", "et"):
        return ExtraTreesClassifier(n_estimators=50, max_depth=12, min_samples_leaf=2, random_state=random_state, class_weight=cw, n_jobs=-1)
    elif name_clean in ("gradient_boosting", "hist_gb", "gb"):
        # HistGradientBoostingClassifier handles tabular data fast and natively
        return HistGradientBoostingClassifier(max_iter=50, max_depth=8, random_state=random_state)
    else:
        raise ValueError(
            f"Unsupported model: '{model_name}'. Choose from 'decision_tree', 'random_forest', 'extra_trees', 'gradient_boosting'."
        )


def get_feature_selector(
    selector_name: str,
    n_features: int = 15,
    w_rel: float = 0.5,
    w_red: float = 0.3,
    w_cost: float = 0.2,
    random_state: int = 42
) -> BaseEstimator:
    """Instantiate the requested feature selector (custom LRRC-FS or baseline)."""
    name_clean = selector_name.lower().strip()

    if name_clean in ("lrrc", "lrrc_fs", "lrrc-fs"):
        return LRRCSFeatureSelector(
            n_features_to_select=n_features,
            relevance_weight=w_rel,
            redundancy_weight=w_red,
            cost_weight=w_cost,
            random_state=random_state
        )
    elif name_clean in ("all", "all_features", "none"):
        return AllFeaturesSelector()
    elif name_clean in ("variance", "variance_threshold"):
        return VarianceThresholdSelector(threshold=0.01)
    elif name_clean in ("kbest", "select_k_best", "f_classif"):
        return EstablishedKBestSelector(k=n_features)
    else:
        raise ValueError(
            f"Unsupported feature selector: '{selector_name}'. Choose from 'lrrc', 'all', 'variance', 'kbest'."
        )


def apply_resampling(
    X_train: np.ndarray,
    y_train: np.ndarray,
    strategy: Optional[str] = None,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Apply resampling exclusively to training data.
    Never applied to the validation or test partitions.
    """
    if not strategy or strategy.lower() in ("none", "false"):
        return X_train, y_train, "None"

    strat = strategy.lower().strip()
    if strat in ("under_sample", "undersample", "rus"):
        rus = RandomUnderSampler(random_state=random_state)
        X_res, y_res = rus.fit_resample(X_train, y_train)
        logger.info(f"Applied RandomUnderSampler: reduced train size from {len(X_train)} to {len(X_res)}.")
        return X_res, y_res, "RandomUnderSampler"

    elif strat in ("smote", "oversample"):
        # Safe check for minimum class count required by SMOTE k_neighbors
        unique, counts = np.unique(y_train, return_counts=True)
        min_samples = int(np.min(counts))
        if min_samples < 2:
            logger.warning(
                f"Minority class has only {min_samples} sample(s). Cannot safely apply SMOTE. Skipping resampling."
            )
            return X_train, y_train, "Skipped (class too small for SMOTE)"
        k_neighbors = min(5, min_samples - 1)
        smote = SMOTE(k_neighbors=k_neighbors, random_state=random_state)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        logger.info(f"Applied SMOTE: increased train size from {len(X_train)} to {len(X_res)}.")
        return X_res, y_res, f"SMOTE(k={k_neighbors})"

    return X_train, y_train, "None"


class TrainedModelBundle:
    """Wrapper encapsulating preprocessor, selector, classifier, and metadata."""

    def __init__(
        self,
        model_name: str,
        task_type: str,
        preprocessor: IoTDataPreprocessor,
        selector: BaseEstimator,
        classifier: BaseEstimator,
        labels: List[str],
        metadata: Dict[str, Any]
    ):
        self.model_name = model_name
        self.task_type = task_type
        self.preprocessor = preprocessor
        self.selector = selector
        self.classifier = classifier
        self.labels = labels
        self.metadata = metadata

    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Run end-to-end inference from raw/aligned features to decoded label strings."""
        X_trans = self.preprocessor.transform(X)
        X_sub = self.selector.transform(X_trans)
        y_indices = self.classifier.predict(X_sub)
        return self.preprocessor.decode_target(y_indices)

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Return class probability distributions."""
        X_trans = self.preprocessor.transform(X)
        X_sub = self.selector.transform(X_trans)
        if hasattr(self.classifier, "predict_proba"):
            return self.classifier.predict_proba(X_sub)
        # Fallback for models without predict_proba
        preds = self.classifier.predict(X_sub)
        n_classes = len(self.labels)
        probs = np.zeros((len(preds), n_classes))
        for i, p in enumerate(preds):
            probs[i, p] = 1.0
        return probs

    def save(self, file_path: Path) -> Path:
        """Persist model bundle with joblib."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_dict = {
            "model_name": self.model_name,
            "task_type": self.task_type,
            "preprocessor": self.preprocessor,
            "selector": self.selector,
            "classifier": self.classifier,
            "labels": self.labels,
            "manifest": self.preprocessor.manifest_.to_dict() if self.preprocessor.manifest_ else None,
            "selected_features": getattr(self.selector, "selected_features_", []),
            "metadata": self.metadata
        }
        joblib.dump(bundle_dict, file_path, compress=3)
        logger.info(f"Persisted model bundle to {file_path}")
        return file_path

    @classmethod
    def load(cls, file_path: Path) -> TrainedModelBundle:
        """Safely load and validate model bundle compatibility."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")

        try:
            bundle_dict = joblib.load(file_path)
        except Exception as exc:
            raise ValueError(f"Failed to load model file {file_path}: {exc}")

        # Validate bundle structure
        required_keys = ["model_name", "task_type", "preprocessor", "selector", "classifier", "labels"]
        for k in required_keys:
            if k not in bundle_dict:
                raise ValueError(f"Incompatible or corrupted model bundle: missing key '{k}'.")

        return cls(
            model_name=bundle_dict["model_name"],
            task_type=bundle_dict["task_type"],
            preprocessor=bundle_dict["preprocessor"],
            selector=bundle_dict["selector"],
            classifier=bundle_dict["classifier"],
            labels=bundle_dict["labels"],
            metadata=bundle_dict.get("metadata", {})
        )


def train_model(
    data_path: Path,
    task_type: str = "binary",
    model_name: str = "random_forest",
    feature_selector: str = "lrrc",
    n_features: int = 15,
    sample_limit: Optional[int] = 20000,
    resampling_strategy: Optional[str] = None,
    use_class_weight: bool = False,
    random_seed: int = 42
) -> Tuple[TrainedModelBundle, TrainingRun]:
    """
    Execute complete end-to-end training, feature selection, evaluation, and persistence pipeline.
    """
    settings = get_settings()
    data_path = Path(data_path)
    run_id = f"run_{task_type}_{model_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"Starting training run {run_id} on {data_path.name}...")

    # 1. Load data
    df_raw, is_synth, files = load_dataset(data_path, sample_limit=sample_limit)

    # 2. Split dataset with leakage resistance safeguards
    df_train, df_test, _ = split_dataset(
        df_raw,
        target_column="label",
        test_size=settings.test_size,
        val_size=0.0,
        random_seed=random_seed,
        stratify=True
    )

    # 3. Fit Preprocessing ONLY on training set
    preprocessor = IoTDataPreprocessor(task_type=task_type, target_column="label")
    X_train_raw, y_train_raw = preprocessor.extract_features_and_target(df_train)
    X_test_raw, y_test_raw = preprocessor.extract_features_and_target(df_test)

    X_train_trans = preprocessor.fit_transform(X_train_raw, y_train_raw)
    y_train_enc = preprocessor.encode_target(y_train_raw)

    X_test_trans = preprocessor.transform(X_test_raw)
    y_test_enc = preprocessor.encode_target(y_test_raw)
    classes_list = [str(c) for c in preprocessor.label_encoder_.classes_]

    # Convert to DataFrames preserving feature column names for selectors
    df_X_train = pd.DataFrame(X_train_trans, columns=preprocessor.feature_names_)
    df_X_test = pd.DataFrame(X_test_trans, columns=preprocessor.feature_names_)

    # 4. Fit Feature Selector ONLY on training set
    selector = get_feature_selector(
        feature_selector,
        n_features=n_features,
        w_rel=settings.lrrc_relevance_weight,
        w_red=settings.lrrc_redundancy_weight,
        w_cost=settings.lrrc_cost_weight,
        random_state=random_seed
    )
    X_train_selected = selector.fit_transform(df_X_train, y_train_enc)
    X_test_selected = selector.transform(df_X_test)
    selected_features = getattr(selector, "selected_features_", preprocessor.feature_names_)

    # 5. Apply Resampling if requested (ONLY on training partition)
    X_train_final, y_train_final, resampling_applied = apply_resampling(
        X_train_selected,
        y_train_enc,
        strategy=resampling_strategy,
        random_state=random_seed
    )

    # 6. Train Classifier
    t_start = time.perf_counter()
    clf = get_classifier(model_name, random_state=random_seed, use_class_weight=use_class_weight)
    clf.fit(X_train_final, y_train_final)
    training_duration = time.perf_counter() - t_start

    # 7. Evaluate on Test Split
    latency_ms = measure_inference_latency(clf, X_test_selected)
    y_pred_enc = clf.predict(X_test_selected)

    eval_report = evaluate_predictions(
        y_true=y_test_enc,
        y_pred=y_pred_enc,
        labels=classes_list,
        task_type=task_type,
        model_name=model_name,
        feature_selector=feature_selector,
        training_duration_seconds=training_duration,
        inference_latency_ms=latency_ms
    )

    # 8. Save Metrics & Plots
    metrics_path = save_metrics_json(eval_report, run_id)
    plot_path = plot_and_save_confusion_matrix(eval_report.confusion_matrix, classes_list, run_id)

    # 9. Create and Save Model Bundle
    metadata = {
        "run_id": run_id,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "is_synthetic": is_synth,
        "dataset_name": data_path.name,
        "sample_limit": sample_limit,
        "task_type": task_type,
        "model_name": model_name,
        "feature_selector": feature_selector,
        "selected_features_count": len(selected_features),
        "selected_features": selected_features,
        "train_samples": len(X_train_final),
        "test_samples": len(X_test_selected),
        "training_duration_seconds": round(training_duration, 4),
        "inference_latency_ms": round(latency_ms, 4),
        "resampling": resampling_applied,
        "class_weight": use_class_weight,
        "accuracy": eval_report.accuracy,
        "macro_f1": eval_report.macro_f1,
    }

    model_file = settings.model_dir / f"{run_id}.joblib"
    bundle = TrainedModelBundle(
        model_name=model_name,
        task_type=task_type,
        preprocessor=preprocessor,
        selector=selector,
        classifier=clf,
        labels=classes_list,
        metadata=metadata
    )
    bundle.save(model_file)

    # 10. Record Training Run in EventStore
    training_run = TrainingRun(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        dataset_name=data_path.name,
        is_synthetic=is_synth,
        task_type=task_type,
        model_name=model_name,
        feature_selector=feature_selector,
        selected_features_count=len(selected_features),
        selected_features=selected_features,
        train_samples=len(X_train_final),
        test_samples=len(X_test_selected),
        training_duration_seconds=round(training_duration, 4),
        inference_latency_ms_per_sample=round(latency_ms, 4),
        accuracy=eval_report.accuracy,
        precision=eval_report.precision,
        recall=eval_report.recall,
        macro_f1=eval_report.macro_f1,
        weighted_f1=eval_report.weighted_f1,
        false_positive_rate=eval_report.false_positive_rate,
        model_path=str(model_file),
        status="SUCCESS",
        class_imbalance_handled=f"{resampling_applied} (class_weight={use_class_weight})",
        metrics_file=str(metrics_path),
        confusion_matrix_plot=str(plot_path)
    )

    event_store = EventStore()
    event_store.save_training_run(training_run)

    logger.info(
        f"Training run {run_id} complete! Accuracy: {eval_report.accuracy:.4f}, "
        f"Macro F1: {eval_report.macro_f1:.4f}, Latency: {latency_ms:.4f} ms/sample."
    )

    return bundle, training_run
