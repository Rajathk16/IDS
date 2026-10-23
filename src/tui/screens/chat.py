"""Terminal conversation interface for DevRakshak with cyberpunk banner, commands, and deterministic explanations."""

from __future__ import annotations

from typing import List, Tuple
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Input, Label, RichLog
from src.core.engine import IDSEngine
from src.core.policies import get_policies
from src.core.settings import get_settings

DEVRAKSHAK_BANNER = """
[bold cyan] ██████  ███████ ██    ██ ██████   █████  ██   ██ ███████ ██   ██  █████  ██   ██ [/bold cyan]
[bold cyan] ██   ██ ██      ██    ██ ██   ██ ██   ██ ██  ██  ██      ██   ██ ██   ██ ██  ██  [/bold cyan]
[bold #38bdf8] ██   ██ █████   ██    ██ ██████  ███████ █████   ███████ ███████ ███████ █████   [/bold #38bdf8]
[bold #c084fc] ██   ██ ██       ██  ██  ██   ██ ██   ██ ██  ██       ██ ██   ██ ██   ██ ██  ██  [/bold #c084fc]
[bold #a855f7] ██████  ███████   ████   ██   ██ ██   ██ ██   ██ ███████ ██   ██ ██   ██ ██   ██ [/bold #a855f7]
"""

WELCOME_HEADER = """
[bold cyan]D E V R A K S H A K[/bold cyan] [bold magenta]//[/bold magenta] [bold white]AI IOT INTRUSION & DDOS DEFENSE SYSTEM[/bold white]
[dim cyan]Contextual flow analysis[/dim cyan] [magenta]•[/magenta] [dim cyan]LRRC-FS feature selection[/dim cyan] [magenta]•[/magenta] [dim cyan]Complete observability[/dim cyan]
[dim]v1.0.0[/dim]   [dim]Dataset:[/dim] [cyan]CICIoT2023[/cyan]   [dim]Mode:[/dim] [bold yellow]OFFLINE PROTOTYPE[/bold yellow]

[bold cyan]GETTING STARTED[/bold cyan]

[bold cyan]01[/bold cyan]  Ask DEVRAKSHAK a question or describe an IoT traffic analysis task.
[bold cyan]02[/bold cyan]  DEVRAKSHAK audits raw network flow CSV schemas and evaluates data quality.
[bold cyan]03[/bold cyan]  Train classifiers using the custom LRRC-FS feature selector.
[bold cyan]04[/bold cyan]  Inspect structured detection events, security policies, and confusion matrices.

[bold cyan]/help[/bold cyan] [dim]view commands[/dim]   [bold cyan]/audit[/bold cyan] [dim]audit dataset[/dim]   [bold cyan]/train[/bold cyan] [dim]train model[/dim]   [bold cyan]/monitor[/bold cyan] [dim]telemetry[/dim]   [bold cyan]/status[/bold cyan] [dim]system health[/dim]
"""


class ChatScreenWidget(Widget):
    """Interactive conversation interface providing deterministic explanations and system queries."""

    DEFAULT_CSS = """
    ChatScreenWidget {
        height: 100%;
        layout: vertical;
        background: #070a13;
    }
    #chat-log {
        height: 1fr;
        border: solid #1e293b;
        background: #080c16;
        padding: 1 2;
    }
    #chat-input-bar {
        height: 3;
        background: #090d1a;
        border: solid #1e293b;
        padding: 0 1;
    }
    #chat-input {
        width: 100%;
        height: 100%;
        background: #090d1a;
        border: none;
        color: #e2e8f0;
    }
    #chat-input:focus {
        border: none;
    }
    """

    def __init__(self, engine: IDSEngine):
        super().__init__()
        self.engine = engine

    def compose(self) -> ComposeResult:
        yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)
        with Container(id="chat-input-bar"):
            yield Input(
                id="chat-input",
                placeholder="► Describe a task or query for DEVRAKSHAK... (supports /help, /audit, /train, /status)"
            )

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        # Render the large DevRakshak cyberpunk banner
        log.write(DEVRAKSHAK_BANNER)
        log.write(WELCOME_HEADER)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return

        input_widget = self.query_one("#chat-input", Input)
        input_widget.value = ""

        log = self.query_one("#chat-log", RichLog)
        log.write(f"\n[bold cyan]User ►[/bold cyan] {query}")

        # Check for commands or natural language query
        self._dispatch_query(query, log)

    def _dispatch_query(self, query: str, log: RichLog) -> None:
        q = query.strip().lower()

        if q in ("/help", "help", "?", "commands"):
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                "### 🧭 DEVRAKSHAK Command & Query Directory\n\n"
                "| Command | Description |\n"
                "| :--- | :--- |\n"
                "| `/status` | Overview of system health, active datasets, models, and detection counts |\n"
                "| `/audit` | Execute real-time schema audit on raw network flow CSV data |\n"
                "| `/lrrc` | Deep mathematical breakdown of the LRRC-FS feature selection formula |\n"
                "| `/models` | Architectural comparison of supported classifiers (RF, DT, ET, HistGB) |\n"
                "| `/metrics` | Explanation of Macro F1, False Positive Rate, and latency trade-offs |\n"
                "| `/runs` | List the latest training runs and evaluation metrics |\n"
                "| `/policies` | Review active alert threshold rules and severity mapping |\n"
                "| `/imbalance` | Why high accuracy is deceptive on imbalanced IoT traffic |\n"
                "| `/monitor` | Summarize offline detection metrics and attack distribution |"
            ))

        elif q in ("/audit", "audit"):
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green] Executing dataset audit...")
            try:
                res = self.engine.audit(max_rows=10000)
                origin = "[yellow]SYNTHETIC Test Data[/yellow]" if res.is_synthetic else "[green]Authentic CICIoT2023[/green]"
                table = Table(title="Dataset Schema & Quality Audit", show_header=False)
                table.add_row("Dataset Origin", origin)
                table.add_row("Audited Files", str(res.file_count))
                table.add_row("Audited Rows", f"{res.total_rows:,}")
                table.add_row("Target Column", f"`{res.target_column}`")
                table.add_row("Features Inspected", str(len(res.feature_columns)))
                table.add_row("Missing (NaN) Count", str(res.missing_value_count))
                table.add_row("Infinite (+/- Inf) Count", str(res.infinite_value_count))
                table.add_row("Duplicate Rows", f"{res.duplicate_row_count:,}")
                log.write(table)
            except Exception as e:
                log.write(f"[red]Audit error: {e}[/red]")

        elif q in ("/status", "status"):
            ds = self.engine.discover_datasets()
            runs = self.engine.list_runs(limit=10)
            summary = self.engine.get_monitor_stats()
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                f"### 🛡️ System Status\n"
                f"- **Raw CSV Files Available:** {len(ds['raw'])}\n"
                f"- **Synthetic Offline Datasets:** {len(ds['synthetic'])}\n"
                f"- **Recorded Training Runs:** {len(runs)}\n"
                f"- **Offline Flow Records Evaluated:** {summary['total_records_processed']:,}\n"
                f"- **Attacks Identified:** {summary['attack_count']:,} ({summary['benign_count']:,} Benign)\n"
                f"- **Persistence Database:** `{self.engine.settings.db_path}`"
            ))

        elif q in ("/lrrc", "lrrc", "features", "feature selection"):
            s = self.engine.settings
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                "### 🧮 Lightweight Relevance-Redundancy-Cost Feature Selector (LRRC-FS)\n\n"
                "**1. Mathematical Formulation:**\n"
                "$$\\text{Score}(f) = w_{\\text{rel}} \\cdot \\hat{R}(f) - w_{\\text{red}} \\cdot \\hat{D}(f, S) - w_{\\text{cost}} \\cdot \\hat{C}(f)$$\n\n"
                f"**2. Active Weight Configuration:**\n"
                f"- $w_{{\\text{{rel}}}}$ (Relevance Weight) = `{s.lrrc_relevance_weight}`\n"
                f"- $w_{{\\text{{red}}}}$ (Redundancy Penalty Weight) = `{s.lrrc_redundancy_weight}`\n"
                f"- $w_{{\\text{{cost}}}}$ (Extraction Cost Penalty Weight) = `{s.lrrc_cost_weight}`\n\n"
                "**3. Algorithmic Principles:**\n"
                "- **Relevance $\\hat{R}(f)$:** Normalized ANOVA F-statistic quantifying target class variance.\n"
                "- **Redundancy $\\hat{D}(f, S)$:** Mean absolute Pearson correlation between candidate $f$ and selected features $S$.\n"
                "- **Cost $\\hat{C}(f)$:** Penalizes compute-heavy summary metrics (Variance, Covariance, Radius) vs lightweight bitflags (TCP, SYN, UDP).\n"
                "- **Complexity:** $\\mathcal{O}(n \\cdot m^2 + k^2 m)$ with deterministic lexical tie-breaking."
            ))

        elif q in ("/models", "models"):
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                "### 🌲 Supported Classifier Architectures\n\n"
                "1. **Random Forest (`random_forest`):** Default ensemble of 50 bounded-depth trees. Excels in capturing non-linear network interactions while mitigating overfitting.\n"
                "2. **Decision Tree (`decision_tree`):** Ultra-fast, interpretable model with max depth 12. Ideal for sub-millisecond edge IoT verification.\n"
                "3. **Extra Trees (`extra_trees`):** Highly randomized ensemble providing lower variance on noisy packet rate statistics.\n"
                "4. **HistGradientBoosting (`gradient_boosting`):** Histogram-based gradient boosting optimized for tabular metrics."
            ))

        elif q in ("/metrics", "metrics"):
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                "### 📈 Evaluation Metrics Guide\n\n"
                "- **Macro F1-Score:** Unweighted average of F1 across all classes. Critical for IoT security because it prevents minority attacks (e.g. Mirai, SQLi) from being obscured by majority flood traffic.\n"
                "- **Accuracy:** Fraction of correct classifications. High accuracy on imbalanced data is often deceptive!\n"
                "- **False Positive Rate (FPR):** $\\frac{FP}{FP + TN}$. Benign traffic incorrectly flagged as attacks; minimizing FPR prevents operator alert fatigue.\n"
                "- **Inference Latency:** Average time in milliseconds to classify a network flow record."
            ))

        elif q in ("/runs", "runs"):
            runs = self.engine.list_runs(limit=3)
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            if not runs:
                log.write("[dim]No training runs recorded yet. Switch to the [2] RUNS tab to launch a training run.[/dim]")
            else:
                lines = ["### 🚀 Recent Model Training Runs\n"]
                for r in runs:
                    lines.append(
                        f"- `{r.run_id}`: **{r.model_name}** ({r.task_type}) | "
                        f"Macro F1: **{r.macro_f1:.4f}** | Latency: `{r.inference_latency_ms_per_sample:.4f} ms`"
                    )
                log.write(Markdown("\n".join(lines)))

        elif q in ("/policies", "policies"):
            pol = get_policies()
            enabled = [p for p in pol.policies if p.enabled]
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                f"### 🛡️ Active Security Policies\n"
                f"- **Rules Enabled:** {len(enabled)} of {len(pol.policies)}\n"
                f"- **Top Policies:** Mirai (CRITICAL), DDoS Flood (HIGH), Web Exploits (HIGH), Reconnaissance (MEDIUM)\n"
                f"- **Audit History:** {len(pol.audit_log)} changes recorded. Switch to the **[5] POLICIES** tab to modify rules."
            ))

        elif q in ("/imbalance", "imbalance"):
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                "### ⚖️ Handling IoT Class Imbalance\n\n"
                "Real IoT traffic is heavily skewed towards benign packets or massive DDoS floods. "
                "A naive model predicting only the majority class could achieve 95% accuracy while missing every single intrusion! "
                "DEVRAKSHAK counters this through:\n"
                "1. **Cost-Sensitive Class Weighting (`class_weight='balanced'`):** Penalizes misclassifying rare attack classes.\n"
                "2. **Training Partition Resampling:** Optional Random Under-Sampling or SMOTE applied strictly to train splits.\n"
                "3. **Macro F1 Prioritization:** Benchmarking models on equal-weight per-class performance."
            ))

        elif q in ("/monitor", "monitor"):
            summary = self.engine.get_monitor_stats()
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                f"### 📡 Offline Detection Telemetry\n"
                f"- **Total Flow Records Classified:** {summary['total_records_processed']:,}\n"
                f"- **Benign Flows:** {summary['benign_count']:,}\n"
                f"- **Intrusions & DDoS Floods:** {summary['attack_count']:,}\n"
                f"Switch to the **[4] MONITOR** tab to run batch classification or inspect category distributions."
            ))

        else:
            log.write("[bold green]DEVRAKSHAK Assistant:[/bold green]")
            log.write(Markdown(
                f"I processed your query: *'{query}'*.\n\n"
                "Try one of the specialized commands:\n"
                "- `/help` - view all commands\n"
                "- `/audit` - inspect dataset schema and quality\n"
                "- `/lrrc` - understand the LRRC-FS mathematical formula\n"
                "- `/status` - check system datasets and detection counts\n"
                "- `/models` - compare classifier architectures\n"
                "- `/metrics` - learn why Macro F1 matters more than Accuracy"
            ))
