"""Statistical utility functions for SSBC."""

from typing import Any

import numpy as np
from scipy import stats
from scipy.stats import beta as beta_dist


def clopper_pearson_lower(k: int, n: int, confidence: float = 0.95) -> float:
    """Compute lower Clopper-Pearson (one-sided) confidence bound.

    Parameters
    ----------
    k : int
        Number of successes
    n : int
        Total number of trials
    confidence : float, default=0.95
        Confidence level (e.g., 0.95 for 95% confidence)

    Returns
    -------
    float
        Lower confidence bound for the true proportion

    Examples
    --------
    >>> lower = clopper_pearson_lower(k=5, n=10, confidence=0.95)
    >>> print(f"Lower bound: {lower:.3f}")

    Notes
    -----
    Uses Beta distribution quantiles for exact binomial confidence bounds.
    For PAC-style guarantees, you may want to use delta = 1 - confidence.
    """
    if k == 0:
        return 0.0
    # L = Beta^{-1}(1-confidence; k, n-k+1)
    # Note: Using (1-confidence) as the lower tail probability
    alpha = 1 - confidence
    return float(beta_dist.ppf(alpha, k, n - k + 1))


def clopper_pearson_upper(k: int, n: int, confidence: float = 0.95) -> float:
    """Compute upper Clopper-Pearson (one-sided) confidence bound.

    Parameters
    ----------
    k : int
        Number of successes
    n : int
        Total number of trials
    confidence : float, default=0.95
        Confidence level (e.g., 0.95 for 95% confidence)

    Returns
    -------
    float
        Upper confidence bound for the true proportion

    Examples
    --------
    >>> upper = clopper_pearson_upper(k=5, n=10, confidence=0.95)
    >>> print(f"Upper bound: {upper:.3f}")

    Notes
    -----
    Uses Beta distribution quantiles for exact binomial confidence bounds.
    For PAC-style guarantees, you may want to use delta = 1 - confidence.
    """
    if k == n:
        return 1.0
    # U = Beta^{-1}(confidence; k+1, n-k)
    # Note: Using confidence directly for upper tail
    return float(beta_dist.ppf(confidence, k + 1, n - k))


def clopper_pearson_intervals(labels: np.ndarray, confidence: float = 0.95) -> dict[int, dict[str, Any]]:
    """Compute Clopper-Pearson (exact binomial) confidence intervals for class prevalences.

    Parameters
    ----------
    labels : np.ndarray
        Binary labels (0 or 1)
    confidence : float, default=0.95
        Confidence level (e.g., 0.95 for 95% CI)

    Returns
    -------
    dict
        Dictionary with keys 0 and 1, each containing:
        - 'count': number of samples in this class
        - 'proportion': observed proportion
        - 'lower': lower bound of CI
        - 'upper': upper bound of CI

    Examples
    --------
    >>> labels = np.array([0, 0, 1, 1, 0])
    >>> intervals = clopper_pearson_intervals(labels, confidence=0.95)
    >>> print(intervals[0]['proportion'])
    0.6

    Notes
    -----
    The Clopper-Pearson interval is an exact binomial confidence interval
    based on Beta distribution quantiles. It provides conservative coverage
    guarantees.
    """
    alpha = 1 - confidence
    n_total = len(labels)

    intervals = {}

    for label in [0, 1]:
        count = np.sum(labels == label)
        proportion = count / n_total

        # Clopper-Pearson uses Beta distribution quantiles
        # Lower bound: Beta(count, n-count+1) at alpha/2
        # Upper bound: Beta(count+1, n-count) at 1-alpha/2

        if count == 0:
            lower = 0.0
            upper = stats.beta.ppf(1 - alpha / 2, count + 1, n_total - count)
        elif count == n_total:
            lower = stats.beta.ppf(alpha / 2, count, n_total - count + 1)
            upper = 1.0
        else:
            lower = stats.beta.ppf(alpha / 2, count, n_total - count + 1)
            upper = stats.beta.ppf(1 - alpha / 2, count + 1, n_total - count)

        intervals[label] = {"count": count, "proportion": proportion, "lower": lower, "upper": upper}

    return intervals


def cp_interval(count: int, total: int, confidence: float = 0.95) -> dict[str, float]:
    """Compute Clopper-Pearson exact confidence interval.

    Helper function for computing a single CI from count and total.

    Parameters
    ----------
    count : int
        Number of successes
    total : int
        Total number of trials
    confidence : float, default=0.95
        Confidence level

    Returns
    -------
    dict
        Dictionary with keys:
        - 'count': original count
        - 'proportion': count/total
        - 'lower': lower CI bound
        - 'upper': upper CI bound
    """
    alpha = 1 - confidence
    count = int(count)
    total = int(total)

    if total <= 0:
        return {"count": count, "proportion": 0.0, "lower": 0.0, "upper": 0.0}

    p = count / total

    if count == 0:
        lower = 0.0
        upper = stats.beta.ppf(1 - alpha / 2, 1, total)
    elif count == total:
        lower = stats.beta.ppf(alpha / 2, total, 1)
        upper = 1.0
    else:
        lower = stats.beta.ppf(alpha / 2, count, total - count + 1)
        upper = stats.beta.ppf(1 - alpha / 2, count + 1, total - count)

    return {"count": count, "proportion": float(p), "lower": float(lower), "upper": float(upper)}


def ensure_ci(d: dict[str, Any], count: int, total: int, confidence: float = 0.95) -> tuple[float, float, float]:
    """Extract or compute rate and confidence interval from a dictionary.

    If the dictionary already contains rate/CI information, use it.
    Otherwise, compute Clopper-Pearson CI from count/total.

    Parameters
    ----------
    d : dict
        Dictionary that may contain 'rate'/'proportion' and 'lower'/'upper'
    count : int
        Count for CI computation (if needed)
    total : int
        Total for CI computation (if needed)
    confidence : float, default=0.95
        Confidence level

    Returns
    -------
    tuple of (rate, lower, upper)
        Rate and confidence interval bounds
    """
    # Try to get existing rate
    r = None
    if isinstance(d, dict):
        if "rate" in d:
            r = float(d["rate"])
        elif "proportion" in d:
            r = float(d["proportion"])

    # Try to get existing CI
    lo, hi = 0.0, 0.0
    if isinstance(d, dict):
        if "ci_95" in d and isinstance(d["ci_95"], tuple | list) and len(d["ci_95"]) == 2:
            lo, hi = float(d["ci_95"][0]), float(d["ci_95"][1])
        else:
            lo = float(d.get("lower", 0.0))
            hi = float(d.get("upper", 0.0))

    # If missing or invalid, compute CP interval
    if r is None or (lo == 0.0 and hi == 0.0 and (count > 0 or total > 0)):
        ci = cp_interval(count, total, confidence)
        return ci["proportion"], ci["lower"], ci["upper"]

    return float(r), float(lo), float(hi)
