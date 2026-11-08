"""Multi-threaded HTTP Server and REST API backend for DEVRAKSHAK Web Dashboard."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
import sys
import time
import traceback
from typing import Any, Dict, List, Optional
import urllib.parse

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.engine import IDSEngine
from src.core.events import DetectionEvent
from src.core.logging_config import get_logger
from src.core.policies import PolicyConfig, get_policies, save_policies
from src.core.settings import get_settings
from src.data.loader import discover_csv_files, inspect_schema
from src.data.taxonomy import map_to_binary, map_to_category
from src.detection.predictor import OfflinePredictor
from src.training.train import TrainedModelBundle

logger = get_logger("web_server")
STATIC_DIR = Path(__file__).resolve().parent / "static"


def get_system_telemetry() -> Dict[str, Any]:
    """Return genuine system hardware metrics for CPU, RAM, and Disk."""
    disk_percent = 0.0
    disk_used_gb = 0.0
    disk_total_gb = 0.0
    try:
        total, used, free = shutil.disk_usage(".")
        disk_percent = round((used / total) * 100.0, 1)
        disk_used_gb = round(used / (1024 ** 3), 1)
        disk_total_gb = round(total / (1024 ** 3), 1)
    except Exception:
        pass

    mem_percent = 0.0
    mem_total_gb = 0.0
    mem_avail_gb = 0.0
    try:
        if sys.platform == "win32":
            import ctypes
            class MEM(ctypes.Structure):
                _fields_ = [
                    ('l', ctypes.c_ulong),
                    ('load', ctypes.c_ulong),
                    ('tot', ctypes.c_ulonglong),
                    ('avail', ctypes.c_ulonglong),
                    ('pf_tot', ctypes.c_ulonglong),
                    ('pf_avail', ctypes.c_ulonglong),
                    ('v_tot', ctypes.c_ulonglong),
                    ('v_avail', ctypes.c_ulonglong),
                    ('ext', ctypes.c_ulonglong)
                ]
            m = MEM()
            m.l = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            mem_percent = float(m.load)
            mem_total_gb = round(m.tot / (1024 ** 3), 1)
            mem_avail_gb = round(m.avail / (1024 ** 3), 1)
    except Exception:
        pass

    return {
        "disk_percent": disk_percent,
        "disk_used_gb": disk_used_gb,
        "disk_total_gb": disk_total_gb,
        "mem_percent": mem_percent,
        "mem_total_gb": mem_total_gb,
        "mem_avail_gb": mem_avail_gb,
        "cpu_threads": os.cpu_count() or 4
    }


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server preventing requests from blocking each other."""
    daemon_threads = True
    allow_reuse_address = True


class DevRakshakAPIHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler providing REST API endpoints and static asset serving."""

    engine: IDSEngine = None  # Class-level engine instance

    @classmethod
    def get_engine(cls) -> IDSEngine:
        if cls.engine is None:
            cls.engine = IDSEngine()
        return cls.engine

    def log_message(self, format: str, *args: Any) -> None:
        """Pipe HTTP server logging into DEVRAKSHAK logging system."""
        logger.debug(f"{self.address_string()} - {format % args}")

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Send a JSON formatted response."""
        encoded = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error_json(self, message: str, status: int = 400, details: Optional[str] = None) -> None:
        """Send an error payload with status code."""
        payload = {"success": False, "error": message}
        if details:
            payload["details"] = details
        self._send_json(payload, status=status)

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests for APIs and static files."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        try:
            if path.startswith("/api/"):
                self._handle_api_get(path, query)
            else:
                self._handle_static_get(path)
        except Exception as exc:
            logger.error(f"Error handling GET {path}: {exc}", exc_info=True)
            self._send_error_json(str(exc), status=500, details=traceback.format_exc())

    def do_POST(self) -> None:
        """Handle POST requests for actions and APIs."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            # Read JSON body
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            except Exception:
                body = {}

            if path.startswith("/api/"):
                self._handle_api_post(path, body)
            else:
                self._send_error_json(f"Unknown endpoint: {path}", status=404)
        except Exception as exc:
            logger.error(f"Error handling POST {path}: {exc}", exc_info=True)
            self._send_error_json(str(exc), status=500, details=traceback.format_exc())

    def _handle_static_get(self, path: str) -> None:
        """Serve frontend static HTML, CSS, and JS files from STATIC_DIR."""
        if path in ("/", ""):
            file_name = "index.html"
        else:
            file_name = path.lstrip("/")

        file_path = (STATIC_DIR / file_name).resolve()
        # Security: Prevent path traversal out of STATIC_DIR
        try:
            file_path.relative_to(STATIC_DIR)
        except ValueError:
            self._send_error_json("Access denied", status=403)
            return

        if not file_path.is_file():
            # Fallback to index.html for client-side routing
            file_path = STATIC_DIR / "index.html"
            if not file_path.is_file():
                self._send_error_json(f"Static file not found: {file_name}", status=404)
                return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            if file_path.suffix == ".js":
                mime_type = "application/javascript"
            elif file_path.suffix == ".css":
                mime_type = "text/css"
            else:
                mime_type = "text/html"

        try:
            content = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as exc:
            self._send_error_json(f"Failed to read file: {exc}", status=500)

    def _handle_api_get(self, path: str, query: Dict[str, List[str]]) -> None:
        """Route and execute GET API calls."""
        engine = self.get_engine()

        if path == "/api/status":
            saved_models = sorted(list(engine.settings.model_dir.glob("*.joblib")), reverse=True)
            db_size_mb = 0.0
            if engine.settings.db_path.exists():
                db_size_mb = round(engine.settings.db_path.stat().st_size / (1024 * 1024), 2)

            stats = engine.get_monitor_stats()
            discovered = engine.discover_datasets()
            total_raw_bytes = sum(p.stat().st_size for p in discovered["raw"])
            total_raw_gb = round(total_raw_bytes / (1024 ** 3), 2)
            telemetry = get_system_telemetry()

            active_model_name = "None"
            active_task = "None"
            if engine.active_model_bundle:
                active_model_name = engine.active_model_bundle.model_name
                active_task = engine.active_model_bundle.task_type
            elif saved_models:
                active_model_name = saved_models[0].stem
                active_task = "binary" if "binary" in active_model_name else "multiclass"

            response = {
                "success": True,
                "status": "OPERATIONAL",
                "system": "DEVRAKSHAK // AI IoT Intrusion & DDoS Defense",
                "dataset_schema": "CICIoT2023",
                "active_model": active_model_name,
                "active_task": active_task,
                "saved_models_count": len(saved_models),
                "db_path": str(engine.settings.db_path),
                "db_size_mb": db_size_mb,
                "total_detection_events": stats.get("total_records_processed", 0),
                "total_attacks_detected": stats.get("attack_count", 0),
                "total_benign_flows": stats.get("benign_count", 0),
                "category_distribution": stats.get("category_distribution", {}),
                "severity_distribution": stats.get("severity_distribution", {}),
                "total_training_runs": len(engine.list_runs(limit=100)),
                "raw_datasets_count": len(discovered["raw"]),
                "synthetic_datasets_count": len(discovered["synthetic"]),
                "total_dataset_size_gb": total_raw_gb,
                "system_telemetry": telemetry,
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            self._send_json(response)

        elif path == "/api/datasets":
            discovered = engine.discover_datasets()
            files_list = []

            # Raw/Official files
            for p in discovered["raw"]:
                sz_mb = round(p.stat().st_size / (1024 * 1024), 2)
                # Classify type
                is_merged = "merged" in str(p).lower()
                dtype = "Official Merged Partition" if is_merged else "Official Partition"
                files_list.append({
                    "name": p.name,
                    "path": str(p),
                    "relative_path": str(p.relative_to(PROJECT_ROOT)) if p.is_relative_to(PROJECT_ROOT) else str(p),
                    "size_mb": sz_mb,
                    "type": dtype,
                    "is_synthetic": False
                })

            # Synthetic files
            for p in discovered["synthetic"]:
                sz_mb = round(p.stat().st_size / (1024 * 1024), 2)
                files_list.append({
                    "name": p.name,
                    "path": str(p),
                    "relative_path": str(p.relative_to(PROJECT_ROOT)) if p.is_relative_to(PROJECT_ROOT) else str(p),
                    "size_mb": sz_mb,
                    "type": "Synthetic Test Data",
                    "is_synthetic": True
                })

            self._send_json({
                "success": True,
                "total_files": len(files_list),
                "raw_count": len(discovered["raw"]),
                "synthetic_count": len(discovered["synthetic"]),
                "files": files_list
            })

        elif path == "/api/models":
            saved_models = sorted(list(engine.settings.model_dir.glob("*.joblib")), reverse=True)
            models_list = []
            for m in saved_models:
                sz_kb = round(m.stat().st_size / 1024, 1)
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(m.stat().st_mtime))
                task = "binary" if "binary" in m.stem.lower() else "multiclass"
                algo = "decision_tree" if "decision_tree" in m.stem.lower() else "random_forest"
                is_active = (engine.active_model_bundle and engine.active_model_bundle.model_path == str(m)) or (
                    not engine.active_model_bundle and saved_models and saved_models[0] == m
                )
                models_list.append({
                    "name": m.name,
                    "path": str(m),
                    "size_kb": sz_kb,
                    "modified": mtime,
                    "task": task,
                    "algorithm": algo,
                    "is_active": bool(is_active)
                })

            self._send_json({
                "success": True,
                "total_models": len(models_list),
                "models": models_list
            })

        elif path == "/api/runs":
            limit = int(query.get("limit", ["30"])[0])
            runs = engine.list_runs(limit=limit)
            self._send_json({
                "success": True,
                "total_runs": len(runs),
                "runs": [r.model_dump() for r in runs]
            })

        elif path == "/api/events":
            limit = int(query.get("limit", ["100"])[0])
            severity = query.get("severity", [None])[0]
            category = query.get("category", [None])[0]
            events = engine.list_events(limit=limit, severity=severity, category=category)
            self._send_json({
                "success": True,
                "total_events": len(events),
                "events": [e.model_dump() for e in events]
            })

        elif path == "/api/stats":
            stats = engine.get_monitor_stats()
            telemetry = get_system_telemetry()
            self._send_json({
                "success": True,
                "stats": stats,
                "system_telemetry": telemetry
            })

        elif path == "/api/policies":
            policies = get_policies()
            self._send_json({
                "success": True,
                "policies": [p.model_dump() for p in policies.policies]
            })

        elif path == "/api/logs":
            limit = int(query.get("limit", ["80"])[0])
            sev_filter = query.get("severity", [None])[0]
            log_file = engine.settings.log_file

            lines = []
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                        all_lines = f.readlines()
                        if sev_filter:
                            filtered = [l for l in all_lines if sev_filter.upper() in l.upper()]
                        else:
                            filtered = all_lines
                        lines = [l.strip() for l in filtered[-limit:]]
                except Exception as exc:
                    lines = [f"Error reading log file: {exc}"]

            self._send_json({
                "success": True,
                "total_lines": len(lines),
                "lines": lines
            })

        elif path == "/api/settings":
            self._send_json({
                "success": True,
                "settings": engine.settings.model_dump(mode="json")
            })

        else:
            self._send_error_json(f"Unknown GET endpoint: {path}", status=404)

    def _handle_api_post(self, path: str, body: Dict[str, Any]) -> None:
        """Route and execute POST API calls."""
        engine = self.get_engine()

        if path == "/api/audit":
            target_path_str = body.get("path")
            max_rows = int(body.get("max_rows", 50000))

            if target_path_str:
                target_path = Path(target_path_str)
            else:
                discovered = engine.discover_datasets()
                if discovered["raw"]:
                    target_path = discovered["raw"][0]
                elif discovered["synthetic"]:
                    target_path = discovered["synthetic"][0]
                else:
                    self._send_error_json("No dataset found to audit.", status=404)
                    return

            if not target_path.exists():
                self._send_error_json(f"Path does not exist: {target_path}", status=404)
                return

            audit_res = engine.audit(target_path, max_rows=max_rows)
            self._send_json({
                "success": True,
                "audit": audit_res.model_dump()
            })

        elif path == "/api/test":
            try:
                # Test inference on a specific CSV file
                file_path_str = body.get("file_path")
                model_path_str = body.get("model_path")
                sample_limit = int(body.get("sample_limit", 100000))
                record_events = bool(body.get("record_events", True))

                if not file_path_str:
                    discovered = engine.discover_datasets()
                    if discovered["raw"]:
                        target_file = discovered["raw"][0]
                    elif discovered["synthetic"]:
                        target_file = discovered["synthetic"][0]
                    else:
                        self._send_error_json("No dataset file specified or found.", status=400)
                        return
                else:
                    target_file = Path(file_path_str)
                    if not target_file.is_absolute() and not target_file.exists():
                        target_file = (PROJECT_ROOT / target_file).resolve()

                if not target_file.exists():
                    discovered = engine.discover_datasets()
                    if discovered["raw"]:
                        target_file = discovered["raw"][0]
                    elif discovered["synthetic"]:
                        target_file = discovered["synthetic"][0]
                    else:
                        self._send_error_json(f"Dataset file does not exist: {file_path_str}", status=404)
                        return

                model_path = Path(model_path_str) if model_path_str else None
                if model_path and not model_path.is_absolute() and not model_path.exists():
                    model_path = (PROJECT_ROOT / model_path).resolve()

                # Load predictor safely with fallback
                t_start = time.perf_counter()
                predictor = None
                if model_path and model_path.exists():
                    try:
                        predictor = OfflinePredictor(model_path)
                    except Exception as err:
                        logger.warning(f"Could not load requested model {model_path}: {err}")

                if predictor is None:
                    if engine.active_model_bundle and Path(engine.active_model_bundle).exists():
                        predictor = OfflinePredictor(engine.active_model_bundle)
                    else:
                        saved_models = sorted(list(engine.settings.model_dir.glob("*.joblib")), reverse=True)
                        if saved_models:
                            predictor = OfflinePredictor(saved_models[0])
                        else:
                            self._send_error_json("No trained model bundle available. Please run training first.", status=400)
                            return

                # Read sample rows
                df_sample = pd.read_csv(target_file, nrows=sample_limit, low_memory=False)
                if len(df_sample) == 0:
                    self._send_error_json(f"Dataset file {target_file.name} is empty.", status=400)
                    return

                df_sample.columns = [str(c).strip() for c in df_sample.columns]

                # Check for ground truth column
                ground_truth_raw = None
                for cand in ["label", "Label", "LABEL", "class", "Class", "attack_type"]:
                    if cand in df_sample.columns:
                        ground_truth_raw = df_sample[cand].astype(str).tolist()
                        break

                # Execute predictions
                df_result, events = predictor.predict_dataframe(
                    df_sample,
                    source_name=target_file.name,
                    record_events=record_events
                )
                elapsed_sec = round(time.perf_counter() - t_start, 4)
                latency_ms = round((elapsed_sec / max(1, len(df_sample))) * 1000.0, 4)

                # Analyze accuracy and metrics across the ENTIRE sample set (e.g. 1 Lakh, 2 Lakh flows)
                total_tested = len(df_sample)
                attack_count = int(df_result["is_attack"].sum())
                benign_count = int(total_tested - attack_count)
                predicted_categories = {str(k): int(v) for k, v in df_result["attack_category"].value_counts().items()}

                ground_truth_categories = {}
                correct_count = 0
                has_ground_truth = (ground_truth_raw is not None)

                if has_ground_truth:
                    if predictor.bundle.task_type == "binary":
                        ground_truth_mapped = [map_to_binary(str(x)) for x in ground_truth_raw]
                        matches = [gt.upper() == str(pred).upper() for gt, pred in zip(ground_truth_mapped, df_result["predicted_label"])]
                    else:
                        ground_truth_mapped = [map_to_category(str(x)) for x in ground_truth_raw]
                        matches = [gt.lower() == str(pred).lower() for gt, pred in zip(ground_truth_mapped, df_result["predicted_label"])]

                    correct_count = int(sum(matches))
                    for gt in ground_truth_mapped:
                        ground_truth_categories[gt] = ground_truth_categories.get(gt, 0) + 1
                    accuracy = round((correct_count / max(1, total_tested)) * 100.0, 2)
                else:
                    ground_truth_mapped = ["Unknown"] * total_tested
                    matches = [None] * total_tested
                    accuracy = None

                # Prepare top records for UI table display (first 200 rows)
                display_limit = min(200, total_tested, len(events))
                feature_candidates = [
                    "Header_Length", "Protocol Type", "Time_To_Live", "Rate",
                    "Tot sum", "syn_count", "ack_count", "AVG", "Variance", "IAT"
                ]
                feat_subset = [fc for fc in feature_candidates if fc in df_sample.columns]
                sample_feats_table = df_sample[feat_subset].iloc[:display_limit].to_dict(orient="records") if feat_subset else [{} for _ in range(display_limit)]

                records = []
                for idx in range(display_limit):
                    event = events[idx]
                    raw_gt = ground_truth_raw[idx] if ground_truth_raw else None
                    mapped_gt = ground_truth_mapped[idx]
                    is_match = matches[idx]

                    clean_feats = {
                        fc: round(float(v), 2)
                        for fc, v in sample_feats_table[idx].items()
                        if pd.notna(v) and np.isfinite(v)
                    }

                    records.append({
                        "row_index": idx,
                        "ground_truth_raw": raw_gt,
                        "ground_truth_mapped": mapped_gt,
                        "predicted_label": event.predicted_label,
                        "confidence": event.confidence,
                        "is_attack": event.is_attack,
                        "attack_category": event.attack_category,
                        "severity": event.severity,
                        "policy_triggered": event.policy_triggered,
                        "is_match": is_match,
                        "key_features": clean_feats
                    })

                response = {
                    "success": True,
                    "summary": {
                        "dataset_file": target_file.name,
                        "dataset_path": str(target_file),
                        "model_used": predictor.bundle.model_name,
                        "model_task": predictor.bundle.task_type,
                        "model_labels": predictor.bundle.labels,
                        "total_samples_tested": total_tested,
                        "records_displayed": display_limit,
                        "attacks_detected": attack_count,
                        "benign_detected": benign_count,
                        "has_ground_truth": has_ground_truth,
                        "accuracy_percentage": accuracy,
                        "correct_predictions": correct_count if has_ground_truth else None,
                        "misclassified": (total_tested - correct_count) if has_ground_truth else None,
                        "total_time_seconds": elapsed_sec,
                        "latency_ms_per_sample": latency_ms,
                        "predicted_distribution": predicted_categories,
                        "ground_truth_distribution": ground_truth_categories if has_ground_truth else None
                    },
                    "records": records
                }
                self._send_json(response)
            except Exception as exc:
                logger.error(f"Error in /api/test: {exc}", exc_info=True)
                self._send_error_json(f"Inference error: {exc}", status=500, details=traceback.format_exc())

        elif path == "/api/train":
            try:
                dataset_path_str = body.get("dataset_path")
                task_type = body.get("task_type", "binary")
                model_name = body.get("model_name", "random_forest")
                feature_selector = body.get("feature_selector", "lrrc")
                n_features = int(body.get("n_features", 15))
                sample_limit = int(body.get("sample_limit", 15000))
                resampling_strategy = body.get("resampling_strategy")
                use_class_weight = bool(body.get("use_class_weight", False))

                dataset_path = None
                if dataset_path_str:
                    dp = Path(dataset_path_str)
                    if not dp.is_absolute() and not dp.exists():
                        dp = (PROJECT_ROOT / dp).resolve()
                    if dp.exists():
                        dataset_path = dp

                logger.info(
                    f"Web UI requested model training: {model_name} ({task_type}) on "
                    f"{dataset_path or 'default'}, selector={feature_selector}, k={n_features}, limit={sample_limit}"
                )

                bundle, run = engine.train(
                    data_path=dataset_path,
                    task_type=task_type,
                    model_name=model_name,
                    feature_selector=feature_selector,
                    n_features=n_features,
                    sample_limit=sample_limit,
                    resampling_strategy=resampling_strategy if resampling_strategy != "none" else None,
                    use_class_weight=use_class_weight
                )

                self._send_json({
                    "success": True,
                    "run": run.model_dump(),
                    "model_path": bundle.model_path,
                    "features_selected": bundle.selected_features,
                    "labels": bundle.labels
                })
            except Exception as exc:
                logger.error(f"Error in /api/train: {exc}", exc_info=True)
                self._send_error_json(f"Training error: {exc}", status=500, details=traceback.format_exc())

        elif path == "/api/models/activate":
            model_name_or_path = body.get("model_path")
            if not model_name_or_path:
                self._send_error_json("Missing model_path parameter", status=400)
                return

            target_model = Path(model_name_or_path)
            if not target_model.exists():
                # Check in model_dir
                target_model = engine.settings.model_dir / model_name_or_path
            if not target_model.exists():
                self._send_error_json(f"Model file not found: {model_name_or_path}", status=404)
                return

            bundle = TrainedModelBundle.load(target_model)
            engine.active_model_bundle = bundle
            logger.info(f"Active model set to: {target_model.name}")
            self._send_json({
                "success": True,
                "active_model": bundle.model_name,
                "task_type": bundle.task_type,
                "labels": bundle.labels,
                "model_path": bundle.model_path
            })

        elif path == "/api/policies":
            updated_policies = body.get("policies", [])
            policies_config = get_policies()
            
            for item in updated_policies:
                pid = item.get("policy_id")
                for pol in policies_config.policies:
                    if pol.policy_id == pid:
                        if "enabled" in item:
                            pol.enabled = bool(item["enabled"])
                        if "min_confidence" in item:
                            pol.min_confidence = float(item["min_confidence"])
                        elif "confidence_threshold" in item:
                            pol.min_confidence = float(item["confidence_threshold"])
                        if "severity" in item:
                            pol.severity = str(item["severity"])
                        if "description" in item:
                            pol.description = str(item["description"])

            save_policies(policies_config)
            self._send_json({
                "success": True,
                "message": "Security policies updated successfully.",
                "policies": [p.model_dump() for p in policies_config.policies]
            })

        elif path == "/api/experiments/selectors":
            data_path_str = body.get("data_path")
            task_type = body.get("task_type", "binary")
            model_name = body.get("model_name", "random_forest")
            n_features = int(body.get("n_features", 15))
            sample_limit = int(body.get("sample_limit", 5000))

            data_path = Path(data_path_str) if data_path_str else None
            results = engine.run_selector_comparison(
                data_path=data_path,
                task_type=task_type,
                model_name=model_name,
                n_features=n_features,
                sample_limit=sample_limit
            )
            self._send_json({
                "success": True,
                "comparison": results
            })

        elif path == "/api/experiments/imbalance":
            data_path_str = body.get("data_path")
            task_type = body.get("task_type", "binary")
            model_name = body.get("model_name", "random_forest")
            sample_limit = int(body.get("sample_limit", 5000))

            data_path = Path(data_path_str) if data_path_str else None
            results = engine.run_imbalance_comparison(
                data_path=data_path,
                task_type=task_type,
                model_name=model_name,
                sample_limit=sample_limit
            )
            self._send_json({
                "success": True,
                "comparison": results
            })

        elif path == "/api/upload":
            filename = body.get("filename", "uploaded_traffic.csv")
            content = body.get("content", "")

            # Security sanitization
            safe_name = Path(filename).name
            if not safe_name.lower().endswith(".csv"):
                safe_name += ".csv"

            upload_dir = PROJECT_ROOT / "data" / "raw" / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            target_path = upload_dir / safe_name

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Quick inspect
            sample = pd.read_csv(target_path, nrows=5)
            self._send_json({
                "success": True,
                "file_name": safe_name,
                "path": str(target_path),
                "columns": list(sample.columns),
                "columns_count": len(sample.columns)
            })

        elif path == "/api/settings":
            updates = body.get("settings", {})
            from src.core.settings import update_settings
            updated = update_settings(updates)
            self._send_json({
                "success": True,
                "settings": updated.model_dump(mode="json")
            })

        elif path == "/api/synthetic":
            n_samples = int(body.get("n_samples", 2000))
            out_name = body.get("output_name", "synthetic_ciciot2023.csv")
            out_path = engine.generate_synthetic(n_samples=n_samples, output_name=out_name)
            self._send_json({
                "success": True,
                "file_path": str(out_path),
                "file_name": out_path.name,
                "samples_generated": n_samples
            })

        else:
            self._send_error_json(f"Unknown POST endpoint: {path}", status=404)


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_web_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the multi-threaded HTTP server and listen indefinitely."""
    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, DevRakshakAPIHandler)
    logger.info(f"DEVRAKSHAK Web Dashboard initialized on http://{host}:{port}/")
    print("\n" + "=" * 70)
    print(f"[DEVRAKSHAK] AI IoT Intrusion & DDoS Defense System")
    print(f"[WEB] Dashboard is LIVE at: http://localhost:{port}/")
    print(f"[DATASET] Serving official dataset: data/raw/MERGED_CSV/ (63 files)")
    print(f"[STATUS] Press Ctrl+C to stop the web server.")
    print("=" * 70 + "\n", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down DEVRAKSHAK Web Dashboard cleanly...")
    finally:
        httpd.server_close()


def main() -> None:
    """Parse web server arguments and start the dashboard."""
    parser = argparse.ArgumentParser(
        description="DEVRAKSHAK Web-Based Management & Telemetry Dashboard"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to listen on (default: 8000)"
    )

    args = parser.parse_args()
    run_web_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

