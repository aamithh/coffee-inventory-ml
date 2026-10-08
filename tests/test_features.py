"""Hand-computed feature and temporal noninterference checks."""

from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from src.data.quality import assert_no_truth_references
from src.features.build_features import build_features, build_prediction_features
from src.utils.config import load_config


@pytest.fixture
def config():
    return deepcopy(load_config())


@pytest.fixture
def sales():
    dates = pd.date_range("2023-01-01", periods=40)
    parts = []
    for item, offset in (("latte", 0), ("espresso", 100)):
        parts.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "item": item,
                    "category": "hot_drink",
                    "price": 100.0,
                    "promo_flag": 0,
                    "sales": np.arange(1, 41) + offset,
                    "record_status": "clean",
                    "temp_max": np.arange(40) + 20.0,
                    "temp_min": np.arange(40) + 10.0,
                    "rainfall": np.arange(40) % 2,
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def test_hand_computed_lags_rolls_weather(sales, config):
    result = build_features(sales, config)
    row = result.frame.query("item == 'latte'").iloc[7]
    assert row.sales_lag_1 == 7 and row.sales_lag_7 == 1
    assert row.sales_rolling_mean_7 == 4
    assert row.sales_rolling_std_7 == pytest.approx(np.std(np.arange(1, 8), ddof=1))
    assert row.temp_max == 26 and row.temp_min == 16
    assert np.isnan(result.frame.query("item == 'latte'").iloc[0].sales_lag_1)
    assert "record_status" not in result.feature_columns
    assert "target" not in result.feature_columns
    assert row.history_days == 7


@pytest.mark.parametrize("policy", ["exclude", "impute"])
def test_current_future_observations_cannot_change_past_predictors(sales, config, policy):
    config["features"]["censored_target_policy"] = policy
    cutoff = pd.Timestamp("2023-01-22")
    original = build_features(sales, config)
    changed = sales.copy()
    mask = changed.date.ge(cutoff)
    changed.loc[mask, ["sales", "temp_max", "temp_min", "rainfall"]] = [999999, 999, 998, 999]
    changed.loc[mask, "record_status"] = "stockout"
    other = build_features(changed, config)
    columns = original.feature_columns
    pd.testing.assert_frame_equal(
        original.frame.loc[original.frame.date.le(cutoff), columns].reset_index(drop=True),
        other.frame.loc[other.frame.date.le(cutoff), columns].reset_index(drop=True),
    )


def test_cross_item_category_fallback_is_past_only(sales, config):
    result = build_features(sales, config).frame
    row = result.query("item == 'latte'").iloc[1]
    assert row.category_past_mean == 51
    assert result.query("item == 'espresso'").iloc[1].sales_lag_1 == 101
    assert row.cold_start_flag == 1


def test_defects_excluded_and_stockouts_imputed_from_prior_clean(sales, config):
    sales.loc[4, "record_status"] = "stockout"
    sales.loc[4, "sales"] = 1
    sales.loc[5, "record_status"] = "outlier"
    sales.loc[5, "sales"] = 100000
    sales.loc[6, "record_status"] = "missing"
    sales.loc[6, "sales"] = np.nan
    config["features"]["censored_target_policy"] = "impute"
    result = build_features(sales, config).frame.query("item == 'latte'").reset_index(drop=True)
    assert result.loc[4, "target"] == 2.5
    assert result.loc[4, "target_imputed"]
    assert not result.loc[5:6, "target_eligible"].any()
    assert np.isnan(result.loc[5, "sales_lag_1"])
    assert result.loc[7, "sales_rolling_mean_7"] == 2.5
    config["features"]["censored_target_policy"] = "exclude"
    assert not build_features(sales, config).frame.query("item == 'latte'").iloc[4].target_eligible


def test_closed_history_zero_but_target_excluded(sales, config):
    sales.loc[2, "record_status"] = "closed"
    sales.loc[2, "sales"] = 0
    rows = build_features(sales, config).frame.query("item == 'latte'")
    assert rows.iloc[3].sales_lag_1 == 0
    assert not rows.iloc[2].target_eligible


def test_sorted_input_and_duplicate_gap_validation(sales, config):
    first = build_features(sales, config)
    second = build_features(sales.sample(frac=1, random_state=42), config)
    pd.testing.assert_frame_equal(first.frame, second.frame)
    with pytest.raises(ValueError, match="unique"):
        build_features(pd.concat([sales, sales.iloc[:1]]), config)
    with pytest.raises(ValueError, match="contiguous"):
        build_features(sales.drop(index=3), config)


@pytest.mark.parametrize(
    "key,value",
    [
        ("lags", [0]),
        ("rolling_windows", [7, 7]),
        ("censored_target_policy", "future"),
        ("temperature_bins", [30, 20]),
    ],
)
def test_invalid_configuration(sales, config, key, value):
    config["features"][key] = value
    with pytest.raises(ValueError):
        build_features(sales, config)


def test_timestamped_weather_contract(sales, config):
    config["features"]["weather_policy"] = "supplied"
    dates = pd.DatetimeIndex(sales.date.unique())
    weather = pd.DataFrame(
        {
            "date": dates,
            "issued_at": dates - pd.Timedelta(hours=6),
            "temp_max": 30.0,
            "temp_min": 20.0,
            "rainfall": 0.0,
        }
    )
    rows = build_features(sales, config, weather).frame
    assert rows.temp_max.eq(30).all()
    weather.loc[0, "issued_at"] = weather.loc[0, "date"]
    with pytest.raises(ValueError, match="issued before"):
        build_features(sales, config, weather)
    with pytest.raises(ValueError, match="requires"):
        build_features(sales, config)


def test_prediction_origin_future_actuals_and_unknown_lags(sales, config):
    origin = "2023-02-10"
    plans = sales.groupby("item").tail(3).copy()
    plans["date"] = plans["date"] + pd.Timedelta(days=3)
    result = build_prediction_features(sales, plans, origin, config)
    rows = result.frame.query("item == 'latte'")
    assert rows.iloc[0].sales_lag_1 == 40
    assert np.isnan(rows.iloc[1].sales_lag_1)
    assert not result.frame.target_eligible.any()
    assert rows.temp_max.eq(59).all()
    with pytest.raises(ValueError, match="strictly"):
        build_prediction_features(sales, plans, "2023-02-09", config)


def test_split_and_guard_on_actual_data(config):
    from src.features.build_features import load_feature_dataset

    result = load_feature_dataset(config)
    assert len(result.frame) == 10960
    assert result.training_rows().date.max() == pd.Timestamp("2025-02-05")
    assert result.training_rows("val").date.min() == pd.Timestamp("2025-02-06")
    assert len(result.feature_columns) == len(set(result.feature_columns))
    assert_no_truth_references(config)


def test_eda_training_scope_and_all_five_figures(sales, config, tmp_path):
    from src.eda.report import create_eda

    from src.data.calendar_features import build_calendar

    sales = sales.merge(
        build_calendar(pd.DatetimeIndex(sorted(sales.date.unique())), config), on="date"
    )
    sales["rain_flag"] = sales.rainfall.ge(config["weather"]["rain_threshold_mm"]).astype(int)
    summary = create_eda(sales, config, tmp_path)
    assert summary["split"] == "train" and summary["rows"] == 80
    assert len(summary["figures"]) == 5
    for filename in summary["figures"].values():
        assert (tmp_path / filename).read_bytes().startswith(b"\x89PNG")
    config["eda"]["split"] = "invalid"
    with pytest.raises(ValueError, match="split"):
        create_eda(sales, config, tmp_path)


def test_late_weather_vintage_rejected_at_fixed_origin(sales, config):
    config["features"]["weather_policy"] = "supplied"
    dates = pd.DatetimeIndex(sales.date.unique())
    weather = pd.DataFrame(
        {
            "date": dates,
            "issued_at": dates - pd.Timedelta(hours=1),
            "temp_max": 30.0,
            "temp_min": 20.0,
            "rainfall": 0.0,
        }
    )
    with pytest.raises(ValueError, match="forecast origin"):
        build_features(sales, config, weather, forecast_origin="2023-01-20")


def test_supplied_future_forecast_needs_only_future_dates(sales, config):
    config["features"]["weather_policy"] = "supplied"
    dates = pd.date_range("2023-02-10", periods=2)
    plans = pd.DataFrame(
        [
            {"date": date, "item": item, "category": "hot_drink", "price": 100.0, "promo_flag": 0}
            for date in dates
            for item in ("latte", "espresso")
        ]
    )
    weather = pd.DataFrame(
        {
            "date": dates,
            "issued_at": pd.Timestamp("2023-02-09 12:00"),
            "temp_max": 30.0,
            "temp_min": 20.0,
            "rainfall": 1.0,
        }
    )
    result = build_prediction_features(sales, plans, "2023-02-10", config, weather)
    assert result.frame.temp_max.eq(30).all()
    assert result.frame.rain_flag.eq(1).all()
    with pytest.raises(ValueError, match="cover"):
        build_prediction_features(sales, plans, "2023-02-10", config, weather.iloc[:1])


def test_truncating_future_preserves_feature_prefix(sales, config):
    cutoff = pd.Timestamp("2023-01-25")
    full = build_features(sales, config)
    prefix = build_features(sales.loc[sales.date.le(cutoff)], config)
    pd.testing.assert_frame_equal(
        full.frame.loc[full.frame.date.le(cutoff), full.feature_columns].reset_index(drop=True),
        prefix.frame[prefix.feature_columns],
    )
