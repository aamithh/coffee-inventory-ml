# Simulation contract (Phase 5)

## Scope and information boundary

The simulator replays every held-out test day: 2025-07-20 through 2025-12-31
(165 days), comparing manual, seasonal-naive and ML policies. Each policy sees the
same customer requests, supplier settings, item prices, initial quantities and
allocation order. Evaluation-only latent demand is loaded from the separate database
after the forecast bank has been constructed. It enters fulfillment and lost-sales
measurement only.

Forecast refreshes occur every seven days; each origin forecasts 17 days so that
every subsequent daily inventory review has the 11-day receipt-centered horizon.
The saved ML model remains frozen. Each refresh uses only historical observed POS
rows dated strictly before its origin. Future plans contain date, item, category,
price and promotion; future sales, statuses and realized weather are excluded.
Past closures are valid zero observations, while censored/missing/outlier rows are
excluded by the feature contract. Future dates beyond generated history use menu
base prices and no promotion, with normal calendar and persistence-weather logic.

All policies use common factual POS histories, not their own replayed/censored sales.
This isolates the replenishment comparison and avoids giving policies evaluation
demand as input, but does not model the observation-feedback loop that a deployed
policy would create. The weekly fixed-origin forecasts intentionally do not absorb
new actual observations between refreshes. Cache reuse requires matching source
database/model/configuration fingerprint and forecast CSV hash.

## Policies

Manual projects the previous seven calendar days' valid item mean, with the
configured fixed 20% buffer. Missing recent means fall back to prior valid item mean.
Supplier minimums/multiples apply. Receipt coverage uses the same configured lead
time and usable shelf-life window, but manual does not limit pack rounding to the
forecast demand-based expiry capacity.

Seasonal naive recursively uses the same-weekday lag-seven count, with the existing
past-only fallbacks. Material sigma is the sample standard deviation of aggregated,
wastage-adjusted item errors over the preceding 28 days, using complete valid pairs.
If fewer than two complete days exist, a configured-buffer mean-demand proxy applies.

ML uses saved point and quantile models. Material sigma comes from the P90-P50 normal
spread proxy. Both forecast policies apply the Phase 4 combined reorder-point/
shortage trigger, safety stock, shelf-life capacity and supplier pack constraints.
This compares complete policies: the forecasts, uncertainty estimates and cap rules
differ from manual. It is not a causal test of only model choice.

## FIFO and daily event order

Each material holds separate lots with receipt date, expiry date and remaining
native quantity. Initial stock is identical for all policies, based only on prior
valid means times initial coverage clipped to usable life. Initial lots are fresh
on the first replay date.

At the start of each day:
1. Discard lots with expiry <= today and record waste.
2. Receive pending deliveries due today, with expiry = receipt + full shelf life.
3. Review each material and place any recommended order; zero-lead orders arrive now.
4. Fulfill whole menu items in alphabetical item order.
5. Record remaining stock, pipeline and holding cost.

A lot received on day d with shelf life N is usable on d through d+N-1.
FIFO consumes oldest receipts first; equal-receipt lots remain in insertion order.
Orders have deterministic supplier lead times and no cancellation/backorders.
Multiple pending receipts remain separately dated.

Decision projections clone lot state and account for expiry and expected consumption
before receipt. Existing pending receipts are time-phased. Purchase quantities cover
the receipt window, constrained by forecast policies' expected expiry capacity.
Late receipts cannot hide earlier projected shortages. Lead-time deficits cannot
be repaired retroactively.

Serving an item requires its entire wastage-adjusted recipe. The maximum whole
quantity is the minimum supported across all recipe materials. No ingredients are
consumed for unserved items; no substitutions or partial products are modeled.
Requests not served become lost sales. Alphabetical allocation is deterministic,
not an optimized revenue or fairness policy.

## Measurements and costs

Daily per-material conservation:
opening + received = consumed + expired waste + closing.
Per-item accounting: demand = served + lost.

Service level = served units / requested units.
Stockout rate = lost units / requested units.
Item-day stockout rate = fraction of all item/date rows with any lost unit, including
closure-zero rows in its denominator. Zero total demand gives service 1 and stockout 0.

Waste units are summed per material in g, ml or pcs, never across incompatible units.
Waste cost = expired quantity * configured unit cost.
Holding cost = end-of-day stock value * holding_cost_daily_fraction.
Lost-sales penalty = lost units * item price * lost_sale_penalty_fraction; full
sales value is a configured proxy, not a measured profit margin.

Total modeled cost = initial stock value + all purchase commitments + holding cost
+ lost-sales penalty. Expired material cost is already embedded in procurement and
must not be added twice. Terminal stock and pending purchase value are shown separately.
The replay does not liquidate remaining stock or run off pending orders after the
test end; supplier commitments can arrive after the last date. Consequently this
gross-cost metric is sensitive to the boundary and is not net economic profit.
Deducting terminal inventory/pipeline values as full salvage can change the ranking.
The small measured ML advantage over manual must be interpreted with that limitation.

## Outputs and verification

reports/simulation.csv: 4,950 material/date/policy rows.
reports/simulation_items.csv: 4,950 fulfillment rows.
reports/simulation_orders.csv: all dated supplier commitments.
reports/simulation_summary.csv: three aggregate policy records.
reports/simulation_waste.csv: 30 native-unit waste records.
reports/simulation_forecasts.csv: frozen policy/material forecast bank.
reports/simulation_metrics.json and simulation.md: measurements and honest comparisons.
Two charts and notebooks/03_simulation.ipynb present the results.

All outputs stage before publication using the shared rollback publisher. Prior
data, databases, features, saved model and Phase 4 recommendations remain unchanged.
Tests cover FIFO/expiry, whole recipes, delivery timing, multiple pending receipts,
supplier-cap conflicts, conservation, cost accounting and future-sales invariance.
Full checks and executed notebook output are in reports/phase_5_verification.txt.

## Measured result

Manual serves 99.14% of requested units, seasonal naive 97.03%, and ML 98.44%.
ML expiry cost is INR 1,731.45 versus manual INR 44,868.33 (96.14% lower).
ML loses 1,383 units versus manual 762: stockouts are worse by 81.50% relative.
Against seasonal naive's 2,626 lost units, ML loses 47.33% fewer units.
ML gross modeled cost is INR 3,035,995.04 versus manual INR 3,042,230.92,
only 0.205% lower. Parameters were not changed after seeing these outcomes.
These synthetic results support a waste/service tradeoff, not an unqualified
claim that ML improves every metric or that the shop will realize these savings.

## Stockout concentration and terminal-value sensitivity

The extra ML lost units are concentrated in short-life food: croissant loses
706 units under ML versus manual 310; sandwich loses 457 versus manual 232.
Beverage lost counts are identical across policies in this replay. This is consistent
with the tradeoff from forecast-based perishable capacity and pack rounding, rather
than a broad reduction in beverage service.

As a sensitivity calculation, deducting full closing-stock and pipeline value from
gross modeled cost gives about INR 2,907,610 for manual and INR 2,933,441 for ML.
Under that full-value terminal assumption ML costs about INR 25,831 more.
This is not a liquidation forecast; it demonstrates why the 0.205% gross-cost
difference should not be presented as robust savings.
