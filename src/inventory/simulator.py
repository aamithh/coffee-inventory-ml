"""Day-by-day counterfactual FIFO replay; evaluation demand never enters forecasts."""

from typing import Any
import numpy as np
import pandas as pd
from src.inventory.bom import bom_matrix
from src.inventory.lots import Stock
from src.inventory.policies import order_quantity
from src.inventory.reorder import planning_horizon

POLICIES = ("manual", "seasonal_naive", "ml")


def replay(
    demand: pd.DataFrame, bank: pd.DataFrame, initial: dict[str, float], config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Replay identical customer requests using each policy's independent lot state."""
    horizon = planning_horizon(config)
    matrix = bom_matrix(config)
    effective = matrix.mul(
        pd.Series({m: 1 + s["wastage_factor"] for m, s in config["materials"].items()}), axis=1
    )
    actual = demand[["date", "item", "demand", "price"]].copy()
    actual["date"] = pd.to_datetime(actual.date)
    values = actual[["demand", "price"]].to_numpy(dtype=float)
    if (
        actual.empty
        or actual.duplicated(["date", "item"]).any()
        or not np.isfinite(values).all()
        or (values < 0).any()
        or actual.demand.ne(np.floor(actual.demand)).any()
    ):
        raise ValueError(
            "Demand must have unique keys and nonnegative integer requests with finite prices."
        )
    dates = pd.DatetimeIndex(sorted(actual.date.unique()))
    if not dates.equals(pd.date_range(dates[0], dates[-1])) or any(
        set(g.item) != set(config["menu"]) for _, g in actual.groupby("date")
    ):
        raise ValueError("Demand must cover every item on contiguous dates.")
    if set(initial) != set(config["materials"]) or any(
        not np.isfinite(v) or v < 0 for v in initial.values()
    ):
        raise ValueError("Initial quantities must cover all materials and be finite/nonnegative.")
    forecasts = bank.copy()
    forecasts["date"] = pd.to_datetime(forecasts.date)
    forecasts["origin"] = pd.to_datetime(forecasts.origin)
    if (
        set(forecasts.policy) != set(POLICIES)
        or forecasts.duplicated(["policy", "origin", "date", "material"]).any()
    ):
        raise ValueError("Forecast bank requires all policies and unique forecast keys.")
    numeric = forecasts[["need", "sigma_daily"]].to_numpy(dtype=float)
    if (
        not np.isfinite(numeric).all()
        or (numeric < 0).any()
        or forecasts.date.lt(forecasts.origin).any()
    ):
        raise ValueError("Invalid forecast-bank quantities/dates.")
    daily = []
    items = []
    orders = []
    for policy in POLICIES:
        stocks = {m: Stock() for m in config["materials"]}
        pending = {m: [] for m in stocks}
        for m, qty in initial.items():
            stocks[m].receive(qty, dates[0], config["materials"][m]["shelf_life_days"])
        for day in dates:
            wasted = {m: stocks[m].expire(day) for m in stocks}
            receipts = {m: 0.0 for m in stocks}
            purchases = {m: 0.0 for m in stocks}
            opening = {m: stocks[m].quantity + wasted[m] for m in stocks}
            for m, shipments in pending.items():
                for arrival, qty in shipments:
                    if arrival == day:
                        stocks[m].receive(qty, day, config["materials"][m]["shelf_life_days"])
                        receipts[m] += qty
                pending[m] = [(arrival, qty) for arrival, qty in shipments if arrival > day]
            origins = forecasts.loc[
                forecasts.policy.eq(policy) & forecasts.origin.le(day), "origin"
            ]
            if origins.empty:
                raise ValueError("Forecast bank has no origin available before review.")
            origin = origins.max()
            for m, material in config["materials"].items():
                needs = (
                    forecasts.loc[
                        forecasts.policy.eq(policy)
                        & forecasts.origin.eq(origin)
                        & forecasts.material.eq(m)
                        & forecasts.date.ge(day)
                    ]
                    .set_index("date")
                    .sort_index()
                )
                if not pd.date_range(day, periods=horizon).isin(needs.index).all():
                    raise ValueError(
                        "Forecast bank must cover every review's full planning horizon."
                    )
                qty = order_quantity(
                    day, stocks[m], pending[m], needs, material, config, policy == "manual"
                )
                if qty:
                    arrival = day + pd.Timedelta(days=material["lead_time_days"])
                    purchases[m] = qty
                    orders.append(
                        dict(
                            policy=policy,
                            date=day,
                            material=m,
                            quantity=qty,
                            arrival=arrival,
                            cost=qty * material["unit_cost"],
                        )
                    )
                    if arrival == day:
                        stocks[m].receive(qty, day, material["shelf_life_days"])
                        receipts[m] += qty
                    else:
                        pending[m].append((arrival, qty))
            consumed = {m: 0.0 for m in stocks}
            for item in sorted(config["menu"]):
                row = actual.loc[actual.date.eq(day) & actual.item.eq(item)].iloc[0]
                recipe = effective.loc[item]
                possible = min(
                    int(np.floor((stocks[m].quantity + 1e-8) / qty))
                    for m, qty in recipe.items()
                    if qty > 0
                )
                served = min(int(row.demand), possible)
                for m, qty in recipe.items():
                    if qty > 0:
                        used = stocks[m].consume(served * qty)
                        consumed[m] += used
                items.append(
                    dict(
                        policy=policy,
                        date=day,
                        item=item,
                        demand=int(row.demand),
                        served=served,
                        lost=int(row.demand) - served,
                        lost_sales_value=(int(row.demand) - served) * row.price,
                    )
                )
            for m, material in config["materials"].items():
                daily.append(
                    dict(
                        policy=policy,
                        date=day,
                        material=m,
                        unit=material["unit"],
                        opening=opening[m],
                        received=receipts[m],
                        consumed=consumed[m],
                        waste=wasted[m],
                        closing=stocks[m].quantity,
                        purchased=purchases[m],
                        pending_quantity=sum(qty for _, qty in pending[m]),
                        waste_cost=wasted[m] * material["unit_cost"],
                        purchase_cost=purchases[m] * material["unit_cost"],
                        holding_cost=stocks[m].quantity
                        * material["unit_cost"]
                        * config["inventory"]["holding_cost_daily_fraction"],
                        closing_value=stocks[m].quantity * material["unit_cost"],
                    )
                )
    daily_frame = pd.DataFrame(daily)
    np.testing.assert_allclose(
        daily_frame.opening + daily_frame.received,
        daily_frame.consumed + daily_frame.waste + daily_frame.closing,
        rtol=1e-10,
        atol=1e-6,
    )
    order_frame = pd.DataFrame(
        orders, columns=["policy", "date", "material", "quantity", "arrival", "cost"]
    )
    return daily_frame, pd.DataFrame(items), order_frame


def policy_summary(daily: pd.DataFrame, items: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Costs include purchases once; expired-stock cost is a diagnostic subset."""
    rows = []
    for policy in POLICIES:
        material = daily.loc[daily.policy.eq(policy)]
        sales = items.loc[items.policy.eq(policy)]
        requested = int(sales.demand.sum())
        lost = int(sales.lost.sum())
        purchase = float(material.purchase_cost.sum())
        holding = float(material.holding_cost.sum())
        penalty = (
            float(sales.lost_sales_value.sum()) * config["inventory"]["lost_sale_penalty_fraction"]
        )
        final = material.loc[material.date.eq(material.date.max())]
        initial_value = sum(
            float(g.iloc[0].opening) * config["materials"][m]["unit_cost"]
            for m, g in material.groupby("material")
        )
        rows.append(
            dict(
                policy=policy,
                requested_units=requested,
                served_units=requested - lost,
                lost_units=lost,
                service_level=(requested - lost) / requested if requested else 1.0,
                stockout_rate=lost / requested if requested else 0.0,
                item_day_stockout_rate=float(sales.lost.gt(0).mean()),
                waste_cost=float(material.waste_cost.sum()),
                purchase_cost=purchase,
                holding_cost=holding,
                lost_sale_penalty=penalty,
                initial_stock_value=initial_value,
                closing_stock_value=float(final.closing_value.sum()),
                pending_stock_value=sum(
                    row.pending_quantity * config["materials"][row.material]["unit_cost"]
                    for row in final.itertuples()
                ),
                total_cost=initial_value + purchase + holding + penalty,
            )
        )
    return pd.DataFrame(rows)
