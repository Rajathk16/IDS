"""Persistent SQLite store for training run history and offline detection events."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.events import DetectionEvent, TrainingRun
from src.core.logging_config import get_logger
from src.core.settings import get_settings

logger = get_logger("event_store")


class EventStore:
    """Manages SQLite tables for tracking training runs, models, and detection events."""

    def __init__(self, db_path: Optional[Path] = None):
        settings = get_settings()
        self.db_path = Path(db_path or settings.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Training runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    dataset_name TEXT NOT NULL,
                    is_synthetic INTEGER NOT NULL,
                    task_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    feature_selector TEXT NOT NULL,
                    selected_features_count INTEGER NOT NULL,
                    selected_features TEXT NOT NULL,
                    train_samples INTEGER NOT NULL,
                    test_samples INTEGER NOT NULL,
                    training_duration_seconds REAL NOT NULL,
                    inference_latency_ms_per_sample REAL NOT NULL,
                    accuracy REAL NOT NULL,
                    precision REAL NOT NULL,
                    recall REAL NOT NULL,
                    macro_f1 REAL NOT NULL,
                    weighted_f1 REAL NOT NULL,
                    false_positive_rate REAL,
                    model_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    class_imbalance_handled TEXT,
                    metrics_file TEXT,
                    confusion_matrix_plot TEXT
                )
            """)

            # Detection events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    predicted_label TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    is_attack INTEGER NOT NULL,
                    attack_category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    policy_triggered TEXT,
                    raw_features TEXT
                )
            """)
            conn.commit()

    def save_training_run(self, run: TrainingRun) -> None:
        """Insert or replace a training run record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO training_runs (
                    run_id, timestamp, dataset_name, is_synthetic, task_type,
                    model_name, feature_selector, selected_features_count, selected_features,
                    train_samples, test_samples, training_duration_seconds,
                    inference_latency_ms_per_sample, accuracy, precision, recall,
                    macro_f1, weighted_f1, false_positive_rate, model_path,
                    status, error_message, class_imbalance_handled, metrics_file,
                    confusion_matrix_plot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.run_id,
                run.timestamp.isoformat(),
                run.dataset_name,
                1 if run.is_synthetic else 0,
                run.task_type,
                run.model_name,
                run.feature_selector,
                run.selected_features_count,
                json.dumps(run.selected_features),
                run.train_samples,
                run.test_samples,
                run.training_duration_seconds,
                run.inference_latency_ms_per_sample,
                run.accuracy,
                run.precision,
                run.recall,
                run.macro_f1,
                run.weighted_f1,
                run.false_positive_rate,
                run.model_path,
                run.status,
                run.error_message,
                run.class_imbalance_handled,
                run.metrics_file,
                run.confusion_matrix_plot
            ))
            conn.commit()
            logger.info(f"Persisted training run {run.run_id} ({run.model_name}) into SQLite store.")

    def list_training_runs(self, limit: int = 50) -> List[TrainingRun]:
        """Fetch historical training runs ordered by most recent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM training_runs ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()

        runs: List[TrainingRun] = []
        for r in rows:
            runs.append(TrainingRun(
                run_id=r["run_id"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                dataset_name=r["dataset_name"],
                is_synthetic=bool(r["is_synthetic"]),
                task_type=r["task_type"],
                model_name=r["model_name"],
                feature_selector=r["feature_selector"],
                selected_features_count=r["selected_features_count"],
                selected_features=json.loads(r["selected_features"]),
                train_samples=r["train_samples"],
                test_samples=r["test_samples"],
                training_duration_seconds=r["training_duration_seconds"],
                inference_latency_ms_per_sample=r["inference_latency_ms_per_sample"],
                accuracy=r["accuracy"],
                precision=r["precision"],
                recall=r["recall"],
                macro_f1=r["macro_f1"],
                weighted_f1=r["weighted_f1"],
                false_positive_rate=r["false_positive_rate"],
                model_path=r["model_path"],
                status=r["status"],
                error_message=r["error_message"],
                class_imbalance_handled=r["class_imbalance_handled"],
                metrics_file=r["metrics_file"],
                confusion_matrix_plot=r["confusion_matrix_plot"]
            ))
        return runs

    def save_detection_events(self, events: List[DetectionEvent]) -> int:
        """Batch insert detection events."""
        if not events:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            records = [
                (
                    e.id,
                    e.timestamp.isoformat(),
                    e.source_file,
                    e.row_index,
                    e.predicted_label,
                    e.confidence,
                    1 if e.is_attack else 0,
                    e.attack_category,
                    e.severity,
                    e.policy_triggered,
                    json.dumps(e.raw_features) if e.raw_features else None
                )
                for e in events
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO detection_events (
                    id, timestamp, source_file, row_index, predicted_label,
                    confidence, is_attack, attack_category, severity,
                    policy_triggered, raw_features
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

        logger.info(f"Persisted {len(events)} detection event(s) into SQLite store.")
        return len(events)

    def list_detection_events(
        self,
        limit: int = 100,
        severity_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[DetectionEvent]:
        """Fetch recent detection events with optional severity and category filters."""
        query = "SELECT * FROM detection_events"
        params: List[Any] = []
        conditions: List[str] = []

        if severity_filter and severity_filter.upper() != "ALL":
            conditions.append("severity = ?")
            params.append(severity_filter.upper())
        if category_filter and category_filter.lower() != "all":
            conditions.append("attack_category = ?")
            params.append(category_filter)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        events: List[DetectionEvent] = []
        for r in rows:
            events.append(DetectionEvent(
                id=r["id"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                source_file=r["source_file"],
                row_index=r["row_index"],
                predicted_label=r["predicted_label"],
                confidence=r["confidence"],
                is_attack=bool(r["is_attack"]),
                attack_category=r["attack_category"],
                severity=r["severity"],
                policy_triggered=r["policy_triggered"],
                raw_features=json.loads(r["raw_features"]) if r["raw_features"] else None
            ))
        return events

    def get_detection_summary(self) -> Dict[str, Any]:
        """Get aggregate counts for MONITOR screen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM detection_events")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM detection_events WHERE is_attack = 0")
            benign = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM detection_events WHERE is_attack = 1")
            attack = cursor.fetchone()[0]

            cursor.execute("""
                SELECT attack_category, COUNT(*) as cnt
                FROM detection_events
                WHERE is_attack = 1
                GROUP BY attack_category
            """)
            category_counts = {row["attack_category"]: row["cnt"] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT severity, COUNT(*) as cnt
                FROM detection_events
                GROUP BY severity
            """)
            severity_counts = {row["severity"]: row["cnt"] for row in cursor.fetchall()}

        return {
            "total_records_processed": total,
            "benign_count": benign,
            "attack_count": attack,
            "category_distribution": category_counts,
            "severity_distribution": severity_counts
        }
