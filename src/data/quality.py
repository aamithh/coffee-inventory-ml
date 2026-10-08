"""Auditable data contracts, measured summaries and machine-readable field descriptions."""

import json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from src.data.calendar_features import daily_dates
from src.utils.config import resolve_path
from src.utils.dates import date_context

FIELD_DETAILS = {
    "date": ("date", "Local sales day; one row per date/item.", "day", "known calendar"),
    "item": ("string", "Editable menu identifier.", "", "known in advance"),
    "category": ("string", "Menu category.", "", "known in advance"),
    "price": (
        "float",
        "Planned selling price, including promotion discount.",
        "INR/sale",
        "known in advance",
    ),
    "promo_flag": (
        "int",
        "This item is the selected promotion for this day.",
        "0/1",
        "planned in advance",
    ),
    "sales": (
        "nullable float",
        "Observed units sold; censored on stockouts, may contain POS errors.",
        "items",
        "after day ends; target",
    ),
    "stockout_flag": (
        "int",
        "Realized item demand exceeded the simulated sales cap.",
        "0/1",
        "after day ends; target-quality metadata",
    ),
    "closure_flag": (
        "int",
        "Shop was closed; observed and latent demand set to zero.",
        "0/1",
        "after day ends; metadata",
    ),
    "missing_flag": (
        "int",
        "Observed sales was deliberately made missing.",
        "0/1",
        "after day ends; metadata",
    ),
    "outlier_flag": (
        "int",
        "Injected POS over-recording error, not latent customer demand.",
        "0/1",
        "after day ends; metadata",
    ),
    "day_of_week": ("int", "Monday=0 through Sunday=6.", "", "known calendar"),
    "weekend_flag": ("int", "Configured weekend weekday.", "0/1", "known calendar"),
    "day_of_month": ("int", "Day number within month.", "day", "known calendar"),
    "week_of_year": ("int", "ISO week number.", "week", "known calendar"),
    "month": ("int", "Calendar month number.", "month", "known calendar"),
    "month_end_flag": ("int", "Final day of the calendar month.", "0/1", "known calendar"),
    "holiday_flag": (
        "int",
        "India/Karnataka holiday from the pinned holidays package.",
        "0/1",
        "known calendar",
    ),
    "holiday_name": ("string", "Holiday name or empty string.", "", "known calendar"),
    "festival_flag": ("int", "Configured shop-relevant festival date.", "0/1", "known calendar"),
    "festival_name": ("string", "Configured festival name or empty string.", "", "known calendar"),
    "days_to_next_festival": (
        "int",
        "Days to next configured festival; zero on event day.",
        "days",
        "known calendar",
    ),
    "days_since_last_festival": (
        "int",
        "Days since last configured festival; zero on event day.",
        "days",
        "known calendar",
    ),
    "payday_flag": ("int", "First/last configured days of a month.", "0/1", "known calendar"),
    "long_weekend_flag": (
        "int",
        "Part of a consecutive holiday/weekend run of configured length.",
        "0/1",
        "known calendar",
    ),
    "temp_max": (
        "float",
        "Daily maximum temperature.",
        "degrees C",
        "synthetic proxy or historical reanalysis",
    ),
    "temp_min": (
        "float",
        "Daily minimum temperature.",
        "degrees C",
        "synthetic proxy or historical reanalysis",
    ),
    "rainfall": (
        "float",
        "Daily precipitation; treated as rain in this demo.",
        "mm",
        "synthetic proxy or historical reanalysis",
    ),
    "rain_flag": (
        "int",
        "Precipitation meets configured threshold.",
        "0/1",
        "same availability as weather",
    ),
    "weather_source": (
        "string",
        "synthetic or open_meteo; source is retained.",
        "",
        "provider metadata",
    ),
}
FIELD_DETAILS.update(
    {
        "record_status": (
            "string",
            "Single precedence: closed > missing > stockout > outlier > clean.",
            "",
            "after day ends; target-quality metadata",
        ),
        "usable_for_training": (
            "bool",
            "Clean rows, plus stockouts only when explicitly configured.",
            "true/false",
            "after day ends; target eligibility, never a predictor",
        ),
    }
)
TRUTH_DETAILS = {
    "date": FIELD_DETAILS["date"],
    "item": FIELD_DETAILS["item"],
    "latent_demand": (
        "int",
        "Uncapped realized customer demand; zero on closure days.",
        "items",
        "oracle; simulation evaluation only",
    ),
    "expected_demand": (
        "float",
        "Generator mean before demand noise; zero on closure days.",
        "items",
        "oracle; data diagnostics only",
    ),
}


TRUTH_DETAILS.update(
    {
        "expected_demand_without_shop_shock": (
            "float",
            "Mean demand excluding the shared shock; residual diagnostic only.",
            "items",
            "oracle; never training",
        ),
        "shop_daily_multiplier": (
            "float",
            "Same mean-one daily lognormal draw across all items.",
            "multiplier",
            "oracle; never training",
        ),
    }
)


def apply_record_status(sales: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Preserve raw flags while assigning exactly one status by explicit precedence."""
    result = sales.copy()
    result["record_status"] = np.select(
        [
            result["closure_flag"].eq(1),
            result["missing_flag"].eq(1),
            result["stockout_flag"].eq(1),
            result["outlier_flag"].eq(1),
        ],
        ["closed", "missing", "stockout", "outlier"],
        default="clean",
    )
    eligible = result["record_status"].eq("clean")
    if config["generator"]["record_status"]["allow_stockout_for_training"]:
        eligible |= result["record_status"].eq("stockout")
    result["usable_for_training"] = eligible.astype(bool)
    return result


def assert_no_truth_references(config: dict[str, Any]) -> None:
    """Fail on conservative source-text references in configured training folders."""
    from src.utils.config import PROJECT_ROOT

    blocked = list(config["leakage_guard"]["blocked_symbols"])
    blocked += [str(config["paths"]["truth_database"]), str(resolve_path(config, "truth_database"))]
    for location in config["leakage_guard"]["protected_folders"]:
        folder = Path(location)
        folder = folder if folder.is_absolute() else PROJECT_ROOT / folder
        if not folder.is_dir():
            raise ValueError(f"Leakage guard folder does not exist: {folder}")
        for source in sorted(folder.rglob("*.py")):
            text = source.read_text(encoding="utf-8").replace(chr(92), "/").lower()
            matches = [token for token in blocked if token.replace(chr(92), "/").lower() in text]
            if matches:
                raise ValueError(f"Simulation truth leakage reference in {source}: {matches}")


def reconcile_sales(sales: pd.DataFrame, truth: pd.DataFrame) -> dict[str, int]:
    """Allocate each row once: latent - observed = stockout + missing - outlier excess."""
    merged = sales[["date", "item", "sales", "record_status"]].merge(
        truth[["date", "item", "latent_demand"]], on=["date", "item"], validate="one_to_one"
    )
    stockout = merged["record_status"].eq("stockout")
    missing = merged["record_status"].eq("missing")
    outlier = merged["record_status"].eq("outlier")
    latent = int(merged["latent_demand"].sum())
    observed = int(merged["sales"].sum())
    stockout_loss = int(
        (merged.loc[stockout, "latent_demand"] - merged.loc[stockout, "sales"]).sum()
    )
    missing_loss = int(merged.loc[missing, "latent_demand"].sum())
    outlier_excess = int(
        (merged.loc[outlier, "sales"] - merged.loc[outlier, "latent_demand"]).sum()
    )
    unexplained = latent - observed - stockout_loss - missing_loss + outlier_excess
    if unexplained != 0:
        raise ValueError(f"Sales reconciliation failed by {unexplained} units.")
    return {
        "latent_units": latent,
        "observed_units": observed,
        "gap": latent - observed,
        "stockout_loss": stockout_loss,
        "missing_loss": missing_loss,
        "outlier_excess": outlier_excess,
        "unexplained_gap": unexplained,
    }


def residual_correlation(truth: pd.DataFrame) -> float | None:
    """Measure cross-item correlation after removing known non-shock mean effects."""
    frame = truth.loc[truth["expected_demand_without_shop_shock"].gt(0)].copy()
    frame["residual"] = frame["latent_demand"] / frame["expected_demand_without_shop_shock"] - 1
    matrix = frame.pivot(index="date", columns="item", values="residual").corr().to_numpy()
    pairs = matrix[np.triu_indices_from(matrix, k=1)]
    pairs = pairs[np.isfinite(pairs)]
    return float(pairs.mean()) if len(pairs) else None


def weather_effects(sales: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
    """Describe actual clean-row group means; these are not causal effect estimates."""
    clean = sales.loc[sales["record_status"].eq("clean")]
    results = {}
    cold_items = config["quality"]["cold_items"]
    rain_items = config["quality"]["rain_items"]
    for item in cold_items + rain_items:
        frame = clean.loc[clean["item"].eq(item)]
        condition = (
            frame["temp_max"].ge(config["quality"]["hot_temperature_threshold"])
            if item in cold_items
            else frame["rain_flag"].eq(1)
        )
        first, second = ("hot", "normal") if item in cold_items else ("rainy", "dry")
        results[item] = {
            f"{first}_mean": _mean_or_none(frame.loc[condition, "sales"]),
            f"{second}_mean": _mean_or_none(frame.loc[~condition, "sales"]),
            f"{first}_rows": int(condition.sum()),
            f"{second}_rows": int((~condition).sum()),
        }
    return results


def validate_sales(sales: pd.DataFrame, config: dict[str, Any]) -> None:
    """Fail structural violations while retaining explicitly marked imperfections."""
    missing_columns = set(FIELD_DETAILS) - set(sales.columns)
    if missing_columns:
        raise ValueError(f"Missing sales fields: {sorted(missing_columns)}")
    if {"latent_demand", "expected_demand"} & set(sales.columns):
        raise ValueError("Oracle demand must not be present in observed sales.")
    dates = daily_dates(config)
    if sales["date"].isna().any():
        raise ValueError("Invalid sales dates.")
    if sales.duplicated(["date", "item"]).any():
        raise ValueError("Duplicate date/item sales rows.")
    expected = pd.MultiIndex.from_product([dates, list(config["menu"])], names=["date", "item"])
    actual = pd.MultiIndex.from_frame(sales[["date", "item"]])
    if len(sales) != len(expected) or not expected.difference(actual).empty:
        raise ValueError("Sales must contain every configured date/item pair exactly once.")
    numeric = sales["sales"].dropna().to_numpy(dtype=float)
    if (
        not np.isfinite(numeric).all()
        or (numeric < 0).any()
        or not np.equal(numeric, np.floor(numeric)).all()
    ):
        raise ValueError("Observed sales must be missing or finite nonnegative whole units.")
    if sales["sales"].isna().ne(sales["record_status"].eq("missing")).any():
        raise ValueError("Missing sales must match missing_flag.")
    for flag in [column for column in sales if column.endswith("_flag")]:
        if not sales[flag].isin([0, 1]).all():
            raise ValueError(f"{flag} must be binary.")
    if not np.isfinite(sales["price"].to_numpy(dtype=float)).all() or (sales["price"] <= 0).any():
        raise ValueError("Prices must be finite and positive.")
    expected_categories = sales["item"].map(
        {item: value["category"] for item, value in config["menu"].items()}
    )
    if sales["category"].ne(expected_categories).any():
        raise ValueError("Item categories must match menu configuration.")
    closed = sales["closure_flag"].eq(1)
    if sales.loc[closed, "sales"].ne(0).any():
        raise ValueError("Closure days must have zero observed sales.")
    derived = apply_record_status(sales, config)
    if not sales["record_status"].equals(derived["record_status"]):
        raise ValueError("record_status violates configured precedence.")
    if not pd.api.types.is_bool_dtype(sales["usable_for_training"]) or not sales[
        "usable_for_training"
    ].equals(derived["usable_for_training"]):
        raise ValueError("usable_for_training violates the eligibility rule.")
    if (sales.groupby("date")["closure_flag"].nunique() != 1).any():
        raise ValueError("Shop closures must apply to all items.")


def validate_truth(truth: pd.DataFrame, sales: pd.DataFrame) -> None:
    """Validate oracle alignment before persistence; never merge it into training sales."""
    if not set(TRUTH_DETAILS).issubset(truth):
        raise ValueError("Truth table is missing required fields.")
    pairs = pd.MultiIndex.from_frame(truth[["date", "item"]])
    public_pairs = pd.MultiIndex.from_frame(sales[["date", "item"]])
    if (
        pairs.has_duplicates
        or len(pairs) != len(public_pairs)
        or not public_pairs.difference(pairs).empty
    ):
        raise ValueError("Truth must align one-to-one with observed date/item rows.")
    values = truth[["latent_demand", "expected_demand"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Truth demand must be finite and nonnegative.")
    if truth["latent_demand"].ne(np.floor(truth["latent_demand"])).any():
        raise ValueError("Latent demand must contain whole units.")
    joined = sales[["date", "item", "closure_flag"]].merge(truth, on=["date", "item"])
    if (
        joined.loc[joined["closure_flag"].eq(1), ["latent_demand", "expected_demand"]]
        .to_numpy()
        .any()
    ):
        raise ValueError("Closure demand must be zero.")


def _mean_or_none(values: pd.Series) -> float | None:
    """Represent unavailable means as null rather than invalid JSON NaN."""
    return float(values.mean()) if values.notna().any() else None


def _ratio_or_none(numerator: float | None, denominator: float | None) -> float | None:
    """Keep summaries honest when no clean weekday observations exist."""
    return (
        numerator / denominator
        if numerator is not None and denominator is not None and denominator > 0
        else None
    )


def data_summary(
    sales: pd.DataFrame,
    truth: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Summarize actual generated data; exclude corrupted/censored rows from pattern means."""
    validate_sales(sales, config)
    validate_truth(truth, sales)
    clean = sales.loc[sales["record_status"].eq("clean")]
    statuses = sales["record_status"].value_counts().to_dict()
    mean_weekday = _mean_or_none(clean.loc[clean["weekend_flag"].eq(0), "sales"])
    mean_weekend = _mean_or_none(clean.loc[clean["weekend_flag"].eq(1), "sales"])
    per_item = []
    for item, frame in sales.groupby("item", sort=True):
        valid = clean.loc[clean["item"].eq(item)]
        weekday = _mean_or_none(valid.loc[valid["weekend_flag"].eq(0), "sales"])
        weekend = _mean_or_none(valid.loc[valid["weekend_flag"].eq(1), "sales"])
        per_item.append(
            {
                "item": item,
                "observed_units": int(frame["sales"].sum()),
                "promo_days": int(frame["promo_flag"].sum()),
                "mean_daily_sales": _mean_or_none(frame["sales"]),
                "missing_rows": int(frame["record_status"].eq("missing").sum()),
                "stockout_rows": int(frame["record_status"].eq("stockout").sum()),
                "clean_weekend_weekday_ratio": _ratio_or_none(weekend, weekday),
            }
        )
    source = sorted(sales["weather_source"].unique().tolist())
    return {
        "rows": len(sales),
        "days": sales["date"].nunique(),
        "items": sales["item"].nunique(),
        "start_date": sales["date"].min().strftime("%Y-%m-%d"),
        "end_date": sales["date"].max().strftime("%Y-%m-%d"),
        "weather_source": source,
        "observed_units_including_pos_outliers": int(sales["sales"].sum()),
        "latent_units": int(truth["latent_demand"].sum()),
        "missing_rows": int(statuses.get("missing", 0)),
        "outlier_rows": int(statuses.get("outlier", 0)),
        "stockout_rows": int(statuses.get("stockout", 0)),
        "closure_days": int(sales.loc[sales["closure_flag"].eq(1), "date"].nunique()),
        "promotion_days": int(sales.loc[sales["promo_flag"].eq(1), "date"].nunique()),
        "promotion_day_fraction": sales.loc[sales["promo_flag"].eq(1), "date"].nunique()
        / sales["date"].nunique(),
        "festival_days": int(sales.loc[sales["festival_flag"].eq(1), "date"].nunique()),
        "clean_weekday_mean": mean_weekday,
        "clean_weekend_mean": mean_weekend,
        "clean_weekend_weekday_ratio": _ratio_or_none(mean_weekend, mean_weekday),
        "per_item": per_item,
        "record_status_counts": {
            status: int(statuses.get(status, 0))
            for status in ("closed", "missing", "stockout", "outlier", "clean")
        },
        "usable_for_training_rows": int(sales["usable_for_training"].sum()),
        "date_context": date_context(config),
        "reconciliation": reconcile_sales(sales, truth),
        "weather_effects_clean": weather_effects(sales, config),
        "cross_item_residual_correlation": residual_correlation(truth),
        "notes": [
            "Observed total retains injected POS over-recording errors and omits missing sales.",
            "Pattern means exclude closures, missing, stockout and POS outlier rows.",
            "Latent and expected demand are isolated oracle data, unavailable to the sales loader.",
            "Historical reanalysis weather is a proxy; it is not known day-ahead forecast weather.",
        ],
    }


def write_data_dictionary(config: dict[str, Any]) -> None:
    """Save public and oracle field contracts as Markdown and JSON."""
    rows = [
        "# Data dictionary",
        "",
        "One observed row per local date/item; daily fields repeat across items.",
        "",
        "Weather values use Celsius and mm. No oracle column belongs in model inputs.",
        "",
    ]
    document = {}
    for table, fields in (("sales", FIELD_DETAILS), ("simulation_truth", TRUTH_DETAILS)):
        rows += [
            f"## {table}",
            "",
            "| Field | Type | Meaning | Unit | Availability |",
            "|---|---|---|---|---|",
        ]
        document[table] = {}
        for field, (dtype, meaning, unit, availability) in fields.items():
            rows.append(f"| {field} | {dtype} | {meaning} | {unit} | {availability} |")
            document[table][field] = {
                "type": dtype,
                "description": meaning,
                "unit": unit,
                "availability": availability,
            }
        rows.append("")
    rows += [
        "simulation_truth is in the separate configured truth_database SQLite file, never the observed database.",
        "Raw quality flags may overlap; reports count record_status exactly once using closed > missing > stockout > outlier > clean.",
        "usable_for_training is metadata for filtering targets, never a feature.",
        "Missing-priority reconciliation assigns all latent demand on missing rows to missing loss, including any hidden stockout loss.",
        "project.as_of_date and forecast_horizon_days define the demo date; split/drift dates are reported, not oracle predictors.",
        "",
        "## Other observed-database SQLite tables",
        "",
        "- calendar: one row/day, calendar fields above.",
        "- weather: one row/day, weather fields above.",
        "- menu: item, category, base_demand (items/day), price (INR/sale).",
        "- materials: material, unit, shelf_life_days, lead_time_days, unit_cost (INR/unit), min_order_qty (units), wastage_factor (fraction).",
        "- recipes: item, material, quantity (material units/sale).",
        "",
    ]
    for key, content in (
        ("data_dictionary", "\n".join(rows)),
        ("data_dictionary_json", json.dumps(document, indent=2) + "\n"),
    ):
        path = resolve_path(config, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def write_quality_report(summary: dict[str, Any], config: dict[str, Any]) -> None:
    """Persist readable statistics computed from the current generated dataset."""
    rows = [
        "# Phase 1.5 data-quality report",
        "",
        f"Range: {summary['start_date']} to {summary['end_date']}.",
        f"Rows: **{summary['rows']:,}**; days: **{summary['days']:,}**; items: **{summary['items']}**.",
        f"Weather source: {', '.join(summary['weather_source'])}.",
        "",
        "| Check | Measured result |",
        "|---|---:|",
        "| Duplicate or missing date/item pairs | 0 (validated) |",
        "| Negative, nonfinite, or fractional observed sales | 0 (validated) |",
        f"| Missing sales | {summary['missing_rows']} |",
        f"| Injected POS outliers | {summary['outlier_rows']} |",
        f"| Realized stockout rows | {summary['stockout_rows']} |",
        f"| Shop closure days | {summary['closure_days']} |",
        f"| Promotion days | {summary['promotion_days']} ({summary['promotion_day_fraction']:.2%}) |",
        f"| Configured festival days | {summary['festival_days']} |",
        f"| Recorded sales sum (includes POS outliers) | {summary['observed_units_including_pos_outliers']:,} |",
        f"| Uncapped latent demand sum (oracle) | {summary['latent_units']:,} |",
        "",
        "## Observed seasonality",
        "",
        "Pattern means exclude missing, closure, stockout and injected outlier rows.",
        f"Weekday mean per item/day: {summary['clean_weekday_mean']}.",
        f"Weekend mean per item/day: {summary['clean_weekend_mean']}.",
        f"Weekend/weekday ratio: {summary['clean_weekend_weekday_ratio']}.",
        "",
        "| Item | Recorded units | Mean/day | Missing | Stockouts | Clean weekend/weekday |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summary["per_item"]:
        mean = item["mean_daily_sales"]
        ratio = item["clean_weekend_weekday_ratio"]
        mean_text = f"{mean:.2f}" if mean is not None else "unavailable"
        ratio_text = f"{ratio:.3f}" if ratio is not None else "unavailable"
        rows.append(
            f"| {item['item']} | {item['observed_units']:,} | {mean_text} | "
            f"{item['missing_rows']} | {item['stockout_rows']} | {ratio_text} |"
        )
    rows += ["", "## Exclusive record status", "", "| Status | Rows |", "|---|---:|"]
    rows += [f"| {status} | {count} |" for status, count in summary["record_status_counts"].items()]
    rows += [
        f"Training-eligible rows: {summary['usable_for_training_rows']}.",
        "",
        "## As-of, splits and drift",
        "",
    ]
    rows += [f"- {key}: {value}" for key, value in summary["date_context"].items()]
    rows += ["", "## Reconciliation (mutually exclusive status priority)", ""]
    rows += [f"- {key}: {value}" for key, value in summary["reconciliation"].items()]
    rows += [
        "",
        "## Clean-row weather comparisons",
        "",
        "Descriptive means; seasonality, promotions, trend and drift can confound these groups.",
    ]
    rows += [f"- {item}: {values}" for item, values in summary["weather_effects_clean"].items()]
    rows += [
        f"Cross-item normalized residual correlation: {summary['cross_item_residual_correlation']}.",
        "",
        "## Interpretation and limits",
        "",
    ]
    rows += [f"- {note}" for note in summary["notes"]]
    rows += [
        "- These are synthetic sales with real or synthetic weather, not observations from a real shop.",
        "- Observed and latent totals need not match: censoring, missing sales and POS errors act differently.",
        "- Raw weather/festival group comparisons are confounded; controlled effect tests hold other inputs fixed.",
        "- No model accuracy, inventory-policy benefit or forecasting leakage test is claimed in Phase 1.",
        "",
        "## Sources",
        "",
        "- [Open-Meteo historical weather documentation](https://open-meteo.com/en/docs/historical-weather-api)",
        "- [India holiday documentation](https://holidays.readthedocs.io/en/latest/auto_gen_docs/india/)",
        "",
    ]
    path = resolve_path(config, "data_report")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows), encoding="utf-8")
