"""Saved-artifact and fixed-origin recursive menu forecasts."""

from typing import Any
import joblib
import numpy as np
import pandas as pd
from src.features.build_features import build_prediction_features
from src.models.baselines import baseline_predictions
from src.models.evaluate import ordered_quantiles
from src.utils.config import resolve_path


def load_artifact(config: dict[str, Any]) -> dict:
    """Load a trusted local joblib artifact; external untrusted pickle files are unsupported."""
    return joblib.load(resolve_path(config, "model_bundle"))


def recursive_forecast(
    artifact: dict,
    history: pd.DataFrame,
    plans: pd.DataFrame,
    origin: str | pd.Timestamp,
    config: dict[str, Any],
    model_name: str | None = None,
    weather_forecasts: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Advance day-by-day with predicted counts and frozen-origin weather, never future actuals."""
    cutoff = pd.Timestamp(origin)
    if pd.to_datetime(history.date).ge(cutoff).any():
        raise ValueError("History must precede forecast origin.")
    name = model_name or artifact["selected_point"]
    bundle = artifact["point_models"][artifact["selected_point"]]
    checked = [artifact["point_models"].get(name, bundle), *artifact["quantile_models"]]
    if any(pd.Timestamp(model.trained_through) >= cutoff for model in checked):
        raise ValueError("Model was trained on or after the requested forecast origin.")
    required = ["date", "item", "category", "price", "promo_flag"]
    future = plans[required].copy()
    future["date"] = pd.to_datetime(future["date"])
    dates = pd.DatetimeIndex(sorted(future.date.unique()))
    if dates.empty or dates[0] != cutoff or not dates.equals(pd.date_range(cutoff, dates[-1])):
        raise ValueError("Plans must cover contiguous dates starting at origin.")
    context = history.copy()
    original_counts = (
        history.loc[history.record_status.isin(["clean", "closed"])].groupby("item").size()
    )
    frozen_weather = (
        history.sort_values("date").groupby("item")[["temp_max", "temp_min", "rainfall"]].last()
    )
    forecasts = []
    for day in dates:
        plan = future.loc[future.date.eq(day)]
        features = build_prediction_features(context, plan, day, config, weather_forecasts)
        rows = features.frame
        cold = rows.item.map(original_counts).fillna(0).lt(config["features"]["cold_start_days"])
        rows.loc[cold, "history_days"] = rows.loc[cold, "item"].map(original_counts).fillna(0)
        if name in artifact["point_models"]:
            point = artifact["point_models"][name].predict(rows)
        else:
            point = baseline_predictions(rows, name, bundle, config)
        raw = np.column_stack([model.predict(rows) for model in artifact["quantile_models"]])
        quantiles, _ = ordered_quantiles(raw)
        result = rows[["date", "item"]].copy()
        result["forecast"] = point
        result[["p10", "p50", "p90"]] = quantiles
        result["origin"] = cutoff
        result["horizon_day"] = (day - cutoff).days + 1
        result["quantile_crossed"] = (np.diff(raw, axis=1) < 0).any(axis=1)
        forecasts.append(result)
        appended = plan.copy()
        prediction_map = pd.Series(point, index=rows.item)
        appended["sales"] = appended.item.map(prediction_map)
        appended["record_status"] = "clean"
        for column in ("temp_max", "temp_min", "rainfall"):
            appended[column] = appended.item.map(frozen_weather[column])
        context = pd.concat([context, appended], ignore_index=True)
    return pd.concat(forecasts, ignore_index=True)
