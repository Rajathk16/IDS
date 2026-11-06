"""Statistical utilities for confidence intervals and evaluation metrics."""

from __future__ import annotations
from scipy.stats import beta


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact binomial 95% CI. k=false positives, n=total negatives."""
    if n == 0:
        return (0.0, 1.0)
    lo = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k)
    return (lo, hi)


def fpr_with_ci(fp: int, n_negatives: int, alpha: float = 0.05) -> str:
    """Returns human-readable FPR string with 95% CI."""
    if n_negatives == 0:
        return "N/A (no negative samples)"
    fpr = fp / n_negatives
    lo, hi = clopper_pearson(fp, n_negatives, alpha)
    return f"{fp}/{n_negatives} benign ({fpr:.4f}; 95% CI [{lo:.4f}, {hi:.4f}])"
