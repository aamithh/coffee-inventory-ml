# Progress

## Phase 1.5 changelog — complete (2026-10-07)
- Backed up 11 original CSV/database/configuration/documentation artifacts to data/processed/backup_pre_1_5.
- Hardening shared shocks, promotions, stable seeds, weather recovery, dates, statuses, truth isolation, SQLite safety and Windows commands.
- All 79 tests pass; two validated pipeline runs match CSV and database-content hashes.
- Truth is isolated in simulation_truth.db; Windows CLI and database override are verified.
- 2027 lunar festival extension remains an explicit guarded TODO. Current results through Phase 8 are recorded below.

## Dashboard presentation refresh — complete (2026-10-08)

- Introduced Brew & Balance branding, warm café colors, clear summary cards and simple navigation.
- Added homepage shortcuts, readable chart/table labels, compact shopping lists and expandable technical details.
- Improved phone layout and fixed the stock editor to load the selected ingredient quantities.
- All 219 tests passed, including two new dashboard interaction checks; Ruff lint/63-file formatting and pip checks passed.
- Reviewed desktop (1280x900) and phone (390x844); phone page width equals viewport width.
- All 42 original data/model/figure/notebook hashes, persistent inventory and 11 backup hashes remain unchanged.
- The initial verifier reached the mobile screenshot check before that capture was saved. The subsequent targeted image audit passed; complete original output and continuation are retained below and in reports/dashboard_redesign_verification.txt.
- Dashboard remains available locally on port 8501.

```text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 32%]
........................................................................ [ 65%]
........................................................................ [ 98%]
...                                                                      [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:37
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\starlette\testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

.venv\Lib\site-packages\matplotlib\_mathtext.py:45
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
219 passed, 15 warnings in 182.97s (0:03:02)
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
63 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
Live dashboard CLI: HTTP 200 health=ok
Live dashboard root: HTTP 200; Streamlit application shell available
Live dashboard output (complete):

  You can now view your Streamlit app in your browser.

  URL: http://127.0.0.1:50069

Seven screens, stock forms, conflicts, what-if and shopping shortcut: PASS
Selected ingredient loads its own stock quantities: PASS
Protected feature/model source reference scan: PASS
Original data/model/figure/notebook hashes unchanged: 42 files PASS
Persistent demo inventory unchanged: PASS
Pre-1.5 backups: 11 hashes unchanged PASS
Browser review capture: redesign_desktop.jpg; valid image (66104 bytes)
Traceback (most recent call last):
  File "C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\src\verification\dashboard_redesign.py", line 62, in main
    with Image.open(path) as image:
         ^^^^^^^^^^^^^^^^
  File "C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\PIL\Image.py", line 3513, in open
    fp = builtins.open(filename, "rb")
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\aamit\\OneDrive\\Desktop\\ProjectX\\coffee-inventory-ml\\reports\\dashboard_screenshots\\redesign_mobile.jpg'

Continuation: the first screenshot check ran before the mobile capture was saved.
Completed screenshot audit after browser review (tests and lint were already successful):
Browser review capture: redesign_desktop.jpg; valid image 1280x900 (66104 bytes) PASS
Browser review capture: redesign_mobile.jpg; valid image 390x843 (27347 bytes) PASS
Mobile browser review: viewport=390; pageWidth=390; no horizontal page overflow PASS
Targeted screenshot audit exit_code=0
All required checks completed; no verification step skipped.
```

## Phase 8 — complete (2026-10-08)

- Replaced stale incremental README text with final setup/usage, architecture
  diagram, module responsibilities, measured results and operational limitations.
- Completed docs/report.md with problem, data, leakage/validation methods,
  forecast results, inventory formulas, FIFO results, economics and future work.
- Added exactly six slides in docs/slide_outline.md and a timed four-minute
  demo script in docs/demo_script.md; updated assumptions/dashboard guidance.
- Added a final verification runner. Full suite: 217 passed, 15 dependency
  deprecation warnings. Ruff lint, 62-file format check and pip check pass.
- Rebuilt all 1,096 configured dates, four tuning candidates/five folds,
  inventory and all 165 simulation dates into empty temporary output paths.
  The validated weather cache was the only copied input; models/forecasts/replay
  were regenerated. Model selection/WAPE and every policy summary match saved results.
- Verified real API/dashboard CLI startup, forecast/material/order/metrics/scenario
  responses, invalid-horizon validation, Swagger and OpenAPI; stopped process trees.
- Fixed verifier-only empty schema-directory and Windows child-log cleanup
  issues discovered by the first attempt. Its complete output is retained in
  reports/phase_8_attempt_1.txt. The final rerun passed.
- Saved executed notebooks pass schema/no-error checks. All 42 original data,
  model, figure and notebook files plus eleven pre-1.5 backups retain their hashes.
- All 22 direct dependency pins match installed versions; document links/UTF-8
  checks pass. Six-slide and 3–5 minute demo requirements are satisfied.
- Final results remain LightGBM WAPE 21.49% vs seasonal 28.91% (25.65% improvement).
  ML waste cost is 96.14% lower than manual, but lost units are 81.50% higher;
  the 0.205% gross-cost advantage reverses under full terminal stock credit.
- Existing Windows venv/wrapper and approved local checks were used. Fresh pip
  installation and GNU Make execution were not independently verified;
  README gives the exact fresh setup/Make commands. No required final check
  remains blocked by sandbox restrictions. No paid/external verification service.
- Full final output is below and in reports/phase_8_verification.txt.
- STOP: all requested phases complete. No additional phase started.

### Full Phase 8 verification output

~~~text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
.                                                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:37
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\starlette\testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

.venv\Lib\site-packages\matplotlib\_mathtext.py:45
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
217 passed, 15 warnings in 211.93s (0:03:31)
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
62 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
Isolated workflow: full configured history/grid; empty sales/model/replay outputs
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task setup-check --config C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\data\processed\.pipeline_staging\final_workflow_4se2pm2o\config.yaml
No broken requirements found.
Python: 3.11.9
Executable: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe
Virtual environment: True
Required library imports: 17 OK
{
  "train_start": "2023-01-01",
  "train_end": "2025-02-05",
  "val_start": "2025-02-06",
  "val_end": "2025-07-19",
  "test_start": "2025-07-20",
  "test_end": "2025-12-31",
  "as_of_date": "2025-07-20",
  "forecast_horizon_days": 7,
  "calendar_required_through": "2025-07-27",
  "drift_start": "2025-02-06",
  "drift_plateau_date": "2025-08-05",
  "drift_start_split": "val",
  "drift_ramp_overlap_days": {
    "train": 0,
    "val": 164,
    "test": 16
  },
  "drift_appears_in_test": true,
  "test_contains_shifted_demand": true,
  "split_rule": "floor(train*n), floor(validation*n), remainder to test; never shuffle"
}
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task data --config C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\data\processed\.pipeline_staging\final_workflow_4se2pm2o\config.yaml
Pipeline start; requested weather provider: auto
OneDrive warning: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml. Use a non-synced location such as C:/dev/coffee-inventory-ml, exclude data/processed from sync, or set COFFEE_DB_DIR. SQLite uses DELETE journaling.
Weather source (start): open_meteo
Weather source (end): open_meteo; pipeline succeeded
{
  "rows": 10960,
  "days": 1096,
  "items": 10,
  "start_date": "2023-01-01",
  "end_date": "2025-12-31",
  "weather_source": [
    "open_meteo"
  ],
  "observed_units_including_pos_outliers": 484112,
  "latent_units": 484775,
  "missing_rows": 56,
  "outlier_rows": 67,
  "stockout_rows": 266,
  "closure_days": 9,
  "promotion_days": 511,
  "promotion_day_fraction": 0.46624087591240876,
  "festival_days": 15,
  "clean_weekday_mean": 42.30460921843687,
  "clean_weekend_mean": 50.6588785046729,
  "clean_weekend_weekday_ratio": 1.197478937651908,
  "per_item": [
    {
      "item": "americano",
      "observed_units": 39398,
      "promo_days": 74,
      "mean_daily_sales": 36.21139705882353,
      "missing_rows": 8,
      "stockout_rows": 28,
      "clean_weekend_weekday_ratio": 1.1264682552233236
    },
    {
      "item": "cappuccino",
      "observed_units": 60688,
      "promo_days": 69,
      "mean_daily_sales": 55.67706422018349,
      "missing_rows": 6,
      "stockout_rows": 24,
      "clean_weekend_weekday_ratio": 1.1571453571694508
    },
    {
      "item": "cold_coffee",
      "observed_units": 56560,
      "promo_days": 77,
      "mean_daily_sales": 51.70018281535649,
      "missing_rows": 2,
      "stockout_rows": 20,
      "clean_weekend_weekday_ratio": 1.3188158517311015
    },
    {
      "item": "croissant",
      "observed_units": 35408,
      "promo_days": 59,
      "mean_daily_sales": 32.51423324150597,
      "missing_rows": 7,
      "stockout_rows": 28,
      "clean_weekend_weekday_ratio": 1.307461352657005
    },
    {
      "item": "espresso",
      "observed_units": 56862,
      "promo_days": 66,
      "mean_daily_sales": 52.31094756209752,
      "missing_rows": 9,
      "stockout_rows": 27,
      "clean_weekend_weekday_ratio": 1.1505844161615086
    },
    {
      "item": "hot_chocolate",
      "observed_units": 29307,
      "promo_days": 84,
      "mean_daily_sales": 26.788848263254113,
      "missing_rows": 2,
      "stockout_rows": 32,
      "clean_weekend_weekday_ratio": 1.1739135548449495
    },
    {
      "item": "iced_latte",
      "observed_units": 42621,
      "promo_days": 69,
      "mean_daily_sales": 39.065994500458295,
      "missing_rows": 5,
      "stockout_rows": 31,
      "clean_weekend_weekday_ratio": 1.3290241920077412
    },
    {
      "item": "latte",
      "observed_units": 67302,
      "promo_days": 61,
      "mean_daily_sales": 61.63186813186813,
      "missing_rows": 4,
      "stockout_rows": 20,
      "clean_weekend_weekday_ratio": 1.157015586444655
    },
    {
      "item": "masala_chai",
      "observed_units": 57639,
      "promo_days": 56,
      "mean_daily_sales": 52.97702205882353,
      "missing_rows": 8,
      "stockout_rows": 25,
      "clean_weekend_weekday_ratio": 1.1694708717943545
    },
    {
      "item": "sandwich",
      "observed_units": 38327,
      "promo_days": 72,
      "mean_daily_sales": 35.13015582034831,
      "missing_rows": 5,
      "stockout_rows": 31,
      "clean_weekend_weekday_ratio": 1.1397682749201115
    }
  ],
  "record_status_counts": {
    "closed": 90,
    "missing": 56,
    "stockout": 266,
    "outlier": 67,
    "clean": 10481
  },
  "usable_for_training_rows": 10481,
  "date_context": {
    "train_start": "2023-01-01",
    "train_end": "2025-02-05",
    "val_start": "2025-02-06",
    "val_end": "2025-07-19",
    "test_start": "2025-07-20",
    "test_end": "2025-12-31",
    "as_of_date": "2025-07-20",
    "forecast_horizon_days": 7,
    "calendar_required_through": "2025-07-27",
    "drift_start": "2025-02-06",
    "drift_plateau_date": "2025-08-05",
    "drift_start_split": "val",
    "drift_ramp_overlap_days": {
      "train": 0,
      "val": 164,
      "test": 16
    },
    "drift_appears_in_test": true,
    "test_contains_shifted_demand": true,
    "split_rule": "floor(train*n), floor(validation*n), remainder to test; never shuffle"
  },
  "reconciliation": {
    "latent_units": 484775,
    "observed_units": 484112,
    "gap": 663,
    "stockout_loss": 5020,
    "missing_loss": 2420,
    "outlier_excess": 6777,
    "unexplained_gap": 0
  },
  "weather_effects_clean": {
    "cold_coffee": {
      "hot_mean": 66.72881355932203,
      "normal_mean": 44.34893617021277,
      "hot_rows": 354,
      "normal_rows": 705
    },
    "iced_latte": {
      "hot_mean": 49.68604651162791,
      "normal_mean": 34.19027181688126,
      "hot_rows": 344,
      "normal_rows": 699
    },
    "hot_chocolate": {
      "rainy_mean": 31.311377245508982,
      "dry_mean": 23.111721611721613,
      "rainy_rows": 501,
      "dry_rows": 546
    },
    "masala_chai": {
      "rainy_mean": 62.4859437751004,
      "dry_mean": 45.78481012658228,
      "rainy_rows": 498,
      "dry_rows": 553
    }
  },
  "cross_item_residual_correlation": 0.08218818233882166,
  "notes": [
    "Observed total retains injected POS over-recording errors and omits missing sales.",
    "Pattern means exclude closures, missing, stockout and POS outlier rows.",
    "Latent and expected demand are isolated oracle data, unavailable to the sales loader.",
    "Historical reanalysis weather is a proxy; it is not known day-ahead forecast weather."
  ]
}
WARNING OneDrive warning: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml. Use a non-synced location such as C:/dev/coffee-inventory-ml, exclude data/processed from sync, or set COFFEE_DB_DIR. SQLite uses DELETE journaling.
INFO Weather source (start): open_meteo
INFO Weather source (end): open_meteo; pipeline succeeded
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task features --config C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\data\processed\.pipeline_staging\final_workflow_4se2pm2o\config.yaml
{
  "rows": 10960,
  "predictors": 40,
  "split_counts": {
    "test": {
      "rows": 1650,
      "eligible_targets": 1593
    },
    "train": {
      "rows": 7670,
      "eligible_targets": 7326
    },
    "val": {
      "rows": 1640,
      "eligible_targets": 1562
    }
  },
  "eda": {
    "split": "train",
    "rows": 7670,
    "clean_rows": 7326,
    "start_date": "2023-01-01",
    "end_date": "2025-02-05",
    "weekly_clean_mean": {
      "0": 38.09942638623327,
      "1": 39.64957264957265,
      "2": 39.70037807183365,
      "3": 40.04381694255112,
      "4": 42.727878211227406,
      "5": 47.975190839694655,
      "6": 47.93480345158198
    },
    "festival_groups": {
      "before festival": {
        "mean": 50.964285714285715,
        "count": 196
      },
      "festival day": {
        "mean": 36.885714285714286,
        "count": 105
      },
      "ordinary": {
        "mean": 42.1423487544484,
        "count": 7025
      }
    },
    "stockout_fraction_by_item": {
      "cold_coffee": 0.018252933507170794,
      "latte": 0.018252933507170794,
      "cappuccino": 0.02216427640156454,
      "espresso": 0.02346805736636245,
      "iced_latte": 0.02346805736636245,
      "masala_chai": 0.02346805736636245,
      "croissant": 0.024771838331160364,
      "americano": 0.024771838331160364,
      "hot_chocolate": 0.024771838331160364,
      "sandwich": 0.028683181225554105
    },
    "figures": {
      "weekly": "eda_weekly.png",
      "festival": "eda_festival.png",
      "weather": "eda_weather.png",
      "trend": "eda_trend.png",
      "stockouts": "eda_stockouts.png"
    },
    "limitations": "Synthetic sales; historical realized weather; group differences are confounded. EDA uses train dates by default."
  }
}
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task train --config C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\data\processed\.pipeline_staging\final_workflow_4se2pm2o\config.yaml
CV candidate 1/4 complete: {'num_leaves': 15, 'learning_rate': 0.03}
CV candidate 2/4 complete: {'num_leaves': 15, 'learning_rate': 0.05}
CV candidate 3/4 complete: {'num_leaves': 31, 'learning_rate': 0.03}
CV candidate 4/4 complete: {'num_leaves': 31, 'learning_rate': 0.05}
Validation ML point selection: lightgbm; WAPE=0.207240
Recursive test origins 4/23 complete
Recursive test origins 8/23 complete
Recursive test origins 12/23 complete
Recursive test origins 16/23 complete
Recursive test origins 20/23 complete
{
  "selected_point_model": "lightgbm",
  "selection": "validation WAPE after train-only five-fold tuning",
  "best_parameters": {
    "num_leaves": 15,
    "learning_rate": 0.03
  },
  "training_through": "2025-07-19",
  "test_rows": 1593,
  "one_day_test_metrics": [
    {
      "model": "ridge",
      "item": "overall",
      "rows": 1593,
      "wape": 0.20672707785944983,
      "mae": 11.118490803367283,
      "rmse": 14.642547139997916,
      "bias": -0.7062035713100376,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "lightgbm",
      "item": "overall",
      "rows": 1593,
      "wape": 0.21492760998826535,
      "mae": 11.559543528540244,
      "rmse": 15.548871939553486,
      "bias": -2.18610886597426,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "naive",
      "item": "overall",
      "rows": 1593,
      "wape": 0.29402912489155003,
      "mae": 15.81389412010881,
      "rmse": 20.890915309543782,
      "bias": -0.1609123247541327,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "item": "overall",
      "rows": 1593,
      "wape": 0.28905949087853217,
      "mae": 15.546610169491526,
      "rmse": 20.70440772643603,
      "bias": -0.3166038920276208,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "moving_average",
      "item": "overall",
      "rows": 1593,
      "wape": 0.232384698454939,
      "mae": 12.498445580366484,
      "rmse": 16.406700748847424,
      "bias": -0.29345051265955224,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "quantile_p50",
      "item": "overall",
      "rows": 1593,
      "wape": 0.21928874211312455,
      "mae": 11.794100161974997,
      "rmse": 15.966126727689879,
      "bias": -3.2828901541078177,
      "interval_coverage": 0.7407407407407407,
      "mean_interval_width": 32.89390973602061
    }
  ],
  "relative_wape_improvement": 0.2564589063135738,
  "required_wape_improvement": 0.15,
  "meets_requested_improvement": true,
  "raw_quantile_crossings": 0,
  "nominal_interval_coverage": 0.8,
  "recursive_test_metrics": [
    {
      "model": "lightgbm",
      "horizon_day": 1,
      "rows": 224,
      "wape": 0.20235057338307727,
      "mae": 12.441850210737158,
      "rmse": 16.986129370527646,
      "bias": -2.8546696440153463,
      "interval_coverage": 0.78125,
      "mean_interval_width": 37.081062593876915
    },
    {
      "model": "lightgbm",
      "horizon_day": 2,
      "rows": 218,
      "wape": 0.2503067043597271,
      "mae": 11.983720520194824,
      "rmse": 16.403029883094682,
      "bias": -2.18195740649673,
      "interval_coverage": 0.6743119266055045,
      "mean_interval_width": 30.663778149564727
    },
    {
      "model": "lightgbm",
      "horizon_day": 3,
      "rows": 224,
      "wape": 0.2166779827033463,
      "mae": 10.911284128989937,
      "rmse": 14.769251965092755,
      "bias": -2.9999686459506205,
      "interval_coverage": 0.7678571428571429,
      "mean_interval_width": 31.255328578118192
    },
    {
      "model": "lightgbm",
      "horizon_day": 4,
      "rows": 219,
      "wape": 0.20772302723483985,
      "mae": 10.444958794109846,
      "rmse": 13.80577251499552,
      "bias": -1.2897739733675408,
      "interval_coverage": 0.7671232876712328,
      "mean_interval_width": 31.496523497238808
    },
    {
      "model": "lightgbm",
      "horizon_day": 5,
      "rows": 224,
      "wape": 0.23665483224582143,
      "mae": 11.636233581944095,
      "rmse": 15.732397666134837,
      "bias": -0.35339070117172705,
      "interval_coverage": 0.7142857142857143,
      "mean_interval_width": 30.226993969929612
    },
    {
      "model": "lightgbm",
      "horizon_day": 6,
      "rows": 222,
      "wape": 0.19937137461378426,
      "mae": 11.146835593271577,
      "rmse": 14.282815274448888,
      "bias": -3.8357436922626262,
      "interval_coverage": 0.7432432432432432,
      "mean_interval_width": 33.825821547893945
    },
    {
      "model": "lightgbm",
      "horizon_day": 7,
      "rows": 223,
      "wape": 0.2029759613373367,
      "mae": 11.849063070356273,
      "rmse": 15.420144404118952,
      "bias": -0.4907855323024416,
      "interval_coverage": 0.7982062780269058,
      "mean_interval_width": 37.67359228500186
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 1,
      "rows": 224,
      "wape": 0.2977346983228055,
      "mae": 18.30669642857143,
      "rmse": 24.848633130463757,
      "bias": 0.12217261904761896,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 2,
      "rows": 218,
      "wape": 0.3046820606176743,
      "mae": 14.587003058103976,
      "rmse": 19.339800537012188,
      "bias": -0.10382262996941899,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 3,
      "rows": 224,
      "wape": 0.2744473995271867,
      "mae": 13.820386904761904,
      "rmse": 17.75556376584132,
      "bias": -0.11264880952380953,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 4,
      "rows": 219,
      "wape": 0.2790713161399685,
      "mae": 14.032572298325723,
      "rmse": 18.695449108047608,
      "bias": 0.08310502283105012,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 5,
      "rows": 224,
      "wape": 0.3326009321469645,
      "mae": 16.35386904761905,
      "rmse": 22.13929051536678,
      "bias": 0.9610119047619047,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 6,
      "rows": 222,
      "wape": 0.26433021806853585,
      "mae": 14.778678678678679,
      "rmse": 18.886993103946125,
      "bias": 0.14864864864864877,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 7,
      "rows": 223,
      "wape": 0.2705868797050238,
      "mae": 15.795964125560538,
      "rmse": 20.72967335125246,
      "bias": -0.6689088191330345,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "lightgbm",
      "horizon_day": "overall",
      "rows": 1554,
      "wape": 0.2152539487155814,
      "mae": 11.4893526577623,
      "rmse": 15.381101323851572,
      "bias": -2.0010978006334423,
      "interval_coverage": 0.7496782496782497,
      "mean_interval_width": 33.1860901013381
    },
    {
      "model": "seasonal_naive",
      "horizon_day": "overall",
      "rows": 1554,
      "wape": 0.28833457912376725,
      "mae": 15.39009009009009,
      "rmse": 20.480444122347333,
      "bias": 0.06229086229086219,
      "interval_coverage": null,
      "mean_interval_width": null
    }
  ],
  "limitations": [
    "Synthetic shop data; no real-shop generalization claim.",
    "Persistence weather is less informative than future realized weather, deliberately excluded.",
    "One-day scores use earlier observed test history; recursive scores use predictions.",
    "Quantile intervals are empirical and uncalibrated; recursive uncertainty is conditional on a predicted history path.",
    "Cold-start point forecasts use past category means; quantile fallback uses training-category empirical quantiles.",
    "SHAP drivers are model associations, not causal effects."
  ]
}
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task inventory --config C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\data\processed\.pipeline_staging\final_workflow_4se2pm2o\config.yaml
{
  "origin": "2025-07-20",
  "forecast_days": 11,
  "item_forecast_rows": 110,
  "material_forecast_rows": 110,
  "materials": 10,
  "orders_now": 10,
  "estimated_order_cost": 88365.0,
  "currency": "INR",
  "illustrative_snapshot": true,
  "materials_with_pre_arrival_shortfall": 4,
  "materials_with_unmet_order_quantity": 4
}
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task simulate --config C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\data\processed\.pipeline_staging\final_workflow_4se2pm2o\config.yaml
Forecast refresh 1/24: 2025-07-20 (past observed history only)
Forecast refresh 2/24: 2025-07-27 (past observed history only)
Forecast refresh 3/24: 2025-08-03 (past observed history only)
Forecast refresh 4/24: 2025-08-10 (past observed history only)
Forecast refresh 5/24: 2025-08-17 (past observed history only)
Forecast refresh 6/24: 2025-08-24 (past observed history only)
Forecast refresh 7/24: 2025-08-31 (past observed history only)
Forecast refresh 8/24: 2025-09-07 (past observed history only)
Forecast refresh 9/24: 2025-09-14 (past observed history only)
Forecast refresh 10/24: 2025-09-21 (past observed history only)
Forecast refresh 11/24: 2025-09-28 (past observed history only)
Forecast refresh 12/24: 2025-10-05 (past observed history only)
Forecast refresh 13/24: 2025-10-12 (past observed history only)
Forecast refresh 14/24: 2025-10-19 (past observed history only)
Forecast refresh 15/24: 2025-10-26 (past observed history only)
Forecast refresh 16/24: 2025-11-02 (past observed history only)
Forecast refresh 17/24: 2025-11-09 (past observed history only)
Forecast refresh 18/24: 2025-11-16 (past observed history only)
Forecast refresh 19/24: 2025-11-23 (past observed history only)
Forecast refresh 20/24: 2025-11-30 (past observed history only)
Forecast refresh 21/24: 2025-12-07 (past observed history only)
Forecast refresh 22/24: 2025-12-14 (past observed history only)
Forecast refresh 23/24: 2025-12-21 (past observed history only)
Forecast refresh 24/24: 2025-12-28 (past observed history only)
{
  "test_start": "2025-07-20",
  "test_end": "2025-12-31",
  "test_days": 165,
  "forecast_refresh_days": 7,
  "daily_material_rows": 4950,
  "item_rows": 4950,
  "order_rows": 4086,
  "policies": [
    {
      "policy": "manual",
      "requested_units": 88436,
      "served_units": 87674,
      "lost_units": 762,
      "service_level": 0.9913835994391424,
      "stockout_rate": 0.008616400560857568,
      "item_day_stockout_rate": 0.03515151515151515,
      "waste_cost": 44868.334285714256,
      "purchase_cost": 2869065.0,
      "holding_cost": 15726.362923092862,
      "lost_sale_penalty": 111268.0,
      "initial_stock_value": 46171.55408571428,
      "closing_stock_value": 84630.75825000006,
      "pending_stock_value": 49990.0,
      "total_cost": 3042230.917008807
    },
    {
      "policy": "seasonal_naive",
      "requested_units": 88436,
      "served_units": 85810,
      "lost_units": 2626,
      "service_level": 0.9703062101406666,
      "stockout_rate": 0.029693789859333304,
      "item_day_stockout_rate": 0.11393939393939394,
      "waste_cost": 5539.002285714268,
      "purchase_cost": 2743660.0,
      "holding_cost": 12609.570404521433,
      "lost_sale_penalty": 403674.0,
      "initial_stock_value": 46171.55408571428,
      "closing_stock_value": 63012.97025000005,
      "pending_stock_value": 49450.0,
      "total_cost": 3206115.124490236
    },
    {
      "policy": "ml",
      "requested_units": 88436,
      "served_units": 87053,
      "lost_units": 1383,
      "service_level": 0.9843615722104121,
      "stockout_rate": 0.01563842778958795,
      "item_day_stockout_rate": 0.07757575757575758,
      "waste_cost": 1731.4508571428523,
      "purchase_cost": 2770800.0,
      "holding_cost": 11675.490536521433,
      "lost_sale_penalty": 207348.0,
      "initial_stock_value": 46171.55408571428,
      "closing_stock_value": 57644.24167857147,
      "pending_stock_value": 44910.0,
      "total_cost": 3035995.044622236
    }
  ],
  "relative_reduction_vs_manual": {
    "seasonal_naive": {
      "waste_cost": 0.8765498569560706,
      "stockout_rate": -2.446194225721785,
      "total_cost": -0.053869746232992656
    },
    "ml": {
      "waste_cost": 0.9614104048053744,
      "stockout_rate": -0.81496062992126,
      "total_cost": 0.0020497695791949536
    }
  }
}
exit_code=0
Regenerated model selection/WAPE and all policy summary numbers match saved results: PASS
Live CLI API: loopback startup and ready health PASS
GET /forecast/items?days=1: HTTP 200; 10 rows
GET /forecast/materials?days=1: HTTP 200; 10 rows
GET /recommendations/orders: HTTP 200; 10 rows
GET /inventory: HTTP 200; 10 rows
GET /model/metrics: HTTP 200; saved model/simulation measurements available
POST /whatif: HTTP 200; point-total change=-51.808763
GET /forecast/items?days=31: HTTP 422; limit validation PASS
GET /docs and /openapi.json: HTTP 200; seven business paths, eight endpoint operations
Live server output (complete):
INFO:     Started server process [35860]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:63480 (Press CTRL+C to quit)
INFO:     127.0.0.1:63481 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "GET /forecast/items?days=1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "GET /forecast/materials?days=1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "GET /recommendations/orders HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "GET /inventory HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "GET /model/metrics HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "POST /whatif HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "GET /forecast/items?days=31 HTTP/1.1" 422 Unprocessable Entity
INFO:     127.0.0.1:63481 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:63481 - "GET /openapi.json HTTP/1.1" 200 OK
Live dashboard CLI: HTTP 200 health=ok
Live dashboard root: HTTP 200; Streamlit application shell available
Live dashboard output (complete):

  You can now view your Streamlit app in your browser.

  URL: http://127.0.0.1:63485

Isolated workflow and both live CLI startups: PASS; temporary outputs removed afterward
Protected feature/model source reference scan: PASS
Saved executed notebook: 01_eda.ipynb; schema/no-error output PASS
Saved executed notebook: 02_modeling.ipynb; schema/no-error output PASS
Saved executed notebook: 03_simulation.ipynb; schema/no-error output PASS
Original data/model/figure/notebook file hashes unchanged: 42 files PASS
Pre-1.5 backup integrity: 11 artifacts PASS
Final document: docs/report.md PRESENT
Final document: docs/slide_outline.md PRESENT
Final document: docs/demo_script.md PRESENT
Weather tests use mocks; workflow uses the validated real cache; live HTTP is loopback only.
Fresh pip installation and GNU Make execution were not run: existing Windows venv/wrapper verified.
Phase 8 complete. All requested phases finished.

Additional dependency/document checks (complete):
numpy==2.2.6 MATCH
pandas==2.2.3 MATCH
scikit-learn==1.6.1 MATCH
lightgbm==4.6.0 MATCH
statsmodels==0.14.4 MATCH
shap==0.47.2 MATCH
matplotlib==3.10.3 MATCH
plotly==6.1.2 MATCH
fastapi==0.115.12 MATCH
uvicorn==0.34.3 MATCH
streamlit==1.45.1 MATCH
SQLAlchemy==2.0.41 MATCH
pytest==8.3.5 MATCH
PyYAML==6.0.2 MATCH
joblib==1.5.1 MATCH
holidays==0.74 MATCH
httpx==0.28.1 MATCH
requests==2.32.3 MATCH
jupyterlab==4.4.3 MATCH
nbformat==5.10.4 MATCH
ruff==0.11.13 MATCH
scipy==1.15.3 MATCH
README.md: UTF-8 / local links PASS
docs/report.md: UTF-8 / local links PASS
docs/slide_outline.md: UTF-8 / local links PASS
docs/demo_script.md: UTF-8 / local links PASS
Slide outline: 6 slides PASS
Demo script: timed 0:00 to 4:00; within requested 3-5 minutes
~~~

## Phase 7 — complete (2026-10-08)

- Added seven Streamlit screens: Overview, Demand Forecast, Raw Materials,
  Order Recommendations, Insights, Model Performance and What-If.
- Connected local service modules by default, with optional HTTP API transport.
  Forecasts, BOM needs, order proposals, SHAP explanations and saved performance
  results use actual project artifacts and past-only observed history.
- Added native-unit stock coverage, versioned stock editing with stale-form
  conflict/reload handling, CSV export and isolated scenario comparison.
- Displayed the fixed planning date, illustrative inventory, uncalibrated
  forecast intervals and honest waste/service/terminal-cost tradeoffs.
- Improved readable labels, currency encoding, light theme, interval lines and
  percentage displays. Existing calculations and model selection remain unchanged.
- Added 19 dashboard tests; removed the obsolete unimplemented-dashboard test.
  Full suite: 217 passed, 15 dependency deprecation warnings. Lint, formatting,
  dependency checks and live CLI health/root checks pass.
- Captured and validated three live browser screenshots. Updated README,
  assumptions, report and docs/dashboard_guide.md with all seven capture steps.
- All twelve protected artifacts, persistent demo inventory and eleven pre-1.5
  backups remain unchanged. Weather tests use mocks; live checks use loopback.
- Approved verification access resolved Windows sandbox restrictions; no checks
  remain unrun. Temporary verification and review servers were stopped.
- Full output is below and in reports/phase_7_verification.txt.
- STOP before Phase 8 final quality/docs; wait for the next continue instruction.

### Full Phase 7 verification output

~~~text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
.                                                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:37
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\starlette\testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

.venv\Lib\site-packages\matplotlib\_mathtext.py:45
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
217 passed, 15 warnings in 116.41s (0:01:56)
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
61 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
Live dashboard CLI: HTTP 200 health=ok
Live dashboard root: HTTP 200; Streamlit application shell available
Live dashboard output (complete):

  You can now view your Streamlit app in your browser.

  URL: http://127.0.0.1:56604

Seven screens, stock/scenario forms, conflicts, export and HTTP backend: AppTest checks PASS
Protected feature/model source reference scan: PASS
Browser screenshot: overview.jpg; valid JPEG (35735 bytes)
Browser screenshot: demand_forecast.jpg; valid JPEG (33532 bytes)
Browser screenshot: model_performance.jpg; valid JPEG (28575 bytes)
Prior source artifacts unchanged (SHA-256):
sales_csv: f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1; unchanged=True
truth_csv: 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87; unchanged=True
weather_cache: 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2; unchanged=True
database: 12cf4d174c631000756f3ecdd3d4d7d782fc8e3ad003a5282daaf806e20ef078; unchanged=True
truth_database: a4e210e059cb4413c75494aa41d4278af12d27fa1d484ff1f04e0635208381c1; unchanged=True
features_csv: a5e512e7f7ec05cd44185c3b3f984a7a630262f38bb207a367ccc936405d14ba; unchanged=True
model_bundle: cbd62bcd640d7d629d6f002a9947e3ad94d88a08414948ddd84c2d4e99e7ce9f; unchanged=True
demo_forecast: 1ad2a54404b8e0928dd8c2f5b31c2b8500e136d3509094669391515ae45ac357; unchanged=True
inventory_orders: e56839153aa91a18552e0072e1d0938d058e7f3f1fdca121ab91f9c36bef3dd3; unchanged=True
simulation: d134d8ebc9e3058926e7b2c76727a9ede055b63ed7e1e4f74de5e834357221df; unchanged=True
simulation_metrics: 190f41e06f9433673307986ce25a173f57e695bed1564453af22512c674e144c; unchanged=True
simulation_forecasts: 4bdfa5247262cabddbe0918353485549699d62b480105568acd9e91a28b0fb52; unchanged=True
Persistent demo inventory unchanged: PASS
Pre-1.5 backup integrity: 11 artifacts unchanged
Weather regressions use mocks; live startup uses only loopback HTTP.
Phase 7 complete. Stop before Phase 8 final quality/docs.
~~~

## Phase 6 — complete (2026-10-08)

- Implemented eight FastAPI endpoint operations on seven business paths: health,
  item/material forecasts, orders, GET/POST inventory, what-if and model metrics.
- Added Pydantic request/response schemas, finite numeric and strict scenario-boolean
  validation, horizon/material/date checks, and HTTP 422/409/503 error handling.
- Added lazy saved-model loading with past-only observed history, isolated scenario
  weather/promotions/festival-date changes and unchanged baseline/inventory state.
- Added single-process versioned aggregate snapshots, partial material-row updates,
  expected-version conflict detection, restart persistence and staged atomic writes.
  Initial stock remains illustrative; POST updates use a separate JSON state path.
- Inventory API supports one pending batch per material and no existing lot-age
  detail, matching the Phase 4 public planner. Phase 5 FIFO replay stays separate.
- Enabled the api CLI/Windows wrapper/Makefile path and exported OpenAPI schema.
  Configured default is localhost:8000; origin remains reproducible demo date.
- Added 35 API tests; removed the obsolete api-unimplemented test case.
  Tests cover actual model forecasts/BOM, scenarios, concurrent revisions, restart,
  failed-write recovery, invalid values and missing-model errors.
- Fixed a discovered FastAPI NaN error-serialization edge case: validation responses
  retain type/location/message without echoing a rejected nonfinite value.
- Full suite: 199 passed, 15 dependency deprecation warnings. Ruff lint/format and
  pip dependency checks pass. Live CLI startup, all route responses, Swagger and
  OpenAPI pass on a temporary loopback port; server was stopped after verification.
- Live smoke what-if point-total delta: -51.808763; scenario results are model
  associations, not guaranteed causal uplift.
- Prior data/DB/features/model/forecast/order/simulation artifacts and all eleven
  pre-1.5 backups retain their hashes. Persistent demo inventory is unchanged.
- Existing Windows filesystem restrictions required approved verification access.
  No checks remain unrun. Weather regressions use mocks; smoke uses loopback only.
- Updated README, assumptions, project report and docs/api_contract.md.
  Full output is below and in reports/phase_6_verification.txt.
- STOP before Phase 7 dashboard; wait for the next continue instruction.

### Full Phase 6 verification output

~~~text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 36%]
........................................................................ [ 72%]
.......................................................                  [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:37
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\starlette\testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

.venv\Lib\site-packages\matplotlib\_mathtext.py:45
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
199 passed, 15 warnings in 27.57s
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
57 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
Live CLI API: loopback startup and ready health PASS
GET /forecast/items?days=1: HTTP 200; 10 rows
GET /forecast/materials?days=1: HTTP 200; 10 rows
GET /recommendations/orders: HTTP 200; 10 rows
GET /inventory: HTTP 200; 10 rows
GET /model/metrics: HTTP 200; saved model/simulation measurements available
POST /whatif: HTTP 200; point-total change=-51.808763
GET /forecast/items?days=31: HTTP 422; limit validation PASS
GET /docs and /openapi.json: HTTP 200; seven business paths, eight endpoint operations
Live server output (complete):
INFO:     Started server process [67900]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:51933 (Press CTRL+C to quit)
INFO:     127.0.0.1:51935 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "GET /forecast/items?days=1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "GET /forecast/materials?days=1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "GET /recommendations/orders HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "GET /inventory HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "GET /model/metrics HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "POST /whatif HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "GET /forecast/items?days=31 HTTP/1.1" 422 Unprocessable Entity
INFO:     127.0.0.1:51935 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:51935 - "GET /openapi.json HTTP/1.1" 200 OK
Protected feature/model source reference scan: PASS
Prior source artifacts unchanged (SHA-256):
sales_csv: f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1; unchanged=True
truth_csv: 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87; unchanged=True
weather_cache: 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2; unchanged=True
database: 12cf4d174c631000756f3ecdd3d4d7d782fc8e3ad003a5282daaf806e20ef078; unchanged=True
truth_database: a4e210e059cb4413c75494aa41d4278af12d27fa1d484ff1f04e0635208381c1; unchanged=True
features_csv: a5e512e7f7ec05cd44185c3b3f984a7a630262f38bb207a367ccc936405d14ba; unchanged=True
model_bundle: cbd62bcd640d7d629d6f002a9947e3ad94d88a08414948ddd84c2d4e99e7ce9f; unchanged=True
demo_forecast: 1ad2a54404b8e0928dd8c2f5b31c2b8500e136d3509094669391515ae45ac357; unchanged=True
inventory_orders: e56839153aa91a18552e0072e1d0938d058e7f3f1fdca121ab91f9c36bef3dd3; unchanged=True
simulation: d134d8ebc9e3058926e7b2c76727a9ede055b63ed7e1e4f74de5e834357221df; unchanged=True
simulation_metrics: 190f41e06f9433673307986ce25a173f57e695bed1564453af22512c674e144c; unchanged=True
simulation_forecasts: 4bdfa5247262cabddbe0918353485549699d62b480105568acd9e91a28b0fb52; unchanged=True
Live smoke leaves persistent inventory state unchanged: PASS
Pre-1.5 backup integrity: 11 artifacts unchanged
Weather regressions use mocks; live smoke uses only local loopback HTTP.
Phase 6 complete. Stop before Phase 7 dashboard.
~~~

## Phase 5 — complete (2026-10-08)

- Implemented day-by-day FIFO lot replay, start-of-day expiry, multiple lead-time
  deliveries, zero-lead receipts, whole-recipe fulfillment and lost-sales accounting.
- Compared manual buffered prior-week means, seasonal-naive forecasts and saved ML
  forecasts over all 165 test days with identical initial stock and customer demand.
- Forecasts refresh at 24 weekly origins; daily reviews have an 11-day horizon.
  Bank contains 12,240 rows. Future recorded sales mutations do not change forecasts.
  Evaluation-only demand is loaded after the forecast bank is frozen.
- Common factual POS histories deliberately isolate the inventory comparison;
  policy-dependent sales-observation feedback is not modeled.
- Exported 4,950 daily material rows, 4,950 item fulfillment rows, 4,086 supplier
  commitments, three policy summaries, 30 material/unit waste records, metadata,
  JSON metrics, comparison report and two visually verified charts.
- Executed notebooks/03_simulation.ipynb: three code cells and two embedded plots.
- Service: manual 99.14%, seasonal naive 97.03%, ML 98.44%.
  Lost units: manual 762, seasonal naive 2,626, ML 1,383, from 88,436 requests.
- ML waste cost INR 1,731.45 versus manual INR 44,868.33 (96.14% lower);
  ML loses 81.50% more units than manual, but 47.33% fewer than seasonal naive.
  Extra losses are in croissants/sandwiches. No test-outcome parameter tuning.
- Gross modeled cost: manual INR 3,042,230.92; seasonal naive INR 3,206,115.12;
  ML INR 3,035,995.04. ML's 0.205% advantage over manual is small and sensitive
  to inventory boundary accounting. Full terminal-value credit reverses that ranking:
  manual about INR 2,907,610, ML INR 2,933,441. No robust savings claim.
- Added 24 simulation tests; removed the obsolete simulate-unimplemented case.
  Full suite: 165 passed with 14 existing Matplotlib/Pyparsing warnings.
  Lint, formatting, dependency checks, CLI, notebook, conservation, cache integrity,
  source hashes and all 11 pre-1.5 backup hashes pass.
- First full attempt found that obsolete placeholder test; after updating its
  expected phase behavior, all checks passed. Approved filesystem access enabled
  Windows temporary replacement tests and Jupyter runtime. Nothing remains unrun.
- Updated README, assumptions, project report and docs/simulation_contract.md.
  Full final verification output is below and in reports/phase_5_verification.txt.
- STOP before Phase 6 API; wait for the next continue instruction.

### Full Phase 5 verification output

~~~text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 43%]
........................................................................ [ 87%]
.....................                                                    [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

.venv\Lib\site-packages\matplotlib\_mathtext.py:45
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
165 passed, 14 warnings in 21.83s
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
53 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task simulate
Forecast cache: source/model/config fingerprint and CSV hash verified
{
  "test_start": "2025-07-20",
  "test_end": "2025-12-31",
  "test_days": 165,
  "forecast_refresh_days": 7,
  "daily_material_rows": 4950,
  "item_rows": 4950,
  "order_rows": 4086,
  "policies": [
    {
      "policy": "manual",
      "requested_units": 88436,
      "served_units": 87674,
      "lost_units": 762,
      "service_level": 0.9913835994391424,
      "stockout_rate": 0.008616400560857568,
      "item_day_stockout_rate": 0.03515151515151515,
      "waste_cost": 44868.334285714256,
      "purchase_cost": 2869065.0,
      "holding_cost": 15726.362923092862,
      "lost_sale_penalty": 111268.0,
      "initial_stock_value": 46171.55408571428,
      "closing_stock_value": 84630.75825000006,
      "pending_stock_value": 49990.0,
      "total_cost": 3042230.917008807
    },
    {
      "policy": "seasonal_naive",
      "requested_units": 88436,
      "served_units": 85810,
      "lost_units": 2626,
      "service_level": 0.9703062101406666,
      "stockout_rate": 0.029693789859333304,
      "item_day_stockout_rate": 0.11393939393939394,
      "waste_cost": 5539.002285714268,
      "purchase_cost": 2743660.0,
      "holding_cost": 12609.570404521433,
      "lost_sale_penalty": 403674.0,
      "initial_stock_value": 46171.55408571428,
      "closing_stock_value": 63012.97025000005,
      "pending_stock_value": 49450.0,
      "total_cost": 3206115.124490236
    },
    {
      "policy": "ml",
      "requested_units": 88436,
      "served_units": 87053,
      "lost_units": 1383,
      "service_level": 0.9843615722104121,
      "stockout_rate": 0.01563842778958795,
      "item_day_stockout_rate": 0.07757575757575758,
      "waste_cost": 1731.4508571428523,
      "purchase_cost": 2770800.0,
      "holding_cost": 11675.490536521433,
      "lost_sale_penalty": 207348.0,
      "initial_stock_value": 46171.55408571428,
      "closing_stock_value": 57644.24167857147,
      "pending_stock_value": 44910.0,
      "total_cost": 3035995.044622236
    }
  ],
  "relative_reduction_vs_manual": {
    "seasonal_naive": {
      "waste_cost": 0.8765498569560706,
      "stockout_rate": -2.446194225721785,
      "total_cost": -0.053869746232992656
    },
    "ml": {
      "waste_cost": 0.9614104048053744,
      "stockout_rate": -0.81496062992126,
      "total_cost": 0.0020497695791949536
    }
  }
}
exit_code=0
Simulation notebook: 3 cells executed, 2 embedded charts; schema validated
Python: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe
Test dates: 2025-07-20 through 2025-12-31
        policy  requested_units  served_units  lost_units  service_level  stockout_rate  item_day_stockout_rate   waste_cost  purchase_cost  holding_cost  lost_sale_penalty  initial_stock_value  closing_stock_value  pending_stock_value   total_cost
        manual            88436         87674         762       0.991384       0.008616                0.035152 44868.334286      2869065.0  15726.362923           111268.0         46171.554086         84630.758250              49990.0 3.042231e+06
seasonal_naive            88436         85810        2626       0.970306       0.029694                0.113939  5539.002286      2743660.0  12609.570405           403674.0         46171.554086         63012.970250              49450.0 3.206115e+06
            ml            88436         87053        1383       0.984362       0.015638                0.077576  1731.450857      2770800.0  11675.490537           207348.0         46171.554086         57644.241679              44910.0 3.035995e+06
Relative reductions vs manual: {
  "seasonal_naive": {
    "waste_cost": 0.8765498569560706,
    "stockout_rate": -2.446194225721785,
    "total_cost": -0.053869746232992656
  },
  "ml": {
    "waste_cost": 0.9614104048053744,
    "stockout_rate": -0.81496062992126,
    "total_cost": 0.0020497695791949536
  }
}
        policy        material unit   waste_units   waste_cost
        manual           bread  pcs    268.100000  2144.800000
        manual chocolate_syrup   ml      0.000000     0.000000
        manual    coffee_beans    g      0.000000     0.000000
        manual croissant_dough  pcs    192.497143  8662.371429
        manual        cup_cold  pcs      0.000000     0.000000
        manual         cup_hot  pcs      0.000000     0.000000
        manual             ice    g 213354.285714  2133.542857
        manual            milk   ml 532127.000000 31927.620000
        manual           sugar    g      0.000000     0.000000
        manual      tea_leaves    g      0.000000     0.000000
            ml           bread  pcs      4.140000    33.120000
            ml chocolate_syrup   ml      0.000000     0.000000
            ml    coffee_beans    g      0.000000     0.000000
            ml croissant_dough  pcs      0.000000     0.000000
            ml        cup_cold  pcs      0.000000     0.000000
            ml         cup_hot  pcs      0.000000     0.000000
            ml             ice    g  63039.085714   630.390857
            ml            milk   ml  17799.000000  1067.940000
            ml           sugar    g      0.000000     0.000000
            ml      tea_leaves    g      0.000000     0.000000
seasonal_naive           bread  pcs     33.700000   269.600000
seasonal_naive chocolate_syrup   ml      0.000000     0.000000
seasonal_naive    coffee_beans    g      0.000000     0.000000
seasonal_naive croissant_dough  pcs      4.777143   214.971429
seasonal_naive        cup_cold  pcs      0.000000     0.000000
seasonal_naive         cup_hot  pcs      0.000000     0.000000
seasonal_naive             ice    g  42039.085714   420.390857
seasonal_naive            milk   ml  77234.000000  4634.040000
seasonal_naive           sugar    g      0.000000     0.000000
seasonal_naive      tea_leaves    g      0.000000     0.000000
FIFO material mass balance and item demand reconciliation: PASS
Daily material rows: 4950 ; item rows: 4950
Protected feature/model source reference scan: PASS
Daily FIFO mass balance, nonnegative stock, identical policy demand, unit fulfillment and cost accounting: PASS
Forecast bank: 12240 rows, 24 origins per policy, valid dates and cache integrity: PASS
CSV newline audit: PASS
No prior-phase source artifacts changed (SHA-256):
sales_csv: f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1; unchanged=True
truth_csv: 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87; unchanged=True
weather_cache: 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2; unchanged=True
database: 12cf4d174c631000756f3ecdd3d4d7d782fc8e3ad003a5282daaf806e20ef078; unchanged=True
truth_database: a4e210e059cb4413c75494aa41d4278af12d27fa1d484ff1f04e0635208381c1; unchanged=True
features_csv: a5e512e7f7ec05cd44185c3b3f984a7a630262f38bb207a367ccc936405d14ba; unchanged=True
model_bundle: cbd62bcd640d7d629d6f002a9947e3ad94d88a08414948ddd84c2d4e99e7ce9f; unchanged=True
demo_forecast: 1ad2a54404b8e0928dd8c2f5b31c2b8500e136d3509094669391515ae45ac357; unchanged=True
inventory_orders: e56839153aa91a18552e0072e1d0938d058e7f3f1fdca121ab91f9c36bef3dd3; unchanged=True
Pre-1.5 backup integrity: 11 artifacts unchanged
Weather regressions use mocked responses. No external requests or supplier orders are made.
Phase 5 complete. Stop before Phase 6 API.
~~~

## Phase 4 — complete (2026-10-08)

- Added validated recipe BOM conversion for point/P10/P50/P90 forecasts, including
  one preparation wastage adjustment and native material units.
- Added covariance-aware past residual aggregation and the default P90-P50 sigma
  proxy, normal safety stock and mean-demand reorder points.
- Planned stock consumption before supplier delivery; time-phased pending receipts
  prevent late arrivals from hiding an earlier shortage.
- Added receipt-centered coverage, shelf-life capacity, supplier minimum/pack rounding,
  zero feasible-pack handling, explicit pre-delivery shortages and unmet quantities.
- Added the inventory CLI, Windows wrapper and Makefile target; saved-model demo
  expands to 11 days, 110 item rows, 110 material rows and ten recommendations.
- Demo snapshot is illustrative. Estimated proposed-order cost is INR 88,365;
  four materials have pre-arrival shortages and four have unfilled desired quantities.
  This is not a savings estimate or a supplier purchase.
- Added 26 hand-worked/invalid-input tests. Full suite: 142 passed, 14 existing
  Matplotlib/Pyparsing deprecation warnings. Ruff source/test lint and format pass;
  dependency checks and all material/CSV/source-hash/backup audits pass.
- Initial sandbox test run: 137 passed, five Windows temporary-file replacement
  failures (WinError 5). Approved verification outside the sandbox passed all 142.
  No verification step remains unrun. Weather regressions use mocked responses.
- An exploratory repository-wide Ruff scan also found existing notebook import
  style issues; the established source/test lint scope passes. Notebook sources
  were not changed by this phase.
- Full contract: docs/inventory_contract.md. Full command output:
  reports/phase_4_verification.txt. Seven new inventory outputs publish from staging.
- Stop here before Phase 5. FIFO lot expiry, policy comparisons and measured
  waste/stockout/cost benefits remain for the next continue instruction.

### Full Phase 4 verification output

~~~text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 50%]
......................................................................   [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

.venv\Lib\site-packages\matplotlib\_mathtext.py:45
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
142 passed, 14 warnings in 19.37s
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
48 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task inventory
{
  "origin": "2025-07-20",
  "forecast_days": 11,
  "item_forecast_rows": 110,
  "material_forecast_rows": 110,
  "materials": 10,
  "orders_now": 10,
  "estimated_order_cost": 88365.0,
  "currency": "INR",
  "illustrative_snapshot": true,
  "materials_with_pre_arrival_shortfall": 4,
  "materials_with_unmet_order_quantity": 4
}
exit_code=0
Protected feature/model source reference scan: PASS
Forecast/BOM recomputation: PASS; 110 item rows, 110 material rows, 11 days
Ten-material recommendation replay, expiry caps, MOQ and pack multiples: PASS
CSV newline audit: PASS; no doubled carriage returns
Recommendations (complete):
       material unit  order_now  order_qty  safety_stock  pre_arrival_shortfall  unmet_order_quantity                                                                                                                                                                                 reason
   coffee_beans    g       True    51000.0   5169.158035               0.000000              0.000000                                                                                                                        inventory position at/below reorder point or projected shortage
           milk   ml       True    55000.0  27355.036107               0.000000          28249.747381                                                              inventory position at/below reorder point or projected shortage; shelf-life capacity limits safety stock or pack rounding
          sugar    g       True    23000.0   2234.314287               0.000000              0.000000                                                                                                                        inventory position at/below reorder point or projected shortage
chocolate_syrup   ml       True     8000.0    674.680244               0.000000              0.000000                                                                                                                        inventory position at/below reorder point or projected shortage
     tea_leaves    g       True     2500.0    201.593546               0.000000              0.000000                                                                                                                        inventory position at/below reorder point or projected shortage
            ice    g       True    44000.0   6286.509668               0.000000           6856.445763                                                              inventory position at/below reorder point or projected shortage; shelf-life capacity limits safety stock or pack rounding
croissant_dough  pcs       True       30.0     16.147328               2.740446             20.996855 inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu; shelf-life capacity limits safety stock or pack rounding
          bread  pcs       True       80.0     44.859456               6.038982             46.175964 inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu; shelf-life capacity limits safety stock or pack rounding
        cup_hot  pcs       True     3000.0    310.750606             349.098200              0.000000                                                           inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu
       cup_cold  pcs       True      900.0    110.544998              86.932573              0.000000                                                           inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu
No source artifacts changed (SHA-256):
sales_csv: f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1; unchanged=True
truth_csv: 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87; unchanged=True
weather_cache: 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2; unchanged=True
database: 12cf4d174c631000756f3ecdd3d4d7d782fc8e3ad003a5282daaf806e20ef078; unchanged=True
truth_database: a4e210e059cb4413c75494aa41d4278af12d27fa1d484ff1f04e0635208381c1; unchanged=True
features_csv: a5e512e7f7ec05cd44185c3b3f984a7a630262f38bb207a367ccc936405d14ba; unchanged=True
model_bundle: cbd62bcd640d7d629d6f002a9947e3ad94d88a08414948ddd84c2d4e99e7ce9f; unchanged=True
demo_forecast: 1ad2a54404b8e0928dd8c2f5b31c2b8500e136d3509094669391515ae45ac357; unchanged=True
Pre-1.5 backup integrity: 11 artifacts unchanged
Weather regression tests use mocked API responses; inventory planning uses existing cached observations.
Phase 4 complete. Stop before Phase 5 simulation.
~~~

## Phase 3 — complete (2026-10-08)

- Implemented yesterday/seasonal naive and seven-day average baselines, Ridge,
  global LightGBM point regression and P10/P50/P90 quantile models.
- Added fold-fitted numeric median imputation, Ridge scaling and unknown-safe item/category
  one-hot encoding. Predictors remain the explicit 40-column feature contract.
- Tuned four LightGBM combinations on five expanding training-date folds; additionally
  scored Ridge and all baselines on those folds (40 fold/model/candidate records).
- Validation selected LightGBM, leaves 15, learning rate 0.03, 300 trees. Refit train+validation
  through 2025-07-19, then scored 1,593 common clean test targets.
- One-day WAPE: naive 29.40%, seasonal naive 28.91%, average 23.24%, Ridge 20.67%,
  selected LightGBM 21.49%, quantile P50 21.93%.
- Selected-model improvement over seasonal naive: 25.65% relative, above the requested 15%.
  Ridge was better on test; deployment choice remained validation-selected, without test retuning.
- Seven-day recursive evaluation: 23 weekly origins, 1,554 clean targets; LightGBM WAPE
  21.53% vs seasonal naive 28.83%. Future actual sales/weather mutations do not change forecasts.
- P10-P90 one-day coverage 74.07%, recursive coverage 74.97%, below nominal 80%.
  Zero raw one-day quantile crossings. Intervals remain uncalibrated; full path uncertainty
  is not propagated. This limitation is explicit in the modeling contract and reports.
- Implemented past-category cold-start point fallback and training-category empirical
  quantile fallback; saved artifact reload reproduces exported test predictions.
- Added SHAP summary and top-five signed driver explanations. Contributions are additive
  model associations, not causal claims; clipping/cold-start overrides are explained separately.
- Executed modeling notebook: four code cells and three embedded charts, schema valid.
  All charts visually inspected. Saved 70 demo forecast rows (ten items, seven dates).
- Added 20 modeling tests and updated the now-implemented train CLI test: 116 total tests pass,
  14 existing dependency deprecation warnings. Lint, format, pip and Windows train wrapper pass.
- Corrected Windows CSV newline translation; all 121 metric records, 1,593 predictions,
  40 CV records, 16 recursive metric records and 70 demo rows retain identical values.
- Original sales/weather/evaluation CSVs, both databases, feature export and the 11-artifact
  pre-1.5 backup are unchanged. All model outputs were staged and verified before publication.
- No network was needed; existing mocked weather tests passed. Escalated verification handled
  previously established pytest replacement/Jupyter runtime sandbox restrictions. No check
  remains blocked. Optional SARIMAX is still disabled and explicitly not implemented.
- Updated README, assumptions, report, modeling contract and full verification transcript.
- Next: Phase 4 BOM conversion, safety stock, reorder quantities, lead time/shelf-life caps
  and hand-computed inventory tests. Stopped; awaiting continue.

## Phase 2 — complete (2026-10-08)

- Implemented 40 predictors: calendar/cycles, forecast-weather, planned promotions/price, item/category, past-only lags/rolling statistics and cold-start category history.
- Added configurable stockout target exclusion or prior-clean rolling imputation; quality and targets remain outside the predictor manifest.
- Added fixed-origin prediction inputs that reject post-origin history/late forecasts and leave unknown future lags missing for later recursive predictions.
- Created and executed notebooks/01_eda.ipynb: four code cells, five embedded plots, schema validated. All figures visually checked.
- EDA uses training dates only: 7,670 rows, 7,326 clean targets. Pre-festival mean 50.96; ordinary 42.14; festival day 36.89 units/item/day. These are descriptive comparisons.
- Exported 10,960 feature rows; eligible targets: train 7,326, validation 1,562, test 1,593. No models trained.
- Added 18 tests covering hand calculations, censored targets, item isolation, current/future mutation, prefix equivalence, forecast issue times and origin boundaries, invalid inputs and EDA edge cases.
- Final full suite: 97 passed, 14 existing dependency deprecation warnings. Lint, format and pip checks pass. Windows wrapper and notebook execution pass.
- Sales, truth, weather CSVs and both SQLite files remain byte-identical to before Phase 2. No new backup was needed because the source artifacts were never replaced.
- Sandbox restrictions blocked initial pytest temporary-file replacement and Jupyter user runtime initialization. Escalated reruns completed both; no verification remains blocked. Weather tests remain mocked.
- Parameter/availability assumptions: docs/feature_contract.md and docs/assumptions.md. Full verification transcript: reports/phase_2_verification.txt.
- Next: Phase 3 baselines, Ridge, LightGBM and quantiles with walk-forward validation, fold-fitted preprocessing, recursive horizons, cold-start fallback and honest held-out comparisons. Stopped; awaiting continue.

## Phase 0 — complete (2026-10-07)
### Work completed
- Created the requested coffee-inventory-ml structure, package initializers and
  clearly marked later-phase module/notebook placeholders.
- Created a project-local .venv using Python 3.11.9 and installed pinned dependencies.
- Added config/config.yaml with 10 menu items, 10 materials, recipes, INR prices/costs,
  three-year dates, seed 42, weather choice, validation, model and inventory settings.
- Added typed configuration loading and project-relative path resolution.
- Added Makefile targets, README, PRD, assumptions, report skeleton and .gitignore.
- Saved requirements-lock-windows-py311.txt as a complete snapshot of this environment.

### Verification results
- Final pytest: **20 passed**, 14 warnings, 10.34 seconds.
- Tests: 17 required-library imports plus 3 configuration/material/path checks.
- pip check: **No broken requirements found**.
- Ruff lint: **All checks passed**.
- Ruff format check: **29 files already formatted** after formatting 3 setup files.
- All three notebook skeletons validated with nbformat.
- Configured history: 2023-01-01 through 2025-12-31, **1,096 days**.
- No dataset generated, forecast trained or simulation performed; no performance claims.

### Decisions and limitations
- Bengaluru, synthetic weather by default, illustrative INR costs and recipes.
- Top-level dependencies are pinned in requirements.txt; SciPy is explicitly pinned
  to 1.15.3 alongside statsmodels 0.14.4.
- The full environment snapshot is specific to Windows/Python 3.11; requirements.txt
  remains the main install input for other supported platforms/Python versions.
- GNU Make is absent on this host. Setup and tests were executed using the equivalent
  Windows Python commands in README; Makefile execution itself was not verified.
- The 14 warnings are third-party Matplotlib/Pyparsing deprecated method warnings.
  They did not cause failures and have not been hidden.
- API, dashboard and later pipeline targets are placeholders until their phases.
- Dependency download and installation were slow, but completed successfully.

### Next step — Phase 1 (only after "continue")
Implement and test synthetic sales generation, India calendar, swappable weather,
SQLite loading, data dictionary and data-quality checks. Produce real sample rows,
summary statistics and seasonality checks.

## Remaining phases
1. Data — complete (details below)
2. EDA and features — pending
3. Modeling — pending
4. Inventory engine — pending
5. Simulation — pending
6. API — pending
7. Dashboard — pending
8. Quality and docs — pending

## Phase 1 — complete (2026-10-07)

### Work completed
- Implemented configurable synthetic sales with negative-binomial noise, weekly/monthly
  seasonality, payday and festival effects, temperature/rain responses, promotions,
  slow trend and gradual drift.
- Added India/Karnataka holiday features, an editable five-festival calendar,
  next/previous festival distances and boundary-safe long-weekend detection.
- Implemented validated Open-Meteo historical and seeded synthetic weather providers,
  explicit automatic fallback, recorded provenance and input-fingerprinted caching.
- Added observed-sales CSV, isolated simulation truth, weather/calendar CSVs, and seven
  transactional SQLite tables with unique indexes and a read-only sales loader.
- Added structural data-quality checks, readable/JSON dictionaries, a sample CSV,
  summary JSON and a readable quality report.
- Documented equations, every Phase 1 parameter, recipes, material assumptions,
  calendar coverage, quality imperfections and weather availability limits.

### Actual generated results
- **10,960 rows**, **1,096 days**, **10 items**, 2023-01-01 to 2025-12-31.
- Weather source: **Open-Meteo historical reanalysis**; network fetch succeeded.
- Recorded sales: **493,475 units**, including injected POS errors and excluding
  missing records. Latent customer demand: **495,101 units** (oracle; evaluation only).
- **265 stockout rows**, **60 missing sales**, **56 injected POS outliers**.
- **11 shop closure days**, **81 promotion days (7.39%)**, **15 configured festival days**.
- Clean mean sales/item/day: weekdays **43.23**, weekends **51.66**;
  weekend lift **19.49%**. Clean excludes stockouts, closures, missing and outliers.
- Clean weekend/weekday ratios: cold_coffee **1.341**, iced_latte **1.334**,
  croissant **1.292**. These are observed descriptive ratios, not causal estimates.
- Example 2023-01-01 observations: americano 39, cappuccino 48, cold_coffee 30,
  croissant 44, espresso 36; weather maximum 27.5 C, precipitation 0 mm.

### Tests and checks
- **51 tests passed**, 14 third-party deprecation warnings, **10.29 seconds**:
  31 Phase 1 tests plus the 20 Phase 0 checks.
- Verified shape, nonnegative counts, reproducibility, weekend seasonality, quality
  imperfections, known festivals, calendar boundaries and long weekends.
- Controlled tests verified heat/rain, promotion/cannibalization, festival effects,
  linear trend and gradual drift. They hold unrelated inputs constant.
- Verified mocked API parsing, explicit fallback, strict-provider errors, invalid
  weather rejection, cache use/invalidation, fully missing/closed summary handling.
- Verified SQLite round trips, uniqueness, date filtering, missing-database errors,
  oracle isolation and rollback after an injected mid-refresh failure.
- Initial round-trip test exposed int32/int64 differences; fixed by making calendar
  integer types explicit. The test then passed.
- Final Ruff lint and formatting passed (**31 Python files**).
- pip check: **No broken requirements found**.
- Replayed the production data pipeline: **sales/truth/weather CSV SHA-256 hashes
  unchanged**. Validated **all 10,960 rows read from the actual SQLite database**.
- GNU Make remains unavailable; the generator was executed with the equivalent
  Windows Python command. Makefile execution itself was not claimed.

### Decisions and limitations
- Promotions target one item on about 8% of shop days, not 8% of all item/day rows.
- Quality flags may overlap. POS errors are not extra customer demand; latent
  and expected demand never enter the public sales loader.
- Historical reanalysis is realized weather, not a forecast known before day t.
  It drives synthetic demand; Phase 2 must construct weather forecast inputs from
  information available at prediction time. Do not feed future realized weather into
  training features or claim it is an operational day-ahead forecast.
- The hand-built lunar festival calendar covers 2022–2026; extend it for later years.
- No sales cleaning/imputation, feature leakage proof, model results or inventory
  benefits are claimed yet; those remain in their assigned phases.

### Reviewable artifacts
- reports/data_quality.md and reports/data_summary.json
- reports/sales_sample.csv
- docs/data_dictionary.md and docs/data_dictionary.json
- docs/assumptions.md
- data/raw/sales.csv and data/raw/simulation_truth.csv
- data/external/weather.csv, weather_metadata.json and calendar.csv
- data/processed/coffee.sqlite

### Next step — Phase 2 (only after "continue")
Create EDA plots/notebook, build calendar/weather/category/price/promotion and
shifted lag/rolling features, handle censored targets through configuration, and
prove no future target information is used. Preserve strict as-of weather availability.

## Phase 1.5 verification and decisions

All ten requested hardening areas are implemented: shared mean-one shocks, per-item
promotions with legacy mode, fallback weather retry, stable SHA-256 streams, demo
dates/calendar checks, exclusive statuses and training eligibility, split-aware drift,
separate transactional truth storage and leakage scanning, OneDrive/database handling,
and Windows CLI dispatch.

The original 11-artifact pre-patch snapshot is unchanged and hash-verified. New outputs
were staged and validated before publication. Both production runs used the validated
Open-Meteo historical cache. API failure and recovery were tested with mocked responses;
no required verification step was blocked by sandbox restrictions. No fresh live API
request was needed. To request live data explicitly, use a reviewed alternative config
with data.weather_provider=open_meteo and weather.cache_enabled=false:
.\.venv\Scripts\python.exe -m src.cli --config <alternative-config.yaml> data

Assumptions: fixed promotion spillover peers preserve existing histories when adding
items; update peers deliberately to change spillovers. Missing-priority accounting
assigns hidden stockout losses on missing rows to missing loss. DELETE journaling enables
atomic attached-database writes. Individual artifact replacements and handled-failure
rollback do not guarantee crash-wide atomic publication; backups remain available.
SQLite read connections close explicitly, avoiding Windows file locks.

Partial item: 2027 dated festival extension was not attempted without reliable Holi
coverage in the pinned holiday data. Current explicit dates end in 2026; unsupported
years raise a tested coverage error. No unverified dates were inserted.

Full final verification output follows; it is also saved in
reports/phase_1_5_verification.txt. Reproduce the main checks with:
.\.venv\Scripts\python.exe -m src.data.verify_phase_1_5


```text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 91%]
.......                                                                  [100%]
============================== warnings summary ===============================
tests/test_environment.py::test_required_library_import[lightgbm]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

tests/test_environment.py::test_required_library_import[shap]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
79 passed, 14 warnings in 18.55s
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
37 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m src.cli setup-check
No broken requirements found.
Python: 3.11.9
Executable: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe
Virtual environment: True
Required library imports: 17 OK
{
  "train_start": "2023-01-01",
  "train_end": "2025-02-05",
  "val_start": "2025-02-06",
  "val_end": "2025-07-19",
  "test_start": "2025-07-20",
  "test_end": "2025-12-31",
  "as_of_date": "2025-07-20",
  "forecast_horizon_days": 7,
  "calendar_required_through": "2025-07-27",
  "drift_start": "2025-02-06",
  "drift_plateau_date": "2025-08-05",
  "drift_start_split": "val",
  "drift_ramp_overlap_days": {
    "train": 0,
    "val": 164,
    "test": 16
  },
  "drift_appears_in_test": true,
  "test_contains_shifted_demand": true,
  "split_rule": "floor(train*n), floor(validation*n), remainder to test; never shuffle"
}
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m src.cli train
Not implemented until Phase 3
exit_code=2
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m src.cli simulate
Not implemented until Phase 5
exit_code=2
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m src.cli api
Not implemented until Phase 6
exit_code=2
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m src.cli dashboard
Not implemented until Phase 7
exit_code=2
PIPELINE RUN 1
Pipeline start; requested weather provider: auto
OneDrive warning: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml. Use a non-synced location such as C:/dev/coffee-inventory-ml, exclude data/processed from sync, or set COFFEE_DB_DIR. SQLite uses DELETE journaling.
WARNING:src.data.generator:OneDrive warning: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml. Use a non-synced location such as C:/dev/coffee-inventory-ml, exclude data/processed from sync, or set COFFEE_DB_DIR. SQLite uses DELETE journaling.
Weather source (start): open_meteo
INFO:src.data.generator:Weather source (start): open_meteo
Weather source (end): open_meteo; pipeline succeeded
INFO:src.data.generator:Weather source (end): open_meteo; pipeline succeeded
PIPELINE RUN 2
Pipeline start; requested weather provider: auto
OneDrive warning: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml. Use a non-synced location such as C:/dev/coffee-inventory-ml, exclude data/processed from sync, or set COFFEE_DB_DIR. SQLite uses DELETE journaling.
WARNING:src.data.generator:OneDrive warning: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml. Use a non-synced location such as C:/dev/coffee-inventory-ml, exclude data/processed from sync, or set COFFEE_DB_DIR. SQLite uses DELETE journaling.
Weather source (start): open_meteo
INFO:src.data.generator:Weather source (start): open_meteo
Weather source (end): open_meteo; pipeline succeeded
INFO:src.data.generator:Weather source (end): open_meteo; pipeline succeeded
CSV and database CONTENT SHA-256 (run 1 / run 2)
sales_csv: f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1 / f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1 identical=True
truth_csv: 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87 / 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87 identical=True
weather_cache: 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2 / 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2 identical=True
database:sales: be313aa5c01ee31952c7f6771acc7300b59de355ae188b8e714caf55e25de033 / be313aa5c01ee31952c7f6771acc7300b59de355ae188b8e714caf55e25de033 identical=True
database:weather: fd36437e702053641c128d89809c7a8aacb813fb66c7cc66219a48094e60052b / fd36437e702053641c128d89809c7a8aacb813fb66c7cc66219a48094e60052b identical=True
truth_database:simulation_truth: 083a955af35725bedbe542a934c5004b2cbd5fdc07afe965f3685503dd2d41f1 / 083a955af35725bedbe542a934c5004b2cbd5fdc07afe965f3685503dd2d41f1 identical=True
Reconciliation:
{
  "latent_units": 484775,
  "observed_units": 484112,
  "gap": 663,
  "stockout_loss": 5020,
  "missing_loss": 2420,
  "outlier_excess": 6777,
  "unexplained_gap": 0
}
Closure days=9, rows=90, all 10 items zero observed and latent=True
Negative observed counts=0; noninteger observed counts=0
Clean-row weather comparisons (actual descriptive means):
{
  "cold_coffee": {
    "hot_mean": 66.72881355932203,
    "normal_mean": 44.34893617021277,
    "hot_rows": 354,
    "normal_rows": 705,
    "expected_direction_observed": true
  },
  "iced_latte": {
    "hot_mean": 49.68604651162791,
    "normal_mean": 34.19027181688126,
    "hot_rows": 344,
    "normal_rows": 699,
    "expected_direction_observed": true
  },
  "hot_chocolate": {
    "rainy_mean": 31.311377245508982,
    "dry_mean": 23.111721611721613,
    "rainy_rows": 501,
    "dry_rows": 546,
    "expected_direction_observed": true
  },
  "masala_chai": {
    "rainy_mean": 62.4859437751004,
    "dry_mean": 45.78481012658228,
    "rainy_rows": 498,
    "dry_rows": 553,
    "expected_direction_observed": true
  }
}
Per-item promotion counts:
{
  "americano": 74,
  "cappuccino": 69,
  "cold_coffee": 77,
  "croissant": 59,
  "espresso": 66,
  "hot_chocolate": 84,
  "iced_latte": 69,
  "latte": 61,
  "masala_chai": 56,
  "sandwich": 72
}
Mean cross-item normalized residual correlation: sigma=0 0.005194492109425326; sigma=0.07 0.08218818233882166; increase=0.07699369022939634
Exclusive record statuses:
{
  "closed": 90,
  "missing": 56,
  "stockout": 266,
  "outlier": 67,
  "clean": 10481
}
Training-eligible rows=10481
As-of, chronological splits, drift:
{
  "train_start": "2023-01-01",
  "train_end": "2025-02-05",
  "val_start": "2025-02-06",
  "val_end": "2025-07-19",
  "test_start": "2025-07-20",
  "test_end": "2025-12-31",
  "as_of_date": "2025-07-20",
  "forecast_horizon_days": 7,
  "calendar_required_through": "2025-07-27",
  "drift_start": "2025-02-06",
  "drift_plateau_date": "2025-08-05",
  "drift_start_split": "val",
  "drift_ramp_overlap_days": {
    "train": 0,
    "val": 164,
    "test": 16
  },
  "drift_appears_in_test": true,
  "test_contains_shifted_demand": true,
  "split_rule": "floor(train*n), floor(validation*n), remainder to test; never shuffle"
}
Protected-folder truth reference scan: PASS
database: tables=['calendar', 'materials', 'menu', 'recipes', 'sales', 'weather']; integrity=ok; journal_mode=delete
truth_database: tables=['simulation_truth']; integrity=ok; journal_mode=delete
Pre-patch backup integrity: 11 artifacts unchanged
Weather API outage/recovery verified with mocked responses; real historical cache reused.
2027 lunar festival extension: TODO; pinned holiday data does not supply reliable Holi; missing coverage raises a tested validation error.
Phase 1.5 verification complete. Phase 2 has not started.

$ powershell -NoProfile -ExecutionPolicy Bypass -File .\tasks.ps1 -Task setup-check
No broken requirements found.
Python: 3.11.9
Executable: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe
Virtual environment: True
Required library imports: 17 OK
{
  "train_start": "2023-01-01",
  "train_end": "2025-02-05",
  "val_start": "2025-02-06",
  "val_end": "2025-07-19",
  "test_start": "2025-07-20",
  "test_end": "2025-12-31",
  "as_of_date": "2025-07-20",
  "forecast_horizon_days": 7,
  "calendar_required_through": "2025-07-27",
  "drift_start": "2025-02-06",
  "drift_plateau_date": "2025-08-05",
  "drift_start_split": "val",
  "drift_ramp_overlap_days": {
    "train": 0,
    "val": 164,
    "test": 16
  },
  "drift_appears_in_test": true,
  "test_contains_shifted_demand": true,
  "split_rule": "floor(train*n), floor(validation*n), remainder to test; never shuffle"
}
exit_code=0

```

Stopped after Phase 1.5. Awaiting continue before Phase 2.

## Full Phase 2 verification output (2026-10-08)

```text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 74%]
.........................                                                [100%]
============================== warnings summary ===============================
tests/test_environment.py::test_required_library_import[lightgbm]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
tests/test_environment.py::test_required_library_import[lightgbm]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

tests/test_environment.py::test_required_library_import[shap]
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
97 passed, 14 warnings in 17.61s
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
41 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task features
{
  "rows": 10960,
  "predictors": 40,
  "split_counts": {
    "test": {
      "rows": 1650,
      "eligible_targets": 1593
    },
    "train": {
      "rows": 7670,
      "eligible_targets": 7326
    },
    "val": {
      "rows": 1640,
      "eligible_targets": 1562
    }
  },
  "eda": {
    "split": "train",
    "rows": 7670,
    "clean_rows": 7326,
    "start_date": "2023-01-01",
    "end_date": "2025-02-05",
    "weekly_clean_mean": {
      "0": 38.09942638623327,
      "1": 39.64957264957265,
      "2": 39.70037807183365,
      "3": 40.04381694255112,
      "4": 42.727878211227406,
      "5": 47.975190839694655,
      "6": 47.93480345158198
    },
    "festival_groups": {
      "before festival": {
        "mean": 50.964285714285715,
        "count": 196
      },
      "festival day": {
        "mean": 36.885714285714286,
        "count": 105
      },
      "ordinary": {
        "mean": 42.1423487544484,
        "count": 7025
      }
    },
    "stockout_fraction_by_item": {
      "cold_coffee": 0.018252933507170794,
      "latte": 0.018252933507170794,
      "cappuccino": 0.02216427640156454,
      "espresso": 0.02346805736636245,
      "iced_latte": 0.02346805736636245,
      "masala_chai": 0.02346805736636245,
      "croissant": 0.024771838331160364,
      "americano": 0.024771838331160364,
      "hot_chocolate": 0.024771838331160364,
      "sandwich": 0.028683181225554105
    },
    "figures": {
      "weekly": "eda_weekly.png",
      "festival": "eda_festival.png",
      "weather": "eda_weather.png",
      "trend": "eda_trend.png",
      "stockouts": "eda_stockouts.png"
    },
    "limitations": "Synthetic sales; historical realized weather; group differences are confounded. EDA uses train dates by default."
  }
}
exit_code=0
Notebook execution: 4 code cells, 5 embedded PNG plots; schema validated
Python: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe
{
  "rows": 10960,
  "predictors": 40,
  "split_counts": {
    "test": {
      "rows": 1650,
      "eligible_targets": 1593
    },
    "train": {
      "rows": 7670,
      "eligible_targets": 7326
    },
    "val": {
      "rows": 1640,
      "eligible_targets": 1562
    }
  },
  "eda": {
    "split": "train",
    "rows": 7670,
    "clean_rows": 7326,
    "start_date": "2023-01-01",
    "end_date": "2025-02-05",
    "weekly_clean_mean": {
      "0": 38.09942638623327,
      "1": 39.64957264957265,
      "2": 39.70037807183365,
      "3": 40.04381694255112,
      "4": 42.727878211227406,
      "5": 47.975190839694655,
      "6": 47.93480345158198
    },
    "festival_groups": {
      "before festival": {
        "mean": 50.964285714285715,
        "count": 196
      },
      "festival day": {
        "mean": 36.885714285714286,
        "count": 105
      },
      "ordinary": {
        "mean": 42.1423487544484,
        "count": 7025
      }
    },
    "stockout_fraction_by_item": {
      "cold_coffee": 0.018252933507170794,
      "latte": 0.018252933507170794,
      "cappuccino": 0.02216427640156454,
      "espresso": 0.02346805736636245,
      "iced_latte": 0.02346805736636245,
      "masala_chai": 0.02346805736636245,
      "croissant": 0.024771838331160364,
      "americano": 0.024771838331160364,
      "hot_chocolate": 0.024771838331160364,
      "sandwich": 0.028683181225554105
    },
    "figures": {
      "weekly": "eda_weekly.png",
      "festival": "eda_festival.png",
      "weather": "eda_weather.png",
      "trend": "eda_trend.png",
      "stockouts": "eda_stockouts.png"
    },
    "limitations": "Synthetic sales; historical realized weather; group differences are confounded. EDA uses train dates by default."
  }
}
weekly
festival
weather
trend
stockouts
Predictors: 40
['item', 'category', 'price', 'promo_flag', 'day_of_week', 'weekend_flag', 'day_of_month', 'week_of_year', 'month', 'month_end_flag', 'holiday_flag', 'festival_flag', 'days_to_next_festival', 'days_since_last_festival', 'payday_flag', 'long_weekend_flag', 'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos', 'day_of_month_sin', 'day_of_month_cos', 'week_of_year_sin', 'week_of_year_cos', 'temp_max', 'temp_min', 'rainfall', 'rain_flag', 'temp_bucket', 'sales_lag_1', 'sales_lag_7', 'sales_lag_14', 'sales_lag_28', 'sales_rolling_mean_7', 'sales_rolling_std_7', 'sales_rolling_mean_28', 'sales_rolling_std_28', 'history_days', 'cold_start_flag', 'category_past_mean']
Eligible targets by split:
split
test     1593
train    7326
val      1562
Name: target_eligible, dtype: int64
Current/future observation mutation: predictors through 2025-07-20 unchanged — PASS
Protected feature/model source scan: PASS
Source artifacts unchanged (SHA-256):
sales_csv: f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1; unchanged=True
truth_csv: 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87; unchanged=True
weather_cache: 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2; unchanged=True
database: 12cf4d174c631000756f3ecdd3d4d7d782fc8e3ad003a5282daaf806e20ef078; unchanged=True
truth_database: a4e210e059cb4413c75494aa41d4278af12d27fa1d484ff1f04e0635208381c1; unchanged=True
Feature export: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\data\processed\features.csv; predictors=40
No models trained. Phase 2 complete; stop before Phase 3.

```

## Full Phase 3 verification output (2026-10-08)

```text
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pytest -q
........................................................................ [ 62%]
............................................                             [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

.venv\Lib\site-packages\matplotlib\_mathtext.py:45
  C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Lib\site-packages\matplotlib\_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
116 passed, 14 warnings in 19.21s
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m ruff format --check src tests
45 files already formatted
exit_code=0
$ C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe -m pip check
No broken requirements found.
exit_code=0
$ powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\tasks.ps1 -Task train
CV candidate 1/4 complete: {'num_leaves': 15, 'learning_rate': 0.03}
CV candidate 2/4 complete: {'num_leaves': 15, 'learning_rate': 0.05}
CV candidate 3/4 complete: {'num_leaves': 31, 'learning_rate': 0.03}
CV candidate 4/4 complete: {'num_leaves': 31, 'learning_rate': 0.05}
Validation ML point selection: lightgbm; WAPE=0.207240
Recursive test origins 4/23 complete
Recursive test origins 8/23 complete
Recursive test origins 12/23 complete
Recursive test origins 16/23 complete
Recursive test origins 20/23 complete
{
  "selected_point_model": "lightgbm",
  "selection": "validation WAPE after train-only five-fold tuning",
  "best_parameters": {
    "num_leaves": 15,
    "learning_rate": 0.03
  },
  "training_through": "2025-07-19",
  "test_rows": 1593,
  "one_day_test_metrics": [
    {
      "model": "ridge",
      "item": "overall",
      "rows": 1593,
      "wape": 0.20672707785944983,
      "mae": 11.118490803367283,
      "rmse": 14.642547139997916,
      "bias": -0.7062035713100376,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "lightgbm",
      "item": "overall",
      "rows": 1593,
      "wape": 0.21492760998826535,
      "mae": 11.559543528540244,
      "rmse": 15.548871939553486,
      "bias": -2.18610886597426,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "naive",
      "item": "overall",
      "rows": 1593,
      "wape": 0.29402912489155003,
      "mae": 15.81389412010881,
      "rmse": 20.890915309543782,
      "bias": -0.1609123247541327,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "item": "overall",
      "rows": 1593,
      "wape": 0.28905949087853217,
      "mae": 15.546610169491526,
      "rmse": 20.70440772643603,
      "bias": -0.3166038920276208,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "moving_average",
      "item": "overall",
      "rows": 1593,
      "wape": 0.232384698454939,
      "mae": 12.498445580366484,
      "rmse": 16.406700748847424,
      "bias": -0.29345051265955224,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "quantile_p50",
      "item": "overall",
      "rows": 1593,
      "wape": 0.21928874211312455,
      "mae": 11.794100161974997,
      "rmse": 15.966126727689879,
      "bias": -3.2828901541078177,
      "interval_coverage": 0.7407407407407407,
      "mean_interval_width": 32.89390973602061
    }
  ],
  "relative_wape_improvement": 0.2564589063135738,
  "required_wape_improvement": 0.15,
  "meets_requested_improvement": true,
  "raw_quantile_crossings": 0,
  "nominal_interval_coverage": 0.8,
  "recursive_test_metrics": [
    {
      "model": "lightgbm",
      "horizon_day": 1,
      "rows": 224,
      "wape": 0.20235057338307727,
      "mae": 12.441850210737158,
      "rmse": 16.986129370527646,
      "bias": -2.8546696440153463,
      "interval_coverage": 0.78125,
      "mean_interval_width": 37.081062593876915
    },
    {
      "model": "lightgbm",
      "horizon_day": 2,
      "rows": 218,
      "wape": 0.2503067043597271,
      "mae": 11.983720520194824,
      "rmse": 16.403029883094682,
      "bias": -2.18195740649673,
      "interval_coverage": 0.6743119266055045,
      "mean_interval_width": 30.663778149564727
    },
    {
      "model": "lightgbm",
      "horizon_day": 3,
      "rows": 224,
      "wape": 0.2166779827033463,
      "mae": 10.911284128989937,
      "rmse": 14.769251965092755,
      "bias": -2.9999686459506205,
      "interval_coverage": 0.7678571428571429,
      "mean_interval_width": 31.255328578118192
    },
    {
      "model": "lightgbm",
      "horizon_day": 4,
      "rows": 219,
      "wape": 0.20772302723483985,
      "mae": 10.444958794109846,
      "rmse": 13.80577251499552,
      "bias": -1.2897739733675408,
      "interval_coverage": 0.7671232876712328,
      "mean_interval_width": 31.496523497238808
    },
    {
      "model": "lightgbm",
      "horizon_day": 5,
      "rows": 224,
      "wape": 0.23665483224582143,
      "mae": 11.636233581944095,
      "rmse": 15.732397666134837,
      "bias": -0.35339070117172705,
      "interval_coverage": 0.7142857142857143,
      "mean_interval_width": 30.226993969929612
    },
    {
      "model": "lightgbm",
      "horizon_day": 6,
      "rows": 222,
      "wape": 0.19937137461378426,
      "mae": 11.146835593271577,
      "rmse": 14.282815274448888,
      "bias": -3.8357436922626262,
      "interval_coverage": 0.7432432432432432,
      "mean_interval_width": 33.825821547893945
    },
    {
      "model": "lightgbm",
      "horizon_day": 7,
      "rows": 223,
      "wape": 0.2029759613373367,
      "mae": 11.849063070356273,
      "rmse": 15.420144404118952,
      "bias": -0.4907855323024416,
      "interval_coverage": 0.7982062780269058,
      "mean_interval_width": 37.67359228500186
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 1,
      "rows": 224,
      "wape": 0.2977346983228055,
      "mae": 18.30669642857143,
      "rmse": 24.848633130463757,
      "bias": 0.12217261904761896,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 2,
      "rows": 218,
      "wape": 0.3046820606176743,
      "mae": 14.587003058103976,
      "rmse": 19.339800537012188,
      "bias": -0.10382262996941899,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 3,
      "rows": 224,
      "wape": 0.2744473995271867,
      "mae": 13.820386904761904,
      "rmse": 17.75556376584132,
      "bias": -0.11264880952380953,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 4,
      "rows": 219,
      "wape": 0.2790713161399685,
      "mae": 14.032572298325723,
      "rmse": 18.695449108047608,
      "bias": 0.08310502283105012,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 5,
      "rows": 224,
      "wape": 0.3326009321469645,
      "mae": 16.35386904761905,
      "rmse": 22.13929051536678,
      "bias": 0.9610119047619047,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 6,
      "rows": 222,
      "wape": 0.26433021806853585,
      "mae": 14.778678678678679,
      "rmse": 18.886993103946125,
      "bias": 0.14864864864864877,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "seasonal_naive",
      "horizon_day": 7,
      "rows": 223,
      "wape": 0.2705868797050238,
      "mae": 15.795964125560538,
      "rmse": 20.72967335125246,
      "bias": -0.6689088191330345,
      "interval_coverage": null,
      "mean_interval_width": null
    },
    {
      "model": "lightgbm",
      "horizon_day": "overall",
      "rows": 1554,
      "wape": 0.2152539487155814,
      "mae": 11.4893526577623,
      "rmse": 15.381101323851572,
      "bias": -2.0010978006334423,
      "interval_coverage": 0.7496782496782497,
      "mean_interval_width": 33.1860901013381
    },
    {
      "model": "seasonal_naive",
      "horizon_day": "overall",
      "rows": 1554,
      "wape": 0.28833457912376725,
      "mae": 15.39009009009009,
      "rmse": 20.480444122347333,
      "bias": 0.06229086229086219,
      "interval_coverage": null,
      "mean_interval_width": null
    }
  ],
  "limitations": [
    "Synthetic shop data; no real-shop generalization claim.",
    "Persistence weather is less informative than future realized weather, deliberately excluded.",
    "One-day scores use earlier observed test history; recursive scores use predictions.",
    "Quantile intervals are empirical and uncalibrated; recursive uncertainty is conditional on a predicted history path.",
    "Cold-start point forecasts use past category means; quantile fallback uses training-category empirical quantiles.",
    "SHAP drivers are model associations, not causal effects."
  ]
}
exit_code=0
Modeling notebook: 4 code cells executed; 3 embedded charts; schema validated
Python: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe
Validation-selected: lightgbm
Relative one-day WAPE improvement: 0.2564589063135738
Requested improvement achieved: True
comparison
intervals
shap
Trained through: 2025-07-19
{
  "forecast": 54.259332412705426,
  "raw_model_estimate": 54.259332412705504,
  "reference": 43.06334383438392,
  "method": "additive SHAP association; not causal",
  "drivers": [
    {
      "feature": "day_of_week",
      "contribution": 4.846111471980016,
      "explanation": "day of week raised the model estimate by 4.85 units relative to its reference."
    },
    {
      "feature": "history_days",
      "contribution": 3.816796964157435,
      "explanation": "history days raised the model estimate by 3.82 units relative to its reference."
    },
    {
      "feature": "rainfall",
      "contribution": 1.1637398913209247,
      "explanation": "Forecast rainfall raised the model estimate by 1.16 units relative to its reference."
    },
    {
      "feature": "sales_rolling_mean_7",
      "contribution": 0.7804259705655955,
      "explanation": "sales rolling mean 7 raised the model estimate by 0.78 units relative to its reference."
    },
    {
      "feature": "promo_flag",
      "contribution": -0.6970102852778206,
      "explanation": "The planned promotion lowered the model estimate by 0.70 units relative to its reference."
    }
  ]
}

Fixed-origin future sales/weather mutation: PASS
Training cutoff before demo origin: PASS
Protected feature/model reference scan: PASS
Walk-forward: 5 folds; 40 model/candidate/fold rows; every training cutoff before validation
Saved artifact reload vs exported test predictions: PASS
No source artifacts changed (SHA-256):
sales_csv: f0cfccbacc248a03ca2594f8e07d5357fe23e29302b20667ce38639397bf82d1; unchanged=True
truth_csv: 747553c6fcf8c0a3fc1a512b1d089c00ee5b99ced7b3597e8a536b0a2c218a87; unchanged=True
weather_cache: 8de5227a7cff4939e554a3257572ebe1e92a51cc02f76c632a03717bf0a441f2; unchanged=True
database: 12cf4d174c631000756f3ecdd3d4d7d782fc8e3ad003a5282daaf806e20ef078; unchanged=True
truth_database: a4e210e059cb4413c75494aa41d4278af12d27fa1d484ff1f04e0635208381c1; unchanged=True
features_csv: a5e512e7f7ec05cd44185c3b3f984a7a630262f38bb207a367ccc936405d14ba; unchanged=True
Pre-1.5 backup integrity: 11 artifacts unchanged
Optional SARIMAX remains disabled. No inventory engine or simulation implemented.
Phase 3 complete. Stop before Phase 4.

Final CSV formatting audit (no metric/prediction values changed):
model_metrics_csv: 121 records unchanged; Windows CSV newline check=PASS
model_predictions: 1593 records unchanged; Windows CSV newline check=PASS
model_cv_results: 40 records unchanged; Windows CSV newline check=PASS
model_recursive_metrics: 16 records unchanged; Windows CSV newline check=PASS
demo_forecast: 70 records unchanged; Windows CSV newline check=PASS
$ .\.venv\Scripts\python.exe -m ruff check src tests
All checks passed!
exit_code=0
$ .\.venv\Scripts\python.exe -m ruff format --check src tests
45 files already formatted
exit_code=0

Final notebook and local explanation audit:
Modeling notebook: 4 code cells executed; 3 embedded charts; schema validated
Python: C:\Users\aamit\OneDrive\Desktop\ProjectX\coffee-inventory-ml\.venv\Scripts\python.exe
Validation-selected: lightgbm
Relative one-day WAPE improvement: 0.2564589063135738
Requested improvement achieved: True
comparison
intervals
shap
Trained through: 2025-07-19
{
  "forecast": 54.259332412705426,
  "raw_model_estimate": 54.259332412705504,
  "reference": 43.06334383438392,
  "method": "additive SHAP association; not causal",
  "drivers": [
    {
      "feature": "day_of_week",
      "contribution": 4.846111471980016,
      "explanation": "day of week raised the model estimate by 4.85 units relative to its reference."
    },
    {
      "feature": "history_days",
      "contribution": 3.816796964157435,
      "explanation": "history days raised the model estimate by 3.82 units relative to its reference."
    },
    {
      "feature": "rainfall",
      "contribution": 1.1637398913209247,
      "explanation": "Forecast rainfall raised the model estimate by 1.16 units relative to its reference."
    },
    {
      "feature": "sales_rolling_mean_7",
      "contribution": 0.7804259705655955,
      "explanation": "sales rolling mean 7 raised the model estimate by 0.78 units relative to its reference."
    },
    {
      "feature": "promo_flag",
      "contribution": -0.6970102852778206,
      "explanation": "No planned promotion lowered the model estimate by 0.70 units relative to its reference."
    }
  ]
}

Fixed-origin future sales/weather mutation: PASS
Training cutoff before demo origin: PASS

```

Stopped after Phase 3. Awaiting continue before Phase 4.
