"""Data splitting module with leakage prevention, stratification, and validation partitioning."""

from __future__ import annotations

from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from src.core.logging_config import get_logger

logger = get_logger("data_split")


def split_dataset(
    df: pd.DataFrame,
    target_column: str = "label",
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_seed: int = 42,
    stratify: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Split a dataset into training, test, and optional validation partitions.
    
    Leakage resistance safeguards:
      1. Preprocessing, scaling, and feature selection must NOT be performed prior to this split.
      2. Stratification is applied when class frequencies allow (every class count >= 2).
         If rare classes with < 2 records exist, stratification is automatically disabled with a warning.
      3. The test set is NEVER resampled or synthetically balanced.
      4. Explicit note: Random partitioning evaluates in-distribution performance and does
         NOT guarantee generalization to unseen IoT device hardware or future zero-day attacks.
    
    Returns:
        (df_train, df_test, df_val) where df_val may be empty if val_size <= 0.
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataframe.")

    total_rows = len(df)
    if total_rows < 10:
        raise ValueError(f"Dataset too small to split ({total_rows} rows). Need at least 10 rows.")

    y = df[target_column].astype(str)

    # Check whether stratification is mathematically possible
    class_counts = y.value_counts()
    can_stratify = stratify
    if stratify:
        min_count = class_counts.min()
        if min_count < 2:
            logger.warning(
                f"Rare class detected with only {min_count} instance(s) (e.g. {class_counts.idxmin()}). "
                f"Disabling stratification for this split to prevent sklearn error."
            )
            can_stratify = False

    stratify_target = y if can_stratify else None

    # Step 1: Split out Test set
    df_train_full, df_test = train_test_split(
        df,
        test_size=test_size,
        random_state=random_seed,
        stratify=stratify_target,
        shuffle=True
    )

    # Step 2: Split Validation set from remaining training if requested
    df_val = None
    if val_size > 0:
        val_relative_ratio = val_size / (1.0 - test_size)
        y_train_full = df_train_full[target_column].astype(str)
        val_stratify = None
        if can_stratify:
            train_class_counts = y_train_full.value_counts()
            if train_class_counts.min() >= 2:
                val_stratify = y_train_full

        df_train, df_val = train_test_split(
            df_train_full,
            test_size=val_relative_ratio,
            random_state=random_seed,
            stratify=val_stratify,
            shuffle=True
        )
    else:
        df_train = df_train_full

    logger.info(
        f"Split complete -> Train: {len(df_train):,} rows ({(len(df_train)/total_rows)*100:.1f}%), "
        f"Test: {len(df_test):,} rows ({(len(df_test)/total_rows)*100:.1f}%), "
        f"Val: {len(df_val) if df_val is not None else 0:,} rows "
        f"(Stratified: {can_stratify})."
    )

    return df_train, df_test, df_val
