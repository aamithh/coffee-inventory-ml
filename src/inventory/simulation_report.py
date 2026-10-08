"""Forecast-bank construction and staged Phase 5 comparison artifacts."""

from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm
from src.data.artifacts import publish_artifacts
from src.data.loader import load_sales
from src.data.truth_loader import load_truth
from src.inventory.bom import bom_matrix
from src.inventory.requirements import material_requirements
from src.inventory.reorder import planning_horizon
from src.inventory.simulator import replay, policy_summary
from src.models.predict import load_artifact, recursive_forecast
from src.utils.config import resolve_path
from src.utils.dates import get_split_boundaries


def fingerprint(config: dict) -> str:
    """Invalidate cached forecasts whenever source model/history or configuration changes."""
    digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode())
    for key in ("database", "model_bundle"):
        digest.update(resolve_path(config, key).read_bytes())
    return digest.hexdigest()


def past_means(history: pd.DataFrame, origin: pd.Timestamp, config: dict) -> pd.Series:
    """Last calendar week's valid observations, falling back to prior valid item mean."""
    valid = history.loc[history.record_status.isin(["clean", "closed"]) & history.date.lt(origin)]
    recent = valid.loc[
        valid.date.ge(
            origin - pd.Timedelta(days=config["simulation_settings"]["manual_window_days"])
        )
    ]
    values = recent.groupby("item").sales.mean().reindex(config["menu"])
    values = values.fillna(valid.groupby("item").sales.mean()).fillna(0)
    return values.astype(float)


def build_bank(config: dict, observed: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Build all policies using only observed history available before each refresh."""
    bounds = get_split_boundaries(config)
    start, end = bounds["test_start"], bounds["test_end"]
    settings = config["simulation_settings"]
    stride = settings["forecast_refresh_days"]
    horizon = planning_horizon(config) + stride - 1
    artifact = load_artifact(config)
    effective = bom_matrix(config).mul(
        pd.Series({m: 1 + s["wastage_factor"] for m, s in config["materials"].items()}), axis=1
    )
    prior = observed.loc[observed.date.lt(start)]
    initial_means = (
        past_means(prior, start, config).reindex(effective.index).to_numpy() @ effective.to_numpy()
    )
    initial = {
        m: float(value)
        * min(
            config["inventory"]["initial_coverage_days"],
            s["shelf_life_days"] - config["inventory"]["buffer_days"],
        )
        for (m, s), value in zip(config["materials"].items(), initial_means)
    }
    frames = []
    origins = pd.date_range(start, end, freq=f"{stride}D")
    for index, origin in enumerate(origins, 1):
        history = observed.loc[observed.date.lt(origin)].copy()
        dates = pd.date_range(origin, periods=horizon)
        plans = observed.loc[
            observed.date.isin(dates), ["date", "item", "category", "price", "promo_flag"]
        ].copy()
        missing = dates.difference(plans.date.unique())
        if len(missing):
            plans = pd.concat(
                [
                    plans,
                    pd.DataFrame(
                        [
                            dict(
                                date=day,
                                item=item,
                                category=m["category"],
                                price=m["price"],
                                promo_flag=0,
                            )
                            for day in missing
                            for item, m in config["menu"].items()
                        ]
                    ),
                ],
                ignore_index=True,
            )
        ml = recursive_forecast(artifact, history, plans, origin, config)
        seasonal = recursive_forecast(
            artifact, history, plans, origin, config, model_name="seasonal_naive"
        )
        seasonal[["p10", "p50", "p90"]] = np.repeat(
            seasonal.forecast.to_numpy()[:, None], 3, axis=1
        )
        manual = ml.copy()
        manual["forecast"] = manual.item.map(past_means(history, origin, config)) * (
            1 + config["inventory"]["manual_buffer_fraction"]
        )
        manual[["p10", "p50", "p90"]] = np.repeat(manual.forecast.to_numpy()[:, None], 3, axis=1)
        clean = history.loc[history.record_status.isin(["clean", "closed"])]
        wide = clean.pivot(index="date", columns="item", values="sales").reindex(
            index=pd.date_range(history.date.min(), origin - pd.Timedelta(days=1)),
            columns=effective.index,
        )
        residual = (wide - wide.shift(7)).tail(settings["residual_window_days"]).dropna()
        sigmas = (
            pd.Series(
                np.std(residual.to_numpy() @ effective.to_numpy(), axis=0, ddof=1),
                index=effective.columns,
            )
            if len(residual) >= 2
            else None
        )
        for policy, forecast in (("manual", manual), ("seasonal_naive", seasonal), ("ml", ml)):
            needs = material_requirements(forecast, config)
            if policy == "ml":
                spreads = needs.assign(spread=(needs.need_p90 - needs.need_p50) / norm.ppf(0.9))
                sigma = (
                    spreads.loc[
                        spreads.date
                        < origin + pd.Timedelta(days=config["inventory"]["mean_window_days"])
                    ]
                    .groupby("material")
                    .spread.mean()
                )
            elif policy == "seasonal_naive":
                sigma = (
                    sigmas
                    if sigmas is not None
                    else needs.groupby("material").need.mean()
                    * config["inventory"]["manual_buffer_fraction"]
                )
            else:
                sigma = pd.Series(0.0, index=effective.columns)
            needs["sigma_daily"] = needs.material.map(sigma)
            needs["policy"] = policy
            needs["origin"] = origin
            frames.append(needs[["policy", "origin", "date", "material", "need", "sigma_daily"]])
        print(
            f"Forecast refresh {index}/{len(origins)}: {origin.date()} (past observed history only)",
            flush=True,
        )
    return pd.concat(frames, ignore_index=True), initial


def run_simulation(config: dict) -> dict:
    """Compare three frozen policies over all test dates; publish only validated outputs."""
    settings = config["simulation_settings"]
    for key in ("forecast_refresh_days", "manual_window_days", "residual_window_days"):
        if (
            isinstance(settings[key], bool)
            or not isinstance(settings[key], int)
            or settings[key] < 1
        ):
            raise ValueError(f"Invalid simulation {key}.")
    for key in (
        "manual_buffer_fraction",
        "holding_cost_daily_fraction",
        "lost_sale_penalty_fraction",
    ):
        if not np.isfinite(config["inventory"][key]) or config["inventory"][key] < 0:
            raise ValueError(f"Invalid cost/buffer fraction: {key}")
    stamp = fingerprint(config)
    metadata = resolve_path(config, "simulation_metadata")
    cached = resolve_path(config, "simulation_forecasts")
    if (
        settings["reuse_forecast_cache"]
        and metadata.exists()
        and cached.exists()
        and json.loads(metadata.read_text()).get("fingerprint") == stamp
    ):
        bank = pd.read_csv(cached, parse_dates=["date", "origin"])
        info = json.loads(metadata.read_text())
        if hashlib.sha256(cached.read_bytes()).hexdigest() != info["forecast_sha256"]:
            raise ValueError("Simulation forecast cache integrity check failed.")
        initial = info["initial_quantities"]
        print("Forecast cache: source/model/config fingerprint and CSV hash verified", flush=True)
    else:
        bank, initial = build_bank(config, load_sales(config))
    # Evaluation-only demand is loaded after the policy forecast bank is frozen.
    bounds = get_split_boundaries(config)
    oracle = load_truth(config)
    oracle = oracle.loc[
        oracle.date.between(bounds["test_start"], bounds["test_end"]),
        ["date", "item", "latent_demand"],
    ]
    prices = load_sales(
        config, start_date=str(bounds["test_start"].date()), end_date=str(bounds["test_end"].date())
    )[["date", "item", "price"]]
    demand = oracle.rename(columns={"latent_demand": "demand"}).merge(
        prices, on=["date", "item"], validate="one_to_one"
    )
    daily, items, orders = replay(demand, bank, initial, config)
    summary = policy_summary(daily, items, config)
    waste = daily.groupby(["policy", "material", "unit"], as_index=False).agg(
        waste_units=("waste", "sum"), waste_cost=("waste_cost", "sum")
    )
    base = summary.set_index("policy").loc["manual"]
    comparisons = {}
    for row in summary.itertuples():
        if row.policy != "manual":
            comparisons[row.policy] = {
                key: None
                if float(base[key]) == 0
                else float((base[key] - getattr(row, key)) / base[key])
                for key in ("waste_cost", "stockout_rate", "total_cost")
            }
    result = dict(
        test_start=str(bounds["test_start"].date()),
        test_end=str(bounds["test_end"].date()),
        test_days=int(items.date.nunique()),
        forecast_refresh_days=settings["forecast_refresh_days"],
        daily_material_rows=len(daily),
        item_rows=len(items),
        order_rows=len(orders),
        policies=summary.to_dict(orient="records"),
        relative_reduction_vs_manual=comparisons,
    )
    report = [
        "# Phase 5 policy simulation",
        "",
        f"Test dates: {result['test_start']} through {result['test_end']} ({result['test_days']} days).",
        "",
        "| Policy | Service | Stockout units rate | Waste INR | Holding INR | Total cost INR |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples():
        report.append(
            f"| {row.policy} | {row.service_level:.2%} | {row.stockout_rate:.2%} | {row.waste_cost:.2f} | {row.holding_cost:.2f} | {row.total_cost:.2f} |"
        )
    report += ["", "## Measured comparisons", ""]
    for policy, values in comparisons.items():
        report.append(
            f"{policy} relative reductions vs manual: "
            + ", ".join(
                f"{key}: {value:.2%}"
                if value is not None
                else f"{key}: undefined (zero manual denominator)"
                for key, value in values.items()
            )
            + ". Negative values mean worse."
        )
    report += [
        "",
        "## Interpretation and limits",
        "",
        "All policies face identical evaluation demand, initial fresh stock, suppliers and FIFO allocation.",
        "Forecasts refresh weekly from common historical observed POS records; simulated lost sales do not feed future predictors. This isolates the inventory decision comparison but omits policy-dependent observation feedback.",
        "Manual: last week's valid average with a 20% configured buffer and supplier rounding, without a demand-based expiry cap. Forecast policies use the Phase 4 trigger/cap rules, extended for lots and multiple receipts.",
        "Seasonal-naive sigma comes from past aggregate lag-seven residuals; ML sigma uses its uncalibrated P90-P50 spread. These compare complete policies, not only point forecasts.",
        "Whole items are served in alphabetical menu order when materials are scarce; no partial recipe consumption or substitutions.",
        "Expiry is discarded at start of receipt_date + shelf_life_days. Preparation wastage is included once in recipe consumption.",
        "Total cost = initial stock value + purchases + holding + lost-sales penalty. Waste cost is already embedded in stock purchases and is not added again.",
        "Terminal stock and undelivered pipeline value are reported separately; no salvage is assumed. Orders near the end may arrive outside the replay.",
        "Native waste units are reported per material; g, ml and pcs are never summed into one unit metric.",
        "Synthetic results do not establish real-shop savings. Parameters were frozen before replay and were not tuned to force improvement.",
        "",
        "![Policy comparison](figures/simulation_comparison.png)",
        "",
        "![Cumulative costs](figures/simulation_costs.png)",
        "",
    ]
    staging = resolve_path(config, "pipeline_staging")
    staging.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="simulation_") as directory:
        pairs = []
        outputs = {
            "simulation": daily,
            "simulation_items": items,
            "simulation_orders": orders,
            "simulation_summary": summary,
            "simulation_waste": waste,
            "simulation_forecasts": bank,
        }
        for key, frame in outputs.items():
            path = Path(directory) / f"{key}.csv"
            frame.to_csv(path, index=False, lineterminator="\n")
            pairs.append((path, resolve_path(config, key)))
        meta = dict(
            fingerprint=stamp,
            initial_quantities=initial,
            forecast_sha256=hashlib.sha256(
                (Path(directory) / "simulation_forecasts.csv").read_bytes()
            ).hexdigest(),
        )
        for key, text in {
            "simulation_metrics": json.dumps(result, indent=2, allow_nan=False),
            "simulation_metadata": json.dumps(meta, indent=2, allow_nan=False),
            "simulation_report": "\n".join(report) + "\n",
        }.items():
            path = Path(directory) / f"{key}.txt"
            path.write_text(text, encoding="utf-8")
            pairs.append((path, resolve_path(config, key)))
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        for ax, key, label in zip(
            axes,
            ["waste_cost", "stockout_rate", "total_cost"],
            ["Expired stock cost (INR)", "Unserved demand fraction", "Total modeled cost (INR)"],
        ):
            ax.bar(summary.policy, summary[key], color=["#64748b", "#d97706", "#2563eb"])
            ax.set_title(label)
            ax.tick_params(axis="x", rotation=20)
        fig.tight_layout()
        path = Path(directory) / "simulation_comparison.png"
        fig.savefig(path, dpi=config["eda"]["dpi"])
        plt.close(fig)
        pairs.append(
            (path, resolve_path(config, "figures") / config["simulation_figures"]["comparison"])
        )
        costs = daily.groupby(["policy", "date"]).agg(
            purchase=("purchase_cost", "sum"), holding=("holding_cost", "sum")
        )
        penalty = (
            items.groupby(["policy", "date"]).lost_sales_value.sum()
            * config["inventory"]["lost_sale_penalty_fraction"]
        )
        costs["cost"] = costs.purchase + costs.holding + penalty
        fig, ax = plt.subplots(figsize=(10, 4))
        for policy, g in costs.groupby(level="policy"):
            ax.plot(
                g.index.get_level_values("date"),
                g.cost.cumsum()
                + float(summary.set_index("policy").loc[policy, "initial_stock_value"]),
                label=policy,
            )
        ax.set_ylabel("Cumulative modeled cost (INR)")
        ax.legend()
        fig.autofmt_xdate()
        fig.tight_layout()
        path = Path(directory) / "simulation_costs.png"
        fig.savefig(path, dpi=config["eda"]["dpi"])
        plt.close(fig)
        pairs.append(
            (path, resolve_path(config, "figures") / config["simulation_figures"]["costs"])
        )
        publish_artifacts(pairs)
    print(json.dumps(result, indent=2, allow_nan=False), flush=True)
    return result
