"""Phase 1.5 regression tests for every hardening item; weather is mocked."""

from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from contextlib import closing
from typing import Any
import numpy as np
import pandas as pd
import pytest
import requests
from src import cli
from src.data.artifacts import publish_artifacts
from src.data.calendar_features import daily_dates
from src.data.generator import generate_dataset, run_pipeline, promotion_schedule
from src.data.loader import load_sales, save_dataset
from src.data.quality import (
    apply_record_status,
    assert_no_truth_references,
    reconcile_sales,
    residual_correlation,
)
from src.data.truth_loader import load_truth
from src.data.weather import synthetic_weather
from src.utils.config import load_config, resolve_path
from src.utils.dates import (
    get_as_of_date,
    get_split_boundaries,
    get_drift_start_date,
    validate_forecast_calendar,
    date_context,
)


@pytest.fixture
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    result = deepcopy(load_config())
    monkeypatch.delenv(result["sqlite"]["directory_env_variable"], raising=False)
    result["data"]["weather_provider"] = "synthetic"
    result["weather"]["cache_enabled"] = False
    for key, value in result["paths"].items():
        result["paths"][key] = str(tmp_path / value)
    return result


@pytest.fixture(scope="module")
def shocked() -> tuple:
    config = deepcopy(load_config())
    config["data"]["weather_provider"] = "synthetic"
    config["weather"]["cache_enabled"] = False
    return generate_dataset(config)


def test_shared_mean_one_shock_and_residual_correlation(shocked: tuple, config: dict) -> None:
    truth = shocked[1]
    assert truth.groupby("date")["shop_daily_multiplier"].nunique().eq(1).all()
    assert truth["shop_daily_multiplier"].gt(0).all()
    assert abs(truth.drop_duplicates("date")["shop_daily_multiplier"].mean() - 1) < 0.01
    config["generator"]["shop_daily_shock"]["sigma"] = 0
    no_shock = generate_dataset(config)[1]
    assert no_shock["shop_daily_multiplier"].eq(1).all()
    before, after = residual_correlation(no_shock), residual_correlation(truth)
    assert before is not None and after is not None
    assert after - before > 0.03


def test_per_item_promotions_and_non_promoted_cannibalization(shocked: tuple, config: dict) -> None:
    sales, truth, calendar, weather = shocked
    assert sales.groupby("item")["promo_flag"].sum().ge(40).all()
    promotions, any_promo = promotion_schedule(daily_dates(config), config)
    assert sales.groupby("date")["promo_flag"].sum().max() > 1
    from src.data.generator import expected_demand

    daily = calendar.merge(weather, on="date")
    item = next(iter(config["menu"]))
    affected = any_promo & ~promotions[item]
    assert affected.any()
    none = np.zeros(len(daily), dtype=bool)
    base = expected_demand(item, daily, none, none, config)
    actual = expected_demand(item, daily, promotions[item], any_promo, config)
    np.testing.assert_allclose(
        actual[affected] / base[affected], config["data"]["cannibalization_factor"]
    )


@pytest.mark.parametrize("mode", ["per_item", "shop_day"])
def test_item_data_survives_menu_reordering_and_additions(mode: str, config: dict) -> None:
    config["generator"]["promotions"]["mode"] = mode
    original = generate_dataset(config)
    reordered = deepcopy(config)
    reordered["menu"] = dict(reversed(list(config["menu"].items())))
    for old, new in zip(original[:2], generate_dataset(reordered)[:2], strict=True):
        pd.testing.assert_frame_equal(old, new)
    extended = deepcopy(config)
    extended["menu"]["new_latte"] = deepcopy(config["menu"]["latte"])
    extended["recipes"]["new_latte"] = deepcopy(config["recipes"]["latte"])
    added = generate_dataset(extended)
    for old, new in zip(original[:2], added[:2], strict=True):
        pd.testing.assert_frame_equal(
            old, new.loc[new["item"].isin(config["menu"])].reset_index(drop=True)
        )


def test_fallback_cache_retries_api_and_refreshes(
    config: dict, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    config["data"]["weather_provider"] = "auto"
    config["weather"]["cache_enabled"] = True

    def offline(*args: Any, **kwargs: Any) -> None:
        raise requests.Timeout("mock offline")

    monkeypatch.setattr(requests, "get", offline)
    first = run_pipeline(config)
    metadata = resolve_path(config, "weather_metadata")
    assert first["weather_source"] == ["synthetic_fallback"]
    assert json.loads(metadata.read_text())["source"] == "synthetic_fallback"
    frame = synthetic_weather(daily_dates(config), config)

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "daily": {
                    "time": frame["date"].dt.strftime("%Y-%m-%d").tolist(),
                    "temperature_2m_max": (frame["temp_max"] + 1).tolist(),
                    "temperature_2m_min": frame["temp_min"].tolist(),
                    "precipitation_sum": frame["rainfall"].tolist(),
                }
            }

    calls = []

    def recovered(*args: Any, **kwargs: Any) -> Response:
        calls.append(1)
        return Response()

    monkeypatch.setattr(requests, "get", recovered)
    second = run_pipeline(config)
    assert calls == [1]
    assert second["weather_source"] == ["open_meteo"]
    assert json.loads(metadata.read_text())["source"] == "open_meteo"
    assert (
        pd.read_csv(resolve_path(config, "weather_cache"))["weather_source"].eq("open_meteo").all()
    )

    def unexpected(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("real cache should be reused")

    monkeypatch.setattr(requests, "get", unexpected)
    run_pipeline(config)
    output = capsys.readouterr().out
    assert "Weather source (start): synthetic_fallback" in output
    assert "Weather source (end): open_meteo; pipeline succeeded" in output
    assert "Weather source: open_meteo" in resolve_path(config, "data_report").read_text()


def test_split_as_of_horizon_and_drift_defaults(config: dict) -> None:
    dates = daily_dates(config)
    bounds = get_split_boundaries(config)
    assert bounds["train_end"] < bounds["val_start"] <= bounds["val_end"] < bounds["test_start"]
    assert get_as_of_date(config) == bounds["test_start"]
    assert bounds["train_end"] == dates[int(len(dates) * 0.70) - 1]
    assert get_drift_start_date(config) == bounds["val_start"]
    context = date_context(config)
    assert context["drift_start_split"] == "val"
    assert context["drift_appears_in_test"]
    assert sum(context["drift_ramp_overlap_days"].values()) == config["data"]["drift_duration_days"]
    validate_forecast_calendar(config)
    config["project"]["as_of_date"] = "2026-12-29"
    with pytest.raises(ValueError, match="Forecast calendar.*2027"):
        validate_forecast_calendar(config)
    config["project"]["as_of_date"] = "2025-12-01"
    assert str(get_as_of_date(config).date()) == "2025-12-01"
    config["generator"]["drift"]["start_date"] = "2025-08-01"
    assert date_context(config)["drift_start_split"] == "test"


@pytest.mark.parametrize("horizon", [0, -1, True, 1.5])
def test_invalid_horizon_rejected(horizon: Any, config: dict) -> None:
    config["project"]["forecast_horizon_days"] = horizon
    with pytest.raises(ValueError, match="positive integer"):
        validate_forecast_calendar(config)


def test_flag_precedence_and_optional_stockout_eligibility(config: dict) -> None:
    frame = pd.DataFrame(
        {
            "closure_flag": [1, 0, 0, 0, 0],
            "missing_flag": [1, 1, 0, 0, 0],
            "stockout_flag": [1, 1, 1, 0, 0],
            "outlier_flag": [1, 1, 1, 1, 0],
        }
    )
    status = apply_record_status(frame, config)
    assert status["record_status"].tolist() == ["closed", "missing", "stockout", "outlier", "clean"]
    assert status["usable_for_training"].tolist() == [False, False, False, False, True]
    assert status["record_status"].value_counts().sum() == len(frame)
    config["generator"]["record_status"]["allow_stockout_for_training"] = True
    assert apply_record_status(frame, config)["usable_for_training"].tolist() == [
        False,
        False,
        True,
        False,
        True,
    ]


def test_exclusive_reconciliation_and_status_counts(shocked: tuple) -> None:
    sales, truth = shocked[:2]
    audit = reconcile_sales(sales, truth)
    assert audit["gap"] == audit["stockout_loss"] + audit["missing_loss"] - audit["outlier_excess"]
    assert audit["unexplained_gap"] == 0
    assert sales["record_status"].value_counts().sum() == len(sales)
    assert sales.loc[sales["usable_for_training"], "record_status"].eq("clean").all()


@pytest.mark.parametrize(
    "reference",
    [
        "from src.data.truth_loader import load_truth",
        "table = 'simulation_truth'",
        "path = 'data/processed/simulation_truth.db'",
        "key = 'truth_database'",
    ],
)
def test_configured_truth_source_guard(reference: str, config: dict, tmp_path: Path) -> None:
    protected = tmp_path / "future_training_folder"
    protected.mkdir()
    config["leakage_guard"]["protected_folders"] = [str(protected)]
    source = protected / "model.py"
    source.write_text("value = 1\n")
    assert_no_truth_references(config)
    source.write_text(reference)
    with pytest.raises(ValueError, match="leakage reference"):
        assert_no_truth_references(config)


def test_actual_feature_and_model_folders_are_guarded(config: dict) -> None:
    assert_no_truth_references(config)


def test_separate_truth_migration_and_observed_loader_independence(
    shocked: tuple, config: dict
) -> None:
    database = resolve_path(config, "database")
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("CREATE TABLE simulation_truth (legacy INTEGER)")
        connection.execute("CREATE TABLE unrelated (value INTEGER)")
        connection.execute("INSERT INTO unrelated VALUES (42)")
        connection.commit()
    save_dataset(*shocked, config)
    pd.testing.assert_frame_equal(load_truth(config), shocked[1])
    with closing(sqlite3.connect(database)) as connection:
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='simulation_truth'"
            ).fetchone()
            is None
        )
        assert connection.execute("SELECT value FROM unrelated").fetchone() == (42,)
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    resolve_path(config, "truth_database").unlink()
    pd.testing.assert_frame_equal(load_sales(config), shocked[0])


def test_attached_transaction_rolls_back_both_databases(
    shocked: tuple, config: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_dataset(*shocked, config)
    sales_before, truth_before = load_sales(config), load_truth(config)
    method = pd.DataFrame.to_sql

    def fail(frame: pd.DataFrame, name: str, *args: Any, **kwargs: Any) -> Any:
        value = method(frame, name, *args, **kwargs)
        if name == "simulation_truth":
            raise RuntimeError("after oracle replacement")
        return value

    monkeypatch.setattr(pd.DataFrame, "to_sql", fail)
    with pytest.raises(RuntimeError, match="oracle replacement"):
        save_dataset(*shocked, config)
    pd.testing.assert_frame_equal(load_sales(config), sales_before)
    pd.testing.assert_frame_equal(load_truth(config), truth_before)


def test_database_environment_override(
    config: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "non_synced"
    monkeypatch.setenv("COFFEE_DB_DIR", str(directory))
    assert resolve_path(config, "database") == directory / Path(config["paths"]["database"]).name
    assert (
        resolve_path(config, "truth_database")
        == directory / Path(config["paths"]["truth_database"]).name
    )
    run_pipeline(config)
    assert resolve_path(config, "database").exists()
    assert resolve_path(config, "truth_database").exists()
    assert len(load_sales(config)) == len(daily_dates(config)) * len(config["menu"])


def test_wal_rejected_for_multi_database_commit(shocked: tuple, config: dict) -> None:
    config["sqlite"]["journal_mode"] = "WAL"
    with pytest.raises(ValueError, match="DELETE journaling"):
        save_dataset(*shocked, config)


def test_onedrive_warning_and_output_preservation(
    config: dict, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(
        "src.data.generator.PROJECT_ROOT",
        Path(config["paths"]["processed"]) / "OneDrive" / "project",
    )
    run_pipeline(config)
    assert "OneDrive warning:" in capsys.readouterr().out
    targets = [
        resolve_path(config, key)
        for key in (
            "database",
            "truth_database",
            "sales_csv",
            "truth_csv",
            "weather_cache",
            "data_summary",
        )
    ]
    before = {str(path): path.read_bytes() for path in targets}

    def fail(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("staged validation failed")

    monkeypatch.setattr("src.data.generator.write_quality_report", fail)
    with pytest.raises(RuntimeError, match="staged validation"):
        run_pipeline(config)
    assert before == {str(path): path.read_bytes() for path in targets}


def test_publication_failure_restores_preexisting_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    sources = [tmp_path / "new-a", tmp_path / "new-b"]
    targets = [tmp_path / "old-a", tmp_path / "old-b"]
    for index, (source, target) in enumerate(zip(sources, targets, strict=True)):
        source.write_text(f"new {index}")
        target.write_text(f"old {index}")
    original = os.replace
    failed = False

    def replace(source: Any, target: Any) -> None:
        nonlocal failed
        if Path(target) == targets[1] and not failed:
            failed = True
            raise OSError("injected publish failure")
        original(source, target)

    monkeypatch.setattr("src.data.artifacts.os.replace", replace)
    with pytest.raises(OSError, match="publish failure"):
        publish_artifacts(list(zip(sources, targets, strict=True)))
    assert [path.read_text() for path in targets] == ["old 0", "old 1"]


def test_cli_test_dispatch_uses_current_interpreter(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    calls = []

    class Result:
        returncode = 0

    def run(args: list, **kwargs: Any) -> Result:
        calls.append(args)
        return Result()

    monkeypatch.setattr("src.cli.subprocess.run", run)
    assert cli.main(["test"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "-q"]]
