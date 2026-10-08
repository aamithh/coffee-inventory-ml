"""Export a reproducible illustrative inventory plan without changing training data."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import pandas as pd
from src.data.artifacts import publish_artifacts
from src.data.loader import load_sales
from src.inventory.bom import bom_matrix
from src.inventory.requirements import material_requirements
from src.inventory.reorder import planning_horizon, recommend_orders
from src.models.predict import load_artifact, recursive_forecast
from src.utils.config import resolve_path
from src.utils.dates import get_as_of_date


def run_inventory(config: dict, snapshot: pd.DataFrame | None = None) -> dict:
    """Use saved forecasts and a supplied snapshot, or clearly marked demo stock."""
    origin = get_as_of_date(config)
    horizon = planning_horizon(config)
    last = origin + pd.Timedelta(days=horizon - 1)
    history = load_sales(config, end_date=str((origin - pd.Timedelta(days=1)).date()))
    # Only known planned metadata is passed; no future actual demand/weather.
    plans = load_sales(config, start_date=str(origin.date()), end_date=str(last.date()))[
        ["date", "item", "category", "price", "promo_flag"]
    ]
    if len(plans) != horizon * len(config["menu"]):
        raise ValueError("Demo planned metadata does not cover the inventory horizon.")
    forecasts = recursive_forecast(load_artifact(config), history, plans, origin, config)
    needs = material_requirements(forecasts, config)
    illustrative = snapshot is None
    if illustrative:
        initial = config["inventory"]["initial_coverage_days"]
        if (
            not isinstance(initial, (int, float))
            or isinstance(initial, bool)
            or not 0 <= initial < float("inf")
        ):
            raise ValueError("Initial coverage must be finite and nonnegative.")
        means = (
            needs.loc[
                needs.date < origin + pd.Timedelta(days=config["inventory"]["mean_window_days"])
            ]
            .groupby("material")
            .need.mean()
        )
        snapshot = pd.DataFrame(
            [
                dict(
                    material=name,
                    on_hand=float(means[name])
                    * min(initial, m["shelf_life_days"] - config["inventory"]["buffer_days"]),
                    on_order=0.0,
                    arrival_date=None,
                )
                for name, m in config["materials"].items()
            ]
        )
    orders = recommend_orders(needs, snapshot, origin, config)
    summary = dict(
        origin=str(origin.date()),
        forecast_days=horizon,
        item_forecast_rows=len(forecasts),
        material_forecast_rows=len(needs),
        materials=len(orders),
        orders_now=int(orders.order_now.sum()),
        estimated_order_cost=float(orders.estimated_order_cost.sum()),
        currency=config["project"]["currency"],
        illustrative_snapshot=illustrative,
        materials_with_pre_arrival_shortfall=int(orders.pre_arrival_shortfall.gt(0).sum()),
        materials_with_unmet_order_quantity=int(orders.unmet_order_quantity.gt(0).sum()),
    )
    report = [
        "# Phase 4 inventory plan",
        "",
        f"Planning date: {origin.date()}; horizon: {horizon} days.",
        "Stock snapshot: illustrative mean-demand coverage, not a measured shop inventory."
        if illustrative
        else "Stock snapshot: supplied by the caller.",
        "",
        "| Material | Unit | Order now | Quantity | Safety stock | Reason |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in orders.itertuples():
        report.append(
            f"| {row.material} | {row.unit} | {row.order_now} | {row.order_qty:.2f} | {row.safety_stock:.2f} | {row.reason} |"
        )
    report += [
        "",
        "Quantile totals and the normal-spread safety stock are planning proxies, not calibrated 95% guarantees.",
        "Coverage starts at delivery. Pending arrivals are received before daily consumption.",
        "Short shelf-life caps use receipt-window demand; longer shelf lives use mean demand times usable life.",
        "Pack constraints can prevent a feasible order; unmet quantities and pre-delivery shortages are explicit.",
        "Aggregate stock is assumed usable through the planning window. Lot expiry and FIFO belong to Phase 5.",
        "Orders above the reorder point are reviewed again tomorrow; an unknown future order date is left blank.",
        "No purchases are placed and no policy simulation or savings claim is made.",
    ]
    frames = {
        "inventory_bom": bom_matrix(config).reset_index(),
        "inventory_forecasts": forecasts,
        "material_requirements": needs,
        "inventory_snapshot": snapshot,
        "inventory_orders": orders,
    }
    staging = resolve_path(config, "pipeline_staging")
    staging.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="inventory_") as directory:
        pairs = []
        for key, frame in frames.items():
            path = Path(directory) / f"{key}.csv"
            frame.to_csv(path, index=False, lineterminator="\n")
            pairs.append((path, resolve_path(config, key)))
        for key, content in {
            "inventory_summary": json.dumps(summary, indent=2, allow_nan=False),
            "inventory_report": "\n".join(report) + "\n",
        }.items():
            path = Path(directory) / f"{key}.txt"
            path.write_text(content, encoding="utf-8")
            pairs.append((path, resolve_path(config, key)))
        publish_artifacts(pairs)
    print(json.dumps(summary, indent=2, allow_nan=False), flush=True)
    return summary
