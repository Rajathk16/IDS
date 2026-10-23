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
        record_events: bool = True
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
        preds = self.bundle.predict(X_df)
        probs = self.bundle.predict_proba(X_df)

        elapsed = time.perf_counter() - t0
        latency_ms = (elapsed / max(1, len(df))) * 1000.0

        events: List[DetectionEvent] = []
        confidences = np.max(probs, axis=1)

        for i in range(len(df)):
            pred_label = str(preds[i])
            conf = float(confidences[i])
            is_atk = pred_label.lower() not in ("benign", "benigntraffic", "normal")
            
            # Map to category for policy matching
            if self.bundle.task_type == "binary":
                cat = "Benign" if not is_atk else "Attack"
            else:
                cat = map_to_category(pred_label)

            # Evaluate policy
            severity, triggered_policy = self.policies.evaluate(cat, conf)

            # Sample key numeric features for audit record
            sample_feats = {}
            for k in ["flow_duration", "Rate", "Tot sum", "syn_count", "ack_count"]:
                if k in df.columns:
                    val = df.iloc[i][k]
                    if pd.notna(val) and np.isfinite(val):
                        sample_feats[k] = float(val)

            event = DetectionEvent(
                source_file=source_name,
                row_index=i,
                predicted_label=pred_label,
                confidence=round(conf, 4),
                is_attack=is_atk,
                attack_category=cat,
                severity=severity,
                policy_triggered=triggered_policy,
                raw_features=sample_feats if sample_feats else None
            )
            events.append(event)

        # Annotate input DataFrame with prediction columns
        df_result = df.copy()
        df_result["predicted_label"] = preds
        df_result["prediction_confidence"] = np.round(confidences, 4)
        df_result["is_attack"] = [e.is_attack for e in events]
        df_result["attack_category"] = [e.attack_category for e in events]
        df_result["alert_severity"] = [e.severity for e in events]
        df_result["policy_triggered"] = [e.policy_triggered for e in events]

        if record_events:
            self.event_store.save_detection_events(events)

        logger.info(
            f"Inference complete: processed {len(df):,} records in {elapsed:.3f}s "
            f"({latency_ms:.4f} ms/sample). Attacks detected: {sum(e.is_attack for e in events):,}."
        )

        return df_result, events

    def predict_csv_file(
        self,
        csv_path: Path,
        sample_limit: Optional[int] = None,
        record_events: bool = True
    ) -> Tuple[pd.DataFrame, List[DetectionEvent]]:
        """Run offline inference directly on a CSV file."""
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Input file not found: {csv_path}")

        df = pd.read_csv(csv_path, nrows=sample_limit)
        return self.predict_dataframe(df, source_name=csv_path.name, record_events=record_events)
