"""Chronological splits and reproducible demo dates, independent of the system clock."""

from typing import Any
import pandas as pd
from src.data.calendar_features import build_calendar, daily_dates


def get_split_boundaries(config: dict[str, Any]) -> dict[str, pd.Timestamp]:
    """Floor train/validation sizes by date; assign all remaining dates to test."""
    dates = daily_dates(config)
    fractions = config["validation"]
    values = [fractions[key] for key in ("train_fraction", "validation_fraction", "test_fraction")]
    if any(not 0 < value < 1 for value in values) or abs(sum(values) - 1) > 1e-9:
        raise ValueError("Split fractions must be positive and sum to one.")
    train_count = int(len(dates) * values[0])
    val_count = int(len(dates) * values[1])
    if min(train_count, val_count, len(dates) - train_count - val_count) < 1:
        raise ValueError("Date range is too short for three nonempty chronological splits.")
    return {
        "train_start": dates[0],
        "train_end": dates[train_count - 1],
        "val_start": dates[train_count],
        "val_end": dates[train_count + val_count - 1],
        "test_start": dates[train_count + val_count],
        "test_end": dates[-1],
    }


def get_as_of_date(config: dict[str, Any]) -> pd.Timestamp:
    """Use the explicit demo date, or the first held-out test date when null."""
    override = config["project"].get("as_of_date")
    if override is None:
        return get_split_boundaries(config)["test_start"]
    date = pd.Timestamp(override)
    if pd.isna(date) or date.tzinfo is not None or date != date.normalize():
        raise ValueError("project.as_of_date must be a valid, timezone-free calendar date.")
    return date


def get_drift_start_date(config: dict[str, Any]) -> pd.Timestamp:
    """Default the gradual shift to validation start; allow an explicit override."""
    override = config["generator"]["drift"]["start_date"]
    date = get_split_boundaries(config)["val_start"] if override is None else pd.Timestamp(override)
    if pd.isna(date) or date.tzinfo is not None or date != date.normalize():
        raise ValueError("generator.drift.start_date must be a valid calendar date.")
    return date


def validate_forecast_calendar(config: dict[str, Any]) -> None:
    """Validate lunar and public holiday coverage through as-of plus the horizon."""
    horizon = config["project"]["forecast_horizon_days"]
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
        raise ValueError("project.forecast_horizon_days must be a positive integer.")
    as_of = get_as_of_date(config)
    dates = pd.date_range(as_of, as_of + pd.Timedelta(days=horizon))
    try:
        build_calendar(dates, config)
        # Building a full year also verifies that public holidays are actually populated.
        for year in sorted(set(dates.year)):
            annual = build_calendar(pd.date_range(f"{year}-01-01", f"{year}-12-31"), config)
            if not annual["holiday_flag"].any():
                raise ValueError(f"No public holiday coverage for {year}.")
    except (ValueError, IndexError) as error:
        raise ValueError(
            f"Forecast calendar does not cover {as_of.date()} through {dates[-1].date()}: {error}"
        ) from error


def date_context(config: dict[str, Any]) -> dict[str, Any]:
    """Describe the drift ramp's overlap with each split for reports and verification."""
    boundaries = get_split_boundaries(config)
    start = get_drift_start_date(config)
    end = start + pd.Timedelta(days=config["data"]["drift_duration_days"])
    start_split = next(
        (
            name
            for name in ("train", "val", "test")
            if boundaries[f"{name}_start"] <= start <= boundaries[f"{name}_end"]
        ),
        "outside_history",
    )
    overlap = {
        name: max(
            0,
            (
                min(end - pd.Timedelta(days=1), boundaries[f"{name}_end"])
                - max(start, boundaries[f"{name}_start"])
            ).days
            + 1,
        )
        for name in ("train", "val", "test")
    }
    return {
        **{key: date.strftime("%Y-%m-%d") for key, date in boundaries.items()},
        "as_of_date": get_as_of_date(config).strftime("%Y-%m-%d"),
        "forecast_horizon_days": config["project"]["forecast_horizon_days"],
        "calendar_required_through": (
            get_as_of_date(config) + pd.Timedelta(days=config["project"]["forecast_horizon_days"])
        ).strftime("%Y-%m-%d"),
        "drift_start": start.strftime("%Y-%m-%d"),
        "drift_plateau_date": end.strftime("%Y-%m-%d"),
        "drift_start_split": start_split,
        "drift_ramp_overlap_days": overlap,
        "drift_appears_in_test": bool(
            end >= boundaries["test_start"] and start <= boundaries["test_end"]
        ),
        "test_contains_shifted_demand": bool(start < boundaries["test_end"]),
        "split_rule": "floor(train*n), floor(validation*n), remainder to test; never shuffle",
    }
