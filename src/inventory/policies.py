"""Forecast-only decisions from FIFO stock and multiple dated pending deliveries."""

import math
import pandas as pd
from scipy.stats import norm
from src.inventory.lots import Stock


def order_quantity(
    day: pd.Timestamp,
    stock: Stock,
    pending: list[tuple[pd.Timestamp, float]],
    needs: pd.DataFrame,
    material: dict,
    config: dict,
    manual: bool = False,
) -> float:
    """Project expiry/consumption to receipt before applying Phase 4 ordering formulas."""
    lead = material["lead_time_days"]
    settings = config["inventory"]
    life = material["shelf_life_days"] - settings["buffer_days"]
    coverage = min(settings["target_coverage_days"], life)
    arrival = day + pd.Timedelta(days=lead)
    end = arrival + pd.Timedelta(days=coverage)
    future = stock.copy()
    shortage = 0.0
    for date in pd.date_range(day, periods=lead):
        future.expire(date)
        for receipt, qty in pending:
            if receipt == date:
                future.receive(qty, date, material["shelf_life_days"])
        wanted = float(needs.loc[date, "need"])
        shortage += wanted - future.consume(wanted)
    future.expire(arrival)
    for receipt, qty in pending:
        if receipt == arrival:
            future.receive(qty, arrival, material["shelf_life_days"])
    at_arrival = future.quantity
    incoming = sum(qty for receipt, qty in pending if arrival < receipt < end)
    target = float(needs.loc[(needs.index >= arrival) & (needs.index < end), "need"].sum())
    mean = float(needs.need.iloc[: settings["mean_window_days"]].mean())
    sigma = float(needs.sigma_daily.iloc[0])
    safety = 0.0 if manual else float(norm.ppf(settings["service_level"])) * sigma * math.sqrt(lead)
    position = stock.quantity + sum(qty for receipt, qty in pending if receipt <= arrival)
    gap = 0.0
    for date in pd.date_range(arrival, periods=coverage):
        future.expire(date)
        for receipt, qty in pending:
            if arrival < receipt == date:
                future.receive(qty, date, material["shelf_life_days"])
        wanted = float(needs.loc[date, "need"])
        gap += wanted - future.consume(wanted)
    desired = max(0, target + safety - at_arrival - incoming, gap)
    # The manual rule buys last week's average with a fixed buffer and pack rounding;
    # it does not forecast calendar variation or impose a demand-based expiry cap.
    if manual:
        desired = max(0, target - at_arrival - incoming, gap)
        trigger = position <= mean * lead or shortage > 1e-9 or gap > 1e-9
        cap = float("inf")
    else:
        trigger = position <= mean * lead + safety or shortage > 1e-9 or gap > 1e-9
        cap = max(0, (target if life <= coverage else mean * life) - at_arrival - incoming)
    if not trigger or desired <= settings["rounding_tolerance"]:
        return 0.0
    multiple = float(material.get("order_multiple", material["min_order_qty"]))
    minimum = float(material["min_order_qty"])
    if not math.isfinite(multiple) or multiple <= 0:
        raise ValueError("Supplier multiple must be finite and positive.")
    qty = math.ceil(max(desired, minimum) / multiple - settings["rounding_tolerance"]) * multiple
    if not manual:
        qty = min(qty, math.floor(cap / multiple + settings["rounding_tolerance"]) * multiple)
    return qty if qty >= minimum else 0.0
