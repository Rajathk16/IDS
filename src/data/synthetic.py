"""Synthetic CICIoT2023 dataset generator for testing and offline development.

All generated data is explicitly tagged and identified as synthetic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd
from src.core.logging_config import get_logger
from src.data.taxonomy import CICIOT2023_FEATURE_NAMES, CICIOT2023_CATEGORY_MAPPING

logger = get_logger("synthetic_generator")


def generate_synthetic_dataset(
    output_path: Path,
    n_samples: int = 3000,
    random_seed: int = 42,
    include_anomalous_values: bool = False
) -> Path:
    """
    Generate a small synthetic CSV matching the official CICIoT2023 schema.
    
    This function is strictly for unit testing and offline development when
    the official multi-gigabyte dataset is not yet downloaded. All outputs
    are explicitly marked as synthetic in the CSV and accompanying metadata.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(random_seed)

    logger.info(f"Generating synthetic CICIoT2023 dataset with {n_samples} samples at {output_path}")

    # Attack types and target sample distribution
    sample_classes = [
        ("BenignTraffic", 0.35),
        ("DDoS-UDP_Flood", 0.15),
        ("DDoS-TCP_Flood", 0.10),
        ("DDoS-SlowLoris", 0.05),
        ("DoS-UDP_Flood", 0.08),
        ("Recon-PortScan", 0.07),
        ("Recon-OSScan", 0.05),
        ("SqlInjection", 0.04),
        ("DictionaryBruteForce", 0.03),
        ("MITM-ArpSpoofing", 0.03),
        ("Mirai-greeth_flood", 0.03),
        ("Mirai-udpplain", 0.02),
    ]

    labels: list[str] = []
    for cls_name, ratio in sample_classes:
        count = int(n_samples * ratio)
        labels.extend([cls_name] * count)
    while len(labels) < n_samples:
        labels.append("BenignTraffic")
    labels = labels[:n_samples]
    rng.shuffle(labels)

    data: Dict[str, np.ndarray] = {}

    for feat in CICIOT2023_FEATURE_NAMES:
        if feat in ("Protocol Type", "IPv", "LLC"):
            # Categorical/discrete protocol indicators
            data[feat] = rng.choice([0, 1, 6, 17], size=n_samples)
        elif "flag_number" in feat:
            # Binary flag indicators (0 or 1)
            data[feat] = rng.binomial(1, p=0.15, size=n_samples)
        elif feat in ("HTTP", "HTTPS", "DNS", "Telnet", "SMTP", "SSH", "IRC", "TCP", "UDP", "DHCP", "ARP", "ICMP"):
            # Protocol one-hot style flags
            data[feat] = rng.binomial(1, p=0.2, size=n_samples)
        elif "count" in feat:
            # Packet and flag counts
            data[feat] = rng.poisson(lam=5, size=n_samples)
        elif feat in ("Rate", "Srate", "Drate"):
            # Packet arrival rates (higher for floods)
            base_rate = rng.exponential(scale=100.0, size=n_samples)
            data[feat] = np.round(base_rate, 4)
        elif feat in ("flow_duration", "Duration"):
            # Flow durations in seconds
            data[feat] = np.round(rng.exponential(scale=2.5, size=n_samples), 4)
        elif feat in ("Tot sum", "Min", "Max", "AVG", "Std", "Tot size"):
            # Packet length statistics
            data[feat] = np.round(rng.normal(loc=500.0, scale=200.0, size=n_samples).clip(0, 1500), 2)
        else:
            # General numerical flow metrics (Weight, Radius, Covariance, Magnitude, etc.)
            data[feat] = np.round(rng.uniform(0.0, 100.0, size=n_samples), 4)

    df = pd.DataFrame(data)

    # Condition specific attack features to reflect realistic attack signatures
    for idx, label in enumerate(labels):
        if "Flood" in label or "DDoS" in label:
            df.loc[idx, "Rate"] *= 10.0
            df.loc[idx, "syn_count"] += 20
        elif "Mirai" in label:
            df.loc[idx, "Rate"] *= 8.0
            df.loc[idx, "flow_duration"] = max(0.01, df.loc[idx, "flow_duration"] * 0.1)
        elif "Scan" in label:
            df.loc[idx, "syn_flag_number"] = 1
            df.loc[idx, "ack_flag_number"] = 0

    if include_anomalous_values:
        # Inject small realistic testing artifacts (a few NaNs and Infs to test audit/cleaner)
        nan_indices = rng.choice(n_samples, size=max(1, int(n_samples * 0.005)), replace=False)
        inf_indices = rng.choice(n_samples, size=max(1, int(n_samples * 0.003)), replace=False)
        df.loc[nan_indices, "Rate"] = np.nan
        df.loc[inf_indices, "flow_duration"] = np.inf

    df["label"] = labels

    # Write CSV
    df.to_csv(output_path, index=False)

    # Write sidecar metadata identifying it as synthetic
    meta_path = output_path.with_suffix(".meta.json")
    meta = {
        "is_synthetic": True,
        "generator": "src.data.synthetic.generate_synthetic_dataset",
        "n_samples": n_samples,
        "random_seed": random_seed,
        "notice": "THIS IS SYNTHETIC TEST DATA EXCLUSIVELY FOR OFFLINE DEVELOPMENT. IT IS NOT THE REAL CICIOT2023 DATASET."
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Synthetic dataset saved with {len(df)} rows and {len(df.columns)} columns.")
    return output_path
