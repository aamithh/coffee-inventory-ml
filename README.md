# Coffee inventory ML

A complete college project that forecasts daily coffee-shop menu demand, converts
it into ingredient needs and proposes orders with lead-time, shelf-life and
uncertainty constraints. FastAPI and a seven-screen Streamlit dashboard run locally
without paid services. Phases 0–8 are implemented.

This is a **synthetic Bengaluru shop**, not a real-shop deployment. The saved
planning date is **2025-07-20**; initial dashboard stock is illustrative.

## For your report collaborator

This repository includes the fitted model and verified synthetic demo data, so
you can explore the dashboard without regenerating data or retraining.

Start with [the project report](docs/report.md), [the slide outline](docs/slide_outline.md),
[the demo script](docs/demo_script.md) and [the data dictionary](docs/data_dictionary.md).
Measured results and charts are in reports/; the fitted model is in models/.
The interface is named **Brew & Balance**. The dataset is synthetic; do not describe
these measurements as proof of real-world performance.

After downloading/cloning this repository, install Python 3.11 and run from its folder:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.cli setup-check
.\.venv\Scripts\python.exe -m src.cli dashboard
~~~

Open http://localhost:8501. You do not need to run data, train or simulate to view
the included demo. Stop the dashboard with Ctrl+C.

## Setup and usage

Run from this folder. For the existing Windows environment:

~~~powershell
.\.venv\Scripts\python.exe -m src.cli setup-check
.\tasks.ps1 -Task dashboard
# Open http://127.0.0.1:8501
~~~

Stop servers with Ctrl+C. The default local dashboard needs no separate API.

For a fresh environment, install Python 3.11 and run:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\tasks.ps1 -Task setup-check
.\tasks.ps1 -Task data
.\tasks.ps1 -Task features
.\tasks.ps1 -Task train
.\tasks.ps1 -Task inventory
.\tasks.ps1 -Task simulate
.\tasks.ps1 -Task test
~~~

Python 3.11.9 is verified; source targets Python 3.10+. requirements.txt pins direct
dependencies. Training builds features directly from observed data; features also
exports EDA/feature reports. Simulation needs generated data and a fitted model.
Do not rebuild the saved demo during a presentation.

GNU Make is optional. Where installed, the equivalent requested sequence is:

~~~powershell
make setup
make data
make train
make simulate
make inventory
make api
# Separate terminal:
make dashboard
~~~

Final verification exercises the command implementations through tasks.ps1 in the
existing venv with empty temporary sales/model/replay outputs. A fresh pip install
and GNU Make execution were not independently tested on this host.

## Commands and configuration

| Task | Purpose |
|---|---|
| setup-check | Venv, required imports, dates and dependency validation |
| data | Seeded generator, quality checks and separate observed/truth SQLite |
| features | Past-only feature export, training EDA and five figures |
| train | Five-fold tuning, validation selection, test evaluation and saved models |
| inventory | BOM requirements and supplier/expiry-constrained illustrative orders |
| simulate | FIFO replay of manual, seasonal-naive and ML policies |
| api | FastAPI at configured localhost:8000 |
| dashboard | Seven-screen Streamlit app at configured localhost:8501 |
| test | Full pytest suite |

Paths, menu, recipes, assumptions and controls are in
[config/config.yaml](config/config.yaml). Alternative configuration:

~~~powershell
.\.venv\Scripts\python.exe -m src.cli --config config/config.yaml data
.\tasks.ps1 -Task data --config config/config.yaml
~~~

Auto weather uses a validated real cache or free historical Open-Meteo data;
after fallback it retries the API next generation. For fully offline generation,
set data.weather_provider to synthetic in a separate YAML file. Changing weather
or domain settings changes results; retrain/replay before comparing scores.
Historical reanalysis drives generation, not future forecast inputs.

## Architecture

~~~mermaid
flowchart LR
  C[YAML settings] --> D[Generator / weather / calendar]
  D --> O[(Observed SQLite and CSV)]
  D --> T[(Separate evaluation truth)]
  O --> F[Past-only features / training EDA]
  F --> M[Train CV / validation selection / saved models]
  M --> P[Recursive forecasts / SHAP]
  O --> P
  P --> B[BOM / material needs / reorder planner]
  B --> S[FIFO policy replay]
  T --> S
  P --> A[FastAPI and service modules]
  B --> A
  A --> U[Streamlit dashboard]
  S --> R[Results / charts / report]
~~~

Truth enters evaluation only after forecasts are frozen. Feature/model modules
cannot access it through the public loader. Prediction uses known plans/calendar,
past observations and weather issued before origin, with persistence by default.

| Folder | Responsibility |
|---|---|
| src/data | Stable RNG, weather/cache, calendar, quality, SQLite, staged publication |
| src/features, src/eda | Past-only lags/rolling/category inputs and training plots |
| src/models | Baselines, Ridge/LightGBM/quantiles, chronological scores, recursion, SHAP |
| src/inventory | BOM, needs, reorder constraints, FIFO lots and policy replay |
| src/api | Validated endpoints and single-process versioned inventory service |
| src/dashboard | Views, local/HTTP backend, charts and forms |
| src/utils, src/verification | Config/date/metric utilities and reproducible checks |
| notebooks | Thin executed EDA/model/simulation narratives calling core modules |
| tests | Core calculations, leakage, API validation and dashboard interaction |

## Measured results

One-day scores use **1,593 clean held-out item-days**. Deployment selection was
frozen using validation before test scoring.

| Model | One-day test WAPE |
|---|---:|
| Yesterday naive | 29.40% |
| Seasonal naive | 28.91% |
| Seven-day mean | 23.24% |
| Ridge | 20.67% |
| Selected LightGBM | 21.49% |
| Quantile P50 | 21.93% |

LightGBM improves seasonal-naive WAPE **25.65% relatively**, exceeding the requested
15%. Ridge scored better on test; deployment was not changed using that result.
Seven-day recursive WAPE is 21.53% versus 28.83% seasonal naive. P10–P90 coverage
is 74.07% versus nominal 80%, so the bands are uncalibrated.

The 165-day FIFO replay uses identical stock and 88,436 requested menu units:

| Policy | Service | Lost units | Expiry INR | Gross modeled cost INR |
|---|---:|---:|---:|---:|
| Manual | 99.14% | 762 | 44,868.33 | 3,042,230.92 |
| Seasonal naive | 97.03% | 2,626 | 5,539.00 | 3,206,115.12 |
| ML | 98.44% | 1,383 | 1,731.45 | 3,035,995.04 |

ML expiry cost is **96.14% lower than manual**, but lost units are **81.50% higher**.
Against seasonal naive ML loses 47.33% fewer units. Its 0.205% gross-cost advantage
over manual reverses under full closing-stock/pipeline credit. These results show
a waste/service tradeoff, not universal or real-shop savings. No policy/generator
parameters were tuned to force favorable test results.

## API and dashboard

~~~powershell
.\tasks.ps1 -Task api
# Swagger: http://127.0.0.1:8000/docs
# Separate terminal:
.\tasks.ps1 -Task dashboard
~~~

API paths: /health, /forecast/items, /forecast/materials,
/recommendations/orders, GET/POST /inventory, /whatif and /model/metrics.
Stock updates require expected_version and save to separate JSON. Strict request
validation returns clear 422/409/503 errors.

The dashboard interface is named **Brew & Balance**, with a colorful café theme,
plain-language labels and guided shortcuts. Screens: Overview, Demand Forecast, Raw Materials, Order Recommendations,
Insights, Model Performance and What-If. Stock forms detect stale revisions;
scenarios preserve baseline/model/inventory. CSV order exports are proposals,
not purchases. Future actuals are unavailable at the historical demo origin.

Use one inventory writer process. To share edits, set dashboard.backend to http
and dashboard.api_url to the running API. Independent local writer processes
must not edit the same JSON store. Restart after artifact/config changes.

## Verification and documentation

~~~powershell
.\.venv\Scripts\python.exe -m src.verification.phase_8
~~~

This runs full pytest, Ruff lint/format, pip checks, a full-size isolated workflow,
live API/dashboard startup, saved notebook validation and original-file hash audits.
Complete transcript: reports/phase_8_verification.txt and [PROGRESS.md](PROGRESS.md).
Weather tests use mocks; the workflow uses the validated historical cache.
Existing processed outputs are preserved. Windows sandbox restrictions may require
approved access for temporary replacements and loopback sockets; the exact command
above can also be run locally.

Read the [final report](docs/report.md), [six-slide outline](docs/slide_outline.md)
and [four-minute demo script](docs/demo_script.md).
Detailed contracts: [assumptions](docs/assumptions.md),
[data dictionary](docs/data_dictionary.md), [features](docs/feature_contract.md),
[modeling](docs/modeling_contract.md), [inventory](docs/inventory_contract.md),
[simulation](docs/simulation_contract.md), [API](docs/api_contract.md) and
[dashboard/screenshot guide](docs/dashboard_guide.md).

Saved models/reports/figures and three live dashboard screenshots are included.
The trusted local bundle is models/forecast_bundle.joblib; metrics are in
reports/metrics.json and reports/simulation_metrics.json.

## Persistence and limits

coffee.sqlite contains observed records; simulation_truth.db is evaluation-only.
Use src.data.loader.load_sales for observed data. DELETE journaling and explicit
connection closure support Windows replacements. To use non-synced database paths:

~~~powershell
$env:COFFEE_DB_DIR = 'C:\dev\coffee-data'
.\tasks.ps1 -Task data
# Keep the variable set for all later consumers.
# Remove only when returning to the original databases:
Remove-Item Env:\COFFEE_DB_DIR
~~~

The override changes both databases only. Outputs validate in staging before
publication; handled failures roll back. Multiple-file process crashes are not
globally atomic. Eleven original backups and their manifest remain under
data/processed/backup_pre_1_5.

Synthetic demand, assumed prices/storage, common factual POS history across
policies, uncalibrated intervals and unknown aggregate stock ages limit claims.
Lunar dates end in 2026; unsupported 2027 requests fail until reviewed dates are
added. Multiworker authentication/transactional inventory is future work.
