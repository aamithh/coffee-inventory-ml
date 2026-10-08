"""Real Streamlit screen/form tests plus pure chart and backend contract checks."""

from copy import deepcopy
import pandas as pd
import pytest
import yaml
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from src.api.main import create_app
from src.dashboard.backend import DashboardBackend
from src.dashboard.views import stock_table, forecast_chart
from src.utils.config import PROJECT_ROOT, load_config, resolve_path

SCREENS = (
    "Overview",
    "Demand Forecast",
    "Raw Materials",
    "Order Recommendations",
    "Insights",
    "Model Performance",
    "What-If",
)


@pytest.fixture
def settings(tmp_path, monkeypatch):
    config = deepcopy(load_config())
    config["paths"]["api_inventory_state"] = str(tmp_path / "inventory.json")
    config["paths"]["pipeline_staging"] = str(tmp_path / "staging")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv(config["dashboard"]["config_environment_variable"], str(path))
    return config


def app(settings, screen="Overview"):
    result = AppTest.from_file(
        str(PROJECT_ROOT / "src/dashboard/app.py"),
        default_timeout=settings["dashboard"]["app_test_timeout_seconds"],
    ).run()
    if screen != "Overview":
        result.radio[0].set_value(screen).run()
    return result


@pytest.mark.parametrize("screen", SCREENS)
def test_all_screens_render(settings, screen):
    result = app(settings, screen)
    assert not result.exception
    assert not result.error
    assert result.header[0].value == screen
    assert any("2025-07-20" in c.value for c in result.caption)
    assert not resolve_path(settings, "api_inventory_state").exists()


def test_overview_currency_and_metrics(settings):
    result = app(settings)
    assert len(result.metric) == 3
    assert result.metric[2].value.startswith("\u20b9")
    assert all("\u00c2" not in c.value for c in result.caption)
    assert any("illustrative" in text.value.lower() for text in result.info)


def test_forecast_horizon_and_item_selection(settings):
    result = app(settings, "Demand Forecast")
    result.slider(key="forecast_days").set_value(3).run()
    result.selectbox(key="demand_item").set_value("latte").run()
    assert not result.exception
    assert len(result.dataframe[0].value) == 3
    assert len(result.get("plotly_chart")) == 1


def test_material_update_refreshes_revision(settings):
    result = app(settings, "Raw Materials")
    result.selectbox(key="stock_material").set_value("milk").run()
    result.number_input(key="stock_on_hand").set_value(1000)
    next(b for b in result.button if b.label == "Save measured stock").click().run()
    assert not result.exception and not result.error
    saved = DashboardBackend(settings).inventory()
    milk = next(row for row in saved["rows"] if row["material"] == "milk")
    assert milk["on_hand"] == 1000 and saved["version"] == 1
    assert result.success
    assert any("revision 1" in c.value.lower() for c in result.caption)


def test_stale_form_version_detected(settings):
    result = app(settings, "Raw Materials")
    outside = DashboardBackend(settings)
    outside.update({"expected_version": 0, "rows": [{"material": "sugar", "on_hand": 123}]})
    result.number_input(key="stock_on_hand").set_value(50)
    next(b for b in result.button if b.label == "Save measured stock").click().run()
    assert not result.exception
    assert "Stock changed" in result.error[0].value
    assert outside.inventory()["version"] == 1
    result.button(key="reload_stock").click().run()
    assert not result.exception and not result.error


def test_scenario_submission_does_not_write_inventory(settings):
    result = app(settings, "What-If")
    result.selectbox(key="scenario_item").set_value("latte")
    result.selectbox(key="scenario_promo").set_value("Enable promotion")
    next(b for b in result.button if b.label == "Compare scenario").click().run()
    assert not result.exception and not result.error
    assert result.metric[0].label == "Expected menu-unit change"
    assert len(result.dataframe[0].value) == 10
    assert not resolve_path(settings, "api_inventory_state").exists()


def test_invalid_scenario_shows_error(settings):
    result = app(settings, "What-If")
    result.slider(key="scenario_max").set_value(10)
    result.slider(key="scenario_min").set_value(25)
    next(b for b in result.button if b.label == "Compare scenario").click().run()
    assert not result.exception
    assert result.error


def test_order_export_exists(settings):
    result = app(settings, "Order Recommendations")
    assert len(result.get("download_button")) == 1
    assert len(result.dataframe[0].value) == 10


def test_overview_shortcut_opens_shopping_list(settings):
    result = app(settings)
    next(b for b in result.button if "Open shopping list" in b.label).click().run()
    assert not result.exception and not result.error
    assert result.header[0].value == "Order Recommendations"
    assert len(result.get("download_button")) == 1


def test_stock_selection_loads_selected_material_values(settings):
    result = app(settings, "Raw Materials")
    result.selectbox(key="stock_material").set_value("milk").run()
    expected = next(
        r for r in DashboardBackend(settings).inventory()["rows"] if r["material"] == "milk"
    )
    assert result.number_input(key="stock_on_hand").value == expected["on_hand"]
    assert result.number_input(key="stock_on_order").value == expected["on_order"]
    assert not resolve_path(settings, "api_inventory_state").exists()


def test_missing_model_shows_view_error(settings, monkeypatch, tmp_path):
    settings["paths"]["model_bundle"] = str(tmp_path / "missing.joblib")
    path = tmp_path / "missing.yaml"
    path.write_text(yaml.safe_dump(settings), encoding="utf-8")
    monkeypatch.setenv(settings["dashboard"]["config_environment_variable"], str(path))
    result = app(settings)
    assert not result.exception
    assert result.error and "Unable to load" in result.error[0].value


def test_chart_excludes_invalid_history(settings):
    forecast = pd.DataFrame(
        dict(
            date=pd.date_range("2025-07-20", periods=2),
            item="latte",
            forecast=[10, 12],
            p10=[5, 6],
            p90=[15, 18],
        )
    )
    history = pd.DataFrame(
        dict(
            date=pd.date_range("2025-07-17", periods=3),
            item="latte",
            sales=[4, 999, 6],
            record_status=["clean", "outlier", "clean"],
        )
    )
    chart = forecast_chart(forecast, history, "latte", settings["dashboard"]["colors"])
    assert list(chart.data[0].y) == [4, 6]
    assert len(chart.data) == 4 and chart.data[2].fill == "tonexty"


def test_stock_cover_native_units_and_zero_need():
    inventory = {"rows": [{"material": "m", "on_hand": 20, "on_order": 0, "arrival_date": None}]}
    needs = pd.DataFrame(dict(material=["m", "m"], need=[5, 5]))
    orders = pd.DataFrame(
        [
            dict(
                material="m",
                unit="g",
                order_now=True,
                pre_arrival_shortfall=0,
                unmet_order_quantity=0,
            )
        ]
    )
    result = stock_table(inventory, needs, orders)
    assert result.days_of_cover.iloc[0] == 4
    assert result.unit.iloc[0] == "g"
    needs["need"] = 0
    assert pd.isna(stock_table(inventory, needs, orders).days_of_cover.iloc[0])


def test_http_backend_reuses_api_contract(settings):
    settings["dashboard"]["backend"] = "http"
    backend = DashboardBackend(settings)
    backend.http.close()
    backend.http = TestClient(create_app(settings))
    forecast = backend.forecast(1)
    assert len(forecast) == 10
    assert len(backend.orders()) == 10
    assert backend.inventory()["version"] == 0
    changed = backend.update(
        {"expected_version": 0, "rows": [{"material": "milk", "on_hand": 100}]}
    )
    assert changed["version"] == 1


def test_dashboard_cli_dispatch(settings, monkeypatch):
    from src import cli

    calls = []
    monkeypatch.setattr(cli, "load_config", lambda _: settings)
    monkeypatch.setattr(cli, "validate_forecast_calendar", lambda _: None)

    class Result:
        returncode = 0

    def fake(command, **kwargs):
        calls.append(command)
        return Result()

    monkeypatch.setattr(cli.subprocess, "run", fake)
    assert cli.main(["dashboard"]) == 0
    assert calls[0][:3] == [cli.sys.executable, "-m", "streamlit"]
    assert "--server.headless" in calls[0]
