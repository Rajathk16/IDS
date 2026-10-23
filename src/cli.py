"""Command Line Interface for the AI-Based Intrusion and DDoS Detection System."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path when invoked directly as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.core.engine import IDSEngine
from src.core.logging_config import setup_logging
from src.core.policies import get_policies, save_policies
from src.core.settings import get_settings

console = Console()


def cmd_synthetic(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Generate synthetic test dataset."""
    console.print(f"[bold cyan]Generating synthetic CICIoT2023 test data ({args.samples} samples)...[/bold cyan]")
    out = engine.generate_synthetic(n_samples=args.samples, output_name=args.output)
    console.print(f"[green][OK] Successfully generated synthetic dataset at:[/green] [bold]{out}[/bold]")
    console.print("[yellow]Note: All generated records are strictly identified as synthetic test data.[/yellow]")


def cmd_discover(args: argparse.Namespace, engine: IDSEngine) -> None:
    """List available raw and synthetic datasets."""
    datasets = engine.discover_datasets()
    
    table = Table(title="Discovered Datasets", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", width=12)
    table.add_column("File Name", style="white")
    table.add_column("Size", style="green", justify="right")
    table.add_column("Full Path", style="dim")

    for f in datasets["raw"]:
        sz_mb = f.stat().st_size / (1024 * 1024)
        table.add_row("Official Raw", f.name, f"{sz_mb:.2f} MB", str(f))

    for f in datasets["synthetic"]:
        sz_mb = f.stat().st_size / (1024 * 1024)
        table.add_row("Synthetic", f.name, f"{sz_mb:.2f} MB", str(f))

    if not datasets["raw"] and not datasets["synthetic"]:
        console.print("[yellow]No CSV files found in data/raw or data/synthetic.[/yellow]")
        console.print("Run: [bold]python src/cli.py synthetic[/bold] to generate a test dataset.")
    else:
        console.print(table)


def cmd_audit(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Run data quality and schema audit."""
    target_path = Path(args.path) if args.path else None
    console.print(f"[bold cyan]Auditing dataset at {target_path or 'default discovery'}...[/bold cyan]")
    result = engine.audit(target_path=target_path, max_rows=args.max_rows)

    console.print("\n[bold green][OK] Dataset Audit Completed[/bold green]")
    summary_table = Table(title="Audit Summary", show_header=False)
    summary_table.add_row("Dataset Origin", "[yellow]SYNTHETIC[/yellow]" if result.is_synthetic else "[green]Real CICIoT2023[/green]")
    summary_table.add_row("Audited Files", str(result.file_count))
    summary_table.add_row("Audited Rows", f"{result.total_rows:,}")
    summary_table.add_row("Total Size", f"{result.total_size_mb:.2f} MB")
    summary_table.add_row("Target Column", f"`{result.target_column}`")
    summary_table.add_row("Missing (NaN) Count", str(result.missing_value_count))
    summary_table.add_row("Infinite (+/- Inf) Count", str(result.infinite_value_count))
    summary_table.add_row("Duplicate Rows", f"{result.duplicate_row_count:,}")
    summary_table.add_row("Estimated Memory", f"{result.memory_usage_mb:.2f} MB")
    console.print(summary_table)

    if result.class_distribution:
        dist_table = Table(title="Target Class Distribution", show_header=True, header_style="bold blue")
        dist_table.add_column("Class Label", style="white")
        dist_table.add_column("Count", justify="right")
        dist_table.add_column("Percentage", justify="right")
        total = max(1, result.total_rows)
        for lbl, cnt in sorted(result.class_distribution.items(), key=lambda x: x[1], reverse=True)[:15]:
            dist_table.add_row(lbl, f"{cnt:,}", f"{(cnt/total)*100:.2f}%")
        console.print(dist_table)

    if result.warnings:
        console.print("\n[bold yellow]Quality Warnings:[/bold yellow]")
        for w in result.warnings:
            console.print(f"  [!] {w}")


def cmd_train(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Train and evaluate an intrusion detection model."""
    console.print(
        f"[bold cyan]Training Model: {args.model} | Task: {args.task} | "
        f"Selector: {args.selector} ({args.features} feats) | Samples: {args.samples or 'All'}...[/bold cyan]"
    )
    bundle, run = engine.train(
        data_path=Path(args.path) if args.path else None,
        task_type=args.task,
        model_name=args.model,
        feature_selector=args.selector,
        n_features=args.features,
        sample_limit=args.samples,
        resampling_strategy=args.resample,
        use_class_weight=args.class_weight
    )

    console.print(f"\n[bold green][OK] Training Run Succeeded: {run.run_id}[/bold green]")
    res_table = Table(show_header=False)
    res_table.add_row("Model Name", run.model_name)
    res_table.add_row("Task Type", run.task_type)
    res_table.add_row("Feature Selector", run.feature_selector)
    res_table.add_row("Features Selected", f"{run.selected_features_count} features: {run.selected_features[:5]}...")
    res_table.add_row("Training Duration", f"{run.training_duration_seconds:.3f} s")
    res_table.add_row("Inference Latency", f"{run.inference_latency_ms_per_sample:.4f} ms/sample")
    res_table.add_row("Accuracy", f"{run.accuracy:.4f}")
    res_table.add_row("Macro F1-Score", f"[bold green]{run.macro_f1:.4f}[/bold green]")
    res_table.add_row("Weighted F1-Score", f"{run.weighted_f1:.4f}")
    if run.false_positive_rate is not None:
        res_table.add_row("False Positive Rate", f"{run.false_positive_rate:.4f}")
    res_table.add_row("Model Bundle Saved", run.model_path)
    res_table.add_row("Confusion Matrix Plot", run.confusion_matrix_plot or "None")
    console.print(res_table)


def cmd_compare_selectors(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Run empirical comparison across feature selection algorithms."""
    console.print("[bold cyan]Running Empirical Feature Selection Comparison...[/bold cyan]")
    path = Path(args.path) if args.path else None
    res = engine.run_selector_comparison(data_path=path)
    console.print(f"[bold green][OK] Comparison complete! Report generated at:[/bold green] {res['report_file']}")

    table = Table(title="Feature Selection Performance Comparison", show_header=True, header_style="bold magenta")
    table.add_column("Selector", style="cyan")
    table.add_column("Features", justify="right")
    table.add_column("Train (s)", justify="right")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Macro F1", justify="right", style="bold green")
    table.add_column("FPR", justify="right")

    for r in res["results"]:
        if r.get("status") == "SUCCESS":
            fpr = f"{r['false_positive_rate']:.4f}" if r.get("false_positive_rate") is not None else "-"
            table.add_row(
                r["selector"],
                str(r["feature_count"]),
                f"{r['training_duration_s']:.2f}",
                f"{r['inference_latency_ms']:.4f}",
                f"{r['accuracy']:.4f}",
                f"{r['macro_f1']:.4f}",
                fpr
            )
    console.print(table)


def cmd_predict(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Run offline predictions on a CSV file."""
    csv_file = Path(args.input)
    model_file = Path(args.model) if args.model else None
    console.print(f"[bold cyan]Running offline inference on {csv_file.name}...[/bold cyan]")

    df_out, events = engine.predict_offline(csv_file, model_path=model_file, sample_limit=args.samples)
    
    atk_count = sum(e.is_attack for e in events)
    benign_count = len(events) - atk_count

    console.print(f"\n[bold green][OK] Offline Inference Complete[/bold green]")
    console.print(f"Total Records: {len(events):,} | Benign: {benign_count:,} | Attacks Detected: [bold red]{atk_count:,}[/bold red]")

    # Show first few detections
    sample_table = Table(title=f"Sample Detections (First {min(10, len(events))} rows)", show_header=True)
    sample_table.add_column("Row", justify="right")
    sample_table.add_column("Predicted Label", style="cyan")
    sample_table.add_column("Confidence", justify="right")
    sample_table.add_column("Category", style="yellow")
    sample_table.add_column("Severity", style="bold")
    sample_table.add_column("Policy Alert", style="red")

    for e in events[:10]:
        sev_color = "red" if e.severity in ("HIGH", "CRITICAL") else ("yellow" if e.severity == "MEDIUM" else "green")
        sample_table.add_row(
            str(e.row_index),
            e.predicted_label,
            f"{e.confidence:.2f}",
            e.attack_category,
            f"[{sev_color}]{e.severity}[/{sev_color}]",
            e.policy_triggered or "-"
        )
    console.print(sample_table)

    if args.output:
        df_out.to_csv(args.output, index=False)
        console.print(f"[green]Full annotated predictions exported to {args.output}[/green]")


def cmd_runs(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Display history of training runs."""
    runs = engine.list_runs(limit=args.limit)
    if not runs:
        console.print("[yellow]No training runs recorded yet in SQLite database.[/yellow]")
        return

    table = Table(title="Historical Training & Evaluation Runs", show_header=True, header_style="bold blue")
    table.add_column("Run ID", style="dim")
    table.add_column("Timestamp", style="white")
    table.add_column("Model", style="cyan")
    table.add_column("Task", style="yellow")
    table.add_column("Selector", style="magenta")
    table.add_column("Feats", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Macro F1", justify="right", style="bold green")
    table.add_column("Latency (ms)", justify="right")

    for r in runs:
        table.add_row(
            r.run_id[:20],
            r.timestamp.strftime("%Y-%m-%d %H:%M"),
            r.model_name,
            r.task_type,
            r.feature_selector,
            str(r.selected_features_count),
            f"{r.accuracy:.4f}",
            f"{r.macro_f1:.4f}",
            f"{r.inference_latency_ms_per_sample:.4f}"
        )
    console.print(table)


def cmd_events(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Display detection events."""
    events = engine.list_events(limit=args.limit, severity=args.severity, category=args.category)
    if not events:
        console.print("[yellow]No detection events match the requested filter.[/yellow]")
        return

    table = Table(title="Recent Detection Events", show_header=True, header_style="bold red")
    table.add_column("Time", style="dim")
    table.add_column("Source", style="white")
    table.add_column("Row", justify="right")
    table.add_column("Label", style="cyan")
    table.add_column("Conf", justify="right")
    table.add_column("Category", style="yellow")
    table.add_column("Severity", style="bold")
    table.add_column("Policy Rule", style="magenta")

    for e in events:
        sev_color = "red" if e.severity in ("HIGH", "CRITICAL") else ("yellow" if e.severity == "MEDIUM" else "green")
        table.add_row(
            e.timestamp.strftime("%H:%M:%S"),
            Path(e.source_file).name,
            str(e.row_index),
            e.predicted_label,
            f"{e.confidence:.2f}",
            e.attack_category,
            f"[{sev_color}]{e.severity}[/{sev_color}]",
            e.policy_triggered or "-"
        )
    console.print(table)


def cmd_policy(args: argparse.Namespace, engine: IDSEngine) -> None:
    """Manage alert policies."""
    policies = get_policies()
    if args.action == "show":
        table = Table(title="Configured Alert Policies", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="white")
        table.add_column("Category", style="yellow")
        table.add_column("Min Conf", justify="right")
        table.add_column("Severity", style="bold")
        table.add_column("Enabled", justify="center")

        for p in policies.policies:
            status = "[green]ENABLED[/green]" if p.enabled else "[red]DISABLED[/red]"
            table.add_row(p.policy_id, p.name, p.attack_category, f"{p.min_confidence:.2f}", p.severity, status)
        console.print(table)

    elif args.action == "toggle":
        if not args.id:
            console.print("[red]Error: Specify --id POL-xxx to toggle policy.[/red]")
            return
        success = policies.toggle_policy(args.id, args.enable)
        if success:
            save_policies()
            console.print(f"[green][OK] Policy {args.id} enabled state set to {args.enable}.[/green]")
        else:
            console.print(f"[red]Policy ID {args.id} not found.[/red]")


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="AI-Based Intrusion and DDoS Detection System for IoT Networks (CICIoT2023)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Operational subcommands")

    # tui
    subparsers.add_parser("tui", help="Launch interactive Textual Terminal User Interface")

    # synthetic
    p_syn = subparsers.add_parser("synthetic", help="Generate synthetic CICIoT2023 test data")
    p_syn.add_argument("--samples", type=int, default=3000, help="Number of samples to generate")
    p_syn.add_argument("--output", type=str, default="synthetic_ciciot2023.csv", help="Output file name")

    # discover
    subparsers.add_parser("discover", help="Discover available raw and synthetic datasets")

    # audit
    p_aud = subparsers.add_parser("audit", help="Audit dataset schema and data quality")
    p_aud.add_argument("--path", type=str, default=None, help="Path to CSV file or directory")
    p_aud.add_argument("--max-rows", type=int, default=50000, help="Max rows to inspect")

    # train
    p_trn = subparsers.add_parser("train", help="Train and evaluate a classifier")
    p_trn.add_argument("--path", type=str, default=None, help="Path to input dataset CSV")
    p_trn.add_argument("--task", type=str, default="binary", choices=["binary", "multiclass"])
    p_trn.add_argument("--model", type=str, default="random_forest", choices=["decision_tree", "random_forest", "extra_trees", "gradient_boosting"])
    p_trn.add_argument("--selector", type=str, default="lrrc", choices=["lrrc", "all", "variance", "kbest"])
    p_trn.add_argument("--features", type=int, default=15, help="Number of features to select")
    p_trn.add_argument("--samples", type=int, default=10000, help="Sample limit for memory efficiency")
    p_trn.add_argument("--resample", type=str, default=None, choices=["under_sample", "smote", None])
    p_trn.add_argument("--class-weight", action="store_true", help="Apply class-weighted cost learning")

    # compare-selectors
    p_cmp = subparsers.add_parser("compare-selectors", help="Empirically compare feature selectors")
    p_cmp.add_argument("--path", type=str, default=None, help="Path to dataset")

    # predict
    p_prd = subparsers.add_parser("predict", help="Run offline inference on a CSV file")
    p_prd.add_argument("--input", type=str, required=True, help="Input CSV file to classify")
    p_prd.add_argument("--model", type=str, default=None, help="Path to saved .joblib model bundle")
    p_prd.add_argument("--samples", type=int, default=1000, help="Max rows to classify")
    p_prd.add_argument("--output", type=str, default=None, help="Export annotated CSV to this path")

    # runs
    p_run = subparsers.add_parser("runs", help="List previous training runs")
    p_run.add_argument("--limit", type=int, default=20, help="Number of runs to show")

    # events
    p_evt = subparsers.add_parser("events", help="List detection events")
    p_evt.add_argument("--limit", type=int, default=50, help="Number of events to show")
    p_evt.add_argument("--severity", type=str, default=None, help="Filter severity (INFO, LOW, MEDIUM, HIGH, CRITICAL)")
    p_evt.add_argument("--category", type=str, default=None, help="Filter attack category")

    # policy
    p_pol = subparsers.add_parser("policy", help="Inspect and manage alert policies")
    p_pol.add_argument("action", choices=["show", "toggle"])
    p_pol.add_argument("--id", type=str, default=None, help="Policy ID (e.g. POL-001)")
    p_pol.add_argument("--enable", action="store_true", default=True, help="Set policy enabled state")
    p_pol.add_argument("--disable", dest="enable", action="store_false", help="Disable policy")

    return parser


def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()
    engine = IDSEngine()

    if not args.command:
        # Default behavior: run TUI if in interactive terminal, otherwise show help
        from src.tui.app import run_tui
        run_tui()
        return

    if args.command == "tui":
        from src.tui.app import run_tui
        run_tui()
    elif args.command == "synthetic":
        cmd_synthetic(args, engine)
    elif args.command == "discover":
        cmd_discover(args, engine)
    elif args.command == "audit":
        cmd_audit(args, engine)
    elif args.command == "train":
        cmd_train(args, engine)
    elif args.command == "compare-selectors":
        cmd_compare_selectors(args, engine)
    elif args.command == "predict":
        cmd_predict(args, engine)
    elif args.command == "runs":
        cmd_runs(args, engine)
    elif args.command == "events":
        cmd_events(args, engine)
    elif args.command == "policy":
        cmd_policy(args, engine)


if __name__ == "__main__":
    main()
