"""Dataset audit module for inspecting schemas, missing/infinite values, duplicates, and class distributions."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from src.core.events import DatasetAuditResult
from src.core.logging_config import get_logger
from src.core.settings import get_settings
from src.data.loader import discover_csv_files, inspect_schema, is_synthetic_file, iterate_csv_chunks
from src.data.taxonomy import CICIOT2023_FEATURE_NAMES

logger = get_logger("data_audit")


def audit_dataset(
    target_path: Path,
    target_column: Optional[str] = None,
    chunk_size: int = 50000,
    max_rows_for_audit: Optional[int] = 100000
) -> DatasetAuditResult:
    """
    Perform a comprehensive, memory-conscious data audit on raw CSV files.
    
    Inspects:
      - File sizes and disk footprint
      - Total rows and chunk-based processing
      - Schema verification against CICIoT2023 canonical features
      - Detection of NaN and positive/negative infinity values
      - Class label frequencies and severe imbalance warnings
      - Duplicate row estimates
    """
    settings = get_settings()
    target = Path(target_path)
    files = discover_csv_files(target)

    total_bytes = sum(f.stat().st_size for f in files)
    total_mb = round(total_bytes / (1024 * 1024), 2)
    is_synth = any(is_synthetic_file(f) for f in files)

    logger.info(f"Auditing {len(files)} file(s) ({total_mb} MB) at {target}")

    base_cols, detected_target = inspect_schema(files[0])
    chosen_target = target_column or detected_target

    warnings: List[str] = []
    if is_synth:
        warnings.append("SYNTHETIC DATA: This dataset is synthetic test data, not authentic CICIoT2023 traffic.")

    if not chosen_target:
        warnings.append("CRITICAL: No target label column found. Training cannot proceed without a label column.")

    # Check for missing CICIoT2023 features in schema
    feature_columns = [c for c in base_cols if c != chosen_target]
    missing_ciciot = [f for f in CICIOT2023_FEATURE_NAMES if f not in feature_columns]
    if missing_ciciot:
        warnings.append(
            f"Schema difference: {len(missing_ciciot)} official CICIoT2023 feature(s) not present "
            f"(e.g., {missing_ciciot[:3]}). Preprocessing will adapt to available columns."
        )

    total_rows = 0
    missing_count = 0
    infinite_count = 0
    duplicate_count = 0
    class_distribution: Dict[str, int] = {}
    sampled_rows_seen = 0

    # Accumulate stats chunk-by-chunk to stay under memory limits
    for file_path in files:
        if max_rows_for_audit is not None and total_rows >= max_rows_for_audit:
            break

        for chunk in iterate_csv_chunks(file_path, chunk_size=chunk_size):
            if max_rows_for_audit is not None:
                remaining = max_rows_for_audit - total_rows
                if remaining <= 0:
                    break
                if remaining < len(chunk):
                    chunk = chunk.iloc[:remaining]

            total_rows += len(chunk)
            sampled_rows_seen += len(chunk)

            # Check for NaNs
            missing_count += int(chunk.isna().sum().sum())

            # Check for positive or negative infinity in numeric columns
            numeric_cols = chunk.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                inf_mask = np.isinf(chunk[numeric_cols].to_numpy())
                infinite_count += int(np.sum(inf_mask))

            # Duplicate estimation
            duplicate_count += int(chunk.duplicated().sum())

            # Class label distribution
            if chosen_target and chosen_target in chunk.columns:
                counts = chunk[chosen_target].value_counts().to_dict()
                for label, cnt in counts.items():
                    lbl_str = str(label)
                    class_distribution[lbl_str] = class_distribution.get(lbl_str, 0) + int(cnt)

    # Class imbalance analysis
    if class_distribution:
        total_labeled = sum(class_distribution.values())
        min_class_count = min(class_distribution.values())
        max_class_count = max(class_distribution.values())
        imbalance_ratio = max_class_count / max(1, min_class_count)
        if imbalance_ratio > 20:
            warnings.append(
                f"Severe class imbalance detected: ratio {imbalance_ratio:.1f}:1 "
                f"between majority and minority classes. Class weighting or resampling recommended."
            )

    approx_memory_mb = round((total_rows * len(base_cols) * 8) / (1024 * 1024), 2)

    result = DatasetAuditResult(
        target_path=str(target),
        is_synthetic=is_synth,
        file_count=len(files),
        total_size_mb=total_mb,
        total_rows=total_rows,
        column_count=len(base_cols),
        feature_columns=feature_columns,
        target_column=chosen_target,
        missing_value_count=missing_count,
        infinite_value_count=infinite_count,
        duplicate_row_count=duplicate_count,
        class_distribution=class_distribution,
        memory_usage_mb=approx_memory_mb,
        warnings=warnings,
        schema_valid=bool(chosen_target is not None and len(feature_columns) > 0)
    )

    # Save Markdown report
    save_audit_report(result)
    return result


def save_audit_report(audit: DatasetAuditResult) -> Path:
    """Format and save a readable Markdown audit report."""
    settings = get_settings()
    reports_dir = settings.results_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    ts_str = audit.timestamp.strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"audit_report_{ts_str}.md"

    md = [
        "# Dataset Audit Report - IoT Network Intrusion & DDoS Detection",
        f"**Audit Timestamp:** {audit.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Target Path:** `{audit.target_path}`",
        f"**Dataset Origin:** {'SYNTHETIC (Development Test Data)' if audit.is_synthetic else 'Real CICIoT2023'}",
        "",
        "## Summary Statistics",
        f"- **File Count:** {audit.file_count}",
        f"- **Total Size on Disk:** {audit.total_size_mb:.2f} MB",
        f"- **Audited Row Count:** {audit.total_rows:,}",
        f"- **Column Count:** {audit.column_count}",
        f"- **Feature Columns:** {len(audit.feature_columns)}",
        f"- **Target Column:** `{audit.target_column}`",
        f"- **Missing (NaN) Values:** {audit.missing_value_count:,}",
        f"- **Infinite (+/- Inf) Values:** {audit.infinite_value_count:,}",
        f"- **Duplicate Rows:** {audit.duplicate_row_count:,}",
        f"- **Estimated In-Memory Footprint:** {audit.memory_usage_mb:.2f} MB",
        "",
        "## Target Class Distribution",
        "| Class Label | Row Count | Percentage |",
        "| :--- | :--- | :--- |"
    ]

    total_rows = max(1, audit.total_rows)
    for label, count in sorted(audit.class_distribution.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_rows) * 100
        md.append(f"| `{label}` | {count:,} | {pct:.2f}% |")

    md.append("")
    md.append("## Quality Warnings & Observations")
    if audit.warnings:
        for w in audit.warnings:
            md.append(f"- ⚠️ {w}")
    else:
        md.append("- ✅ No critical data quality issues identified.")

    md.append("")
    md.append("## Feature Columns Inspected")
    md.append("```")
    md.append(", ".join(audit.feature_columns))
    md.append("```")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    logger.info(f"Dataset audit report generated and saved to {report_file}")
    return report_file
