"""Past-only item features and explicit predictor contracts for daily forecasting."""

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
from src.data.calendar_features import build_calendar
from src.data.loader import load_sales
from src.utils.dates import get_split_boundaries

CALENDAR_COLUMNS = [
    "day_of_week",
    "weekend_flag",
    "day_of_month",
    "week_of_year",
    "month",
    "month_end_flag",
    "holiday_flag",
    "festival_flag",
    "days_to_next_festival",
    "days_since_last_festival",
    "payday_flag",
    "long_weekend_flag",
]
WEATHER_COLUMNS = ["temp_max", "temp_min", "rainfall"]


@dataclass
class FeatureDataset:
    """Keep predictors separate from target-quality and evaluation metadata."""

    frame: pd.DataFrame
    feature_columns: list[str]

    def training_rows(self, split: str = "train") -> pd.DataFrame:
        """Select eligible targets; never infer predictors from all numeric columns."""
        return self.frame.loc[self.frame["split"].eq(split) & self.frame["target_eligible"]].copy()


def _settings(config: dict[str, Any]) -> dict[str, Any]:
    settings = config["features"]
    for key in ("lags", "rolling_windows"):
        values = settings[key]
        if (
            not values
            or len(set(values)) != len(values)
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 1
                for value in values
            )
        ):
            raise ValueError(f"{key} must contain distinct positive integers.")
    if settings["censored_target_policy"] not in ("exclude", "impute"):
        raise ValueError("censored_target_policy must be exclude or impute.")
    if settings["weather_policy"] not in ("persistence", "supplied"):
        raise ValueError("weather_policy must be persistence or supplied.")
    bins = settings["temperature_bins"]
    if not bins or not np.isfinite(bins).all() or np.any(np.diff(bins) <= 0):
        raise ValueError("temperature_bins must be finite and strictly increasing.")
    if settings["imputation_window"] < 1 or settings["cold_start_days"] < 1:
        raise ValueError("History windows must be positive.")
    return settings


def _ordered(sales: pd.DataFrame) -> pd.DataFrame:
    """Fail on gaps so positional shifts always represent calendar-day lags."""
    required = {"date", "item", "category", "price", "promo_flag", "sales", "record_status"}
    if not required.issubset(sales):
        raise ValueError(f"Missing inputs: {sorted(required - set(sales))}")
    frame = sales.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    if frame["date"].isna().any() or frame.duplicated(["date", "item"]).any():
        raise ValueError("Dates/items must be valid and unique.")
    if frame["date"].dt.tz is not None or frame["date"].ne(frame["date"].dt.normalize()).any():
        raise ValueError("Dates must be timezone-free calendar dates.")
    frame = frame.sort_values(["item", "date"]).reset_index(drop=True)
    for _, group in frame.groupby("item"):
        if group["date"].diff().dropna().ne(pd.Timedelta(days=1)).any():
            raise ValueError("Each item must have contiguous daily rows; retain missing-day rows.")
    return frame


def _forecast_weather(
    frame: pd.DataFrame,
    settings: dict[str, Any],
    forecasts: pd.DataFrame | None,
    origin: pd.Timestamp | None,
) -> pd.DataFrame:
    if settings["weather_policy"] == "persistence":
        if forecasts is not None:
            raise ValueError("Use supplied weather policy when passing weather forecasts.")
        if not set(WEATHER_COLUMNS).issubset(frame):
            raise ValueError("Persistence weather requires observed weather columns.")
        return frame.groupby("item")[WEATHER_COLUMNS].shift(1)
    if forecasts is None:
        raise ValueError("Supplied weather requires date, issued_at and forecast weather.")
    expected = {"date", "issued_at", *WEATHER_COLUMNS}
    if not expected.issubset(forecasts):
        raise ValueError("Forecast weather must include date, issued_at and forecast values.")
    weather = forecasts[list(expected)].copy()
    weather["date"] = pd.to_datetime(weather["date"])
    weather["issued_at"] = pd.to_datetime(weather["issued_at"])
    if weather["date"].duplicated().any() or weather[["date", "issued_at"]].isna().any().any():
        raise ValueError("Supply one valid forecast vintage per date.")
    if weather["date"].dt.tz is not None or weather["issued_at"].dt.tz is not None:
        raise ValueError("Forecast timestamps must be timezone-free local shop times.")
    if weather["issued_at"].ge(weather["date"]).any():
        raise ValueError("Weather forecasts must be issued before their prediction date.")
    if origin is not None and weather["issued_at"].ge(origin).any():
        raise ValueError("Weather forecasts must be issued before the forecast origin.")
    joined = frame[["date"]].merge(weather, on="date", how="left", validate="many_to_one")
    values = joined[WEATHER_COLUMNS]
    required_rows = (
        frame["date"].ge(origin).to_numpy()
        if origin is not None
        else np.ones(len(frame), dtype=bool)
    )
    if not np.isfinite(values.loc[required_rows].to_numpy(dtype=float)).all():
        raise ValueError("Forecast weather must cover every requested row.")
    if values["temp_min"].gt(values["temp_max"]).any() or values["rainfall"].lt(0).any():
        raise ValueError("Invalid forecast temperatures or rainfall.")
    return values.set_axis(frame.index)


def build_features(
    sales: pd.DataFrame,
    config: dict[str, Any],
    weather_forecasts: pd.DataFrame | None = None,
    forecast_origin: str | pd.Timestamp | None = None,
) -> FeatureDataset:
    """Build one-day-ahead rows using observations strictly before each target date.

    Calendar and planned price/promotion are known ahead. Weather is either yesterday's
    persistence forecast or an explicitly timestamped forecast. No fitted global
    statistics or future-dependent imputations are used.
    """
    settings = _settings(config)
    frame = _ordered(sales)
    origin = pd.Timestamp(forecast_origin) if forecast_origin is not None else None
    dates = pd.DatetimeIndex(sorted(frame["date"].unique()))
    calendar = build_calendar(dates, config).set_index("date")
    result = frame[["date", "item", "category", "price", "promo_flag", "record_status"]].copy()
    for column in CALENDAR_COLUMNS:
        result[column] = frame["date"].map(calendar[column])
    predictors = ["item", "category", "price", "promo_flag", *CALENDAR_COLUMNS]
    for column, period in settings["cyclical_periods"].items():
        if column not in CALENDAR_COLUMNS or period <= 0:
            raise ValueError("Cyclical periods must name calendar columns and be positive.")
        for name, function in (("sin", np.sin), ("cos", np.cos)):
            feature = f"{column}_{name}"
            result[feature] = function(2 * np.pi * result[column] / period)
            predictors.append(feature)
    weather = _forecast_weather(frame, settings, weather_forecasts, origin)
    for column in WEATHER_COLUMNS:
        result[column] = weather[column]
    result["rain_flag"] = (
        weather["rainfall"].ge(config["weather"]["rain_threshold_mm"]).astype(float)
    )
    result.loc[weather["rainfall"].isna(), "rain_flag"] = np.nan
    result["temp_bucket"] = pd.cut(
        weather["temp_max"], [-np.inf, *settings["temperature_bins"], np.inf], labels=False
    )
    predictors += [*WEATHER_COLUMNS, "rain_flag", "temp_bucket"]
    # Bad observations never enter lag history; closure zero is a legitimate past count.
    clean = frame["record_status"].eq("clean")
    history = frame["sales"].where(clean | frame["record_status"].eq("closed"))
    group_key = frame["item"]
    for lag in settings["lags"]:
        column = f"sales_lag_{lag}"
        result[column] = history.groupby(group_key).shift(lag)
        predictors.append(column)
    for window in settings["rolling_windows"]:
        grouped = history.groupby(group_key)
        for statistic in ("mean", "std"):
            column = f"sales_rolling_{statistic}_{window}"
            result[column] = grouped.transform(
                lambda values: getattr(values.shift(1).rolling(window, min_periods=1), statistic)()
            )
            predictors.append(column)
    result["history_days"] = (
        history.notna()
        .astype(int)
        .groupby(group_key)
        .transform(lambda values: values.cumsum().shift(1, fill_value=0))
    )
    result["cold_start_flag"] = result["history_days"].lt(settings["cold_start_days"]).astype(int)
    predictors += ["history_days", "cold_start_flag"]
    # This fallback pools only past clean category sales, including other established items.
    category_daily = (
        frame.assign(clean_sales=frame["sales"].where(clean))
        .groupby(["date", "category"])["clean_sales"]
        .agg(["sum", "count"])
        .reset_index()
    )
    category_daily = category_daily.sort_values(["category", "date"])
    for column in ("sum", "count"):
        category_daily[column] = category_daily.groupby("category")[column].transform(
            lambda values: values.cumsum().shift(1, fill_value=0)
        )
    category_daily["category_past_mean"] = category_daily["sum"] / category_daily["count"].replace(
        0, np.nan
    )
    result["category_past_mean"] = (
        frame[["date", "category"]]
        .merge(
            category_daily[["date", "category", "category_past_mean"]],
            on=["date", "category"],
            how="left",
            validate="many_to_one",
        )["category_past_mean"]
        .to_numpy()
    )
    predictors.append("category_past_mean")
    result["target"] = frame["sales"].where(clean)
    result["target_imputed"] = False
    if settings["censored_target_policy"] == "impute":
        estimate = (
            frame["sales"]
            .where(clean)
            .groupby(group_key)
            .transform(
                lambda values: values.shift(1)
                .rolling(settings["imputation_window"], min_periods=1)
                .mean()
            )
        )
        censored = frame["record_status"].eq("stockout") & estimate.notna()
        result.loc[censored, "target"] = estimate[censored]
        result.loc[censored, "target_imputed"] = True
    result["target_eligible"] = result["target"].notna()
    boundaries = get_split_boundaries(config)
    result["split"] = np.select(
        [
            result["date"].between(boundaries["train_start"], boundaries["train_end"]),
            result["date"].between(boundaries["val_start"], boundaries["val_end"]),
            result["date"].between(boundaries["test_start"], boundaries["test_end"]),
        ],
        ["train", "val", "test"],
        default="future",
    )
    return FeatureDataset(result.sort_values(["date", "item"]).reset_index(drop=True), predictors)


def build_prediction_features(
    history: pd.DataFrame,
    plans: pd.DataFrame,
    origin: str | pd.Timestamp,
    config: dict[str, Any],
    weather_forecasts: pd.DataFrame | None = None,
) -> FeatureDataset:
    """Build future rows without reading post-origin observations.

    Unknown future lags remain missing. A later forecasting loop must append its own
    predictions before advancing; this function never substitutes future actual sales.
    """
    cutoff = pd.Timestamp(origin)
    if pd.to_datetime(history["date"]).ge(cutoff).any():
        raise ValueError("History must be strictly before forecast origin.")
    if pd.to_datetime(plans["date"]).lt(cutoff).any():
        raise ValueError("Plans cannot precede forecast origin.")
    future = plans.copy()
    future["sales"] = np.nan
    future["record_status"] = "missing"
    if config["features"]["weather_policy"] == "persistence":
        latest = history.sort_values("date").groupby("item")[WEATHER_COLUMNS].last()
        for column in WEATHER_COLUMNS:
            future[column] = future["item"].map(latest[column])
    combined = pd.concat([history, future], ignore_index=True)
    # Supplied forecasts may include historic vintages, but all must predate origin.
    dataset = build_features(combined, config, weather_forecasts, cutoff)
    dataset.frame = dataset.frame.loc[dataset.frame["date"].ge(cutoff)].reset_index(drop=True)
    return dataset


def load_feature_dataset(config: dict[str, Any]) -> FeatureDataset:
    """Load observed sales only and construct the historical one-day-ahead dataset."""
    return build_features(load_sales(config), config)
