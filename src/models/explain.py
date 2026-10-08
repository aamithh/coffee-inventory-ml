"""Exact additive model drivers; explanations describe associations, not causation."""

import numpy as np
import pandas as pd
import shap
from src.models.estimators import ModelBundle


def contributions(bundle: ModelBundle, frame: pd.DataFrame):
    """Tree SHAP for LightGBM; independent linear SHAP around training means for Ridge."""
    transformed = bundle.pipeline.named_steps["preprocess"].transform(frame[bundle.feature_columns])
    model = bundle.pipeline.named_steps["model"]
    names = bundle.pipeline.named_steps["preprocess"].get_feature_names_out()
    if bundle.name == "lightgbm":
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(transformed)
        base = float(np.asarray(explainer.expected_value).reshape(-1)[0])
    else:
        values = (transformed - bundle.transformed_mean) * model.coef_
        base = float(model.intercept_ + bundle.transformed_mean @ model.coef_)
    return np.asarray(values), base, transformed, list(names)


def explain_prediction(bundle: ModelBundle, row: pd.DataFrame, top_n: int = 5) -> dict:
    """Return signed drivers in units and explain clipping/cold-start overrides separately."""
    if len(row) != 1 or top_n < 1:
        raise ValueError("Supply exactly one prediction row and a positive driver count.")
    prediction = float(bundle.predict(row)[0])
    if row.iloc[0].history_days < bundle.cold_start_days:
        return {
            "forecast": prediction,
            "method": "past category average cold-start fallback",
            "drivers": [
                {
                    "feature": "category_past_mean",
                    "contribution": None,
                    "explanation": "Fewer than the configured history days; use prior category demand.",
                }
            ],
        }
    values, base, _, names = contributions(bundle, row)
    order = np.argsort(np.abs(values[0]))[::-1][:top_n]
    drivers = []
    for index in order:
        name = names[index].split("__", 1)[-1]
        direction = "raised" if values[0, index] >= 0 else "lowered"
        label = {
            "rain_flag": "Rain in the weather forecast",
            "weekend_flag": "The weekend schedule",
            "promo_flag": "The planned promotion",
            "temp_max": "Forecast maximum temperature",
            "temp_min": "Forecast minimum temperature",
            "rainfall": "Forecast rainfall",
        }.get(name, name.replace("_", " "))
        if name == "promo_flag" and row.iloc[0].promo_flag == 0:
            label = "No planned promotion"
        elif name == "weekend_flag" and row.iloc[0].weekend_flag == 0:
            label = "The weekday schedule"
        elif name == "rain_flag" and row.iloc[0].rain_flag == 0:
            label = "Dry forecast weather"
        drivers.append(
            {
                "feature": name,
                "contribution": float(values[0, index]),
                "explanation": f"{label} {direction} the model estimate by {abs(values[0, index]):.2f} units relative to its reference.",
            }
        )
    return {
        "forecast": prediction,
        "raw_model_estimate": float(base + values[0].sum()),
        "reference": base,
        "method": "additive SHAP association; not causal",
        "drivers": drivers,
    }
