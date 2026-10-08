# Four-minute demo script

## Preparation

From the project folder:

~~~powershell
.\.venv\Scripts\python.exe -m src.cli setup-check
.\tasks.ps1 -Task dashboard
~~~

Open http://127.0.0.1:8501; expand the sidebar and select Overview with seven days.
Wait for initial model loading before starting the timer. Keep saved model/policy
figures available. Use existing artifacts; do not train during the demo.
If missing, build data/features/train/inventory/simulate using README beforehand.

State that the shop is synthetic, date 2025-07-20 and stock illustrative.
Avoid saving stock unless a separate api_inventory_state path is configured.
What-if changes do not persist inventory. On narrow windows scroll/use fullscreen.

## 0:00–0:35 — Overview

“This project turns expected coffee-shop sales into ingredient order proposals.
The date is a historical demo origin and stock is illustrative. These cards show
expected next-day units, materials needing orders and cost. Alerts identify
shortages that delivery or supplier constraints cannot resolve.”

Point to displayed values; do not invent wall-clock forecasts.

## 0:35–1:15 — Demand Forecast

Choose latte and seven days.
“Gray counts are prior valid POS observations; blue is future forecast and shading
is P10–P90. Future actual sales are unavailable here. Inputs use prior lags/weather
and known plans/calendar; evaluation demand never enters predictors.”

“Selected LightGBM test WAPE is 21.49% versus seasonal naive 28.91%, a 25.65%
relative improvement. Ridge is better on test, but deployment selection was frozen
on validation. Coverage is 74.07%, so bands are not a service guarantee.”

## 1:15–1:55 — Raw Materials and orders

Select Raw Materials then Order Recommendations.
“Recipes convert units to g, ml or pieces with preparation wastage once.
Recommendations consider safety stock, delivery, shelf life and packs. Unmet
quantities remain visible; downloading CSV does not send supplier orders.”

Open the stock editor without saving.
“Forms retain their loaded revision. Stale edits conflict and require Reload stock.
Public stock is aggregate; lot expiry is tracked in the separate FIFO replay.”

## 1:55–2:30 — Insights

Choose latte on Insights.
“These signed SHAP drivers explain the first day's calculation. Training weekday,
festival and weather charts show associations, not causal effects.”
Point to one actual positive/negative driver.

## 2:30–3:20 — Model Performance

Select the Waste & service tab.
“Policies have common demand and initial stock. ML expiry cost falls from INR
44,868 to INR 1,731, but it loses 1,383 units versus manual's 762. Service is 98.44%
versus 99.14%. ML improves both waste and service over seasonal naive, not every
policy. Its 0.205% gross-cost advantage reverses under full terminal stock credit.”

“The result is a waste/service tradeoff, not universal savings.”

## 3:20–4:00 — What-If and close

Set max 35°C, min 25°C, rain 0 mm, enable latte promotion and add first-day festival.
Submit Compare scenario and read the actual delta.
“This isolated scenario leaves baseline, model and stock unchanged. Results may
increase or decrease forecasts; they are model associations.”

“Verification covers leakage, inventory conservation, API/forms and a complete
temporary rebuild. Real POS/lot data, calibration and prospective evaluation
are needed before a live savings claim.”

## Recovery and optional API demonstration

If live charts fail, show saved browser screenshots and model/policy figures,
labeling them saved evidence. If the model is missing, show the error and explain
README build steps; do not claim a live result. Stop servers with Ctrl+C.

Optional substitute: run .\tasks.ps1 -Task api; open
http://127.0.0.1:8000/docs. Execute GET /forecast/items?days=1 and
GET /recommendations/orders. Show invalid days=31 returning 422.
Use GET /inventory to explain revisions; avoid POST to saved demo state.
