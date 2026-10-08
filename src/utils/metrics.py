"""Forecast metrics with explicit denominator and interval semantics."""

import numpy as np


def forecast_metrics(actual, predicted, lower=None, upper=None) -> dict:
    """WAPE is absolute error / total actual; bias is mean predicted minus actual."""
    y, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if (
        y.ndim != 1
        or y.shape != p.shape
        or len(y) == 0
        or not np.isfinite(y).all()
        or not np.isfinite(p).all()
    ):
        raise ValueError("Metrics require aligned, nonempty finite one-dimensional arrays.")
    denominator = float(np.abs(y).sum())
    error = p - y
    result = {
        "rows": len(y),
        "wape": float(np.abs(error).sum() / denominator) if denominator else None,
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
        "bias": float(error.mean()),
    }
    if (lower is None) != (upper is None):
        raise ValueError("Supply both interval bounds.")
    if lower is not None:
        lo, hi = np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)
        if (
            lo.shape != y.shape
            or hi.shape != y.shape
            or not np.isfinite(lo).all()
            or not np.isfinite(hi).all()
            or (lo > hi).any()
        ):
            raise ValueError("Intervals must be finite, aligned and ordered.")
        result.update(
            interval_coverage=float(((y >= lo) & (y <= hi)).mean()),
            mean_interval_width=float((hi - lo).mean()),
        )
    return result
