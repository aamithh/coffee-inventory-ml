"""Comparable historical baselines with explicit missing-lag fallback."""

import numpy as np
import pandas as pd
from src.models.estimators import ModelBundle

BASELINES = {
    "naive": "sales_lag_1",
    "seasonal_naive": "sales_lag_7",
    "moving_average": "sales_rolling_mean_7",
}


def baseline_predictions(
    frame: pd.DataFrame, name: str, reference: ModelBundle, config: dict
) -> np.ndarray:
    """Use exact lag when available, then configured past-only fallback columns."""
    if name not in BASELINES:
        raise ValueError(f"Unknown baseline: {name}")
    values = frame[BASELINES[name]].copy()
    for column in config["models"]["baseline_fallback_columns"]:
        values = values.fillna(frame[column])
    fallback = (
        frame["category_past_mean"]
        .fillna(frame.category.map(reference.category_means))
        .fillna(reference.overall_mean)
    )
    values = values.fillna(fallback)
    values = values.where(frame.history_days.ge(reference.cold_start_days), fallback)
    return np.maximum(values.to_numpy(dtype=float), 0.0)
