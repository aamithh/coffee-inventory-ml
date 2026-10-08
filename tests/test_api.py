"""Endpoint behavior, scenario isolation and atomic versioned stock updates."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from src.api.main import create_app
from src.data.calendar_features import build_calendar
from src.utils.config import load_config, resolve_path


@pytest.fixture
def settings(tmp_path):
    config = deepcopy(load_config())
    config["paths"]["api_inventory_state"] = str(tmp_path / "inventory.json")
    config["paths"]["pipeline_staging"] = str(tmp_path / "staging")
    return config


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


def payload(version=0, quantity=100):
    return {
        "expected_version": version,
        "rows": [{"material": "milk", "on_hand": quantity, "on_order": 0, "arrival_date": None}],
    }


def test_docs_schema_and_health(client):
    assert client.get("/health").json()["status"] == "ready"
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    for path in (
        "/forecast/items",
        "/forecast/materials",
        "/recommendations/orders",
        "/inventory",
        "/whatif",
        "/model/metrics",
        "/health",
    ):
        assert path in schema["paths"]
    assert schema["paths"]["/inventory"]["post"]["requestBody"]


@pytest.mark.parametrize("days", ["0", "-1", "31", "1.5", "nonsense"])
def test_invalid_forecast_horizon(client, days):
    assert client.get(f"/forecast/items?days={days}").status_code == 422


def test_real_item_and_material_forecasts(client, settings):
    items = client.get("/forecast/items?days=1")
    assert items.status_code == 200
    rows = items.json()["forecasts"]
    assert len(rows) == 10
    assert all(0 <= r["p10"] <= r["p50"] <= r["p90"] for r in rows)
    materials = client.get("/forecast/materials?days=1")
    assert materials.status_code == 200
    by_material = {r["material"]: r for r in materials.json()["requirements"]}
    counts = {r["item"]: r["forecast"] for r in rows}
    expected = sum(
        counts[item] * recipe.get("milk", 0) for item, recipe in settings["recipes"].items()
    ) * (1 + settings["materials"]["milk"]["wastage_factor"])
    assert by_material["milk"]["need"] == pytest.approx(expected)


def test_orders_use_inventory_revision(client):
    initial = client.get("/inventory").json()
    assert initial["illustrative"] and initial["version"] == 0
    changed = client.post("/inventory", json=payload(quantity=1e8))
    assert changed.status_code == 200
    response = client.get("/recommendations/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["inventory_version"] == 1 and not data["illustrative_inventory"]
    milk = next(r for r in data["recommendations"] if r["material"] == "milk")
    assert milk["order_qty"] == 0


def test_patch_persists_restart_and_other_rows(client, settings):
    initial = client.get("/inventory").json()
    changed = client.post("/inventory", json=payload())
    assert changed.status_code == 200
    saved = changed.json()
    assert len(saved["rows"]) == 10 and saved["version"] == 1
    before = {r["material"]: r for r in initial["rows"]}
    after = {r["material"]: r for r in saved["rows"]}
    assert after["milk"]["on_hand"] == 100
    assert after["sugar"] == before["sugar"]
    assert TestClient(create_app(settings)).get("/inventory").json() == saved


def test_stale_revision_conflict(client):
    assert client.post("/inventory", json=payload()).status_code == 200
    response = client.post("/inventory", json=payload(quantity=200))
    assert response.status_code == 409
    assert "version 1" in response.json()["detail"]


def test_concurrent_updates_one_revision(client):
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda value: client.post("/inventory", json=payload(quantity=value)).status_code,
                [10, 20],
            )
        )
    assert sorted(responses) == [200, 409]


@pytest.mark.parametrize(
    "change",
    [
        {"on_hand": -1},
        {"on_hand": True},
        {"material": "unknown"},
        {"on_order": 1},
        {"on_order": 1, "arrival_date": "2020-01-01"},
        {"on_order": 0, "arrival_date": "2025-07-21"},
        {"unexpected": 5},
    ],
)
def test_invalid_inventory_row(client, change):
    body = payload()
    body["rows"][0].update(change)
    assert client.post("/inventory", json=body).status_code == 422
    assert client.get("/inventory").json()["version"] == 0


def test_duplicate_inventory_rows(client):
    body = payload()
    body["rows"] *= 2
    assert client.post("/inventory", json=body).status_code == 422


def test_nonfinite_inventory(client):
    body = json.dumps(payload()).replace('"on_hand": 100', '"on_hand": NaN')
    assert (
        client.post(
            "/inventory", content=body, headers={"Content-Type": "application/json"}
        ).status_code
        == 422
    )


def test_failed_publication_preserves_previous_revision(client, settings, monkeypatch):
    assert client.post("/inventory", json=payload()).status_code == 200
    path = resolve_path(settings, "api_inventory_state")
    before = path.read_bytes()

    def fail(_):
        raise OSError("mock write failure")

    monkeypatch.setattr("src.api.service.publish_artifacts", fail)
    assert client.post("/inventory", json=payload(1, 200)).status_code == 503
    assert path.read_bytes() == before
    assert client.get("/inventory").json()["version"] == 1


@pytest.mark.parametrize(
    "body",
    [
        {"days": 31},
        {"days": 0},
        {"days": True},
        {"days": 1, "rainfall": -1},
        {"days": 1, "temp_max": 10, "temp_min": 20},
        {"days": 1, "promotions": {"unknown": True}},
        {"days": 1, "promotions": {"latte": "yes"}},
        {"days": 1, "festivals": {"2025-07-25": True}},
        {"days": 1, "unknown": 1},
    ],
)
def test_invalid_scenario(client, body):
    assert client.post("/whatif", json=body).status_code == 422


def test_scenario_isolation_and_actual_model_change(client, settings):
    before = client.get("/forecast/items?days=1").json()
    inventory = client.get("/inventory").json()
    model_before = hashlib.sha256(resolve_path(settings, "model_bundle").read_bytes()).hexdigest()
    response = client.post(
        "/whatif",
        json={
            "days": 1,
            "temp_max": 36,
            "temp_min": 25,
            "rainfall": 0,
            "promotions": {"latte": True},
            "festivals": {"2025-07-20": True},
        },
    )
    assert response.status_code == 200
    scenario = response.json()
    assert scenario["baseline"] == before
    assert scenario["scenario"]["scenario"]
    assert len(scenario["material_requirements"]["requirements"]) == 10
    assert abs(scenario["point_total_change"]) > 1e-6
    assert client.get("/forecast/items?days=1").json() == before
    assert client.get("/inventory").json() == inventory
    assert (
        hashlib.sha256(resolve_path(settings, "model_bundle").read_bytes()).hexdigest()
        == model_before
    )


def test_festival_override_add_remove_isolated(settings):
    dates = pd.date_range("2025-07-20", periods=2)
    original = build_calendar(dates, settings)
    changed = deepcopy(settings)
    changed["calendar"]["scenario_festivals"] = {"2025-07-20": "scenario"}
    assert build_calendar(dates, changed).festival_flag.iloc[0] == 1
    pd.testing.assert_frame_equal(build_calendar(dates, settings), original)
    changed["calendar"]["scenario_festivals"] = {"2025-07-20": ""}
    assert build_calendar(dates, changed).festival_flag.iloc[0] == 0


def test_metrics(client):
    response = client.get("/model/metrics")
    assert response.status_code == 200
    assert response.json()["metrics"]["selected_point_model"] == "lightgbm"
    assert response.json()["simulation"]["test_days"] == 165


def test_missing_model_is_clear_503(settings):
    settings["paths"]["model_bundle"] = "models/nonexistent_api_test.joblib"
    client = TestClient(create_app(settings))
    assert client.get("/health").json()["status"] == "degraded"
    response = client.get("/forecast/items?days=1")
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]


def test_api_cli_dispatch(settings, monkeypatch):
    from src import cli

    calls = []
    monkeypatch.setattr(cli, "load_config", lambda _: settings)
    monkeypatch.setattr(cli, "validate_forecast_calendar", lambda _: None)
    monkeypatch.setattr("uvicorn.run", lambda app, **kwargs: calls.append(kwargs))
    assert cli.main(["api"]) == 0
    assert calls[0]["host"] == "127.0.0.1" and calls[0]["port"] == 8000
