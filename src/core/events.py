"""Structured Pydantic data models for events, audits, runs, and metrics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DetectionEvent(BaseModel):
    """Structured record of an offline intrusion detection event."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_file: str = Field(description="Name or path of the input CSV processed")
    row_index: int = Field(description="Zero-indexed row number from the source data")
    predicted_label: str = Field(description="Model prediction (e.g. 'BENIGN', 'DDoS-UDP_Flood')")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Prediction probability")
    is_attack: bool = Field(description="True if classified as any attack; False if Benign")
    attack_category: str = Field(
        default="Benign",
        description="Category: 'Benign', 'DDoS', 'DoS', 'Recon', 'Web', 'BruteForce', 'Spoofing', 'Mirai'"
    )
    severity: str = Field(
        default="INFO",
        description="Alert severity: 'INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'"
    )
    policy_triggered: Optional[str] = Field(default=None, description="Policy rule name if alerted")
    raw_features: Optional[Dict[str, float]] = Field(
        default=None,
        description="Key numerical feature values from the packet flow record"
    )


class TrainingRun(BaseModel):
    """Metadata and evaluation results from a machine learning training run."""

    run_id: str = Field(default_factory=lambda: f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dataset_name: str
    is_synthetic: bool = False
    task_type: str = Field(description="'binary' or 'multiclass'")
    model_name: str = Field(description="'decision_tree', 'random_forest', 'extra_trees', etc.")
    feature_selector: str = Field(description="'lrrc', 'all', 'variance', 'kbest'")
    selected_features_count: int
    selected_features: List[str]
    train_samples: int
    test_samples: int
    training_duration_seconds: float
    inference_latency_ms_per_sample: float
    accuracy: float
    precision: float
    recall: float
    macro_f1: float
    weighted_f1: float
    false_positive_rate: Optional[float] = None
    model_path: str
    status: str = "SUCCESS"  # SUCCESS, FAILED, RUNNING
    error_message: Optional[str] = None
    class_imbalance_handled: Optional[str] = None
    metrics_file: Optional[str] = None
    confusion_matrix_plot: Optional[str] = None


class DatasetAuditResult(BaseModel):
    """Audit report for inspecting CICIoT2023 or synthetic CSV files."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_path: str
    is_synthetic: bool = False
    file_count: int
    total_size_mb: float
    total_rows: int
    column_count: int
    feature_columns: List[str]
    target_column: Optional[str] = None
    missing_value_count: int = 0
    infinite_value_count: int = 0
    duplicate_row_count: int = 0
    class_distribution: Dict[str, int] = Field(default_factory=dict)
    memory_usage_mb: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    schema_valid: bool = True


class EvaluationReport(BaseModel):
    """Comprehensive evaluation metrics and confusion matrix details."""

    task_type: str
    model_name: str
    feature_selector: str
    accuracy: float
    precision: float
    recall: float
    macro_f1: float
    weighted_f1: float
    false_positive_rate: Optional[float] = None
    inference_latency_ms: float
    training_duration_seconds: float
    per_class_metrics: Dict[str, Dict[str, float]]
    labels: List[str]
    confusion_matrix: List[List[int]]
    warning: Optional[str] = None
