# Phase 6 API contract

The FastAPI application exposes eight endpoint operations on seven business paths.
Create independent test/application state with `create_app(config)`. Importing the
module constructs the app but does not load a model or write inventory. The saved
model loads lazily and is reused; restart the server after changing model/config
artifacts. The default server is one process on 127.0.0.1:8000.

## Routes

| Method | Path | Behavior |
|---|---|---|
| GET | /health | Artifact existence and inventory readability; ready or degraded |
| GET | /forecast/items?days=7 | Item point forecasts and ordered P10/P50/P90 |
| GET | /forecast/materials?days=7 | Wastage-adjusted BOM requirements in native units |
| GET | /recommendations/orders | Receipt-centered recommendations using current inventory revision |
| GET | /inventory | Versioned snapshot, effective date and illustrative flag |
| POST | /inventory | Patch supplied material rows after expected-version check |
| POST | /whatif | Baseline/scenario forecasts, scenario material needs and point-total delta |
| GET | /model/metrics | Saved model metrics and available simulation results |

Swagger UI is at /docs; schema JSON is at /openapi.json. The verified schema is
also exported to reports/api_openapi.json. Unknown payload fields are rejected.

## Forecast origin and inputs

The API uses the configured project.as_of_date, or the first held-out test date
when null. This is the reproducible demo origin (currently 2025-07-20), not the
computer's current date. GET forecast days must be an integer from 1 through
api.max_forecast_days (currently 30). Calendar coverage is checked for the entire
request. Unsupported lunar-calendar years fail clearly.

Histories contain only observed sales before origin. Future model plans contain
only date, item, category, price and promotion. Dates beyond generated metadata use
menu base prices with no promotion. Weather defaults to prior persistence.
Models trained on/after origin are rejected by the existing forecast contract.
Neither API forecasting nor recommendations load evaluation-only demand.

Item responses contain as_of_date, days, model, scenario, forecasts and limitations.
Material responses contain as_of_date, days, requirements and limitations.
Forecast counts and material needs are fractional expectations, not whole sales.
Quantile bands and summed material quantiles remain uncalibrated proxies.

Recommendations forecast through every supplier lead time plus usable receipt
coverage, currently 11 days. They report inventory_version, illustrative_inventory,
quantity, order dates, safety stock, reorder point, pre-arrival shortage, unfilled
quantity, estimated cost and reason. They do not place supplier orders.
The aggregate snapshot supports one pending receipt per material, matching the
Phase 4 public planner. Existing lot ages are not supplied through this API;
the Phase 5 FIFO engine is a separate evaluation component.

## Inventory revisions and atomic writes

Before any caller update, GET /inventory returns the saved Phase 4 illustrative
snapshot, version 0. If that CSV is unavailable, prior valid observed means produce
a clearly illustrative fallback. GET requests do not create persistent state.

POST /inventory accepts:
~~~json
{
  "expected_version": 0,
  "rows": [
    {"material": "milk", "on_hand": 100000, "on_order": 5000,
     "arrival_date": "2025-07-21"}
  ]
}
~~~

Rows replace the supplied materials' complete aggregate row; omitted materials are
preserved. Omitted on_order defaults to zero and arrival_date to null. Material keys
must be known and unique. Quantities must be finite, nonnegative numeric values;
booleans are rejected. Positive pending stock requires an arrival on/after the
snapshot date; zero pending stock requires a null arrival.

expected_version is a required nonnegative integer. A successful update increments
the version and sets illustrative=false. A stale version returns HTTP 409 with the
current revision. Caller-supplied values are not independently verified stock counts.

Updates serialize through the application lock, stage the JSON and publish with
the shared atomic replacement/rollback helper. A failed write leaves the previous
revision unchanged. State persists in the separate configured api_inventory_state
JSON and survives restart. Generated CSVs, databases, model and simulation artifacts
are not modified.

Use a single application/server process: the lock is process-local. CLI startup
requires api.workers=1. Running multiple workers/processes against one JSON state
is unsupported; a transactional database-backed revision store is a future extension.

## What-if scenarios

Example:
~~~json
{
  "days": 1,
  "temp_max": 35,
  "temp_min": 25,
  "rainfall": 0,
  "promotions": {"latte": true},
  "festivals": {"2025-07-20": true}
}
~~~

Weather fields apply uniformly across the requested horizon. Missing weather values
use prior persistence values, and resulting minimum/maximum must be ordered.
Rainfall must be nonnegative and all supplied weather values finite. Scenario
weather is explicitly hypothetical, with an internally synthesized issue time
before origin; it is not presented as an externally sourced weather forecast.

Promotions are strict booleans keyed by known menu item, applying across the horizon.
The scenario also applies the configured promotion discount to base menu price.
Festival booleans are keyed by dates inside the requested horizon: true inserts
a scenario festival, false removes the event for that date. Calendar distances
and long-weekend flags are recomputed in the isolated configuration copy.
Original required lunar-calendar coverage is still enforced.

The response includes unchanged baseline forecast, scenario forecast, scenario
material requirements and point_total_change. Scenarios do not save configuration,
models, inventory or reports. Changes represent model associations; they do not
establish causal uplift. An empty scenario reproduces the baseline.

## Errors and readiness

HTTP 422 covers invalid request values, unknown/duplicate materials/items, invalid
pending dates, out-of-horizon scenarios and unsupported calendar/forecast ranges.
HTTP 409 covers stale inventory revisions.
HTTP 503 covers unavailable required files and file-access failures.
Validation errors return type, location and message without echoing rejected values;
this allows NaN/Infinity input to fail with valid JSON rather than a serialization error.
Health is a lightweight file/readability check; a forecast request additionally
verifies model loading and prediction behavior.

This is a local development API with no authentication, TLS or external deployment
in this phase. Localhost is the configured default. External hosting and multiuser
security are outside the current request.

## Running and verification

~~~powershell
.\tasks.ps1 -Task api
# In another PowerShell session:
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod 'http://127.0.0.1:8000/forecast/items?days=7'
.\.venv\Scripts\python.exe -m src.verification.phase_6
~~~

Tests exercise real saved-model forecasts, hand-checked BOM conversion, recommendations
after inventory updates, scenario isolation, strict validation, persistence/restart,
concurrent revision conflicts, failed publication recovery and missing-artifact errors.
The full verifier also launches the real CLI server on a temporary loopback port,
checks routes/docs/schema, stops that server, and verifies unchanged prior artifacts
and all pre-1.5 backups. No live smoke POST updates persistent demo inventory.
Stop before Phase 7 dashboard until the next continue instruction.
