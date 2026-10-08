"""Model arithmetic, fold isolation, recursive noninterference and explanation checks."""

from copy import deepcopy
from dataclasses import dataclass
import joblib
import numpy as np
import pandas as pd
import pytest
from src.features.build_features import build_features
from src.models.baselines import baseline_predictions
from src.models.estimators import fit_bundle
from src.models.evaluate import (
    walk_forward_splits,
    clean_scoring_rows,
    ordered_quantiles,
    metric_table,
)
from src.models.explain import contributions, explain_prediction
from src.models.predict import recursive_forecast
from src.utils.config import load_config
from src.utils.metrics import forecast_metrics


@pytest.fixture
def config():
    config = deepcopy(load_config())
    config["models"]["lightgbm"]["n_estimators"] = 12
    config["models"]["lightgbm"]["min_child_samples"] = 3
    return config


@pytest.fixture
def sales():
    dates = pd.date_range("2023-01-01", periods=70)
    return pd.DataFrame(
        {
            "date": dates,
            "item": "latte",
            "category": "hot_drink",
            "price": 160.0,
            "promo_flag": 0,
            "sales": 20.0 + np.arange(70) % 7,
            "record_status": "clean",
            "temp_max": 30.0,
            "temp_min": 20.0,
            "rainfall": 0.0,
        }
    )


@pytest.fixture
def dataset(sales, config):
    return build_features(sales, config)


def test_metric_hand_computations():
    result = forecast_metrics([10, 20], [12, 18], [8, 17], [13, 19])
    assert result["wape"] == pytest.approx(4 / 30)
    assert result["mae"] == 2 and result["rmse"] == 2 and result["bias"] == 0
    assert result["interval_coverage"] == 0.5
    assert forecast_metrics([0], [0])["wape"] is None


@pytest.mark.parametrize(
    "actual,predicted", [([], []), ([1], [np.nan]), ([1, 2], [1]), ([[1]], [[1]])]
)
def test_metric_rejects_invalid_arrays(actual, predicted):
    with pytest.raises(ValueError):
        forecast_metrics(actual, predicted)


def test_interval_ordering_and_crossing():
    result, count = ordered_quantiles([[9, 5, 2], [-2, 3, 8]])
    np.testing.assert_equal(result, [[2, 5, 9], [0, 3, 8]])
    assert count == 1
    with pytest.raises(ValueError):
        forecast_metrics([2], [2], [3], [1])


def test_walk_forward_groups_dates_and_expands(dataset):
    rows = pd.concat([dataset.frame, dataset.frame.assign(item="espresso")], ignore_index=True)
    previous = 0
    for training, validation in walk_forward_splits(rows, 5):
        train_dates = set(rows.loc[training, "date"])
        valid_dates = set(rows.loc[validation, "date"])
        assert max(train_dates) < min(valid_dates)
        assert not train_dates & valid_dates and len(train_dates) > previous
        previous = len(train_dates)
    assert len(list(walk_forward_splits(rows, 5))) == 5


@pytest.mark.parametrize("name", ["ridge", "lightgbm"])
def test_preprocessing_training_only_and_serialization(dataset, config, tmp_path, name):
    rows = dataset.frame.iloc[:45].copy()
    rows.loc[10, "price"] = np.nan
    fitted = fit_bundle(name, rows, dataset.feature_columns, config)
    pre = fitted.pipeline.named_steps["preprocess"]
    imputer = pre.named_transformers_["numeric"].named_steps["impute"]
    numeric = [column for column in dataset.feature_columns if column not in ("item", "category")]
    assert imputer.statistics_[numeric.index("price")] == 160
    future = dataset.frame.iloc[45:].copy()
    future["price"] = 999999
    future["item"] = "new_item"
    future["category"] = "new_category"
    prediction = fitted.predict(future)
    assert np.isfinite(prediction).all()
    assert imputer.statistics_[numeric.index("price")] == 160
    path = tmp_path / "bundle.joblib"
    joblib.dump(fitted, path)
    np.testing.assert_allclose(joblib.load(path).predict(future), prediction)


@pytest.mark.parametrize("name", ["ridge", "lightgbm"])
def test_cold_start_point_fallback(dataset, config, name):
    bundle = fit_bundle(name, dataset.frame.iloc[:50], dataset.feature_columns, config)
    rows = dataset.frame.iloc[-1:].copy()
    rows["history_days"] = 3
    rows["category_past_mean"] = 42
    rows["item"] = "new_item"
    assert bundle.predict(rows)[0] == 42
    explanation = explain_prediction(bundle, rows)
    assert explanation["method"] == "past category average cold-start fallback"


def test_quantile_cold_start_uses_training_distribution(dataset, config):
    rows = dataset.frame.iloc[-1:].copy()
    rows["history_days"] = 0
    low = fit_bundle(
        "lightgbm", dataset.frame.iloc[:50], dataset.feature_columns, config, quantile=0.1
    )
    high = fit_bundle(
        "lightgbm", dataset.frame.iloc[:50], dataset.feature_columns, config, quantile=0.9
    )
    assert low.predict(rows)[0] < high.predict(rows)[0]


def test_baseline_exact_values_and_missing_fallback(dataset, config):
    reference = fit_bundle("ridge", dataset.frame.iloc[:50], dataset.feature_columns, config)
    row = dataset.frame.iloc[-1:].copy()
    row["sales_lag_1"] = 10
    row["sales_lag_7"] = 12
    row["sales_rolling_mean_7"] = 14
    assert baseline_predictions(row, "naive", reference, config)[0] == 10
    assert baseline_predictions(row, "seasonal_naive", reference, config)[0] == 12
    assert baseline_predictions(row, "moving_average", reference, config)[0] == 14
    row["sales_lag_7"] = np.nan
    assert baseline_predictions(row, "seasonal_naive", reference, config)[0] == 14


@dataclass
class LagBundle:
    trained_through: str = "2023-01-31"
    category_means: dict = None
    overall_mean: float = 20.0
    cold_start_days: int = 14

    def predict(self, frame):
        return frame.sales_lag_1.fillna(20).to_numpy() + 1


def recursive_setup(sales):
    model = LagBundle()
    return {
        "selected_point": "stub",
        "point_models": {"stub": model},
        "quantile_models": [model, model, model],
    }


def test_recursive_uses_predictions_and_ignores_future_actual_weather(sales, config):
    artifact = recursive_setup(sales)
    history = sales.iloc[:40]
    plans = sales.iloc[40:43].copy()
    original = recursive_forecast(artifact, history, plans, "2023-02-10", config)
    mutated = plans.copy()
    mutated[["sales", "temp_max", "temp_min", "rainfall"]] = [999999, 999, 998, 999]
    mutated["record_status"] = "outlier"
    other = recursive_forecast(artifact, history, mutated, "2023-02-10", config)
    pd.testing.assert_frame_equal(original, other)
    first = history.sales.iloc[-1] + 1
    np.testing.assert_equal(original.forecast.to_numpy(), [first, first + 1, first + 2])
    assert original.horizon_day.tolist() == [1, 2, 3]


def test_recursive_rejects_leaked_history_model_and_plan_gaps(sales, config):
    artifact = recursive_setup(sales)
    with pytest.raises(ValueError, match="History"):
        recursive_forecast(artifact, sales.iloc[:42], sales.iloc[40:43], "2023-02-10", config)
    artifact["point_models"]["stub"].trained_through = "2023-02-10"
    with pytest.raises(ValueError, match="trained"):
        recursive_forecast(artifact, sales.iloc[:40], sales.iloc[40:43], "2023-02-10", config)
    artifact = recursive_setup(sales)
    with pytest.raises(ValueError, match="contiguous"):
        recursive_forecast(artifact, sales.iloc[:40], sales.iloc[[40, 42]], "2023-02-10", config)


@pytest.mark.parametrize("name", ["ridge", "lightgbm"])
def test_explanations_add_up_and_return_five_drivers(dataset, config, name):
    bundle = fit_bundle(name, dataset.frame.iloc[:50], dataset.feature_columns, config)
    row = dataset.frame.iloc[-1:]
    values, base, _, _ = contributions(bundle, row)
    raw = bundle.pipeline.predict(row[dataset.feature_columns])[0]
    assert base + values[0].sum() == pytest.approx(raw, abs=1e-6)
    explanation = explain_prediction(bundle, row)
    assert len(explanation["drivers"]) == 5
    assert explanation["forecast"] == pytest.approx(bundle.predict(row)[0])


def test_common_clean_rows_and_per_item_metrics(dataset):
    rows = dataset.frame.copy()
    rows.loc[0, ["record_status", "target_imputed"]] = ["stockout", True]
    scored = clean_scoring_rows(rows)
    assert len(scored) == len(rows) - 1
    table = metric_table(scored, {"perfect": scored.target.to_numpy()})
    assert table.wape.eq(0).all() and set(table.item) == {"overall", "latte"}


def test_small_train_only_search_reports_all_models_and_folds(dataset, config):
    from src.models.train import tune_lightgbm

    config["models"]["tuning"] = {"num_leaves": [5], "learning_rate": [0.05]}
    parameters, results = tune_lightgbm(dataset.frame, dataset.feature_columns, config)
    assert parameters == {"num_leaves": 5, "learning_rate": 0.05}
    assert set(results.model) == {"lightgbm", "ridge", "naive", "seasonal_naive", "moving_average"}
    assert len(results) == 25
    assert (pd.to_datetime(results.train_end) < pd.to_datetime(results.validation_start)).all()
    config["validation"]["walk_forward_folds"] = 4
    with pytest.raises(ValueError, match="five"):
        tune_lightgbm(dataset.frame, dataset.feature_columns, config)


def test_cli_train_dispatch_implemented(monkeypatch, config):
    from src import cli

    calls = []
    monkeypatch.setattr("src.models.train.run_training", lambda cfg: calls.append(cfg))
    assert cli.main(["train"]) == 0
    assert len(calls) == 1
