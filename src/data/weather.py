"""Swappable daily weather providers with validated, explicit provenance."""

import hashlib
import json
import logging
from typing import Any
import numpy as np
import pandas as pd
import requests
from src.utils.config import resolve_path

LOGGER = logging.getLogger(__name__)
WEATHER_COLUMNS = ["date", "temp_max", "temp_min", "rainfall", "rain_flag", "weather_source"]


def validate_weather(frame: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Reject incomplete, duplicate, missing or physically inconsistent weather."""
    if not set(WEATHER_COLUMNS).issubset(frame.columns):
        raise ValueError("Weather is missing required columns.")
    result = frame[WEATHER_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    if result["date"].duplicated().any() or set(result["date"]) != set(dates):
        raise ValueError("Weather must cover every requested date exactly once.")
    result = result.sort_values("date").reset_index(drop=True)
    numeric = result[["temp_max", "temp_min", "rainfall", "rain_flag"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Weather contains missing or nonfinite numeric values.")
    if (result["temp_min"] > result["temp_max"]).any() or (result["rainfall"] < 0).any():
        raise ValueError("Weather has invalid temperatures or negative rainfall.")
    if not result["rain_flag"].isin([0, 1]).all():
        raise ValueError("rain_flag must be binary.")
    if result["weather_source"].isna().any() or result["weather_source"].eq("").any():
        raise ValueError("Weather source must be recorded.")
    result["rain_flag"] = result["rain_flag"].astype(int)
    return result


def synthetic_weather(dates: pd.DatetimeIndex, config: dict[str, Any]) -> pd.DataFrame:
    """Generate reproducible seasonal temperatures and intermittent monsoon rainfall."""
    settings = config["weather"]
    # A separate configured stream prevents sales RNG changes from changing weather.
    rng = np.random.default_rng(
        np.random.SeedSequence([config["project"]["seed"], settings["random_stream"]])
    )
    phase = (
        2
        * np.pi
        * (dates.dayofyear.to_numpy() - settings["temperature_peak_day"])
        / settings["year_days"]
    )
    temp_max = settings["base_temp_max"] + settings["temperature_amplitude"] * np.cos(phase)
    temp_max += rng.normal(0, settings["temperature_noise_std"], len(dates))
    spread = rng.normal(settings["diurnal_spread"], settings["diurnal_spread_std"], len(dates))
    temp_min = temp_max - np.maximum(settings["min_diurnal_spread"], spread)
    monsoon = dates.month.isin(settings["monsoon_months"])
    probability = np.where(
        monsoon, settings["monsoon_rain_probability"], settings["dry_rain_probability"]
    )
    rainfall = rng.gamma(settings["rain_gamma_shape"], settings["rain_gamma_scale"], len(dates))
    rainfall *= rng.random(len(dates)) < probability
    frame = pd.DataFrame(
        {
            "date": dates,
            "temp_max": np.round(temp_max, settings["decimals"]),
            "temp_min": np.round(temp_min, settings["decimals"]),
            "rainfall": np.round(rainfall, settings["decimals"]),
            "weather_source": "synthetic",
        }
    )
    frame["rain_flag"] = (frame["rainfall"] >= settings["rain_threshold_mm"]).astype(int)
    return validate_weather(frame, dates)


def open_meteo_weather(dates: pd.DatetimeIndex, config: dict[str, Any]) -> pd.DataFrame:
    """Fetch historical reanalysis; this is not an archived day-ahead forecast."""
    response = requests.get(
        config["weather"]["archive_url"],
        params={
            "latitude": config["data"]["latitude"],
            "longitude": config["data"]["longitude"],
            "start_date": dates.min().strftime("%Y-%m-%d"),
            "end_date": dates.max().strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": config["project"]["timezone"],
            "temperature_unit": "celsius",
            "precipitation_unit": "mm",
        },
        timeout=config["data"]["weather_timeout_seconds"],
    )
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Open-Meteo response has no daily weather mapping.")
    frame = pd.DataFrame(
        {
            "date": daily.get("time", []),
            "temp_max": daily.get("temperature_2m_max", []),
            "temp_min": daily.get("temperature_2m_min", []),
            "rainfall": daily.get("precipitation_sum", []),
            "weather_source": "open_meteo",
        }
    )
    frame["rain_flag"] = (frame["rainfall"] >= config["weather"]["rain_threshold_mm"]).astype(int)
    return validate_weather(frame[frame["date"].isin(dates.strftime("%Y-%m-%d"))], dates)


def weather_cache_key(dates: pd.DatetimeIndex, config: dict[str, Any]) -> str:
    """Fingerprint provider inputs so an incompatible cache is never reused."""
    payload = {
        "start": str(dates.min()),
        "end": str(dates.max()),
        "count": len(dates),
        "seed": config["project"]["seed"],
        "weather": config["weather"],
        "provider": config["data"]["weather_provider"],
        "latitude": config["data"]["latitude"],
        "longitude": config["data"]["longitude"],
        "timezone": config["project"]["timezone"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def get_weather(dates: pd.DatetimeIndex, config: dict[str, Any]) -> pd.DataFrame:
    """Reuse only a compatible source; auto always retries a synthetic fallback."""
    provider = config["data"]["weather_provider"]
    if provider not in {"synthetic", "open_meteo", "auto"}:
        raise ValueError("weather_provider must be synthetic, open_meteo or auto.")
    cache, metadata = (
        resolve_path(config, "weather_cache"),
        resolve_path(config, "weather_metadata"),
    )
    if config["weather"]["cache_enabled"] and cache.exists() and metadata.exists():
        try:
            meta = json.loads(metadata.read_text(encoding="utf-8"))
            source = meta["source"]
            # Backward compatibility for the original metadata's one-element list.
            if isinstance(source, list):
                source = source[0] if len(source) == 1 else None
            allowed = {"synthetic"} if provider == "synthetic" else {"open_meteo"}
            if meta["cache_key"] == weather_cache_key(dates, config) and source in allowed:
                cached = validate_weather(pd.read_csv(cache), dates)
                if set(cached["weather_source"]) == {source}:
                    return cached
            if provider == "auto" and source in {"synthetic", "synthetic_fallback"}:
                LOGGER.info(
                    "Cached synthetic fallback is not a successful auto cache; retrying API."
                )
        except (ValueError, KeyError, TypeError):
            LOGGER.warning("Ignoring an invalid weather cache.")
    if provider == "synthetic":
        return synthetic_weather(dates, config)
    try:
        return open_meteo_weather(dates, config)
    except (requests.RequestException, ValueError, TypeError) as error:
        if provider == "open_meteo":
            raise
        LOGGER.warning(
            "Historical weather unavailable (%s); using seeded synthetic fallback.",
            type(error).__name__,
        )
        fallback = synthetic_weather(dates, config)
        fallback["weather_source"] = "synthetic_fallback"
        return fallback
