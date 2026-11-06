"""Dataset builder for balanced train/val pools and held-out test evaluation sets.

CLI: python -m src.data.build_dataset [--raw-dir data/raw] [--output-dir data/processed] [--n-per-class 6000] [--test-rows 100000] [--seed 42]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from src.core.logging_config import get_logger
from src.data.taxonomy import (
    CICIOT2023_FEATURE_NAMES,
    get_supported_categories,
    map_to_category
)

logger = get_logger("build_dataset")

POSSIBLE_LABEL_COLUMNS = [
    "label", "Label", "LABEL", "class", "Class", "CLASS", "attack_type", "Attack_type"
]


def deduplicate_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows (all feature columns + label)."""
    return df.drop_duplicates().reset_index(drop=True)


def find_target_column(columns: List[str]) -> Optional[str]:
    """Detect label column from schema."""
    for c in POSSIBLE_LABEL_COLUMNS:
        if c in columns:
            return c
    return None


def save_dataset_pool(df: pd.DataFrame, base_path: Path) -> Path:
    """Save dataframe as parquet if pyarrow is installed, otherwise fallback to CSV."""
    base_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyarrow  # noqa: F401
        target_path = base_path.with_suffix(".parquet")
        df.to_parquet(target_path, index=False)
        logger.info(f"Saved parquet pool to {target_path} ({len(df):,} rows)")
        return target_path
    except ImportError:
        target_path = base_path.with_suffix(".csv")
        df.to_csv(target_path, index=False)
        logger.info(f"Saved CSV pool to {target_path} ({len(df):,} rows)")
        return target_path


def load_dataset_pool(base_path: Path) -> pd.DataFrame:
    """Load dataframe from parquet if present, otherwise CSV."""
    parquet_path = base_path.with_suffix(".parquet")
    csv_path = base_path.with_suffix(".csv")
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    elif csv_path.exists():
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"Neither {parquet_path} nor {csv_path} found.")


def build_dataset_pipeline(
    raw_dir: Path = Path("data/raw/MERGED_CSV"),
    output_dir: Path = Path("data/processed"),
    n_per_class: int = 6000,
    test_rows: int = 100000,
    seed: int = 42,
    chunk_size: int = 50000
) -> int:
    """Execute streaming chunked dataset construction."""
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)

    # Check for raw CSV files
    if not raw_dir.exists():
        print(f"[build_dataset] ERROR: Directory '{raw_dir}' does not exist. Provide the CICIoT2023 CSVs there.", flush=True)
        return 1

    csv_files = sorted(list(raw_dir.rglob("Merged*.csv")))
    if not csv_files:
        print(f"[build_dataset] ERROR: No Merged*.csv files found under '{raw_dir}'. Place the CICIoT2023 files there.", flush=True)
        return 1

    total_files = len(csv_files)
    logger.info(f"Found {total_files} CSV files in {raw_dir}")

    # File split
    if total_files >= 13:
        train_files = csv_files[:53] if total_files >= 63 else csv_files[:-10]
        test_files = csv_files[53:] if total_files >= 63 else csv_files[-10:]
    else:
        split_idx = max(1, int(total_files * 0.7))
        train_files = csv_files[:split_idx]
        test_files = csv_files[split_idx:]

    logger.info(f"Train/Val files: {len(train_files)} | Test files: {len(test_files)}")

    categories = get_supported_categories()
    collected_train: Dict[str, List[pd.DataFrame]] = {cat: [] for cat in categories}
    counts_train: Dict[str, int] = {cat: 0 for cat in categories}

    # Inspect first file schema
    first_df = pd.read_csv(train_files[0], nrows=2)
    target_col = find_target_column(list(first_df.columns))
    if not target_col:
        raise ValueError(f"Could not identify target label column in {train_files[0].name}")

    # 1. Stream train CSV files
    logger.info(f"Streaming train CSV files to collect up to {n_per_class} rows per class...")
    for fpath in train_files:
        # Check if quota already filled for all classes
        if all(c >= n_per_class for c in counts_train.values()):
            logger.info("Target class quotas fulfilled across all categories.")
            break

        for chunk in pd.read_csv(fpath, chunksize=chunk_size):
            if target_col not in chunk.columns:
                continue

            mapped_labels = chunk[target_col].astype(str).apply(map_to_category)
            chunk = chunk.copy()
            chunk["mapped_category"] = mapped_labels

            for cat in categories:
                needed = n_per_class - counts_train[cat]
                if needed <= 0:
                    continue

                cat_rows = chunk[chunk["mapped_category"] == cat]
                if len(cat_rows) > 0:
                    to_take = cat_rows.iloc[:needed]
                    collected_train[cat].append(to_take)
                    counts_train[cat] += len(to_take)

    # Combine training rows
    all_train_parts = []
    for cat, parts in collected_train.items():
        if parts:
            all_train_parts.append(pd.concat(parts, ignore_index=True))

    if not all_train_parts:
        print("[build_dataset] Warning: No training data collected. Exiting.")
        return 0

    df_train_raw = pd.concat(all_train_parts, ignore_index=True)
    logger.info(f"Raw collected train rows: {len(df_train_raw):,}")

    # 2. Deduplicate
    df_train_dedup = deduplicate_dataset(df_train_raw)
    logger.info(f"Deduplicated train rows: {len(df_train_dedup):,}")

    # 3. Train/Val 80/20 Stratified Split
    val_stratify = df_train_dedup["mapped_category"] if df_train_dedup["mapped_category"].nunique() > 1 else None
    df_train_pool, df_val_pool = train_test_split(
        df_train_dedup,
        test_size=0.2,
        random_state=seed,
        stratify=val_stratify
    )
    logger.info(f"Train pool: {len(df_train_pool):,} rows | Val pool: {len(df_val_pool):,} rows")

    # 4. Stream held-out test files (natural distribution)
    logger.info(f"Streaming held-out test files (target: {test_rows:,} rows)...")
    collected_test_chunks: List[pd.DataFrame] = []
    test_collected_count = 0

    for fpath in test_files:
        if test_collected_count >= test_rows * 2:
            break
        for chunk in pd.read_csv(fpath, chunksize=chunk_size):
            if target_col not in chunk.columns:
                continue
            chunk = chunk.copy()
            chunk["mapped_category"] = chunk[target_col].astype(str).apply(map_to_category)
            collected_test_chunks.append(chunk)
            test_collected_count += len(chunk)
            if test_collected_count >= test_rows * 2:
                break

    if collected_test_chunks:
        df_test_raw = pd.concat(collected_test_chunks, ignore_index=True)
        df_test_dedup = deduplicate_dataset(df_test_raw)
        if len(df_test_dedup) > test_rows:
            df_test_pool = df_test_dedup.sample(n=test_rows, random_state=seed).reset_index(drop=True)
        else:
            df_test_pool = df_test_dedup
    else:
        df_test_pool = pd.DataFrame()

    logger.info(f"Test pool: {len(df_test_pool):,} rows")

    # 5. Save output pools
    output_dir.mkdir(parents=True, exist_ok=True)
    save_dataset_pool(df_train_pool, output_dir / "train_pool")
    save_dataset_pool(df_val_pool, output_dir / "val_pool")
    save_dataset_pool(df_test_pool, output_dir / "test_pool")

    # Build summary
    summary = {
        "n_train": len(df_train_pool),
        "n_val": len(df_val_pool),
        "n_test": len(df_test_pool),
        "train_class_distribution": df_train_pool["mapped_category"].value_counts().to_dict(),
        "val_class_distribution": df_val_pool["mapped_category"].value_counts().to_dict(),
        "test_class_distribution": df_test_pool["mapped_category"].value_counts().to_dict() if len(df_test_pool) > 0 else {},
        "train_files": [f.name for f in train_files],
        "test_files": [f.name for f in test_files],
        "seed": seed,
        "n_per_class": n_per_class
    }
    summary_path = output_dir / "dataset_build_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Dataset build complete. Summary saved to {summary_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Build balanced train/val and natural test dataset pools.")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Directory of raw Merged*.csv files (searched recursively)")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory for processed pools")
    parser.add_argument("--n-per-class", type=int, default=6000, help="Max rows per class for train/val pool")
    parser.add_argument("--test-rows", type=int, default=100000, help="Max rows for natural test pool")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--chunk-size", type=int, default=50000, help="Chunk size for CSV streaming")
    args = parser.parse_args()

    return build_dataset_pipeline(
        raw_dir=Path(args.raw_dir),
        output_dir=Path(args.output_dir),
        n_per_class=args.n_per_class,
        test_rows=args.test_rows,
        seed=args.seed,
        chunk_size=args.chunk_size
    )


if __name__ == "__main__":
    sys.exit(main())
