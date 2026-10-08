"""Phase 1 contracts, reproducibility, causal pattern checks and SQLite round trips."""

from copy import deepcopy
import sqlite3
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import pytest
import requests
from src.data.calendar_features import build_calendar, daily_dates
from src.data.generator import expected_demand, generate_dataset, run_pipeline
from src.data.loader import load_sales, save_dataset
from src.data.quality import FIELD_DETAILS, validate_sales, validate_truth
from src.data.weather import get_weather, open_meteo_weather, synthetic_weather, validate_weather
from src.utils.config import load_config, resolve_path
from src.utils.dates import get_drift_start_date
from src.data.truth_loader import load_truth


@pytest.fixture
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    settings = deepcopy(load_config())
    monkeypatch.delenv(settings["sqlite"]["directory_env_variable"], raising=False)
    settings["data"]["weather_provider"] = "synthetic"
    settings["weather"]["cache_enabled"] = False
    for key, value in settings["paths"].items():
        settings["paths"][key] = str(tmp_path / value)
    return settings


@pytest.fixture(scope="module")
def dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    settings = deepcopy(load_config())
    settings["data"]["weather_provider"] = "synthetic"
    settings["weather"]["cache_enabled"] = False
    return generate_dataset(settings)


def test_shape_nonnegative_and_oracle_isolation(dataset: tuple, config: dict) -> None:
    sales, truth, calendar, weather = dataset
    expected_rows = len(daily_dates(config)) * len(config["menu"])
    assert len(sales) == len(truth) == expected_rows
    assert len(calendar) == len(weather) == len(daily_dates(config))
    assert sales["sales"].dropna().ge(0).all()
    assert set(sales) == set(FIELD_DETAILS)
    assert "latent_demand" not in sales and "expected_demand" not in sales
    validate_sales(sales, config)
    validate_truth(truth, sales)


def test_seed_reproducibility_and_change(dataset: tuple, config: dict) -> None:
    replay = generate_dataset(config)
    for original, repeated in zip(dataset, replay, strict=True):
        pd.testing.assert_frame_equal(original, repeated)
    config["project"]["seed"] += 1
    assert not generate_dataset(config)[0]["sales"].equals(dataset[0]["sales"])


def test_observed_weekend_seasonality(dataset: tuple) -> None:
    sales = dataset[0]
    clean = sales.loc[
        sales[["closure_flag", "stockout_flag", "missing_flag", "outlier_flag"]].sum(axis=1).eq(0)
    ]
    for category in ("cold_drink", "bakery"):
        frame = clean.loc[clean["category"].eq(category)]
        ratio = (
            frame.loc[frame["weekend_flag"].eq(1), "sales"].mean()
            / frame.loc[frame["weekend_flag"].eq(0), "sales"].mean()
        )
        assert ratio > 1.15


def test_quality_defects_and_closures(dataset: tuple) -> None:
    sales, truth = dataset[:2]
    for field in ("missing_flag", "stockout_flag", "outlier_flag", "closure_flag"):
        assert sales[field].sum() > 0
    assert sales["missing_flag"].eq(1).equals(sales["sales"].isna())
    assert sales.loc[sales["closure_flag"].eq(1), "sales"].eq(0).all()
    capped = sales.loc[sales["stockout_flag"].eq(1) & sales["missing_flag"].eq(0)]
    comparison = capped.merge(truth, on=["date", "item"], validate="one_to_one")
    assert comparison["sales"].lt(comparison["latent_demand"]).all()


def test_promotions_are_shop_day_events(config: dict) -> None:
    config["generator"]["promotions"]["mode"] = "shop_day"
    sales = generate_dataset(config)[0]
    counts = sales.groupby("date")["promo_flag"].sum()
    assert counts.max() == 1
    assert 0.05 < counts.gt(0).mean() < 0.11


def test_calendar_known_events_and_boundary_distances(config: dict) -> None:
    dates = pd.date_range("2023-01-01", "2025-12-31")
    calendar = build_calendar(dates, config).set_index("date")
    for day, name in (
        ("2023-03-08", "Holi"),
        ("2024-10-31", "Diwali"),
        ("2025-12-25", "Christmas"),
        ("2023-01-01", "New Year"),
        ("2025-08-15", "Independence Day"),
    ):
        assert calendar.loc[day, "festival_name"] == name
        assert calendar.loc[day, "days_to_next_festival"] == 0
        assert calendar.loc[day, "days_since_last_festival"] == 0
    assert calendar.loc["2025-12-31", "days_to_next_festival"] == 1
    assert calendar.loc["2025-08-15":"2025-08-17", "long_weekend_flag"].eq(1).all()
    assert calendar.loc["2025-12-31", "payday_flag"] == 1
    assert calendar.loc["2025-12-04", "payday_flag"] == 0


def test_missing_lunar_calendar_year_rejected(config: dict) -> None:
    with pytest.raises(ValueError, match="festival dates"):
        build_calendar(pd.date_range("2027-01-01", periods=10), config)


@pytest.mark.parametrize("kind", ["duplicate", "unsorted", "empty"])
def test_invalid_calendar_dates(kind: str, config: dict) -> None:
    inputs = {
        "duplicate": pd.DatetimeIndex(["2024-01-01", "2024-01-01"]),
        "unsorted": pd.DatetimeIndex(["2024-01-02", "2024-01-01"]),
        "empty": pd.DatetimeIndex([]),
    }
    with pytest.raises(ValueError, match="dates"):
        build_calendar(inputs[kind], config)


def test_weather_seed_physical_constraints(config: dict) -> None:
    dates = daily_dates(config)
    frame = synthetic_weather(dates, config)
    pd.testing.assert_frame_equal(frame, synthetic_weather(dates, config))
    assert frame["temp_min"].le(frame["temp_max"]).all()
    assert frame["rainfall"].ge(0).all()
    assert frame["rain_flag"].sum() > 0
    rainy_months = pd.DatetimeIndex(frame["date"]).month.isin(config["weather"]["monsoon_months"])
    assert (
        frame.loc[rainy_months, "rain_flag"].mean() > frame.loc[~rainy_months, "rain_flag"].mean()
    )


def test_weather_api_contract(monkeypatch: pytest.MonkeyPatch, config: dict) -> None:
    dates = pd.date_range("2024-01-01", periods=2)

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "daily": {
                    "time": ["2024-01-01", "2024-01-02"],
                    "temperature_2m_max": [30.0, 29.0],
                    "temperature_2m_min": [21.0, 20.0],
                    "precipitation_sum": [0.0, 5.0],
                }
            }

    def get(url: str, **kwargs: Any) -> Response:
        assert url == config["weather"]["archive_url"]
        assert (
            kwargs["params"]["daily"] == "temperature_2m_max,temperature_2m_min,precipitation_sum"
        )
        assert kwargs["params"]["timezone"] == config["project"]["timezone"]
        return Response()

    monkeypatch.setattr(requests, "get", get)
    frame = open_meteo_weather(dates, config)
    assert frame["rain_flag"].tolist() == [0, 1]
    assert frame["weather_source"].eq("open_meteo").all()


def test_weather_fallback_is_explicit(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, config: dict
) -> None:
    def fail(*args: Any, **kwargs: Any) -> None:
        raise requests.Timeout("offline")

    monkeypatch.setattr(requests, "get", fail)
    config["data"]["weather_provider"] = "auto"
    dates = daily_dates(config)
    assert get_weather(dates, config)["weather_source"].eq("synthetic_fallback").all()
    assert "using seeded synthetic" in caplog.text
    config["data"]["weather_provider"] = "open_meteo"
    with pytest.raises(requests.Timeout):
        get_weather(dates, config)


@pytest.mark.parametrize(
    "defect", ["missing_date", "duplicate", "negative_rain", "inverted_temperature", "nan"]
)
def test_weather_validation(defect: str, config: dict) -> None:
    dates = daily_dates(config)
    frame = synthetic_weather(dates, config)
    if defect == "missing_date":
        frame = frame.iloc[1:]
    elif defect == "duplicate":
        frame.loc[1, "date"] = frame.loc[0, "date"]
    elif defect == "negative_rain":
        frame.loc[0, "rainfall"] = -1
    elif defect == "inverted_temperature":
        frame.loc[0, "temp_min"] = frame.loc[0, "temp_max"] + 1
    else:
        frame.loc[0, "temp_max"] = np.nan
    with pytest.raises(ValueError):
        validate_weather(frame, dates)


def test_controlled_weather_promotion_and_festival_effects(dataset: tuple, config: dict) -> None:
    daily = dataset[2].merge(dataset[3], on="date")
    dry = daily.copy()
    dry["rain_flag"] = 0
    dry["temp_max"] = 25.0
    zeros = np.zeros(len(daily), dtype=bool)
    hot = dry.copy()
    hot["temp_max"] = 35.0
    for item in ("cold_coffee", "iced_latte"):
        assert (
            expected_demand(item, hot, zeros, zeros, config)
            > expected_demand(item, dry, zeros, zeros, config)
        ).all()
    for item in ("latte", "espresso"):
        assert (
            expected_demand(item, hot, zeros, zeros, config)
            < expected_demand(item, dry, zeros, zeros, config)
        ).all()
    rainy = dry.copy()
    rainy["rain_flag"] = 1
    for item in ("hot_chocolate", "masala_chai", "espresso"):
        assert (
            expected_demand(item, rainy, zeros, zeros, config)
            > expected_demand(item, dry, zeros, zeros, config)
        ).all()
    ones = np.ones(len(daily), dtype=bool)
    base = expected_demand("latte", dry, zeros, zeros, config)
    np.testing.assert_allclose(
        expected_demand("latte", dry, ones, ones, config) / base, config["data"]["promotion_lift"]
    )
    np.testing.assert_allclose(
        expected_demand("latte", dry, zeros, ones, config) / base,
        config["data"]["cannibalization_factor"],
    )
    regular = dry.copy()
    regular["festival_flag"], regular["holiday_flag"] = 0, 0
    regular["days_to_next_festival"] = 30
    pre = regular.copy()
    pre["days_to_next_festival"] = 1
    event = regular.copy()
    event["festival_flag"] = 1
    baseline = expected_demand("latte", regular, zeros, zeros, config)
    np.testing.assert_allclose(
        expected_demand("latte", pre, zeros, zeros, config) / baseline,
        config["data"]["festival_pre_lift"],
    )
    np.testing.assert_allclose(
        expected_demand("latte", event, zeros, zeros, config) / baseline,
        config["data"]["festival_day_factor"],
    )


@pytest.mark.parametrize("defect", ["negative", "duplicate", "missing_unflagged", "oracle"])
def test_sales_quality_rejects_defects(defect: str, dataset: tuple, config: dict) -> None:
    sales = dataset[0].copy()
    row = sales.index[sales["missing_flag"].eq(0)][0]
    if defect == "negative":
        sales.loc[row, "sales"] = -1
    elif defect == "duplicate":
        sales = pd.concat([sales, sales.iloc[[0]]], ignore_index=True)
    elif defect == "missing_unflagged":
        sales.loc[row, "sales"] = np.nan
    else:
        sales["latent_demand"] = 1
    with pytest.raises(ValueError):
        validate_sales(sales, config)


def test_invalid_probability_and_date_bounds(config: dict) -> None:
    config["data"]["promotion_probability"] = 1.1
    with pytest.raises(ValueError, match="promotion_probability"):
        generate_dataset(config)
    config["data"]["promotion_probability"] = 0.08
    config["data"]["end_date"] = "2022-01-01"
    with pytest.raises(ValueError, match="start_date"):
        generate_dataset(config)


def test_sqlite_roundtrip_indexes_and_oracle_isolation(dataset: tuple, config: dict) -> None:
    save_dataset(*dataset, config)
    loaded = load_sales(config)
    pd.testing.assert_frame_equal(dataset[0], loaded)
    with sqlite3.connect(resolve_path(config, "database")) as connection:
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='simulation_truth'"
            ).fetchone()
            is None
        )
        assert len(load_truth(config)) == len(dataset[1])
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO sales SELECT * FROM sales LIMIT 1")
    assert not {"latent_demand", "expected_demand"} & set(loaded)
    subset = load_sales(config, "2024-01-01", "2024-01-02")
    assert len(subset) == 2 * len(config["menu"])
    with pytest.raises(ValueError, match="start_date"):
        load_sales(config, "2025-01-01", "2024-01-01")


def test_failed_sqlite_refresh_rolls_back(
    dataset: tuple, config: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_dataset(*dataset, config)
    original = load_sales(config)
    to_sql = pd.DataFrame.to_sql

    def fail(frame: pd.DataFrame, name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "simulation_truth":
            raise RuntimeError("injected persistence failure")
        return to_sql(frame, name, *args, **kwargs)

    changed = dataset[0].copy()
    row = changed.index[changed["closure_flag"].eq(0) & changed["missing_flag"].eq(0)][0]
    changed.loc[row, "sales"] += 1
    monkeypatch.setattr(pd.DataFrame, "to_sql", fail)
    with pytest.raises(RuntimeError, match="injected"):
        save_dataset(changed, *dataset[1:], config)
    pd.testing.assert_frame_equal(original, load_sales(config))


def test_pipeline_artifacts_and_valid_weather_cache(
    config: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    config["weather"]["cache_enabled"] = True
    summary = run_pipeline(config)
    assert summary["rows"] == len(daily_dates(config)) * len(config["menu"])
    for key in (
        "database",
        "sales_csv",
        "truth_csv",
        "calendar_csv",
        "weather_cache",
        "weather_metadata",
        "data_summary",
        "sales_sample",
        "data_dictionary",
        "data_dictionary_json",
    ):
        assert resolve_path(config, key).exists()

    def fail(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("matching cache should be reused")

    monkeypatch.setattr("src.data.weather.synthetic_weather", fail)
    assert get_weather(daily_dates(config), config)["weather_source"].eq("synthetic").all()
    config["project"]["seed"] += 1
    with pytest.raises(AssertionError, match="cache"):
        get_weather(daily_dates(config), config)


def test_loader_missing_database(config: dict) -> None:
    with pytest.raises(FileNotFoundError, match="Generate data"):
        load_sales(config)


def test_gradual_drift_and_trend_endpoints(dataset: tuple, config: dict) -> None:
    daily = dataset[2].merge(dataset[3], on="date").copy()
    daily["temp_max"] = config["weather"]["demand_reference_temp"]
    for column in (
        "rain_flag",
        "weekend_flag",
        "festival_flag",
        "holiday_flag",
        "payday_flag",
        "long_weekend_flag",
    ):
        daily[column] = 0
    daily["days_to_next_festival"] = 30
    config["data"]["weekday_factors"] = [1.0] * 7
    config["demand_profiles"]["hot_drink"]["monthly_factors"] = [1.0] * 12
    config["data"]["annual_trend"] = 0
    zeros = np.zeros(len(daily), dtype=bool)
    demand = pd.Series(
        expected_demand("espresso", daily, zeros, zeros, config),
        index=pd.DatetimeIndex(daily["date"]),
    )
    start = get_drift_start_date(config)
    base = config["menu"]["espresso"]["base_demand"]
    assert demand.loc[start] == pytest.approx(base)
    halfway = start + pd.Timedelta(days=config["data"]["drift_duration_days"] // 2)
    final = start + pd.Timedelta(days=config["data"]["drift_duration_days"])
    assert demand.loc[halfway] == pytest.approx(base * 1.06)
    assert demand.loc[final] == pytest.approx(base * 1.12)
    assert demand.loc[final + pd.Timedelta(days=30)] == pytest.approx(demand.loc[final])
    config["data"]["drift_lift"] = 0
    config["data"]["annual_trend"] = 0.06
    trend = pd.Series(expected_demand("espresso", daily, zeros, zeros, config), index=demand.index)
    assert 1.0598 < trend.loc["2024-01-01"] / trend.loc["2023-01-01"] < 1.0601


@pytest.mark.parametrize("edge", ["all_missing", "all_closed"])
def test_no_clean_observations_produce_valid_summary(edge: str, config: dict) -> None:
    import json
    from src.data.quality import data_summary

    config["data"]["start_date"], config["data"]["end_date"] = "2024-01-01", "2024-01-14"
    config["data"]["closure_probability"] = 1 if edge == "all_closed" else 0
    config["data"]["missing_probability"] = 1 if edge == "all_missing" else 0
    dataset = generate_dataset(config)
    summary = data_summary(*dataset[:2], config)
    assert summary["clean_weekday_mean"] is None
    assert summary["clean_weekend_weekday_ratio"] is None
    json.dumps(summary, allow_nan=False)
