"""Central orchestration engine coordinating audits, training, inference, and event storage."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from src.core.events import DatasetAuditResult, DetectionEvent, TrainingRun
from src.core.logging_config import get_logger
from src.core.policies import PolicyConfig, get_policies, save_policies
from src.core.settings import AppSettings, get_settings, update_settings
from src.data.audit import audit_dataset
from src.data.loader import discover_csv_files
from src.data.synthetic import generate_synthetic_dataset
from src.detection.event_store import EventStore
from src.detection.predictor import OfflinePredictor
from src.training.experiments import run_class_imbalance_comparison, run_feature_selection_comparison
from src.training.train import TrainedModelBundle, train_model

logger = get_logger("engine")


class IDSEngine:
    """Core domain controller for the IoT Intrusion and DDoS Detection prototype."""

    def __init__(self, settings: Optional[AppSettings] = None):
        self.settings = settings or get_settings()
        self.event_store = EventStore(self.settings.db_path)
        self.active_model_bundle: Optional[TrainedModelBundle] = None

    def discover_datasets(self) -> Dict[str, List[Path]]:
        """Return discovered raw and synthetic CSV files."""
        raw_files = []
        if self.settings.data_dir.exists():
            try:
                raw_files = discover_csv_files(self.settings.data_dir)
            except Exception:
                pass

        synthetic_files = []
        if self.settings.synthetic_dir.exists():
            try:
                synthetic_files = discover_csv_files(self.settings.synthetic_dir)
            except Exception:
                pass

        return {
            "raw": raw_files,
            "synthetic": synthetic_files
        }

    def generate_synthetic(self, n_samples: int = 3000, output_name: str = "synthetic_ciciot2023.csv") -> Path:
        """Generate synthetic dataset for offline experimentation."""
        target_path = self.settings.synthetic_dir / output_name
        return generate_synthetic_dataset(target_path, n_samples=n_samples, random_seed=self.settings.random_seed)

    def audit(self, target_path: Optional[Path] = None, max_rows: int = 50000) -> DatasetAuditResult:
        """Run dataset audit on specified path or default data/raw (fallback to synthetic)."""
        path = target_path
        if not path:
            discovered = self.discover_datasets()
            if discovered["raw"]:
                path = discovered["raw"][0]
            elif discovered["synthetic"]:
                path = discovered["synthetic"][0]
            else:
                # Generate a default synthetic dataset so beginner is never stuck!
                path = self.generate_synthetic(n_samples=2000)

        return audit_dataset(path, max_rows_for_audit=max_rows)

    def train(
        self,
        data_path: Optional[Path] = None,
        task_type: Optional[str] = None,
        model_name: Optional[str] = None,
        feature_selector: Optional[str] = None,
        n_features: Optional[int] = None,
        sample_limit: Optional[int] = None,
        resampling_strategy: Optional[str] = None,
        use_class_weight: bool = False
    ) -> Tuple[TrainedModelBundle, TrainingRun]:
        """Execute a full training run."""
        path = data_path
        if not path:
            discovered = self.discover_datasets()
            if discovered["raw"]:
                path = discovered["raw"][0]
            elif discovered["synthetic"]:
                path = discovered["synthetic"][0]
            else:
                path = self.generate_synthetic(n_samples=3000)

        task = task_type or self.settings.default_task
        model = model_name or self.settings.default_model
        selector = feature_selector or self.settings.default_feature_selector
        k_feats = n_features or self.settings.lrrc_max_features
        limit = sample_limit or self.settings.sample_limit

        bundle, run = train_model(
            data_path=path,
            task_type=task,
            model_name=model,
            feature_selector=selector,
            n_features=k_feats,
            sample_limit=limit,
            resampling_strategy=resampling_strategy,
            use_class_weight=use_class_weight,
            random_seed=self.settings.random_seed
        )
        self.active_model_bundle = bundle
        return bundle, run

    def run_selector_comparison(self, data_path: Optional[Path] = None) -> Dict[str, Any]:
        """Run empirical feature selection comparison."""
        path = data_path or self._get_default_data_path()
        return run_feature_selection_comparison(path, random_seed=self.settings.random_seed)

    def run_imbalance_comparison(self, data_path: Optional[Path] = None) -> Dict[str, Any]:
        """Run class imbalance comparison experiment."""
        path = data_path or self._get_default_data_path()
        return run_class_imbalance_comparison(path, random_seed=self.settings.random_seed)

    def predict_offline(
        self,
        csv_path: Path,
        model_path: Optional[Path] = None,
        sample_limit: Optional[int] = 1000
    ) -> Tuple[pd.DataFrame, List[DetectionEvent]]:
        """Run offline inference on a CSV file."""
        if model_path:
            predictor = OfflinePredictor(model_path)
        elif self.active_model_bundle:
            predictor = OfflinePredictor(self.active_model_bundle)
        else:
            # Check for saved models in model_dir
            saved_models = sorted(list(self.settings.model_dir.glob("*.joblib")), reverse=True)
            if saved_models:
                predictor = OfflinePredictor(saved_models[0])
            else:
                raise FileNotFoundError("No trained model available. Please run training first.")

        return predictor.predict_csv_file(csv_path, sample_limit=sample_limit)

    def list_runs(self, limit: int = 50) -> List[TrainingRun]:
        return self.event_store.list_training_runs(limit=limit)

    def list_events(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[DetectionEvent]:
        return self.event_store.list_detection_events(limit=limit, severity_filter=severity, category_filter=category)

    def get_monitor_stats(self) -> Dict[str, Any]:
        return self.event_store.get_detection_summary()

    def _get_default_data_path(self) -> Path:
        discovered = self.discover_datasets()
        if discovered["raw"]:
            return discovered["raw"][0]
        if discovered["synthetic"]:
            return discovered["synthetic"][0]
        return self.generate_synthetic(n_samples=2500)
