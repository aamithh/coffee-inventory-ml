"""Calendar covariates known before a sales day, including configured festivals."""

from typing import Any
import holidays
import numpy as np
import pandas as pd


def daily_dates(config: dict[str, Any]) -> pd.DatetimeIndex:
    """Return the configured inclusive daily range; reject invalid bounds."""
    start = pd.Timestamp(config["data"]["start_date"])
    end = pd.Timestamp(config["data"]["end_date"])
    if pd.isna(start) or pd.isna(end) or start > end:
        raise ValueError("Data dates must be valid and start_date <= end_date.")
    return pd.date_range(start, end, freq="D")


def festival_events(years: range, config: dict[str, Any]) -> dict[pd.Timestamp, str]:
    """Combine recurring events with editable, explicitly dated lunar festivals."""
    settings = config["calendar"]
    events: dict[pd.Timestamp, str] = {}
    for year in years:
        for name, month_day in settings["recurring_festivals"].items():
            events[pd.Timestamp(f"{year}-{month_day}")] = name
    for date, name in settings["dated_festivals"].items():
        timestamp = pd.Timestamp(date)
        if timestamp.year in years:
            events[timestamp] = name
    # Explicit what-if events alter only selected dates in an isolated config copy.
    for date, name in settings.get("scenario_festivals", {}).items():
        timestamp = pd.Timestamp(date)
        if timestamp.year in years:
            if name:
                events[timestamp] = name
            else:
                events.pop(timestamp, None)
    return events


def build_calendar(dates: pd.DatetimeIndex, config: dict[str, Any]) -> pd.DataFrame:
    """Build calendar flags and distances without using realized sales."""
    if dates.empty or dates.has_duplicates or dates.hasnans or not dates.is_monotonic_increasing:
        raise ValueError("Calendar dates must be nonempty, unique, valid and sorted.")
    settings = config["calendar"]
    years = range(dates.min().year - 1, dates.max().year + 2)
    for year in range(dates.min().year, dates.max().year + 1):
        named = {
            name
            for date, name in settings["dated_festivals"].items()
            if pd.Timestamp(date).year == year
        }
        if not set(settings["required_dated_festivals"]).issubset(named):
            raise ValueError(f"Add configured lunar festival dates for {year}.")
    india = holidays.country_holidays(
        settings["country"],
        subdiv=settings["subdivision"],
        years=years,
        observed=settings["observed"],
    )
    events = festival_events(years, config)
    event_dates = np.array(sorted(events), dtype="datetime64[ns]")
    index = np.searchsorted(event_dates, dates.to_numpy())
    previous = np.searchsorted(event_dates, dates.to_numpy(), side="right") - 1
    days_until = (event_dates[index] - dates.to_numpy()).astype("timedelta64[D]").astype(int)
    days_since = (dates.to_numpy() - event_dates[previous]).astype("timedelta64[D]").astype(int)
    holiday_names = [india.get(date.date(), "") for date in dates]
    festival_names = [events.get(date, "") for date in dates]
    result = pd.DataFrame(
        {
            "date": dates,
            "day_of_week": dates.dayofweek,
            "weekend_flag": dates.dayofweek.isin(settings["weekend_days"]).astype(int),
            "day_of_month": dates.day,
            "week_of_year": dates.isocalendar().week.to_numpy(dtype=int),
            "month": dates.month,
            "month_end_flag": dates.is_month_end.astype(int),
            "holiday_flag": [int(bool(name)) for name in holiday_names],
            "holiday_name": holiday_names,
            "festival_flag": [int(bool(name)) for name in festival_names],
            "festival_name": festival_names,
            "days_to_next_festival": days_until,
            "days_since_last_festival": days_since,
            "payday_flag": (
                (dates.day <= settings["payday_first_days"])
                | ((dates.days_in_month - dates.day) < settings["payday_last_days"])
            ).astype(int),
        }
    )
    # Pad both boundaries so a holiday run is not truncated by the requested range.
    padding = settings["long_weekend_padding_days"]
    extended = pd.date_range(
        dates.min() - pd.Timedelta(days=padding), dates.max() + pd.Timedelta(days=padding)
    )
    off = pd.Series(
        [
            date.dayofweek in settings["weekend_days"] or date.date() in india or date in events
            for date in extended
        ],
        index=extended,
    )
    runs = off.ne(off.shift()).cumsum()
    lengths = off.groupby(runs).transform("size")
    long_weekend = off & (lengths >= settings["long_weekend_min_days"])
    result["long_weekend_flag"] = long_weekend.reindex(dates).astype(int).to_numpy()
    # Canonical integer types keep SQLite round trips consistent across platforms.
    for column in result.select_dtypes(include="integer").columns:
        result[column] = result[column].astype("int64")
    return result
