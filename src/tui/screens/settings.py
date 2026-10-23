"""Settings screen for configuring paths, sample limits, models, and LRRC-FS weights."""

from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select, Static
from src.core.settings import AppSettings, get_settings, update_settings


class SettingsScreenWidget(Widget):
    """Pydantic-validated configuration form with local file persistence."""

    DEFAULT_CSS = """
    SettingsScreenWidget {
        height: 100%;
        layout: vertical;
    }
    #settings-scroll {
        height: 1fr;
        padding: 1 2;
    }
    .form-group {
        margin-bottom: 1;
    }
    .form-label {
        color: $accent;
        text-style: bold;
        margin-bottom: 0;
    }
    #settings-actions {
        height: auto;
        padding: 1;
        background: $panel;
    }
    #settings-status {
        padding: 0 2;
        color: $accent;
    }
    """

    def compose(self) -> ComposeResult:
        settings = get_settings()

        with Vertical():
            with VerticalScroll(id="settings-scroll"):
                yield Label("Data Directory (Raw CSVs)", classes="form-label")
                yield Input(value=str(settings.data_dir), id="inp-data-dir", classes="form-group")

                yield Label("Synthetic Data Directory", classes="form-label")
                yield Input(value=str(settings.synthetic_dir), id="inp-synth-dir", classes="form-group")

                yield Label("Saved Models Directory", classes="form-label")
                yield Input(value=str(settings.model_dir), id="inp-model-dir", classes="form-group")

                yield Label("Sample Limit (Rows loaded in sample mode)", classes="form-label")
                yield Input(value=str(settings.sample_limit or 20000), id="inp-sample-limit", classes="form-group")

                yield Label("Default Classifier Architecture", classes="form-label")
                yield Select(
                    [
                        ("Random Forest (50 trees, max_depth 12)", "random_forest"),
                        ("Decision Tree (Fast, max_depth 12)", "decision_tree"),
                        ("Extra Trees (Randomized)", "extra_trees"),
                        ("HistGradientBoosting", "gradient_boosting"),
                    ],
                    value=settings.default_model,
                    id="sel-default-model",
                    classes="form-group"
                )

                yield Label("Default Prediction Task", classes="form-label")
                yield Select(
                    [
                        ("Binary (BENIGN vs ATTACK)", "binary"),
                        ("Multiclass (8 Attack Categories)", "multiclass"),
                    ],
                    value=settings.default_task,
                    id="sel-default-task",
                    classes="form-group"
                )

                yield Label("LRRC-FS Max Selected Features (k)", classes="form-label")
                yield Input(value=str(settings.lrrc_max_features), id="inp-max-features", classes="form-group")

                yield Label("LRRC Relevance Weight (w_rel)", classes="form-label")
                yield Input(value=str(settings.lrrc_relevance_weight), id="inp-w-rel", classes="form-group")

                yield Label("LRRC Redundancy Weight (w_red)", classes="form-label")
                yield Input(value=str(settings.lrrc_redundancy_weight), id="inp-w-red", classes="form-group")

                yield Label("LRRC Cost Weight (w_cost)", classes="form-label")
                yield Input(value=str(settings.lrrc_cost_weight), id="inp-w-cost", classes="form-group")

                yield Label("Application Log Level", classes="form-label")
                yield Select(
                    [
                        ("INFO", "INFO"),
                        ("DEBUG", "DEBUG"),
                        ("WARNING", "WARNING"),
                        ("ERROR", "ERROR"),
                    ],
                    value=settings.log_level,
                    id="sel-log-level",
                    classes="form-group"
                )

            yield Label("", id="settings-status")
            with Horizontal(id="settings-actions"):
                yield Button("💾 Save Settings", id="btn-save-settings", variant="primary")
                yield Button("↩️ Reset Defaults", id="btn-reset-defaults")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        status = self.query_one("#settings-status", Label)

        if btn_id == "btn-save-settings":
            try:
                data_dir = Path(self.query_one("#inp-data-dir", Input).value.strip())
                synth_dir = Path(self.query_one("#inp-synth-dir", Input).value.strip())
                model_dir = Path(self.query_one("#inp-model-dir", Input).value.strip())
                sample_limit = int(self.query_one("#inp-sample-limit", Input).value.strip())
                default_model = str(self.query_one("#sel-default-model", Select).value)
                default_task = str(self.query_one("#sel-default-task", Select).value)
                max_features = int(self.query_one("#inp-max-features", Input).value.strip())
                w_rel = float(self.query_one("#inp-w-rel", Input).value.strip())
                w_red = float(self.query_one("#inp-w-red", Input).value.strip())
                w_cost = float(self.query_one("#inp-w-cost", Input).value.strip())
                log_lvl = str(self.query_one("#sel-log-level", Select).value)

                # Validate through Pydantic
                new_settings = AppSettings(
                    data_dir=data_dir,
                    synthetic_dir=synth_dir,
                    model_dir=model_dir,
                    sample_limit=sample_limit,
                    default_model=default_model,
                    default_task=default_task,
                    lrrc_max_features=max_features,
                    lrrc_relevance_weight=w_rel,
                    lrrc_redundancy_weight=w_red,
                    lrrc_cost_weight=w_cost,
                    log_level=log_lvl
                )

                update_settings(new_settings)
                status.update("[bold green]✓ Settings validated and persisted to config/settings.json successfully![/bold green]")
            except Exception as exc:
                status.update(f"[bold red]Validation error: {exc}[/bold red]")

        elif btn_id == "btn-reset-defaults":
            default_settings = AppSettings()
            update_settings(default_settings)
            status.update("[bold yellow]✓ Restored factory default settings.[/bold yellow]")
