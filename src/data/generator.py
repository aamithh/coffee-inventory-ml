"""Configurable synthetic demand, observed sales and isolated simulation truth."""

import argparse
import json
import hashlib
from pathlib import Path
import tempfile
import sqlite3
from contextlib import closing
import logging
from typing import Any
import numpy as np
import pandas as pd
from src.data.calendar_features import build_calendar, daily_dates
from src.data.loader import save_dataset
from src.data.artifacts import staged_config, publish_artifacts
from src.data.quality import (
    apply_record_status,
    assert_no_truth_references,
    data_summary,
    validate_sales,
    write_data_dictionary,
    write_quality_report,
)
from src.data.weather import get_weather, validate_weather, weather_cache_key
from src.utils.config import PROJECT_ROOT, load_config, resolve_path
from src.utils.dates import get_drift_start_date, validate_forecast_calendar


def item_rng(item_id: str, random_stream: int, config: dict[str, Any]) -> np.random.Generator:
    """Use SHA-256 rather than process-randomized hash or menu position."""
    identity = int.from_bytes(hashlib.sha256(item_id.encode("utf-8")).digest(), "big")
    return np.random.default_rng(
        np.random.SeedSequence([config["project"]["seed"], random_stream, identity])
    )


def promotion_schedule(
    dates: pd.DatetimeIndex, config: dict[str, Any]
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Use a fixed spillover peer universe to keep existing items stable on menu additions."""
    settings = config["generator"]["promotions"]
    peers = settings["peer_item_ids"]
    universe = sorted(set(peers) | set(config["menu"]))
    if settings["mode"] == "per_item":
        promotions = {
            item: item_rng(item, settings["random_stream"], config).random(len(dates))
            < settings["per_item_probability"]
            for item in universe
        }
    else:
        rng = np.random.default_rng(
            np.random.SeedSequence([config["project"]["seed"], settings["random_stream"]])
        )
        active = rng.random(len(dates)) < config["data"]["promotion_probability"]
        selected = rng.integers(0, len(peers), len(dates))
        promotions = {
            item: active & (selected == peers.index(item))
            if item in peers
            else np.zeros(len(dates), dtype=bool)
            for item in universe
        }
    any_promo = np.any(np.stack([promotions[item] for item in peers]), axis=0)
    return promotions, any_promo


def shop_daily_shock(dates: pd.DatetimeIndex, config: dict[str, Any]) -> np.ndarray:
    """Draw a single shared multiplier/day; negative log-mean keeps expectation one."""
    settings = config["generator"]["shop_daily_shock"]
    rng = np.random.default_rng(
        np.random.SeedSequence([config["project"]["seed"], settings["random_stream"]])
    )
    sigma = settings["sigma"]
    return rng.lognormal(mean=-(sigma**2) / 2, sigma=sigma, size=len(dates))


def validate_generator_settings(config: dict[str, Any]) -> None:
    """Reject probabilities, dimensions and demand parameters that cannot be simulated."""
    settings = config["data"]
    extra = config["generator"]
    promotions = extra["promotions"]
    if promotions["mode"] not in {"shop_day", "per_item"}:
        raise ValueError("generator.promotions.mode must be shop_day or per_item.")
    if not 0 <= promotions["per_item_probability"] <= 1:
        raise ValueError("Per-item promotion probability must be between zero and one.")
    if not promotions["peer_item_ids"] or len(set(promotions["peer_item_ids"])) != len(
        promotions["peer_item_ids"]
    ):
        raise ValueError("Promotion peers must be nonempty and unique.")
    if (
        not np.isfinite(extra["shop_daily_shock"]["sigma"])
        or extra["shop_daily_shock"]["sigma"] < 0
    ):
        raise ValueError("Shop shock sigma must be finite and nonnegative.")
    for key in (
        "promotion_probability",
        "stockout_probability",
        "missing_probability",
        "outlier_probability",
        "closure_probability",
    ):
        if not 0 <= settings[key] <= 1:
            raise ValueError(f"{key} must be between 0 and 1.")
    if settings["noise_dispersion"] <= 0 or settings["drift_duration_days"] <= 0:
        raise ValueError("Dispersion and drift duration must be positive.")
    if len(settings["weekday_factors"]) != 7:
        raise ValueError("weekday_factors must have 7 entries.")
    if not 0 < settings["stockout_cap_min"] <= settings["stockout_cap_max"] <= 1:
        raise ValueError("Stockout capacity fractions must satisfy 0 < min <= max <= 1.")
    if not 0 <= settings["promotion_discount"] < 1:
        raise ValueError("promotion_discount must be in [0, 1).")
    for name, profile in config["demand_profiles"].items():
        if len(profile["monthly_factors"]) != 12 or min(profile["monthly_factors"]) <= 0:
            raise ValueError(f"Invalid monthly factors for {name}.")
    for name, item in config["menu"].items():
        if item["base_demand"] <= 0 or item["price"] <= 0:
            raise ValueError(f"Demand and price must be positive for {name}.")
        if item["category"] not in config["demand_profiles"]:
            raise ValueError(f"Missing demand profile for {name}.")


def expected_demand(
    item: str,
    daily: pd.DataFrame,
    promo: np.ndarray,
    any_promo: np.ndarray,
    config: dict[str, Any],
) -> np.ndarray:
    """Compute uncapped mean demand; return oracle values only to the generator."""
    settings = config["data"]
    menu_item = config["menu"][item]
    profile = {
        **config["demand_profiles"][menu_item["category"]],
        **config["item_effects"].get(item, {}),
    }
    dates = pd.DatetimeIndex(daily["date"])
    elapsed = (dates - pd.Timestamp(settings["start_date"])).days.to_numpy()
    trend = 1 + settings["annual_trend"] * elapsed / config["weather"]["year_days"]
    drift_elapsed = (dates - get_drift_start_date(config)).days.to_numpy()
    drift = 1 + settings["drift_lift"] * np.clip(
        drift_elapsed / settings["drift_duration_days"], 0, 1
    )
    weekly = np.asarray(settings["weekday_factors"])[dates.dayofweek]
    weekend_lift = (
        settings["cold_bakery_weekend_lift"]
        if menu_item["category"] in settings["high_weekend_categories"]
        else settings["weekend_lift"]
    )
    weekly *= np.where(daily["weekend_flag"], weekend_lift, 1)
    monthly = np.asarray(profile["monthly_factors"])[dates.month - 1]
    temperature = np.exp(
        profile["temperature_coefficient"]
        * (daily["temp_max"].to_numpy() - config["weather"]["demand_reference_temp"])
    )
    rain = np.where(daily["rain_flag"], profile["rain_lift"], 1)
    festival = np.where(
        daily["festival_flag"],
        settings["festival_day_factor"],
        np.where(
            (daily["days_to_next_festival"] > 0)
            & (daily["days_to_next_festival"] <= settings["festival_pre_days"]),
            settings["festival_pre_lift"],
            np.where(daily["holiday_flag"], settings["other_holiday_factor"], 1),
        ),
    )
    promotion = np.where(
        promo,
        settings["promotion_lift"],
        np.where(any_promo, settings["cannibalization_factor"], 1),
    )
    mean = menu_item["base_demand"] * trend * drift * weekly * monthly * temperature * rain
    mean *= festival * promotion
    mean *= np.where(daily["payday_flag"], settings["payday_lift"], 1)
    mean *= np.where(daily["long_weekend_flag"], settings["long_weekend_lift"], 1)
    if not np.isfinite(mean).all() or (mean < 0).any():
        raise ValueError("Configured effects produced invalid mean demand.")
    return mean


def generate_dataset(
    config: dict[str, Any],
    weather: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return sales, oracle truth, calendar and weather as separate typed tables."""
    validate_generator_settings(config)
    dates = daily_dates(config)
    calendar = build_calendar(dates, config)
    weather = get_weather(dates, config) if weather is None else validate_weather(weather, dates)
    daily = calendar.merge(weather, on="date", validate="one_to_one")
    settings = config["data"]
    scheduling = np.random.default_rng(
        np.random.SeedSequence([config["project"]["seed"], settings["random_stream"]])
    )
    promotions, any_promo = promotion_schedule(dates, config)
    shock = shop_daily_shock(dates, config)
    closed = scheduling.random(len(dates)) < settings["closure_probability"]
    sales_frames, truth_frames = [], []
    for item, properties in config["menu"].items():
        rng = item_rng(item, config["generator"]["item_random_stream"], config)
        promo = promotions[item]
        mean_without_shock = expected_demand(item, daily, promo, any_promo, config)
        mean = mean_without_shock * shock
        dispersion = settings["noise_dispersion"]
        demand = rng.negative_binomial(dispersion, dispersion / (dispersion + mean))
        demand[closed] = 0
        candidate = (rng.random(len(dates)) < settings["stockout_probability"]) & ~closed
        capacity = np.floor(
            demand
            * rng.uniform(settings["stockout_cap_min"], settings["stockout_cap_max"], len(dates))
        ).astype(int)
        stockout = candidate & (capacity < demand)
        observed = np.where(stockout, capacity, demand).astype(float)
        # Outliers are POS recording errors, not extra latent customer demand.
        outlier = (
            (rng.random(len(dates)) < settings["outlier_probability"])
            & ~closed
            & ~stockout
            & (observed > 0)
        )
        multiplier = rng.uniform(
            settings["outlier_multiplier_min"], settings["outlier_multiplier_max"], len(dates)
        )
        observed[outlier] = np.round(observed[outlier] * multiplier[outlier])
        missing = (rng.random(len(dates)) < settings["missing_probability"]) & ~closed
        observed[missing] = np.nan
        frame = daily.copy()
        frame["item"] = item
        frame["category"] = properties["category"]
        frame["price"] = np.where(
            promo, properties["price"] * (1 - settings["promotion_discount"]), properties["price"]
        )
        frame["promo_flag"] = promo.astype(int)
        frame["sales"] = observed
        frame["stockout_flag"] = stockout.astype(int)
        frame["closure_flag"] = closed.astype(int)
        frame["missing_flag"] = missing.astype(int)
        frame["outlier_flag"] = outlier.astype(int)
        sales_frames.append(frame)
        truth_frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "item": item,
                    "latent_demand": demand,
                    "expected_demand": np.where(closed, 0, mean),
                    "expected_demand_without_shop_shock": np.where(closed, 0, mean_without_shock),
                    "shop_daily_multiplier": shock,
                }
            )
        )
    sales = (
        pd.concat(sales_frames, ignore_index=True)
        .sort_values(["date", "item"])
        .reset_index(drop=True)
    )
    truth = (
        pd.concat(truth_frames, ignore_index=True)
        .sort_values(["date", "item"])
        .reset_index(drop=True)
    )
    sales = apply_record_status(sales, config)
    validate_sales(sales, config)
    return sales, truth, calendar, weather


def _persist_artifacts(
    config: dict[str, Any], dataset: tuple[pd.DataFrame, ...], summary: dict[str, Any]
) -> None:
    """Write to staged paths; this function does not publish to live targets."""
    sales, truth, calendar, weather = dataset
    save_dataset(sales, truth, calendar, weather, config)
    for key, frame in (
        ("sales_csv", sales),
        ("truth_csv", truth),
        ("calendar_csv", calendar),
        ("weather_cache", weather),
    ):
        path = resolve_path(config, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False, date_format="%Y-%m-%d")
    metadata = resolve_path(config, "weather_metadata")
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(
        json.dumps(
            {
                "cache_key": weather_cache_key(pd.DatetimeIndex(calendar["date"]), config),
                "source": summary["weather_source"][0],
                "requested_provider": config["data"]["weather_provider"],
                "note": "Historical reanalysis is not an archived operational forecast.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary_path = resolve_path(config, "data_summary")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    sample_path = resolve_path(config, "sales_sample")
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    sales.head(config["data"]["sample_rows"]).to_csv(sample_path, index=False)
    write_data_dictionary(config)
    write_quality_report(summary, config)


def run_pipeline(config: dict[str, Any]) -> dict[str, Any]:
    """Validate staged outputs before publication, preserving old files on failures."""
    logger = logging.getLogger(__name__)
    source, succeeded = "unresolved", False
    print(
        f"Pipeline start; requested weather provider: {config['data']['weather_provider']}",
        flush=True,
    )
    if "onedrive" in str(PROJECT_ROOT.resolve()).lower():
        warning = (
            f"OneDrive warning: {PROJECT_ROOT}. Use a non-synced location such as "
            f"{config['sqlite']['non_synced_example']}, exclude data/processed from sync, "
            f"or set {config['sqlite']['directory_env_variable']}. SQLite uses DELETE journaling."
        )
        print(warning, flush=True)
        logger.warning(warning)
    try:
        validate_generator_settings(config)
        validate_forecast_calendar(config)
        assert_no_truth_references(config)
        weather = get_weather(daily_dates(config), config)
        source = weather["weather_source"].iloc[0]
        print(f"Weather source (start): {source}", flush=True)
        logger.info("Weather source (start): %s", source)
        dataset = generate_dataset(config, weather)
        summary = data_summary(*dataset[:2], config)
        keys = (
            "database",
            "truth_database",
            "sales_csv",
            "truth_csv",
            "calendar_csv",
            "weather_cache",
            "weather_metadata",
            "data_summary",
            "sales_sample",
            "data_dictionary",
            "data_dictionary_json",
            "data_report",
        )
        staging_root = resolve_path(config, "pipeline_staging").resolve()
        staging_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=staging_root) as directory:
            staging = Path(directory).resolve()
            if not staging.is_relative_to(staging_root):
                raise ValueError("Staging directory escaped its configured root.")
            staged = staged_config(config, staging, keys)
            # Clone existing databases to preserve unrelated tables without touching live outputs.
            for key in ("database", "truth_database"):
                original, snapshot = resolve_path(config, key).resolve(), resolve_path(staged, key)
                if original.exists():
                    snapshot.parent.mkdir(parents=True, exist_ok=True)
                    with closing(
                        sqlite3.connect(original.as_uri() + "?mode=ro", uri=True)
                    ) as source_db:
                        with closing(sqlite3.connect(snapshot)) as target_db:
                            source_db.backup(target_db)
            _persist_artifacts(staged, dataset, summary)
            from src.data.loader import load_sales
            from src.data.truth_loader import load_truth

            validate_sales(load_sales(staged), staged)
            from src.data.quality import validate_truth

            validate_truth(load_truth(staged), dataset[0])
            publish_artifacts(
                [(resolve_path(staged, key), resolve_path(config, key)) for key in keys]
            )
        succeeded = True
        return summary
    finally:
        print(
            f"Weather source (end): {source}; pipeline {'succeeded' if succeeded else 'failed'}",
            flush=True,
        )
        logger.info(
            "Weather source (end): %s; pipeline %s", source, "succeeded" if succeeded else "failed"
        )


def main() -> None:
    """Run the reproducible data stage from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="Optional YAML configuration path.")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_pipeline(load_config(arguments.config))
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
