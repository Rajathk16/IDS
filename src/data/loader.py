"""Memory-conscious CSV loader and schema inspector for CICIoT2023 data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generator, List, Optional, Tuple
import pandas as pd
from src.core.logging_config import get_logger
from src.data.taxonomy import CICIOT2023_FEATURE_NAMES

logger = get_logger("data_loader")

POSSIBLE_LABEL_COLUMNS = [
    "label", "Label", "LABEL", "class", "Class", "CLASS", "attack_type", "Attack_type"
]


def is_synthetic_file(file_path: Path) -> bool:
    """Check if the dataset file is flagged as synthetic via metadata or directory."""
    path = Path(file_path)
    if "synthetic" in str(path).lower():
        return True
    meta_path = path.with_suffix(".meta.json")
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("is_synthetic", False))
        except Exception:
            pass
    return False


def discover_csv_files(target_path: Path) -> List[Path]:
    """Discover all CSV files in a given file path or directory."""
    target = Path(target_path)
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")

    if target.is_file():
        if target.suffix.lower() == ".csv":
            return [target]
        raise ValueError(f"Target file is not a CSV: {target}")

    csv_files = sorted(list(target.glob("*.csv")))
    if not csv_files:
        # Check subdirectories
        csv_files = sorted(list(target.rglob("*.csv")))
    return csv_files


def inspect_schema(file_path: Path) -> Tuple[List[str], Optional[str]]:
    """
    Read only the CSV header (first row) without loading the entire file into RAM.
    Returns (columns_list, detected_target_column).
    """
    sample = pd.read_csv(file_path, nrows=2)
    columns = list(sample.columns)
    target_col = None
    for candidate in POSSIBLE_LABEL_COLUMNS:
        if candidate in columns:
            target_col = candidate
            break
    return columns, target_col


def load_dataset(
    target_path: Path,
    sample_limit: Optional[int] = None,
    chunk_size: int = 50000,
    target_column: Optional[str] = None
) -> Tuple[pd.DataFrame, bool, List[Path]]:
    """
    Load data from a single CSV or multiple CSV files in a memory-conscious manner.
    
    Args:
        target_path: Path to CSV file or directory of CSV files.
        sample_limit: Maximum number of rows to return (useful for 8 GB RAM machines).
        chunk_size: Chunk size when reading large CSV files.
        target_column: Configurable label column. If None, auto-detected.

    Returns:
        (DataFrame, is_synthetic_flag, list_of_loaded_paths)
    """
    files = discover_csv_files(target_path)
    if not files:
        raise FileNotFoundError(f"No CSV files found in {target_path}")

    logger.info(f"Discovered {len(files)} CSV file(s) for loading at {target_path}")

    any_synthetic = any(is_synthetic_file(f) for f in files)
    if any_synthetic:
        logger.warning("Notice: Synthetic test data detected. Metrics and results will be marked as SYNTHETIC.")

    # Inspect the schema of the first file to establish base columns and target
    base_cols, detected_target = inspect_schema(files[0])
    chosen_target = target_column or detected_target

    if not chosen_target or chosen_target not in base_cols:
        raise ValueError(
            f"Could not identify target label column in {files[0].name}. "
            f"Columns found: {base_cols[:10]}... "
            f"Please specify --target-column from the available columns."
        )

    dfs: List[pd.DataFrame] = []
    total_loaded = 0

    for file_path in files:
        if sample_limit is not None and total_loaded >= sample_limit:
            break

        cols, tgt = inspect_schema(file_path)
        if chosen_target not in cols:
            logger.warning(
                f"Skipping {file_path.name}: schema does not contain expected target column '{chosen_target}'."
            )
            continue

        remaining = None if sample_limit is None else (sample_limit - total_loaded)
        if remaining is not None and remaining <= 0:
            break

        # Read in chunks or slice
        if remaining is not None and remaining <= chunk_size:
            chunk = pd.read_csv(file_path, nrows=remaining)
            dfs.append(chunk)
            total_loaded += len(chunk)
        else:
            # Chunked iteration to respect memory limits
            reader = pd.read_csv(file_path, chunksize=chunk_size)
            for chunk in reader:
                if remaining is not None:
                    to_take = min(len(chunk), remaining - total_loaded)
                    if to_take < len(chunk):
                        chunk = chunk.iloc[:to_take]
                dfs.append(chunk)
                total_loaded += len(chunk)
                if remaining is not None and total_loaded >= remaining:
                    break

    if not dfs:
        raise ValueError(f"Failed to load any valid data from {target_path}")

    combined = pd.concat(dfs, ignore_index=True)
    logger.info(
        f"Successfully loaded {len(combined):,} rows and {len(combined.columns)} columns "
        f"(Sample limit: {sample_limit})."
    )
    return combined, any_synthetic, files


def iterate_csv_chunks(
    file_path: Path,
    chunk_size: int = 50000
) -> Generator[pd.DataFrame, None, None]:
    """Yield chunks of a large CSV file sequentially to avoid memory exhaustion."""
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        yield chunk
