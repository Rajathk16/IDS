"""Offline detection monitoring and telemetry screen."""

from __future__ import annotations

from typing import List
from rich.markdown import Markdown
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, Static
from src.core.engine import IDSEngine
from src.core.events import DetectionEvent


class MetricCard(Static):
    """Reusable card displaying high-level offline detection metric."""

    DEFAULT_CSS = """
    MetricCard {
        border: solid $accent;
        background: $panel;
        padding: 1;
        margin: 0 1;
        height: 7;
        content-align: center middle;
    }
    .metric-title {
        color: $text-muted;
        text-style: bold;
    }
    .metric-value {
        text-style: bold;
        color: $accent;
    }
    """

    def __init__(self, title: str, value: str = "0", id: str | None = None):
        super().__init__(id=id)
        self.card_title = title
        self.card_value = value

    def compose(self) -> ComposeResult:
        yield Label(self.card_title, classes="metric-title")
        yield Label(self.card_value, classes="metric-value", id=f"{self.id}-val" if self.id else None)

    def update_value(self, val: str) -> None:
        if self.id:
            lbl = self.query_one(f"#{self.id}-val", Label)
            lbl.update(val)


class MonitorScreenWidget(Widget):
    """Displays offline batch detection statistics, attack category distribution, and recent events."""

    DEFAULT_CSS = """
    MonitorScreenWidget {
        height: 100%;
        layout: vertical;
    }
    #monitor-top-cards {
        height: auto;
        layout: horizontal;
        padding: 1 0;
    }
    #monitor-action-bar {
        height: auto;
        padding: 0 1 1 1;
    }
    #monitor-tables-container {
        height: 1fr;
        layout: horizontal;
    }
    #monitor-category-box {
        width: 35%;
        border: solid $accent;
        margin-right: 1;
    }
    #monitor-events-box {
        width: 65%;
        border: solid $accent;
    }
    #monitor-status-lbl {
        color: $accent;
        padding-left: 1;
    }
    """

    def __init__(self, engine: IDSEngine):
        super().__init__()
        self.engine = engine

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="monitor-top-cards"):
                yield MetricCard("Offline Records Evaluated", "0", id="card-total")
                yield MetricCard("Benign Traffic", "0", id="card-benign")
                yield MetricCard("Attacks Detected", "0", id="card-attack")
                yield MetricCard("Critical/High Alerts", "0", id="card-alerts")

            with Horizontal(id="monitor-action-bar"):
                yield Button("⚡ Run Offline Inference (1,000 Rows)", id="btn-run-inference", variant="primary")
                yield Button("🔄 Refresh Metrics", id="btn-refresh-monitor")
                yield Label("Grounding Note: Statistics represent offline dataset evaluations.", id="monitor-status-lbl")

            with Horizontal(id="monitor-tables-container"):
                with Container(id="monitor-category-box"):
                    yield Label("[bold cyan]Attack Category Breakdown[/bold cyan]")
                    yield DataTable(id="table-categories", cursor_type="row")
                with Container(id="monitor-events-box"):
                    yield Label("[bold red]Recent Offline Detection Events[/bold red]")
                    yield DataTable(id="table-events", cursor_type="row")

    def on_mount(self) -> None:
        cat_table = self.query_one("#table-categories", DataTable)
        cat_table.add_columns("Category", "Detections", "% Share")

        evt_table = self.query_one("#table-events", DataTable)
        evt_table.add_columns("Time", "Row", "Predicted Label", "Conf", "Severity", "Policy Alert")

        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Fetch summary and recent events from event store."""
        summary = self.engine.get_monitor_stats()
        total = summary["total_records_processed"]
        benign = summary["benign_count"]
        attack = summary["attack_count"]

        crit_high = summary["severity_distribution"].get("CRITICAL", 0) + summary["severity_distribution"].get("HIGH", 0)

        # Update cards
        self.query_one("#card-total", MetricCard).update_value(f"{total:,}")
        self.query_one("#card-benign", MetricCard).update_value(f"{benign:,}")
        self.query_one("#card-attack", MetricCard).update_value(f"{attack:,}")
        self.query_one("#card-alerts", MetricCard).update_value(f"{crit_high:,}")

        # Populate Category table
        cat_table = self.query_one("#table-categories", DataTable)
        cat_table.clear()
        total_atks = max(1, attack)
        for cat, cnt in sorted(summary["category_distribution"].items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total_atks) * 100
            cat_table.add_row(cat, f"{cnt:,}", f"{pct:.1f}%")

        # Populate Recent Events
        evt_table = self.query_one("#table-events", DataTable)
        evt_table.clear()
        events = self.engine.list_events(limit=40)
        for e in events:
            sev_color = "red" if e.severity in ("HIGH", "CRITICAL") else ("yellow" if e.severity == "MEDIUM" else "green")
            evt_table.add_row(
                e.timestamp.strftime("%H:%M:%S"),
                str(e.row_index),
                e.predicted_label,
                f"{e.confidence:.2f}",
                f"[{sev_color}]{e.severity}[/{sev_color}]",
                e.policy_triggered or "-"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-monitor":
            self.refresh_stats()
        elif event.button.id == "btn-run-inference":
            self._start_inference_worker()

    @work(exclusive=True, thread=True)
    def _start_inference_worker(self) -> None:
        status = self.query_one("#monitor-status-lbl", Label)
        status.update("⏳ Executing offline model inference on CSV sample...")
        try:
            discovered = self.engine.discover_datasets()
            target_csv = (
                discovered["raw"][0] if discovered["raw"]
                else (discovered["synthetic"][0] if discovered["synthetic"] else self.engine.generate_synthetic())
            )
            df_out, events = self.engine.predict_offline(target_csv, sample_limit=1000)
            self.app.call_from_thread(self._on_inference_done, len(events))
        except Exception as exc:
            self.app.call_from_thread(self._on_inference_error, str(exc))

    def _on_inference_done(self, count: int) -> None:
        status = self.query_one("#monitor-status-lbl", Label)
        status.update(f"✅ Classified {count:,} offline traffic records.")
        self.refresh_stats()

    def _on_inference_error(self, err_msg: str) -> None:
        status = self.query_one("#monitor-status-lbl", Label)
        status.update(f"❌ Inference error: {err_msg}")
