"""Material needs and covariance-aware residual conversion without test-data access."""

from typing import Any
import numpy as np
import pandas as pd
from src.inventory.bom import bom_matrix

FORECAST_COLUMNS = {"forecast": "need", "p10": "need_p10", "p50": "need_p50", "p90": "need_p90"}


def material_requirements(forecasts: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Sum item counts times recipe and preparation wastage; quantile totals are proxies."""
    matrix = bom_matrix(config)
    required = {"date", "item", *FORECAST_COLUMNS}
    if not required.issubset(forecasts):
        raise ValueError(f"Missing forecast columns: {sorted(required - set(forecasts))}")
    frame = forecasts[list(required)].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    if frame.empty or frame.date.isna().any() or frame.duplicated(["date", "item"]).any():
        raise ValueError("Forecast date/item keys must be valid, nonempty and unique.")
    if frame.date.dt.tz is not None or frame.date.ne(frame.date.dt.normalize()).any():
        raise ValueError("Forecast dates must be timezone-free calendar days.")
    if not frame.item.isin(matrix.index).all():
        raise ValueError("Forecast contains an unknown menu item.")
    for _, group in frame.groupby("date"):
        if set(group.item) != set(matrix.index):
            raise ValueError("Every forecast date must cover all configured menu items.")
    numeric = frame[list(FORECAST_COLUMNS)].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (numeric < 0).any():
        raise ValueError("Forecast counts must be finite and nonnegative.")
    if frame.p10.gt(frame.p50).any() or frame.p50.gt(frame.p90).any():
        raise ValueError("Forecast quantiles must be ordered.")
    wastage = pd.Series(
        {name: 1 + value["wastage_factor"] for name, value in config["materials"].items()}
    )
    effective = matrix.mul(wastage, axis=1)
    result = None
    for source, target in FORECAST_COLUMNS.items():
        counts = frame.pivot(index="date", columns="item", values=source).reindex(
            columns=matrix.index
        )
        values = counts.to_numpy() @ effective.to_numpy()
        column = (
            pd.DataFrame(values, index=counts.index, columns=matrix.columns)
            .rename_axis(index="date", columns="material")
            .stack()
            .rename(target)
        )
        result = column.to_frame() if result is None else result.join(column)
    result = result.reset_index()
    result["unit"] = result.material.map(
        {name: value["unit"] for name, value in config["materials"].items()}
    )
    result["expected_cost"] = result.need * result.material.map(
        {name: value["unit_cost"] for name, value in config["materials"].items()}
    )
    return result.sort_values(["date", "material"]).reset_index(drop=True)


def material_residual_sigmas(
    errors: pd.DataFrame, config: dict[str, Any], origin: str | pd.Timestamp
) -> dict[str, float]:
    """Aggregate same-day item errors before sample std, preserving cross-item covariance."""
    matrix = bom_matrix(config)
    if not {"date", "item", "error"}.issubset(errors):
        raise ValueError("Residual inputs require date, item and signed error.")
    frame = errors[["date", "item", "error"]].copy()
    frame["date"] = pd.to_datetime(frame.date)
    if frame.date.isna().any() or frame.date.ge(pd.Timestamp(origin)).any():
        raise ValueError("Residuals must be dated strictly before the planning origin.")
    if (
        frame.duplicated(["date", "item"]).any()
        or not frame.item.isin(matrix.index).all()
        or not np.isfinite(frame.error).all()
    ):
        raise ValueError("Residual keys/errors must be unique, known and finite.")
    pivot = frame.pivot(index="date", columns="item", values="error").reindex(columns=matrix.index)
    if len(pivot) < 2 or pivot.isna().any().any():
        raise ValueError("At least two complete item-error days are required.")
    effective = matrix.mul(
        pd.Series(
            {name: 1 + value["wastage_factor"] for name, value in config["materials"].items()}
        ),
        axis=1,
    )
    material_errors = pivot.to_numpy() @ effective.to_numpy()
    return dict(zip(matrix.columns, np.std(material_errors, axis=0, ddof=1).tolist()))
