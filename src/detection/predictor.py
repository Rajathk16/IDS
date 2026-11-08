"""Offline batch and streaming inference engine using persisted model bundles."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from src.core.events import DetectionEvent
from src.core.logging_config import get_logger
from src.core.policies import get_policies
from src.data.loader import discover_csv_files, load_dataset
from src.data.taxonomy import map_to_category
from src.detection.event_store import EventStore
from src.training.train import TrainedModelBundle

logger = get_logger("offline_predictor")


class OfflinePredictor:
    """Loads a persisted model bundle and executes offline detection on CSV traffic data."""

    def __init__(self, model_bundle: Union[Path, TrainedModelBundle]):
        if isinstance(model_bundle, (str, Path)):
            self.bundle = TrainedModelBundle.load(Path(model_bundle))
        else:
            self.bundle = model_bundle

        self.policies = get_policies()
        self.event_store = EventStore()
        logger.info(
            f"Initialized OfflinePredictor with model '{self.bundle.model_name}' "
            f"(Task: {self.bundle.task_type}, Classes: {self.bundle.labels})."
        )

    def predict_dataframe(
        self,
        df: pd.DataFrame,
        source_name: str = "offline_input.csv",
        record_events: bool = True,
        decision_threshold: Optional[float] = None
    ) -> Tuple[pd.DataFrame, List[DetectionEvent]]:
        """
        Run offline detection on an input DataFrame.
        
        Returns:
            (annotated_dataframe, list_of_detection_events)
        """
        t0 = time.perf_counter()
        # Separate features if label column happens to be present in input
        preprocessor = self.bundle.preprocessor
        X_df, _ = preprocessor.extract_features_and_target(df)

        # Generate predictions and probabilities
        probs = self.bundle.predict_proba(X_df)

        # Threshold calibration for binary classification (mitigates high False Positive Rate)
        if self.bundle.task_type == "binary" and decision_threshold is not None and probs.shape[1] == 2:
            attack_col_indices = [i for i, lbl in enumerate(self.bundle.labels) if "attack" in str(lbl).lower()]
            atk_idx = attack_col_indices[0] if attack_col_indices else 0
            benign_idx = 1 - atk_idx
            atk_probs = probs[:, atk_idx]

            is_attacks = [bool(p >= decision_threshold) for p in atk_probs]
            pred_labels = [str(self.bundle.labels[atk_idx]) if atk else str(self.bundle.labels[benign_idx]) for atk in is_attacks]
            preds = np.array(pred_labels)
            confidences = np.array([float(p if atk else (1.0 - p)) for atk, p in zip(is_attacks, atk_probs)])
        else:
            preds = self.bundle.predict(X_df)
            confidences = np.max(probs, axis=1)
            pred_labels = [str(p) for p in preds]
            is_attacks = [lbl.lower() not in ("benign", "benigntraffic", "normal") for lbl in pred_labels]

        elapsed = time.perf_counter() - t0
        latency_ms = (elapsed / max(1, len(df))) * 1000.0

        # Fast category mapping
        if self.bundle.task_type == "binary":
            categories = ["Benign" if not atk else "Attack" for atk in is_attacks]
        else:
            categories = [map_to_category(lbl) for lbl in pred_labels]

        # Policy evaluation
        severities = []
        policies_triggered = []
        for cat, conf in zip(categories, confidences):
            sev, pol = self.policies.evaluate(cat, float(conf))
            severities.append(sev)
            policies_triggered.append(pol)

        # Vectorized feature dictionary sampling for top rows only
        feat_cols = [k for k in ["flow_duration", "Rate", "Tot sum", "syn_count", "ack_count"] if k in df.columns]
        sample_size = min(len(df), 1000)
        sample_records = df[feat_cols].iloc[:sample_size].to_dict(orient="records") if feat_cols else [{} for _ in range(sample_size)]

        events: List[DetectionEvent] = []
        for i in range(sample_size):
            clean_feats = {k: float(v) for k, v in sample_records[i].items() if pd.notna(v) and np.isfinite(v)}
            events.append(DetectionEvent(
                source_file=source_name,
                row_index=i,
                predicted_label=pred_labels[i],
                confidence=round(float(confidences[i]), 4),
                is_attack=is_attacks[i],
                attack_category=categories[i],
                severity=severities[i],
                policy_triggered=policies_triggered[i],
                raw_features=clean_feats if clean_feats else None
            ))

        # Annotate input DataFrame with prediction columns
        df_result = df.copy()
        df_result["predicted_label"] = preds
        df_result["prediction_confidence"] = np.round(confidences, 4)
        df_result["is_attack"] = is_attacks
        df_result["attack_category"] = categories
        df_result["alert_severity"] = severities
        df_result["policy_triggered"] = policies_triggered

        if record_events and events:
            # Persist high-signal sample events to SQLite
            self.event_store.save_detection_events(events[:500])

        total_attacks = sum(is_attacks)
        logger.info(
            f"Inference complete: processed {len(df):,} records in {elapsed:.3f}s "
            f"({latency_ms:.4f} ms/sample). Attacks detected: {total_attacks:,}."
        )

        return df_result, events

    def predict_csv_file(
        self,
        csv_path: Path,
        sample_limit: Optional[int] = None,
        record_events: bool = True,
        decision_threshold: Optional[float] = None
    ) -> Tuple[pd.DataFrame, List[DetectionEvent]]:
        """Run offline inference directly on a CSV file."""
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Input file not found: {csv_path}")

        df = pd.read_csv(csv_path, nrows=sample_limit)
        return self.predict_dataframe(
            df,
            source_name=csv_path.name,
            record_events=record_events,
            decision_threshold=decision_threshold
        )
