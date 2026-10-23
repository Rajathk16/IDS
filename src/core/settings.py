"""Application settings and configuration management using Pydantic v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Structured, validated configuration for the IoT IDS application."""

    model_config = SettingsConfigDict(
        env_prefix="IOT_IDS_",
        env_file=".env",
        extra="ignore"
    )

    # Directories
    data_dir: Path = Field(
        default=Path("data/raw"),
        description="Directory containing raw CICIoT2023 CSV files"
    )
    synthetic_dir: Path = Field(
        default=Path("data/synthetic"),
        description="Directory for synthetic offline test data"
    )
    processed_dir: Path = Field(
        default=Path("data/processed"),
        description="Directory for preprocessed features and manifests"
    )
    model_dir: Path = Field(
        default=Path("models"),
        description="Directory for saved model bundles and metadata"
    )
    results_dir: Path = Field(
        default=Path("results"),
        description="Directory for metrics, evaluation plots, and reports"
    )
    db_path: Path = Field(
        default=Path("iot_ids.sqlite"),
        description="SQLite database path for training runs and detection events"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Console and file log level")
    log_file: Path = Field(default=Path("iot_ids.log"), description="Log file destination")
    max_log_bytes: int = Field(default=5 * 1024 * 1024, description="Rotating log file max bytes")
    log_backup_count: int = Field(default=3, description="Rotating log file backup count")

    # Pipeline & Resource Controls
    sample_limit: Optional[int] = Field(
        default=20000,
        description="Max records to load when in sample mode (for laptops with 8 GB RAM)"
    )
    chunk_size: int = Field(
        default=50000,
        description="Chunk size for memory-conscious CSV loading"
    )
    random_seed: int = Field(default=42, description="Random state for reproducibility")
    test_size: float = Field(default=0.2, description="Proportion of dataset for test split")
    validation_size: float = Field(default=0.1, description="Proportion of dataset for validation split")

    # LRRC-FS Algorithm Parameters
    lrrc_relevance_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    lrrc_redundancy_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    lrrc_cost_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    lrrc_max_features: int = Field(default=15, ge=1, le=46)

    # Default Training & Inference Settings
    default_task: str = Field(default="binary", description="Default task: 'binary' or 'multiclass'")
    default_model: str = Field(default="random_forest", description="Default model: 'decision_tree', 'random_forest', 'extra_trees'")
    default_feature_selector: str = Field(default="lrrc", description="Default selector: 'lrrc', 'all', 'variance', 'kbest'")
    resampling_strategy: Optional[str] = Field(default=None, description="Resampling strategy: None, 'under_sample', 'smote'")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in levels:
            raise ValueError(f"Invalid log_level: {v}. Must be one of {levels}")
        return v.upper()

    @field_validator("default_task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        tasks = {"binary", "multiclass"}
        if v.lower() not in tasks:
            raise ValueError(f"Invalid default_task: {v}. Must be one of {tasks}")
        return v.lower()

    @field_validator("default_model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        models = {"decision_tree", "random_forest", "extra_trees", "gradient_boosting"}
        if v.lower() not in models:
            raise ValueError(f"Invalid default_model: {v}. Must be one of {models}")
        return v.lower()

    def ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        for path in [
            self.data_dir,
            self.synthetic_dir,
            self.processed_dir,
            self.model_dir,
            self.results_dir,
            self.results_dir / "metrics",
            self.results_dir / "plots",
            self.results_dir / "reports",
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def save_to_file(self, config_path: Path = Path("config/settings.json")) -> None:
        """Persist settings to a JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        # Convert Path objects to strings
        for k, v in data.items():
            if isinstance(v, Path):
                data[k] = str(v)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, config_path: Path = Path("config/settings.json")) -> AppSettings:
        """Load settings from a JSON file, or return defaults if file does not exist."""
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                return cls()
        return cls()


# Global singleton instance for settings
_settings_instance: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Return the global AppSettings instance, loading from config/settings.json if present."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AppSettings.load_from_file()
        _settings_instance.ensure_directories()
    return _settings_instance


def update_settings(new_settings: AppSettings) -> AppSettings:
    """Update and persist application settings."""
    global _settings_instance
    _settings_instance = new_settings
    _settings_instance.ensure_directories()
    _settings_instance.save_to_file()
    return _settings_instance
