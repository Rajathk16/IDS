"""Preprocessing module: cleaning, inf/nan handling, scaling, and transformation manifests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from src.core.logging_config import get_logger
from src.data.taxonomy import map_to_binary, map_to_category

logger = get_logger("preprocessor")


class PreprocessingManifest:
    """Serializable record of fitted preprocessing transformations and column mappings."""

    def __init__(
        self,
        input_features: List[str],
        target_column: str,
        task_type: str,
        classes: List[str],
        imputer_medians: Dict[str, float],
        scaler_means: Dict[str, float],
        scaler_scales: Dict[str, float],
        created_at: Optional[str] = None
    ):
        self.input_features = input_features
        self.target_column = target_column
        self.task_type = task_type
        self.classes = classes
        self.imputer_medians = imputer_medians
        self.scaler_means = scaler_means
        self.scaler_scales = scaler_scales
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_features": self.input_features,
            "target_column": self.target_column,
            "task_type": self.task_type,
            "classes": self.classes,
            "imputer_medians": self.imputer_medians,
            "scaler_means": self.scaler_means,
            "scaler_scales": self.scaler_scales,
            "created_at": self.created_at,
        }

    def save(self, file_path: Path) -> None:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> PreprocessingManifest:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


class IoTDataPreprocessor(BaseEstimator, TransformerMixin):
    """
    Robust preprocessor for CICIoT2023 traffic records.
    
    Cleaning rules:
      1. Replaces positive and negative infinities (+inf, -inf) with NaN.
      2. Imputes NaNs using median values learned STRICTLY from the training partition.
      3. Standardizes numeric features (zero mean, unit variance) using parameters fit ONLY on training.
      4. Encodes targets into integer or string categories deterministically.
      5. Generates a reproducible preprocessing manifest.
    """

    def __init__(
        self,
        task_type: str = "binary",
        target_column: str = "label",
        drop_duplicates_on_train: bool = False
    ):
        self.task_type = task_type  # 'binary' or 'multiclass'
        self.target_column = target_column
        self.drop_duplicates_on_train = drop_duplicates_on_train
        
        self.feature_names_: List[str] = []
        self.imputer_ = SimpleImputer(strategy="median")
        self.scaler_ = StandardScaler()
        self.label_encoder_ = LabelEncoder()
        self.manifest_: Optional[PreprocessingManifest] = None
        self.is_fitted_: bool = False

    def clean_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Replace infinities and invalid numeric values with NaNs for safe imputation.
        Does not drop rows silently; ensures consistent row shapes.
        """
        df_clean = df.copy()
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            df_clean[numeric_cols] = df_clean[numeric_cols].replace([np.inf, -np.inf], np.nan)
        return df_clean

    def extract_features_and_target(
        self,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Optional[np.ndarray]]:
        """
        Separate features X from target y.
        Guarantees that target labels and target-derived strings are excluded from X.
        """
        df_clean = self.clean_records(df)
        
        y: Optional[np.ndarray] = None
        if self.target_column in df_clean.columns:
            raw_labels = df_clean[self.target_column].astype(str)
            if self.task_type == "binary":
                mapped = raw_labels.apply(map_to_binary).to_numpy()
            else:
                mapped = raw_labels.apply(map_to_category).to_numpy()
            y = mapped
            X = df_clean.drop(columns=[self.target_column])
        else:
            X = df_clean

        # Filter strictly to numeric columns (IoT network traffic features)
        # Any residual non-numeric columns are logged and converted or removed
        non_numeric = X.select_dtypes(exclude=[np.number]).columns.tolist()
        if non_numeric:
            logger.warning(
                f"Non-numeric columns detected in features: {non_numeric}. "
                f"Attempting numeric conversion; invalid values coerced to NaN."
            )
            for col in non_numeric:
                X[col] = pd.to_numeric(X[col], errors="coerce")

        return X, y

    def fit(self, X: pd.DataFrame, y: Optional[np.ndarray] = None) -> IoTDataPreprocessor:
        """Fit imputation, scaling, and target encoding on training data only."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        self.feature_names_ = list(X.columns)

        # Fit imputer on X
        X_imputed = self.imputer_.fit_transform(X)

        # Fit scaler on imputed X
        self.scaler_.fit(X_imputed)

        # Fit label encoder if target provided
        classes: List[str] = []
        if y is not None:
            self.label_encoder_.fit(y)
            classes = [str(c) for c in self.label_encoder_.classes_]

        # Construct Manifest
        medians = {col: float(self.imputer_.statistics_[i]) for i, col in enumerate(self.feature_names_)}
        means = {col: float(self.scaler_.mean_[i]) for i, col in enumerate(self.feature_names_)}
        scales = {col: float(self.scaler_.scale_[i]) for i, col in enumerate(self.feature_names_)}

        self.manifest_ = PreprocessingManifest(
            input_features=self.feature_names_,
            target_column=self.target_column,
            task_type=self.task_type,
            classes=classes,
            imputer_medians=medians,
            scaler_means=means,
            scaler_scales=scales
        )

        self.is_fitted_ = True
        logger.info(f"Fitted IoTDataPreprocessor on {len(self.feature_names_)} features.")
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features using fitted imputer and scaler."""
        if not self.is_fitted_:
            raise RuntimeError("IoTDataPreprocessor must be fitted before calling transform().")

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names_)

        # Ensure exact matching column set
        aligned_df = pd.DataFrame(index=X.index)
        for col in self.feature_names_:
            if col in X.columns:
                aligned_df[col] = pd.to_numeric(X[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
            else:
                # If a feature was missing at inference, populate with fitted training median
                aligned_df[col] = self.manifest_.imputer_medians.get(col, 0.0)

        # Impute then scale
        X_imputed = self.imputer_.transform(aligned_df)
        X_scaled = self.scaler_.transform(X_imputed)
        return X_scaled

    def fit_transform(self, X: pd.DataFrame, y: Optional[np.ndarray] = None) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def encode_target(self, y: np.ndarray) -> np.ndarray:
        """Encode categorical labels into integer indices."""
        if not self.is_fitted_:
            raise RuntimeError("Preprocessor must be fitted before encoding targets.")
        return self.label_encoder_.transform(y)

    def decode_target(self, y_indices: np.ndarray) -> np.ndarray:
        """Decode integer indices back into original class label strings."""
        if not self.is_fitted_:
            raise RuntimeError("Preprocessor must be fitted before decoding targets.")
        return self.label_encoder_.inverse_transform(y_indices)
