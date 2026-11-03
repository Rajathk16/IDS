"""Unit tests for DEVRAKSHAK Web Dashboard API handler logic (Socketless In-Memory)."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.web.server import DevRakshakAPIHandler, STATIC_DIR


class MockDevRakshakHandler(DevRakshakAPIHandler):
    """Subclass of DevRakshakAPIHandler to run in-memory without OS network sockets."""

    def __init__(self):
        self.wfile = io.BytesIO()
        self.rfile = io.BytesIO()
        self.headers = {}
        self.response_status = None
        self.response_headers = {}

    def send_response(self, code, message=None):
        self.response_status = code

    def send_header(self, keyword, value):
        self.response_headers[keyword] = value

    def end_headers(self):
        pass

    def get_response_json(self):
        self.wfile.seek(0)
        content = self.wfile.read().decode("utf-8")
        return json.loads(content)


def test_static_files_exist():
    """Verify frontend static assets exist in STATIC_DIR."""
    assert (STATIC_DIR / "index.html").is_file()
    assert (STATIC_DIR / "style.css").is_file()
    assert (STATIC_DIR / "app.js").is_file()

    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert "DEVRAKSHAK" in html
    assert "AI IOT INTRUSION & DDOS DEFENSE" in html
    assert "Merged01.csv" in html or "Official" in html


def test_api_status_in_memory():
    """Verify /api/status endpoint response."""
    handler = MockDevRakshakHandler()
    handler._handle_api_get("/api/status", {})
    assert handler.response_status == 200
    data = handler.get_response_json()
    assert data["success"] is True
    assert data["status"] == "OPERATIONAL"
    assert "active_model" in data
    assert "total_detection_events" in data


def test_api_datasets_in_memory():
    """Verify /api/datasets discovers raw merged files."""
    handler = MockDevRakshakHandler()
    handler._handle_api_get("/api/datasets", {})
    assert handler.response_status == 200
    data = handler.get_response_json()
    assert data["success"] is True
    assert data["total_files"] > 0
    names = [f["name"] for f in data["files"]]
    # Should discover official Merged files
    assert any("merged" in n.lower() for n in names)


def test_api_models_in_memory():
    """Verify /api/models returns saved models list."""
    handler = MockDevRakshakHandler()
    handler._handle_api_get("/api/models", {})
    assert handler.response_status == 200
    data = handler.get_response_json()
    assert data["success"] is True
    assert "models" in data
    assert len(data["models"]) > 0


def test_api_policies_in_memory():
    """Verify /api/policies returns defense rules."""
    handler = MockDevRakshakHandler()
    handler._handle_api_get("/api/policies", {})
    assert handler.response_status == 200
    data = handler.get_response_json()
    assert data["success"] is True
    assert len(data["policies"]) > 0


def test_api_inference_test_in_memory():
    """Verify /api/test runs inference and returns structured detection results."""
    handler = MockDevRakshakHandler()
    handler._handle_api_get("/api/datasets", {})
    datasets_data = handler.get_response_json()
    assert len(datasets_data["files"]) > 0
    test_file_path = datasets_data["files"][0]["path"]

    handler_post = MockDevRakshakHandler()
    handler_post._handle_api_post("/api/test", {
        "file_path": test_file_path,
        "sample_limit": 15,
        "record_events": False
    })
    assert handler_post.response_status == 200
    data = handler_post.get_response_json()
    assert data["success"] is True
    summary = data["summary"]
    assert summary["total_samples_tested"] == 15
    assert len(data["records"]) == 15
    assert "latency_ms_per_sample" in summary
