"""Time-aware model fitting, sealed test evaluation and staged artifact publication."""

from itertools import product
import json
from pathlib import Path
import tempfile
from typing import Any
import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from src.data.artifacts import publish_artifacts
from src.data.loader import load_sales
from src.data.quality import assert_no_truth_references
from src.features.build_features import build_features
from src.models.baselines import BASELINES, baseline_predictions
from src.models.estimators import fit_bundle
from src.models.evaluate import (
    clean_scoring_rows,
    metric_table,
    ordered_quantiles,
    walk_forward_splits,
)
from src.models.explain import contributions, explain_prediction
from src.models.predict import recursive_forecast
from src.utils.config import resolve_path
from src.utils.dates import get_as_of_date, get_split_boundaries
from src.utils.metrics import forecast_metrics


def tune_lightgbm(
    frame: pd.DataFrame, columns: list[str], config: dict[str, Any]
) -> tuple[dict, pd.DataFrame]:
    """Search train-only expanding folds; compare pooled absolute error, not shuffled CV."""
    tuning = config["models"]["tuning"]
    candidates = [dict(zip(tuning, values)) for values in product(*tuning.values())]
    if config["validation"]["walk_forward_folds"] < 5:
        raise ValueError("Use at least five walk-forward folds.")
    records = []
    for candidate_id, parameters in enumerate(candidates):
        for fold, (training, validation) in enumerate(
            walk_forward_splits(frame, config["validation"]["walk_forward_folds"]), 1
        ):
            fitted = fit_bundle("lightgbm", frame.loc[training], columns, config, parameters)
            scored = clean_scoring_rows(frame.loc[validation])
            metrics = forecast_metrics(scored.target, fitted.predict(scored))
            records.append(
                {
                    "model": "lightgbm",
                    "candidate": candidate_id,
                    "parameters": json.dumps(parameters, sort_keys=True),
                    "fold": fold,
                    "train_end": fitted.trained_through,
                    "validation_start": scored.date.min().strftime("%Y-%m-%d"),
                    "validation_end": scored.date.max().strftime("%Y-%m-%d"),
                    "absolute_error": metrics["mae"] * metrics["rows"],
                    "actual_units": float(scored.target.sum()),
                    **metrics,
                }
            )
        print(
            f"CV candidate {candidate_id + 1}/{len(candidates)} complete: {parameters}", flush=True
        )
    for fold, (training, validation) in enumerate(
        walk_forward_splits(frame, config["validation"]["walk_forward_folds"]), 1
    ):
        reference = fit_bundle("ridge", frame.loc[training], columns, config)
        scored = clean_scoring_rows(frame.loc[validation])
        predictions = {"ridge": reference.predict(scored)}
        predictions.update(
            {name: baseline_predictions(scored, name, reference, config) for name in BASELINES}
        )
        for name, values in predictions.items():
            metrics = forecast_metrics(scored.target, values)
            records.append(
                {
                    "model": name,
                    "candidate": -1,
                    "parameters": "{}",
                    "fold": fold,
                    "train_end": reference.trained_through,
                    "validation_start": scored.date.min().strftime("%Y-%m-%d"),
                    "validation_end": scored.date.max().strftime("%Y-%m-%d"),
                    "absolute_error": metrics["mae"] * metrics["rows"],
                    "actual_units": float(scored.target.sum()),
                    **metrics,
                }
            )
    result = pd.DataFrame(records)
    totals = (
        result.loc[result.model.eq("lightgbm")]
        .groupby("candidate")[["absolute_error", "actual_units"]]
        .sum()
    )
    best = int((totals.absolute_error / totals.actual_units).idxmin())
    return candidates[best], result


def evaluate_recursive(
    artifact: dict, sales: pd.DataFrame, config: dict[str, Any], boundaries: dict
) -> pd.DataFrame:
    """Weekly fixed origins with a frozen model; score only future clean actual counts."""
    horizon = config["project"]["forecast_horizon_days"]
    origins = pd.date_range(
        boundaries["test_start"],
        boundaries["test_end"] - pd.Timedelta(days=horizon - 1),
        freq=f"{config['models']['recursive_origin_stride']}D",
    )
    outputs = []
    for index, origin in enumerate(origins):
        history = sales.loc[sales.date.lt(origin)]
        plans = sales.loc[sales.date.between(origin, origin + pd.Timedelta(days=horizon - 1))]
        actual = plans.loc[plans.record_status.eq("clean"), ["date", "item", "sales"]]
        for name in (artifact["selected_point"], "seasonal_naive"):
            forecast = recursive_forecast(artifact, history, plans, origin, config, name)
            joined = forecast.merge(actual, on=["date", "item"], validate="one_to_one")
            joined["model"] = name
            outputs.append(joined)
        if (index + 1) % config["models"]["recursive_progress_every"] == 0:
            print(f"Recursive test origins {index + 1}/{len(origins)} complete", flush=True)
    predictions = pd.concat(outputs, ignore_index=True)
    records = []
    for (name, horizon_day), rows in predictions.groupby(["model", "horizon_day"]):
        records.append(
            {
                "model": name,
                "horizon_day": int(horizon_day),
                **forecast_metrics(
                    rows.sales,
                    rows.forecast,
                    **({"lower": rows.p10, "upper": rows.p90} if name != "seasonal_naive" else {}),
                ),
            }
        )
    for name, rows in predictions.groupby("model"):
        records.append(
            {
                "model": name,
                "horizon_day": "overall",
                **forecast_metrics(
                    rows.sales,
                    rows.forecast,
                    **({"lower": rows.p10, "upper": rows.p90} if name != "seasonal_naive" else {}),
                ),
            }
        )
    return pd.DataFrame(records)


def run_training(config: dict[str, Any]) -> dict:
    """Select on validation, freeze decisions, then evaluate and persist honest test results."""
    if config["models"]["enable_sarimax"]:
        raise NotImplementedError(
            "SARIMAX is an optional stretch; disable it for the required model suite."
        )
    if config["features"]["weather_policy"] != "persistence":
        raise ValueError(
            "Historical training runner requires persistence weather; timestamped forecasts are supported by prediction interfaces."
        )
    if config["models"]["quantiles"] != [0.1, 0.5, 0.9]:
        raise ValueError("The interval contract requires configured quantiles [0.1,0.5,0.9].")
    assert_no_truth_references(config)
    sales = load_sales(config)
    dataset = build_features(sales, config)
    frame, columns = dataset.frame, dataset.feature_columns
    train = frame.loc[frame.split.eq("train")]
    val = clean_scoring_rows(frame.loc[frame.split.eq("val")])
    parameters, cv = tune_lightgbm(train, columns, config)
    validation_models = {
        name: fit_bundle(name, train, columns, config, parameters)
        for name in config["models"]["point_candidates"]
    }
    reference = validation_models["ridge"]
    validation_predictions = {name: model.predict(val) for name, model in validation_models.items()}
    validation_predictions.update(
        {name: baseline_predictions(val, name, reference, config) for name in BASELINES}
    )
    validation_table = metric_table(val, validation_predictions)
    ml_scores = {
        name: forecast_metrics(val.target, predictions)["wape"]
        for name, predictions in validation_predictions.items()
        if name in validation_models
    }
    selected = min(ml_scores, key=ml_scores.get)
    print(f"Validation ML point selection: {selected}; WAPE={ml_scores[selected]:.6f}", flush=True)
    refit = frame.loc[frame.split.isin(["train", "val"])]
    models = {
        name: fit_bundle(name, refit, columns, config, parameters) for name in validation_models
    }
    quantiles = [
        fit_bundle("lightgbm", refit, columns, config, parameters, q)
        for q in config["models"]["quantiles"]
    ]
    artifact = {
        "schema_version": 1,
        "selected_point": selected,
        "point_models": models,
        "quantile_models": quantiles,
        "feature_columns": columns,
        "parameters": parameters,
        "trained_through": models[selected].trained_through,
        "seed": config["project"]["seed"],
    }
    test = clean_scoring_rows(frame.loc[frame.split.eq("test")])
    test_predictions = {name: model.predict(test) for name, model in models.items()}
    test_predictions.update(
        {name: baseline_predictions(test, name, models["ridge"], config) for name in BASELINES}
    )
    raw = np.column_stack([model.predict(test) for model in quantiles])
    intervals, crossings = ordered_quantiles(raw)
    test_predictions["quantile_p50"] = intervals[:, 1]
    table = metric_table(test, test_predictions, intervals[:, 0], intervals[:, 2])
    overall = table.loc[table.item.eq("overall")].set_index("model")
    improvement = 1 - float(overall.loc[selected, "wape"]) / float(
        overall.loc["seasonal_naive", "wape"]
    )
    boundaries = get_split_boundaries(config)
    recursive = evaluate_recursive(artifact, sales, config, boundaries)
    origin = get_as_of_date(config)
    if origin <= pd.Timestamp(artifact["trained_through"]):
        raise ValueError("Demo as-of must follow the saved model training cutoff.")
    end = origin + pd.Timedelta(days=config["project"]["forecast_horizon_days"] - 1)
    plans = sales.loc[
        sales.date.between(origin, end), ["date", "item", "category", "price", "promo_flag"]
    ]
    if plans.date.nunique() != config["project"]["forecast_horizon_days"]:
        raise ValueError("Demo plans must cover the configured forecast horizon.")
    demo = recursive_forecast(artifact, sales.loc[sales.date.lt(origin)], plans, origin, config)
    summary = {
        "selected_point_model": selected,
        "selection": "validation WAPE after train-only five-fold tuning",
        "best_parameters": parameters,
        "training_through": artifact["trained_through"],
        "test_rows": len(test),
        "one_day_test_metrics": overall.reset_index()
        .replace({np.nan: None})
        .to_dict(orient="records"),
        "relative_wape_improvement": improvement,
        "required_wape_improvement": config["models"]["required_wape_improvement"],
        "meets_requested_improvement": bool(
            improvement >= config["models"]["required_wape_improvement"]
        ),
        "raw_quantile_crossings": crossings,
        "nominal_interval_coverage": 0.8,
        "recursive_test_metrics": recursive.replace({np.nan: None}).to_dict(orient="records"),
        "limitations": [
            "Synthetic shop data; no real-shop generalization claim.",
            "Persistence weather is less informative than future realized weather, deliberately excluded.",
            "One-day scores use earlier observed test history; recursive scores use predictions.",
            "Quantile intervals are empirical and uncalibrated; recursive uncertainty is conditional on a predicted history path.",
            "Cold-start point forecasts use past category means; quantile fallback uses training-category empirical quantiles.",
            "SHAP drivers are model associations, not causal effects.",
        ],
    }
    root = resolve_path(config, "pipeline_staging").resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        stage = Path(directory)
        if not stage.resolve().is_relative_to(root):
            raise ValueError("Staging escaped its configured root.")
        pairs = []

        def write(key, content):
            path = stage / key
            path.write_text(content, encoding="utf-8", newline="")
            pairs.append((path, resolve_path(config, key)))

        path = stage / "bundle.joblib"
        joblib.dump(artifact, path)
        # Verify portable artifact predictions before publishing.
        restored = joblib.load(path)
        np.testing.assert_allclose(
            restored["point_models"][selected].predict(test), test_predictions[selected]
        )
        pairs.append((path, resolve_path(config, "model_bundle")))
        write(
            "model_metadata",
            json.dumps(
                {
                    "feature_columns": columns,
                    "categorical": ["item", "category"],
                    "trained_through": artifact["trained_through"],
                    "selected_point": selected,
                    "parameters": parameters,
                    "seed": config["project"]["seed"],
                    "weather_policy": "persistence",
                },
                indent=2,
            )
            + "\n",
        )
        write("metrics", json.dumps(summary, indent=2, allow_nan=False) + "\n")
        write(
            "model_metrics_csv",
            pd.concat(
                [validation_table.assign(split="validation"), table.assign(split="test")]
            ).to_csv(index=False),
        )
        predictions = test[["date", "item", "target"]].copy()
        for name, values in test_predictions.items():
            predictions[name] = values
        predictions[["p10", "p50", "p90"]] = intervals
        write("model_predictions", predictions.to_csv(index=False))
        write("model_cv_results", cv.to_csv(index=False))
        write("model_recursive_metrics", recursive.to_csv(index=False))
        write("demo_forecast", demo.to_csv(index=False))
        explanation = explain_prediction(
            models[selected], test.iloc[:1], config["models"]["explanation_top_n"]
        )
        write("model_explanation", json.dumps(explanation, indent=2) + "\n")
        figure_dir = stage / "figures"
        figure_dir.mkdir()
        fig, ax = plt.subplots(figsize=config["eda"]["figure_size"])
        overall.wape.sort_values().plot.bar(ax=ax)
        ax.set(ylabel="WAPE (fraction)", title="Clean test targets — rolling one-day-ahead")
        fig.tight_layout()
        fig.savefig(figure_dir / config["model_figures"]["comparison"], dpi=config["eda"]["dpi"])
        plt.close(fig)
        top_item = refit.groupby("item").target.sum().idxmax()
        sample = predictions.loc[predictions.item.eq(top_item)]
        fig, ax = plt.subplots(figsize=config["eda"]["figure_size"])
        ax.plot(sample.date, sample.target, label="observed clean target", alpha=0.65)
        ax.plot(sample.date, sample[selected], label=selected)
        ax.fill_between(sample.date, sample.p10, sample.p90, alpha=0.2, label="LightGBM P10-P90")
        ax.set(title=f"{top_item}: clean test targets and empirical intervals", ylabel="Units/day")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figure_dir / config["model_figures"]["intervals"], dpi=config["eda"]["dpi"])
        plt.close(fig)
        explanation_rows = test.sample(
            n=min(len(test), config["models"]["shap_sample_rows"]),
            random_state=config["project"]["seed"],
        )
        values, base, transformed, names = contributions(models["lightgbm"], explanation_rows)
        shap.summary_plot(
            values,
            transformed,
            feature_names=names,
            show=False,
            max_display=config["models"]["shap_max_display"],
            rng=np.random.default_rng(config["project"]["seed"]),
        )
        plt.tight_layout()
        plt.savefig(
            figure_dir / config["model_figures"]["shap"],
            dpi=config["eda"]["dpi"],
            bbox_inches="tight",
        )
        plt.close()
        for filename in config["model_figures"].values():
            pairs.append((figure_dir / filename, resolve_path(config, "figures") / filename))
        report = [
            "# Phase 3 modeling results",
            "",
            f"Selected on validation: **{selected}**. Saved model trained through {artifact['trained_through']}.",
            f"Clean one-day test rows: {len(test)}.",
            f"Relative WAPE improvement over seasonal naive: {improvement:.2%}; requested 15% achieved: {summary['meets_requested_improvement']}.",
            "",
            "## Overall clean test metrics",
            "",
            "| Model | WAPE | MAE | RMSE | Bias | Coverage |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for name, row in overall.iterrows():
            coverage = (
                f"{row.interval_coverage:.3f}" if pd.notna(row.get("interval_coverage")) else "n/a"
            )
            report.append(
                f"| {name} | {row.wape:.4f} | {row.mae:.3f} | {row.rmse:.3f} | {row.bias:.3f} | {coverage} |"
            )
        report += [
            "",
            "Full per-item and validation metrics: model_metrics.csv.",
            "Train-only expanding fold results and parameters: walk_forward.csv.",
            "Fixed-origin horizon metrics: recursive_metrics.csv.",
            "",
            "## Interpretation",
            "",
            "Baseline errors contain day-to-day count noise. ML combines known calendar/promotion effects and smoother prior history.",
            "The shared daily shock, count noise, drift and imperfect persistence weather remain unpredictable components.",
            "All model/parameter decisions were frozen before test scoring. No test-driven tuning or generator changes were made.",
            f"Raw quantile crossing rows: {crossings}; crossings are repaired by sorting and coverage measured afterward.",
            "",
            "## Limits",
            "",
            *["- " + note for note in summary["limitations"]],
            "",
            "## Charts",
            "",
        ]
        for filename in config["model_figures"].values():
            report += [f"![{filename}](figures/{filename})", ""]
        write("model_report", "\n".join(report))
        publish_artifacts(pairs)
    print(json.dumps(summary, indent=2), flush=True)
    return summary
