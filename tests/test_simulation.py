"""Hand-computed FIFO, pipeline, shared-recipe and cost-accounting examples."""

import numpy as np
import pandas as pd
import pytest
from src.inventory.lots import Stock
from src.inventory.policies import order_quantity
from src.inventory.simulator import replay, policy_summary, POLICIES


@pytest.fixture
def config():
    return dict(
        menu={"a": {}},
        recipes={"a": {"m": 1}},
        materials={
            "m": dict(
                unit="pcs",
                unit_cost=2,
                wastage_factor=0,
                min_order_qty=1,
                lead_time_days=1,
                shelf_life_days=3,
            )
        },
        inventory=dict(
            service_level=0.95,
            buffer_days=0,
            target_coverage_days=2,
            mean_window_days=2,
            rounding_tolerance=1e-9,
            holding_cost_daily_fraction=0.1,
            lost_sale_penalty_fraction=1,
        ),
    )


def bank(days=5, need=10):
    return pd.DataFrame(
        [
            dict(
                policy=p,
                origin=pd.Timestamp("2025-01-01"),
                date=d,
                material="m",
                need=need,
                sigma_daily=0,
            )
            for p in POLICIES
            for d in pd.date_range("2025-01-01", periods=days)
        ]
    )


def demand(days=2, requests=10):
    return pd.DataFrame(
        dict(date=pd.date_range("2025-01-01", periods=days), item="a", demand=requests, price=5)
    )


def test_fifo_consumption_and_expiry():
    day = pd.Timestamp("2025-01-01")
    stock = Stock()
    stock.receive(5, day, 2)
    stock.receive(7, day + pd.Timedelta(days=1), 2)
    assert stock.consume(6) == 6
    assert stock.quantity == 6
    assert stock.lots[0].received == day + pd.Timedelta(days=1)
    assert stock.expire(day + pd.Timedelta(days=2)) == 0
    assert stock.expire(day + pd.Timedelta(days=3)) == 6
    assert stock.quantity == 0


def test_expiry_at_start():
    stock = Stock()
    day = pd.Timestamp("2025-01-01")
    stock.receive(4, day, 1)
    assert stock.expire(day) == 0
    assert stock.expire(day + pd.Timedelta(days=1)) == 4


def test_copy_is_independent():
    stock = Stock()
    stock.receive(5, pd.Timestamp("2025-01-01"), 3)
    other = stock.copy()
    other.consume(4)
    assert stock.quantity == 5
    assert other.quantity == 1


@pytest.mark.parametrize("value", [-1, np.nan, np.inf])
def test_invalid_lot(value):
    stock = Stock()
    with pytest.raises(ValueError):
        stock.receive(value, pd.Timestamp("2025-01-01"), 2)
    with pytest.raises(ValueError):
        stock.consume(value)


def test_partial_material_consumption():
    stock = Stock()
    stock.receive(3, pd.Timestamp("2025-01-01"), 2)
    assert stock.consume(5) == 3
    assert stock.quantity == 0


def test_delivery_and_mass_balance(config):
    daily, items, orders = replay(demand(), bank(), {"m": 10}, config)
    assert items.lost.sum() == 0
    first = daily.loc[daily.policy.eq("ml")].iloc[0]
    second = daily.loc[daily.policy.eq("ml")].iloc[1]
    assert first.received == 0
    assert first.consumed == 10
    assert second.received == 20
    assert second.closing == 10
    assert orders.loc[orders.policy.eq("ml")].quantity.iloc[0] == 20
    np.testing.assert_allclose(
        daily.opening + daily.received, daily.consumed + daily.waste + daily.closing
    )


def test_expiry_and_unserved_demand(config):
    config["materials"]["m"].update(shelf_life_days=1, lead_time_days=0)
    config["inventory"].update(target_coverage_days=1)
    daily, items, _ = replay(demand(days=3, requests=0), bank(need=0), {"m": 7}, config)
    assert daily.loc[daily.policy.eq("ml")].waste.sum() == 7
    assert items.lost.sum() == 0


def test_no_stock_no_forecast_lost_sales(config):
    _, items, _ = replay(demand(requests=3), bank(need=0), {"m": 0}, config)
    assert items.served.sum() == 0
    assert items.lost.sum() == 18


def test_whole_recipes_and_alphabetical_priority(config):
    config["menu"]["b"] = {}
    config["recipes"]["a"]["m"] = 2
    config["recipes"]["b"] = {"m": 2}
    actual = pd.DataFrame(
        dict(date=["2025-01-01"] * 2, item=["b", "a"], demand=[1, 1], price=[5, 5])
    )
    daily, items, _ = replay(actual, bank(need=0), {"m": 3}, config)
    one = items.loc[items.policy.eq("ml")].set_index("item")
    assert one.loc["a", "served"] == 1
    assert one.loc["b", "served"] == 0
    assert daily.loc[daily.policy.eq("ml"), "consumed"].iloc[0] == 2


def test_zero_lead_receives_before_sales(config):
    config["materials"]["m"]["lead_time_days"] = 0
    _, items, orders = replay(demand(days=1), bank(), {"m": 0}, config)
    assert items.lost.sum() == 0
    assert (orders.arrival == orders.date).all()


def test_multiple_pending_receipts(config):
    day = pd.Timestamp("2025-01-01")
    needs = bank().loc[lambda f: f.policy.eq("ml")].set_index("date")
    pending = [(day + pd.Timedelta(days=1), 5), (day + pd.Timedelta(days=2), 5)]
    qty = order_quantity(day, Stock(), pending, needs, config["materials"]["m"], config)
    assert qty == 10


def test_expiring_stock_not_counted_at_arrival(config):
    day = pd.Timestamp("2025-01-01")
    stock = Stock()
    stock.receive(100, day, 1)
    needs = bank().loc[lambda f: f.policy.eq("ml")].set_index("date")
    assert order_quantity(day, stock, [], needs, config["materials"]["m"], config) == 20


def test_manual_pack_can_exceed_expected_expiry_capacity(config):
    config["materials"]["m"].update(min_order_qty=5, shelf_life_days=1, lead_time_days=0)
    config["inventory"]["target_coverage_days"] = 1
    needs = bank(need=4).loc[lambda f: f.policy.eq("ml")].set_index("date")
    day = pd.Timestamp("2025-01-01")
    assert order_quantity(day, Stock(), [], needs, config["materials"]["m"], config) == 0
    assert order_quantity(day, Stock(), [], needs, config["materials"]["m"], config, True) == 5


def test_cost_does_not_double_count_waste(config):
    config["materials"]["m"].update(shelf_life_days=1, lead_time_days=0)
    config["inventory"]["target_coverage_days"] = 1
    daily, items, _ = replay(demand(days=2, requests=0), bank(need=0), {"m": 7}, config)
    row = policy_summary(daily, items, config).set_index("policy").loc["ml"]
    assert row.initial_stock_value == 14
    assert row.waste_cost == 14
    assert row.holding_cost == pytest.approx(1.4)
    assert row.total_cost == pytest.approx(15.4)
    assert row.service_level == 1


@pytest.mark.parametrize("column,value", [("demand", -1), ("demand", 0.5), ("price", np.inf)])
def test_invalid_demand(config, column, value):
    frame = demand()
    frame[column] = frame[column].astype(float)
    frame.loc[0, column] = value
    with pytest.raises(ValueError):
        replay(frame, bank(), {"m": 0}, config)


def test_future_forecast_origin_rejected(config):
    forecasts = bank()
    forecasts["origin"] = pd.Timestamp("2025-01-02")
    with pytest.raises(ValueError):
        replay(demand(), forecasts, {"m": 0}, config)


def test_missing_planning_horizon(config):
    with pytest.raises(ValueError, match="horizon"):
        replay(demand(), bank(days=2), {"m": 0}, config)


def test_forecast_bank_not_changed_by_demand(config):
    forecasts = bank()
    before = forecasts.copy(deep=True)
    replay(demand(requests=1), forecasts, {"m": 0}, config)
    replay(demand(requests=100), forecasts, {"m": 0}, config)
    pd.testing.assert_frame_equal(forecasts, before)


def test_forecast_builder_uses_only_prior_observations(config, monkeypatch):
    from src.inventory import simulation_report as module

    start = pd.Timestamp("2025-01-15")
    config["menu"]["a"] = {"category": "drink", "price": 5}
    config["inventory"].update(initial_coverage_days=1, manual_buffer_fraction=0.2)
    config["simulation_settings"] = {
        "forecast_refresh_days": 7,
        "manual_window_days": 7,
        "residual_window_days": 7,
    }
    observed = pd.DataFrame(
        [
            dict(
                date=day,
                item="a",
                category="drink",
                price=5,
                promo_flag=0,
                sales=3,
                record_status="clean",
            )
            for day in pd.date_range("2025-01-01", "2025-01-17")
        ]
    )
    calls = []

    def fake_forecast(artifact, history, plans, origin, settings, model_name=None):
        assert history.date.max() < origin
        assert set(plans) == {"date", "item", "category", "price", "promo_flag"}
        calls.append(model_name)
        result = plans[["date", "item"]].copy()
        result["forecast"] = history.sales.mean()
        result["p10"] = 1
        result["p50"] = 3
        result["p90"] = 5
        return result

    monkeypatch.setattr(
        module, "get_split_boundaries", lambda _: {"test_start": start, "test_end": start}
    )
    monkeypatch.setattr(module, "load_artifact", lambda _: {})
    monkeypatch.setattr(module, "recursive_forecast", fake_forecast)
    monkeypatch.setattr(
        module, "load_truth", lambda _: pytest.fail("Forecast builder accessed evaluation demand")
    )
    before, initial = module.build_bank(config, observed)
    changed = observed.copy()
    changed.loc[changed.date.ge(start), "sales"] = 99999
    after, again = module.build_bank(config, changed)
    pd.testing.assert_frame_equal(before, after)
    assert initial == again
    assert len(calls) == 4


def test_simulate_cli_dispatch(config, monkeypatch):
    from src import cli
    from src.inventory import simulation_report

    calls = []
    monkeypatch.setattr(cli, "load_config", lambda _: config)
    monkeypatch.setattr(cli, "validate_forecast_calendar", lambda _: None)
    monkeypatch.setattr(
        simulation_report, "run_simulation", lambda settings: calls.append(settings)
    )
    assert cli.main(["simulate"]) == 0
    assert calls == [config]
