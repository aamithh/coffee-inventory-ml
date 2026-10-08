"""Chronological validation, common clean scoring targets and metric tables."""

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from src.utils.metrics import forecast_metrics


def walk_forward_splits(frame: pd.DataFrame, folds: int):
    """Expand training by unique date; all items from a day stay on the same side."""
    dates = pd.DatetimeIndex(sorted(frame.date.unique()))
    for train, valid in TimeSeriesSplit(n_splits=folds).split(dates):
        yield frame.date.isin(dates[train]), frame.date.isin(dates[valid])


def clean_scoring_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Evaluate only observed clean targets, even if training imputation is enabled."""
    return frame.loc[frame.record_status.eq("clean") & frame.target.notna()].copy()


def metric_table(
    rows: pd.DataFrame, predictions: dict[str, np.ndarray], lower=None, upper=None
) -> pd.DataFrame:
    """Use identical target rows for every model; report overall and per item."""
    records = []
    for model, prediction in predictions.items():
        for item, mask in [("overall", np.ones(len(rows), dtype=bool))] + [
            (item, rows.item.eq(item).to_numpy()) for item in sorted(rows.item.unique())
        ]:
            args = {}
            if model == "quantile_p50" and lower is not None:
                args = {"lower": np.asarray(lower)[mask], "upper": np.asarray(upper)[mask]}
            records.append(
                {
                    "model": model,
                    "item": item,
                    **forecast_metrics(
                        rows.target.to_numpy()[mask], np.asarray(prediction)[mask], **args
                    ),
                }
            )
    return pd.DataFrame(records)


def ordered_quantiles(values: np.ndarray) -> tuple[np.ndarray, int]:
    """Repair quantile crossing by sorting; report how many raw rows crossed."""
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3 or not np.isfinite(array).all():
        raise ValueError("Three finite quantile columns are required.")
    crossings = int((np.diff(array, axis=1) < 0).any(axis=1).sum())
    return np.sort(np.maximum(array, 0.0), axis=1), crossings
