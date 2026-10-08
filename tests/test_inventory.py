"""Hand-worked inventory examples and invalid-input checks."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from src.inventory.bom import bom_matrix
from src.inventory.requirements import material_requirements, material_residual_sigmas
from src.inventory.reorder import planning_horizon, recommend_orders


@pytest.fixture
def config():
    return dict(
        menu={"a": {}, "b": {}},
        recipes={"a": {"milk": 2}, "b": {"milk": 3}},
        materials={
            "milk": dict(
                unit="ml",
                unit_cost=0.1,
                wastage_factor=0.1,
                min_order_qty=5,
                lead_time_days=2,
                shelf_life_days=30,
            )
        },
        inventory=dict(
            service_level=0.95,
            buffer_days=1,
            target_coverage_days=3,
            mean_window_days=3,
            rounding_tolerance=1e-9,
        ),
    )


def needs(days=5, need=10, spread=0):
    return pd.DataFrame(
        dict(
            date=pd.date_range("2025-01-01", periods=days),
            material="milk",
            need=need,
            need_p10=max(0, need - spread),
            need_p50=need,
            need_p90=need + spread,
        )
    )


def stock(on_hand=0, on_order=0, arrival=None):
    return pd.DataFrame(
        [dict(material="milk", on_hand=on_hand, on_order=on_order, arrival_date=arrival)]
    )


def plan(config, on_hand=0, on_order=0, arrival=None, frame=None, sigma=0):
    return recommend_orders(
        needs() if frame is None else frame,
        stock(on_hand, on_order, arrival),
        "2025-01-01",
        config,
        {"milk": sigma},
    )


def test_bom_and_quantiles(config):
    forecast = pd.DataFrame(
        dict(
            date=["2025-01-01"] * 2,
            item=["a", "b"],
            forecast=[10, 5],
            p10=[8, 4],
            p50=[10, 5],
            p90=[12, 6],
        )
    )
    row = material_requirements(forecast, config).iloc[0]
    assert row.need == pytest.approx(38.5)
    assert row.need_p10 == pytest.approx(30.8)
    assert row.need_p90 == pytest.approx(46.2)
    assert row.expected_cost == pytest.approx(3.85)
    assert bom_matrix(config).loc["b", "milk"] == 3


def test_arrival_stock_consumption_and_rounding(config):
    row = plan(config, on_hand=25, sigma=2).iloc[0]
    assert row.projected_on_hand_at_arrival == 5
    assert row.safety_stock == pytest.approx(norm.ppf(0.95) * 2 * np.sqrt(2))
    assert row.reorder_point == pytest.approx(20 + row.safety_stock)
    # Position 25 > ROP 24.65, but receipt-window shortage triggers a purchase.
    assert row.order_qty == 30
    assert row.order_now
    assert row.expected_arrival == "2025-01-03"


def test_no_order_with_sufficient_stock(config):
    row = plan(config, on_hand=100).iloc[0]
    assert row.order_qty == 0
    assert not row.order_now
    assert pd.isna(row.order_by_date)


@pytest.mark.parametrize(
    "arrival,remaining,pending,quantity",
    [
        ("2025-01-02", 10, 0, 20),
        ("2025-01-03", 20, 0, 10),
        ("2025-01-04", 0, 20, 10),
        ("2025-01-10", 0, 0, 30),
    ],
)
def test_pending_receipt_timing(config, arrival, remaining, pending, quantity):
    row = plan(config, on_order=20, arrival=arrival).iloc[0]
    assert row.projected_on_hand_at_arrival == remaining
    assert row.pending_in_coverage == pending
    assert row.order_qty == quantity


def test_late_receipt_cannot_cover_earlier_need(config):
    row = plan(config, on_order=30, arrival="2025-01-05").iloc[0]
    assert row.desired_order_quantity == 20
    assert row.order_qty == 20


def test_short_shelf_cap_and_unmet_safety(config):
    config["materials"]["milk"]["shelf_life_days"] = 4
    row = plan(config, sigma=10).iloc[0]
    assert row.coverage_days == 3
    assert row.order_qty == 30
    assert row.unmet_order_quantity == pytest.approx(row.safety_stock)
    assert row.shelf_capacity_method == "receipt-window forecast"


def test_pack_cannot_fit(config):
    config["materials"]["milk"].update(shelf_life_days=2, min_order_qty=15)
    row = plan(config).iloc[0]
    assert row.order_qty == 0
    assert not row.order_now
    assert "no feasible supplier pack" in row.reason


def test_nonmultiple_moq(config):
    config["materials"]["milk"].update(min_order_qty=12, order_multiple=5)
    row = plan(config, frame=needs(need=1)).iloc[0]
    assert row.order_qty == 15


def test_residual_covariance_and_cutoff(config):
    errors = pd.DataFrame(
        dict(
            date=["2024-12-30"] * 2 + ["2024-12-31"] * 2, item=["a", "b"] * 2, error=[1, 1, -1, -1]
        )
    )
    sigma = material_residual_sigmas(errors, config, "2025-01-01")["milk"]
    assert sigma == pytest.approx(5.5 * np.sqrt(2))
    with pytest.raises(ValueError, match="strictly before"):
        material_residual_sigmas(errors, config, "2024-12-31")


def test_spread_sigma(config):
    row = recommend_orders(needs(spread=norm.ppf(0.9) * 2), stock(), "2025-01-01", config).iloc[0]
    assert row.sigma_daily == pytest.approx(2)
    assert row.safety_stock == pytest.approx(norm.ppf(0.95) * 2 * np.sqrt(2))


@pytest.mark.parametrize("column,value", [("need", -1), ("need", np.nan), ("need_p90", 0)])
def test_invalid_need(config, column, value):
    frame = needs()
    frame.loc[0, column] = value
    with pytest.raises(ValueError):
        plan(config, frame=frame)


@pytest.mark.parametrize(
    "on_hand,on_order,arrival",
    [(-1, 0, None), (np.inf, 0, None), (0, 1, None), (0, 1, "2024-12-31")],
)
def test_invalid_snapshot(config, on_hand, on_order, arrival):
    with pytest.raises(ValueError):
        plan(config, on_hand, on_order, arrival)


def test_horizon_and_gap(config):
    assert planning_horizon(config) == 5
    with pytest.raises(ValueError, match="horizon"):
        plan(config, frame=needs().iloc[:-1])
    with pytest.raises(ValueError):
        plan(config, frame=pd.concat([needs(), needs().iloc[:1]]))


def test_invalid_recipe(config):
    config["recipes"]["a"]["milk"] = -1
    with pytest.raises(ValueError):
        bom_matrix(config)


def test_expiry_buffer(config):
    config["materials"]["milk"]["shelf_life_days"] = 1
    with pytest.raises(ValueError, match="Shelf life"):
        planning_horizon(config)


def test_zero_lead(config):
    config["materials"]["milk"]["lead_time_days"] = 0
    row = plan(config, sigma=2).iloc[0]
    assert row.safety_stock == 0
    assert row.expected_arrival == "2025-01-01"
    assert row.order_qty == 30


def test_requirements_missing_menu_item(config):
    frame = pd.DataFrame(
        dict(date=["2025-01-01"], item=["a"], forecast=[1], p10=[0], p50=[1], p90=[2])
    )
    with pytest.raises(ValueError, match="all configured"):
        material_requirements(frame, config)


def test_point_not_required_inside_quantiles(config):
    frame = pd.DataFrame(
        dict(
            date=["2025-01-01"] * 2,
            item=["a", "b"],
            forecast=[20, 20],
            p10=[0, 0],
            p50=[1, 1],
            p90=[2, 2],
        )
    )
    assert material_requirements(frame, config).need.iloc[0] == 110
