"""Lead-time-aware replenishment with explicit expiry and pack constraints."""

import math
from typing import Any
import numpy as np
import pandas as pd
from scipy.stats import norm
from src.inventory.bom import bom_matrix


def planning_horizon(config: dict[str, Any]) -> int:
    """Forecast lead time plus receipt-centered coverage, including the mean window."""
    bom_matrix(config)
    settings = config["inventory"]
    for key in ("buffer_days", "target_coverage_days", "mean_window_days"):
        value = settings[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or (key != "buffer_days" and value == 0)
        ):
            raise ValueError(f"Invalid inventory {key}.")
    if not 0.5 < float(settings["service_level"]) < 1:
        raise ValueError("Service level must be between 0.5 and 1.")
    if not 0 < float(settings["rounding_tolerance"]) < 1e-3:
        raise ValueError("Invalid rounding tolerance.")
    if any(m["shelf_life_days"] <= settings["buffer_days"] for m in config["materials"].values()):
        raise ValueError("Shelf life must exceed the expiry buffer.")
    return max(
        settings["mean_window_days"],
        max(
            m["lead_time_days"]
            + min(settings["target_coverage_days"], m["shelf_life_days"] - settings["buffer_days"])
            for m in config["materials"].values()
        ),
    )


def recommend_orders(
    requirements: pd.DataFrame,
    snapshot: pd.DataFrame,
    origin: str | pd.Timestamp,
    config: dict[str, Any],
    residual_sigmas: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Plan a purchase today; pending receipts occur before consumption on their date."""
    horizon = planning_horizon(config)
    start = pd.Timestamp(origin)
    if pd.isna(start) or start.tzinfo is not None or start != start.normalize():
        raise ValueError("Origin must be a timezone-free calendar day.")
    required = {"date", "material", "need", "need_p10", "need_p50", "need_p90"}
    if not required.issubset(requirements):
        raise ValueError("Incomplete material requirements.")
    needs = requirements[list(required)].copy()
    needs["date"] = pd.to_datetime(needs.date)
    if (
        needs.date.isna().any()
        or needs.date.dt.tz is not None
        or needs.date.ne(needs.date.dt.normalize()).any()
        or needs.duplicated(["date", "material"]).any()
    ):
        raise ValueError("Material dates must be valid calendar days with unique keys.")
    if set(needs.material) != set(config["materials"]):
        raise ValueError("Requirements must contain exactly the configured materials.")
    numeric = needs[["need", "need_p10", "need_p50", "need_p90"]].to_numpy(dtype=float)
    if (
        not np.isfinite(numeric).all()
        or (numeric < 0).any()
        or needs.need_p10.gt(needs.need_p50).any()
        or needs.need_p50.gt(needs.need_p90).any()
    ):
        raise ValueError("Material needs must be finite, nonnegative and ordered.")
    if not {"material", "on_hand", "on_order", "arrival_date"}.issubset(snapshot):
        raise ValueError("Snapshot requires material, on_hand, on_order and arrival_date.")
    stocks = snapshot.copy().set_index("material")
    if stocks.index.has_duplicates or set(stocks.index) != set(config["materials"]):
        raise ValueError("Snapshot must contain each configured material exactly once.")
    amounts = stocks[["on_hand", "on_order"]].to_numpy(dtype=float)
    if not np.isfinite(amounts).all() or (amounts < 0).any():
        raise ValueError("Stock quantities must be finite and nonnegative.")
    stocks["arrival_date"] = pd.to_datetime(stocks.arrival_date)
    for row in stocks.itertuples():
        if row.on_order > 0 and (
            pd.isna(row.arrival_date)
            or row.arrival_date.tzinfo is not None
            or row.arrival_date != row.arrival_date.normalize()
            or row.arrival_date < start
        ):
            raise ValueError("Positive pending stock requires a valid arrival on or after origin.")
    settings = config["inventory"]
    z = float(norm.ppf(settings["service_level"]))
    tol = settings["rounding_tolerance"]
    results = []
    for name, material in config["materials"].items():
        frame = needs.loc[needs.material.eq(name)].set_index("date").sort_index()
        dates = pd.date_range(start, periods=horizon)
        if not dates.isin(frame.index).all():
            raise ValueError(
                f"Insufficient contiguous forecast horizon for {name}: need {horizon} days."
            )
        frame = frame.loc[dates]
        mean = float(frame.need.iloc[: settings["mean_window_days"]].mean())
        if residual_sigmas is None:
            sigma = float(
                ((frame.need_p90 - frame.need_p50) / norm.ppf(0.9))
                .iloc[: settings["mean_window_days"]]
                .mean()
            )
            sigma_source = "P90-P50 normal-spread proxy"
        else:
            if (
                name not in residual_sigmas
                or not math.isfinite(residual_sigmas[name])
                or residual_sigmas[name] < 0
            ):
                raise ValueError(
                    "Residual sigmas must cover all materials with finite nonnegative values."
                )
            sigma = float(residual_sigmas[name])
            sigma_source = "past aggregate residual sample standard deviation"
        lead = material["lead_time_days"]
        life = material["shelf_life_days"] - settings["buffer_days"]
        coverage = min(settings["target_coverage_days"], life)
        arrival = start + pd.Timedelta(days=lead)
        end = arrival + pd.Timedelta(days=coverage)
        stock = stocks.loc[name]
        pending = float(stock.on_order)
        pending_date = stock.arrival_date
        remaining = float(stock.on_hand)
        shortfall = 0.0
        for day in pd.date_range(start, periods=lead):
            if pending > 0 and pending_date == day:
                remaining += pending
            daily = float(frame.loc[day, "need"])
            shortfall += max(0, daily - remaining)
            remaining = max(0, remaining - daily)
        if pending > 0 and pending_date == arrival:
            remaining += pending
        relevant_pending = pending if pending > 0 and arrival < pending_date < end else 0.0
        target = float(frame.loc[(frame.index >= arrival) & (frame.index < end), "need"].sum())
        safety = z * sigma * math.sqrt(lead)
        rop = mean * lead + safety
        position = float(stock.on_hand) + (
            pending if pending > 0 and pending_date <= arrival else 0.0
        )
        # A late receipt cannot cover an earlier shortage inside the coverage window.
        balance = remaining
        timing_gap = 0.0
        for day in pd.date_range(arrival, periods=coverage):
            if relevant_pending and pending_date == day:
                balance += relevant_pending
            balance -= float(frame.loc[day, "need"])
            timing_gap = max(timing_gap, -balance)
        desired = max(0, target + safety - remaining - relevant_pending, timing_gap)
        # Short shelf lives use the actual receipt-window demand; longer lives use
        # the mean-rate proxy beyond the finite forecast horizon, explicitly reported.
        capacity_demand = target if life <= coverage else mean * life
        capacity = max(0, capacity_demand - remaining - relevant_pending)
        multiple = float(material.get("order_multiple", material["min_order_qty"]))
        minimum = float(material["min_order_qty"])
        if not math.isfinite(multiple) or multiple <= 0:
            raise ValueError("Order multiple must be finite and positive.")
        rounded = (
            math.ceil(max(desired, minimum) / multiple - tol) * multiple if desired > tol else 0.0
        )
        cap = math.floor(capacity / multiple + tol) * multiple
        feasible = min(rounded, cap)
        if feasible < minimum - tol:
            feasible = 0.0
        trigger = position <= rop + tol or shortfall > tol or timing_gap > tol
        quantity = feasible if trigger else 0.0
        reasons = []
        if trigger:
            reasons.append("inventory position at/below reorder point or projected shortage")
        else:
            reasons.append("inventory position above reorder point")
        if shortfall > tol:
            reasons.append("stock shortage before new delivery; expedite or adjust menu")
        if rounded > cap + tol:
            reasons.append("shelf-life capacity limits safety stock or pack rounding")
        if trigger and desired > tol and quantity == 0:
            reasons.append("no feasible supplier pack fits shelf-life capacity")
        results.append(
            dict(
                material=name,
                unit=material["unit"],
                on_hand=float(stock.on_hand),
                on_order=pending,
                mean_daily_need=mean,
                sigma_daily=sigma,
                sigma_source=sigma_source,
                safety_stock=safety,
                reorder_point=rop,
                inventory_position=position,
                coverage_days=coverage,
                planning_arrival_date=arrival.strftime("%Y-%m-%d"),
                projected_on_hand_at_arrival=remaining,
                pending_in_coverage=relevant_pending,
                target_coverage_demand=target,
                shelf_capacity_demand=capacity_demand,
                shelf_capacity_method="receipt-window forecast"
                if life <= coverage
                else "mean-rate shelf-life proxy",
                max_order_quantity=capacity,
                desired_order_quantity=desired,
                order_now=bool(trigger and quantity > 0),
                order_qty=quantity,
                order_by_date=start.strftime("%Y-%m-%d") if trigger else None,
                expected_arrival=arrival.strftime("%Y-%m-%d") if trigger and quantity > 0 else None,
                pre_arrival_shortfall=shortfall,
                unmet_order_quantity=max(0, desired - quantity) if trigger else 0.0,
                estimated_order_cost=quantity * material["unit_cost"],
                reason="; ".join(reasons),
            )
        )
    return pd.DataFrame(results)
