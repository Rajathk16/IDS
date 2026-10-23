"""Structured application and detection event logs viewer."""

from __future__ import annotations

import logging
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, RichLog, Select
from src.core.logging_config import get_log_buffer


class LogsScreenWidget(Widget):
    """Displays colorized structured application logs with severity filtering."""

    DEFAULT_CSS = """
    LogsScreenWidget {
        height: 100%;
        layout: vertical;
    }
    #logs-filter-bar {
        height: auto;
        padding: 1;
        background: $panel;
    }
    #logs-filter-bar Select {
        width: 24;
        margin-right: 1;
    }
    #logs-display {
        height: 1fr;
        border: solid $accent;
        background: $surface;
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._current_filter: str = "ALL"

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="logs-filter-bar"):
                yield Label("Severity Filter: ", classes="label-align")
                yield Select(
                    [
                        ("All Levels", "ALL"),
                        ("DEBUG and above", "DEBUG"),
                        ("INFO and above", "INFO"),
                        ("WARNING and above", "WARNING"),
                        ("ERROR only", "ERROR"),
                    ],
                    value="ALL",
                    id="select-log-level"
                )
                yield Button("🔄 Refresh", id="btn-refresh-logs")
                yield Button("🧹 Clear Display", id="btn-clear-logs")
            yield RichLog(id="logs-display", wrap=True, markup=True, highlight=True)

    def on_mount(self) -> None:
        self.refresh_logs()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "select-log-level":
            self._current_filter = str(event.value)
            self.refresh_logs()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-logs":
            self.refresh_logs()
        elif event.button.id == "btn-clear-logs":
            log_view = self.query_one("#logs-display", RichLog)
            log_view.clear()

    def refresh_logs(self) -> None:
        log_view = self.query_one("#logs-display", RichLog)
        log_view.clear()

        buffer = get_log_buffer()
        records = buffer.get_records(limit=300, level_filter=self._current_filter)

        if not records:
            log_view.write("[dim]No log records matching current filter.[/dim]")
            return

        for r in records:
            color = "white"
            if r.levelno >= logging.ERROR:
                color = "bold red"
            elif r.levelno >= logging.WARNING:
                color = "bold yellow"
            elif r.levelno == logging.INFO:
                color = "green"
            elif r.levelno <= logging.DEBUG:
                color = "dim cyan"

            msg = (
                f"[dim]{r.asctime if hasattr(r, 'asctime') else ''}[/dim] "
                f"[{color}][{r.levelname}][/{color}] "
                f"[cyan]{r.name}[/cyan]: {r.getMessage()}"
            )
            log_view.write(msg)
