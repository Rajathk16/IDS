"""Training and evaluation runs screen with live execution and detailed metrics inspection."""

from __future__ import annotations

from typing import List, Optional
from rich.markdown import Markdown
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, LoadingIndicator, RichLog, Static
from src.core.engine import IDSEngine
from src.core.events import TrainingRun


class RunsScreenWidget(Widget):
    """Lists historical training runs and triggers model training / comparisons in background workers."""

    DEFAULT_CSS = """
    RunsScreenWidget {
        height: 100%;
        layout: vertical;
    }
    #runs-action-bar {
        height: auto;
        padding: 1;
        background: $panel;
    }
    #runs-action-bar Button {
        margin-right: 1;
    }
    #runs-table-container {
        height: 3fr;
        border: solid $accent;
    }
    #runs-detail-panel {
        height: 2fr;
        border: solid $secondary;
        background: $surface;
        padding: 1;
    }
    #runs-status-bar {
        height: auto;
        color: $accent;
        padding: 0 1;
    }
    """

    def __init__(self, engine: IDSEngine):
        super().__init__()
        self.engine = engine
        self._cached_runs: List[TrainingRun] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="runs-action-bar"):
                yield Button("🚀 Train Model (LRRC-FS)", id="btn-train", variant="primary")
                yield Button("📊 Compare Selectors", id="btn-compare-selectors", variant="success")
                yield Button("🔄 Refresh Runs", id="btn-refresh-runs")
            yield Label("Ready", id="runs-status-bar")
            with Container(id="runs-table-container"):
                yield DataTable(id="runs-table", cursor_type="row")
            with Container(id="runs-detail-panel"):
                yield RichLog(id="runs-detail-log", wrap=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#runs-table", DataTable)
        table.add_columns(
            "Run ID", "Time", "Model", "Task", "Selector", "Feats", "Accuracy", "Macro F1", "Latency (ms)", "Status"
        )
        self.refresh_table()

    def refresh_table(self) -> None:
        """Load runs from SQLite and populate the table."""
        table = self.query_one("#runs-table", DataTable)
        table.clear()
        self._cached_runs = self.engine.list_runs(limit=50)

        for i, r in enumerate(self._cached_runs):
            f1_str = f"[bold green]{r.macro_f1:.4f}[/bold green]" if r.macro_f1 > 0.8 else f"{r.macro_f1:.4f}"
            table.add_row(
                r.run_id[:18],
                r.timestamp.strftime("%m-%d %H:%M"),
                r.model_name,
                r.task_type,
                r.feature_selector,
                str(r.selected_features_count),
                f"{r.accuracy:.4f}",
                f1_str,
                f"{r.inference_latency_ms_per_sample:.4f}",
                f"[green]{r.status}[/green]" if r.status == "SUCCESS" else f"[red]{r.status}[/red]",
                key=str(i)
            )

        detail_log = self.query_one("#runs-detail-log", RichLog)
        if self._cached_runs:
            self._display_run_details(self._cached_runs[0])
        else:
            detail_log.clear()
            detail_log.write("[dim]No training runs found. Click 'Train Model' to initiate a run.[/dim]")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._select_row_by_key(event.row_key.value)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key:
            self._select_row_by_key(event.row_key.value)

    def _select_row_by_key(self, key_str: str) -> None:
        try:
            idx = int(key_str)
            if 0 <= idx < len(self._cached_runs):
                self._display_run_details(self._cached_runs[idx])
        except Exception:
            pass

    def _display_run_details(self, run: TrainingRun) -> None:
        detail_log = self.query_one("#runs-detail-log", RichLog)
        detail_log.clear()

        fpr_str = f"{run.false_positive_rate:.4f}" if run.false_positive_rate is not None else "N/A"
        md = [
            f"### Run Inspection: `{run.run_id}`",
            f"- **Model:** `{run.model_name}` | **Task:** `{run.task_type}` | **Selector:** `{run.feature_selector}` ({run.selected_features_count} feats)",
            f"- **Dataset:** `{run.dataset_name}` ({'SYNTHETIC' if run.is_synthetic else 'Authentic CICIoT2023'})",
            f"- **Train Samples:** {run.train_samples:,} | **Test Samples:** {run.test_samples:,}",
            f"- **Performance:** Accuracy: **{run.accuracy:.4f}** | Macro F1: **{run.macro_f1:.4f}** | Weighted F1: **{run.weighted_f1:.4f}** | FPR: **{fpr_str}**",
            f"- **Efficiency:** Training Duration: **{run.training_duration_seconds:.3f}s** | Inference Latency: **{run.inference_latency_ms_per_sample:.4f} ms/sample**",
            f"- **Saved Model Bundle:** `{run.model_path}`",
            f"- **Confusion Matrix Plot:** `{run.confusion_matrix_plot or 'N/A'}`",
            "",
            f"**Selected Feature Subset:** `{', '.join(run.selected_features[:10])}...`"
        ]
        detail_log.write(Markdown("\n".join(md)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-runs":
            self.refresh_table()
        elif btn_id == "btn-train":
            self._start_training_worker()
        elif btn_id == "btn-compare-selectors":
            self._start_comparison_worker()

    @work(exclusive=True, thread=True)
    def _start_training_worker(self) -> None:
        status = self.query_one("#runs-status-bar", Label)
        status.update("⏳ Running training pipeline in background worker...")
        try:
            bundle, run = self.engine.train(
                task_type=self.engine.settings.default_task,
                model_name=self.engine.settings.default_model,
                feature_selector="lrrc",
                n_features=self.engine.settings.lrrc_max_features,
                sample_limit=self.engine.settings.sample_limit
            )
            self.app.call_from_thread(self._on_training_finished, run)
        except Exception as exc:
            self.app.call_from_thread(self._on_worker_error, str(exc))

    def _on_training_finished(self, run: TrainingRun) -> None:
        status = self.query_one("#runs-status-bar", Label)
        status.update(f"✅ Training completed! Run: {run.run_id} (Macro F1: {run.macro_f1:.4f})")
        self.refresh_table()

    @work(exclusive=True, thread=True)
    def _start_comparison_worker(self) -> None:
        status = self.query_one("#runs-status-bar", Label)
        status.update("⏳ Running feature selection comparison (All, Variance, KBest, LRRC-FS)...")
        try:
            res = self.engine.run_selector_comparison()
            self.app.call_from_thread(self._on_comparison_finished, res)
        except Exception as exc:
            self.app.call_from_thread(self._on_worker_error, str(exc))

    def _on_comparison_finished(self, res: dict) -> None:
        status = self.query_one("#runs-status-bar", Label)
        status.update(f"✅ Feature comparison complete! Report saved to {res.get('report_file')}")
        self.refresh_table()

    def _on_worker_error(self, err_msg: str) -> None:
        status = self.query_one("#runs-status-bar", Label)
        status.update(f"❌ Operation failed: {err_msg}")
