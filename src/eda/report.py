"""Observed-data exploratory plots and reproducible Phase 2 artifacts."""

import json
from pathlib import Path
import tempfile
from typing import Any
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from src.data.artifacts import publish_artifacts
from src.data.loader import load_sales
from src.data.quality import assert_no_truth_references
from src.features.build_features import build_features
from src.utils.config import resolve_path
from src.utils.dates import get_split_boundaries


def create_eda(sales: pd.DataFrame, config: dict[str, Any], output: Path) -> dict[str, Any]:
    """Use training dates by default so held-out patterns do not guide model choices."""
    settings = config["eda"]
    split = settings["split"]
    if split not in ("train", "val", "test"):
        raise ValueError("EDA split must be train, val or test.")
    bounds = get_split_boundaries(config)
    frame = sales.loc[sales.date.between(bounds[f"{split}_start"], bounds[f"{split}_end"])].copy()
    clean = frame.loc[frame.record_status.eq("clean")]
    if clean.empty:
        raise ValueError("EDA requires clean observed training rows.")
    output.mkdir(parents=True, exist_ok=True)
    plots = {}

    def save(name, fig):
        path = output / settings["figures"][name]
        fig.tight_layout()
        fig.savefig(path, dpi=settings["dpi"])
        plt.close(fig)
        plots[name] = path.name

    def axes():
        return plt.subplots(figsize=settings["figure_size"])

    fig, ax = axes()
    weekly = clean.groupby("day_of_week").sales.mean().reindex(range(7))
    weekly.plot.bar(ax=ax)
    ax.set(
        xlabel="Weekday (Monday=0)",
        ylabel="Clean units per item/day",
        title=f"Weekly sales pattern — {split}",
    )
    save("weekly", fig)
    fig, ax = axes()
    clean = clean.assign(festival_group="ordinary")
    clean.loc[
        clean.days_to_next_festival.between(1, config["data"]["festival_pre_days"]),
        "festival_group",
    ] = "before festival"
    clean.loc[clean.festival_flag.eq(1), "festival_group"] = "festival day"
    festival = clean.groupby("festival_group").sales.agg(["mean", "count"])
    festival["mean"].plot.bar(ax=ax, rot=0)
    ax.set(
        ylabel="Clean units per item/day",
        title=f"Festival groups — {split}; descriptive, not causal",
    )
    save("festival", fig)
    fig, axs = plt.subplots(1, 2, figsize=(settings["figure_size"][0], settings["figure_size"][1]))
    cold = clean.loc[clean.item.isin(config["quality"]["cold_items"])].copy()
    cold["temperature_group"] = cold.temp_max.ge(
        config["quality"]["hot_temperature_threshold"]
    ).map({True: "hot", False: "normal"})
    if cold.empty:
        axs[0].text(0.5, 0.5, "No matching clean cold items", ha="center")
    else:
        cold.groupby("temperature_group").sales.mean().plot.bar(ax=axs[0], rot=0)
    rainy = clean.loc[clean.item.isin(config["quality"]["rain_items"])]
    if rainy.empty:
        axs[1].text(0.5, 0.5, "No matching clean rain-sensitive items", ha="center")
    else:
        rainy.groupby("rain_flag").sales.mean().rename(index={0: "dry", 1: "rainy"}).plot.bar(
            ax=axs[1], rot=0
        )
    axs[0].set(title="Cold drinks by temperature", ylabel="Clean units per item/day")
    axs[1].set(title="Chocolate/chai by rain", ylabel="Clean units per item/day")
    save("weather", fig)
    fig, ax = axes()
    daily = clean.groupby("date").sales.mean()
    daily.plot(ax=ax, alpha=0.25, label="daily clean mean")
    daily.rolling(settings["trend_window"], min_periods=1).mean().plot(
        ax=ax, label=f"{settings['trend_window']}-day descriptive mean"
    )
    ax.set(ylabel="Clean units per item/day", title=f"Observed trend — {split}")
    ax.legend()
    save("trend", fig)
    fig, ax = axes()
    stockouts = frame.record_status.eq("stockout").groupby(frame.item).mean().sort_values()
    stockouts.plot.bar(ax=ax)
    ax.set(ylabel="Exclusive stockout fraction", title=f"Censored rows by item — {split}")
    save("stockouts", fig)
    return {
        "split": split,
        "rows": len(frame),
        "clean_rows": len(clean),
        "start_date": frame.date.min().strftime("%Y-%m-%d"),
        "end_date": frame.date.max().strftime("%Y-%m-%d"),
        "weekly_clean_mean": {str(k): float(v) for k, v in weekly.items()},
        "festival_groups": festival.to_dict(orient="index"),
        "stockout_fraction_by_item": stockouts.to_dict(),
        "figures": plots,
        "limitations": "Synthetic sales; historical realized weather; group differences are confounded. EDA uses train dates by default.",
    }


def run_phase_2(config: dict[str, Any]) -> dict[str, Any]:
    """Stage feature exports, manifest and EDA reports without changing source datasets."""
    assert_no_truth_references(config)
    sales = load_sales(config)
    dataset = build_features(sales, config)
    root = resolve_path(config, "pipeline_staging").resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        staging = Path(directory)
        if not staging.resolve().is_relative_to(root):
            raise ValueError("Staging escaped its root.")
        summary = create_eda(sales, config, staging / "figures")
        files = []
        for key, value in (
            ("features_csv", dataset.frame.to_csv(index=False)),
            (
                "feature_manifest",
                json.dumps(
                    {
                        "feature_columns": dataset.feature_columns,
                        "categorical_columns": ["item", "category"],
                        "metadata_columns": [
                            column
                            for column in dataset.frame
                            if column not in dataset.feature_columns
                        ],
                        "weather_policy": config["features"]["weather_policy"],
                        "target_policy": config["features"]["censored_target_policy"],
                        "temporal_contract": "One-day-ahead; all observed inputs strictly before target date. Future lags require recursive predictions.",
                    },
                    indent=2,
                )
                + "\n",
            ),
            ("eda_summary", json.dumps(summary, indent=2) + "\n"),
        ):
            path = staging / key
            path.write_text(value, encoding="utf-8")
            files.append((path, resolve_path(config, key)))
        report = [
            "# Phase 2 exploratory data analysis",
            "",
            f"Scope: {summary['split']}, {summary['start_date']} to {summary['end_date']}.",
            f"Rows: {summary['rows']}; clean rows: {summary['clean_rows']}.",
            summary["limitations"],
            "",
            "Plots use observed weather for descriptive EDA only. Forecast predictors use lagged persistence weather.",
            "Rolling trend lines here summarize observations; they are not model predictors.",
            "Historical feature exports are for rolling one-day-ahead evaluation. Fixed-origin multi-day evaluation must use build_prediction_features and recursive predictions.",
            "",
            "## Plots",
            "",
        ]
        for name, filename in summary["figures"].items():
            report += [f"### {name}", "", f"![{name}](figures/{filename})", ""]
            files.append(
                (staging / "figures" / filename, resolve_path(config, "figures") / filename)
            )
        path = staging / "report.md"
        path.write_text("\n".join(report), encoding="utf-8")
        files.append((path, resolve_path(config, "eda_report")))
        publish_artifacts(files)
    counts = (
        dataset.frame.groupby("split")
        .agg(rows=("target", "size"), eligible_targets=("target_eligible", "sum"))
        .to_dict(orient="index")
    )
    result = {
        "rows": len(dataset.frame),
        "predictors": len(dataset.feature_columns),
        "split_counts": counts,
        "eda": summary,
    }
    print(json.dumps(result, indent=2))
    return result
