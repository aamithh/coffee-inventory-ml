# Phase 7 dashboard contract and screenshot guide

## Running

~~~powershell
.\tasks.ps1 -Task dashboard
~~~

Open http://127.0.0.1:8501. The default local mode directly reuses the existing
forecast/inventory service modules, so a separate API process is not required.
The CLI runs headless Streamlit with usage telemetry disabled and a configured
light theme. Host, port, colors, history range, controls and timeouts are in YAML.

For a dashboard that shares the running API, set dashboard.backend to http and
dashboard.api_url to its configured loopback URL, then start:
~~~powershell
# First terminal:
.\tasks.ps1 -Task api
# Second terminal:
.\tasks.ps1 -Task dashboard
~~~

Keep one writer process for inventory state. In local mode the dashboard owns its
service/lock; do not simultaneously edit the same JSON from a separate local API
process. HTTP mode routes edits through the API's revision lock. All browser sessions
of one local dashboard share its cached service and lock. Restart after replacing
model/config artifacts. Historical plots and explanations still use local modules.

The header shows the configured planning date (currently 2025-07-20), not wall-clock
today. Initial stock is explicitly illustrative. No evaluation-only demand is loaded
by dashboard forecasting or stock planning.

## Screens

| Screen | Contents |
|---|---|
| Overview | Next-day expected menu units, materials to order, proposed cost, delivery/pack alerts and item demand |
| Demand Forecast | Item selector, prior valid observed counts, future point forecast, P10–P90 band and values |
| Raw Materials | Native-unit needs/stock/coverage/status table, stock editor and material forecast |
| Order Recommendations | Quantities, dates, costs, reasons and CSV download |
| Insights | Live first-day signed SHAP drivers plus training weekday/festival/weather plots |
| Model Performance | Held-out metrics/WAPE and FIFO waste/service/cost comparisons |
| What-If | Weather sliders, promotion and first-day festival controls, baseline/scenario comparison |

Every screen has a short help note. The sidebar selects screen and forecast horizon.
On narrow windows it collapses; use the top-left arrow to open navigation.
Tables use readable labels and two decimal places without changing underlying
calculation precision. Error, coverage and service rates display as percentages.
Plotly charts remain interactive.

## Forecast and interpretation rules

Demand charts include only clean/closed prior observations. Defective historical
records are not drawn as reliable actuals. Future actual sales are unavailable at
the demo origin; forecast lines and intervals are shown separately.
Point forecasts can differ from P50. Bands are uncalibrated marginal estimates and
do not propagate complete recursive path uncertainty.

Material days of cover = on_hand / mean point need over the selected forecast horizon.
Zero mean demand gives undefined cover, not an artificial finite number.
Materials remain in their native g/ml/pcs units. Recipe wastage applies once.

Stock status prioritizes shortage before delivery, supplier/expiry unmet quantity,
then order recommendation. Supplier recommendations remain proposals; downloads
do not create purchases. Aggregate inventory lacks existing lot-age expiry detail.

Insights explain the selected saved model on the first forecast day using the same
past-only feature builder. Top-five signed driver phrases and contributions are
associations, not causal effects. Weekday/festival/weather plots describe training
data, and may reflect confounding from trend/promotions.

Model Performance preserves validation-based model selection and shows honest
simulation tradeoffs: ML reduces waste versus manual but loses more sales, and its
small gross-cost advantage can reverse after terminal inventory credit.

## Inventory editor and conflicts

Raw Materials can replace one material's full aggregate row: on-hand quantity,
pending quantity and arrival date. A zero pending quantity sends a null arrival.
The form retains the inventory revision from when its selected material was loaded.
If stock changes while the form is open, saving reports a conflict rather than
silently applying the stale form to the new revision.

Use Reload stock after a conflict. Successful save uses the existing atomic JSON
publisher, increments the revision, and reruns the view to refresh coverage and
recommendations. Tests save only isolated temporary inventory; verification and
visual review leave persistent demo state unchanged.

## What-if form

A submitted scenario applies weather uniformly across the selected horizon,
optional promotion changes to one item and an optional festival change on the first
forecast date. Schema validation enforces finite ordered temperatures and valid
rainfall. The chart/table compares per-item horizon sums, with a total expected-unit
delta. Existing model, inventory and baseline configuration remain unchanged.

If the horizon slider changes after a scenario, the dashboard labels the displayed
result as the previous submitted horizon and asks for a new submission. Results can
increase or decrease forecasts and do not establish causal uplift.

## Screenshot instructions

Start the dashboard, open the browser and expand the sidebar if needed. Use a desktop
window for wider tables; on smaller windows scroll tables horizontally or use their
fullscreen control. Capture the planning date and relevant interpretation note.

1. Overview: capture the three KPI cards, illustrative-stock notice and alerts.
2. Demand Forecast: select latte, leave seven days, and capture prior observations,
   coral forecast line and shaded P10–P90 band. Scroll to include the interval note.
3. Raw Materials: select milk, capture native unit, stock cover and status.
   Expand the editor for a second image without saving illustrative changes.
4. Order Recommendations: capture the quantity/date/reason table; use fullscreen
   when necessary to show the long reason column. CSV export is available.
5. Insights: select latte, capture signed model drivers, then scroll to training plots.
6. Model Performance: capture the Forecast accuracy tab; open Waste & service
   for the FIFO waste/lost-sales charts and tradeoff note.
7. What-If: set max 35°C/min 25°C/rain 0 mm, select latte promotion and a first-day
   festival, submit Compare scenario, then capture controls and comparison together.
   This form does not write inventory.

Windows browser capture can use Win+Shift+S after positioning the desired view.
Existing browser-review captures are in reports/dashboard_screenshots:
overview.jpg, demand_forecast.jpg and model_performance.jpg.
These are screenshots of the live app, not drawn mockups.

## Verification

~~~powershell
.\.venv\Scripts\python.exe -m src.verification.phase_7
~~~

AppTest checks all seven screens, horizon/item changes, actual stock saving,
revision conflicts/reload, scenario validation/isolation, export and error messages.
Pure chart/coverage checks and a TestClient HTTP-backend check cover calculations
and integration. The verifier runs the full suite, lint, formatting and dependencies,
then starts a temporary CLI dashboard and checks loopback health/root before stopping
its process tree. Saved screenshots, prior source hashes and pre-patch backup hashes
are validated. Output is in reports/phase_7_verification.txt.

Windows sandbox loopback restrictions required approved access for live startup.
No external weather requests or supplier orders are made in verification.
Final quality checks and presentation materials are available in report.md,
slide_outline.md, demo_script.md and ../reports/phase_8_verification.txt.

## Brew & Balance visual refresh

The café interface uses warm cream, coral, teal and soft purple. Navigation has
icons, the Overview has three summary cards and direct stock/shopping shortcuts,
and item/material identifiers appear as readable names. Detailed forecast numbers,
shortage quantities, order reasons and evaluation metrics are expandable.

Forecast accuracy and Waste & service are separate tabs on Model Performance.
Insights groups Prediction drivers and Sales patterns; select one training pattern
at a time. What-If uses two numbered steps and a clear Compare scenario button.
Ingredient forms load the selected ingredient's own quantities and retain revision
checks. The sidebar automatically collapses on narrow screens.

Meaning and precision of forecasts, uncertainty, material units, orders and
simulation metrics are unchanged. Demo date/stock labels and service tradeoffs
remain visible. Local CSS requires no remote fonts, images or paid services.
New live captures: redesign_desktop.jpg and redesign_mobile.jpg in
reports/dashboard_screenshots. Earlier captures remain as historical evidence.

Verification:
~~~powershell
.\.venv\Scripts\python.exe -m src.verification.dashboard_redesign
~~~
