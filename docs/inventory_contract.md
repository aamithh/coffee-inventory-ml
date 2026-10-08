# Inventory planning contract (Phase 4)

The planner converts saved item forecasts into material quantities and proposes local
orders. It places no supplier orders. The command uses an explicitly illustrative
snapshot; callers can supply measured stock to `run_inventory(config, snapshot)`.

## Inputs and units

`material_requirements(forecasts, config)` requires one row per configured menu item
per date with date, item, forecast, p10, p50 and p90. All quantities must be finite,
nonnegative; quantiles must be ordered. Point forecasts may differ from P50.
The BOM contains native g, ml and pcs quantities. Need equals the sum of item forecast
times recipe quantity times (1 + material wastage factor). No second wastage adjustment
is applied to ordering. Expected material cost equals point need times unit cost.

Adding item quantiles yields marginal material planning proxies, not calibrated
aggregate quantiles: cross-item dependence and recursive path uncertainty are not
estimated. Uncalibrated model intervals make a 95% service guarantee inappropriate.

`recommend_orders(requirements, snapshot, origin, config, residual_sigmas=None)`
requires contiguous daily material needs through the planning horizon and one stock
row per material: material, on_hand, on_order, arrival_date. A positive pending quantity
requires a calendar arrival date on/after origin. One pending batch per material is
supported in this phase. Quantities and dates are validated before planning.
Snapshot quantities are usable aggregate stock, assumed to remain usable through
the relevant window. Existing lot ages and expiry are unavailable; FIFO expiry
accounting is reserved for Phase 5.

## Uncertainty and lead time

Daily sigma defaults to mean(P90 - P50) / NormalQuantile(0.90), over
inventory.mean_window_days. This assumes an approximately normal upper spread.
Alternatively, pass material residual sigmas computed with
`material_residual_sigmas(errors, config, origin)`: aggregate same-day signed item
errors through the wastage-adjusted BOM, then take sample standard deviation.
At least two complete error days strictly before origin are required. This preserves
cross-item covariance. Callers must use past out-of-sample errors; dates alone cannot
prove how a residual was estimated. The demo does not load held-out residuals.

Safety stock = NormalQuantile(service_level) * sigma_daily * sqrt(lead_time_days).
Reorder point = mean_daily_need * lead_time_days + safety_stock.
The sqrt rule assumes independent daily errors; correlated shocks and uncalibrated
quantiles can invalidate nominal service. Zero lead time produces zero safety stock.

## Receipt-centered quantity

A purchase planned today arrives at origin + lead time, before that day's consumption.
Existing pending stock is received before consumption on its supplied date.
The planner subtracts daily point need from stock before arrival and clips remaining
stock to zero; pre-arrival shortages are reported separately and cannot be repaired
retroactively by a normal delivery.

Coverage starts at receipt:
min(target_coverage_days, shelf_life_days - buffer_days).
Required forecast length is the maximum of mean_window_days and every material's
lead time plus coverage. This produces 11 days in the current configuration.
The saved model is used without retraining, and only future planned item/category/
price/promotion metadata is passed to its forecast function.

Desired purchase = max(0, receipt-window need + safety stock
- projected stock at receipt - pending receipts inside the coverage window).
A prefix shortage check increases this quantity when a late pending receipt would
otherwise mask an earlier shortage. Inventory position counts present stock and
pending receipts due no later than the new delivery. A purchase is triggered by
position <= reorder point, a shortage before delivery, or a projected coverage-window
shortage. Thus the policy proactively fills a forecast shortage even if position
exceeds the mean-based reorder point. The reason field states this combined rule.

## Shelf life and supplier packs

Usable life = shelf_life_days - buffer_days, which must be positive.
When usable life binds coverage, capacity demand is the actual receipt-window sum.
For longer usable lives, capacity demand is mean_daily_need times usable life,
an explicitly labeled proxy beyond the finite forecast horizon. This is an
expected-consumption cap, not a realized-expiry guarantee.

Maximum purchase = max(0, capacity demand - projected receipt stock - relevant pending).
Supplier minimum is materials.<id>.min_order_qty. Optional order_multiple specifies
a distinct pack increment; otherwise the minimum also serves as the pack increment.
Desired quantities round up to a valid multiple at or above the minimum.
Expiry-limited quantities round down to the largest feasible multiple.
If no pack satisfies the minimum and capacity, quantity is zero with an explicit
reason. unmet_order_quantity reports the unfilled desired amount, including safety
stock; it is not a measured lost-sale quantity.

order_now is true only for a positive feasible purchase. order_by_date is today when
the trigger fires, including an infeasible purchase requiring attention.
expected_arrival is populated only for positive purchases. Dates for purchases
without a current trigger remain blank; review them again tomorrow.
planning_arrival_date always identifies today's hypothetical receipt calculation.

## Outputs and reproducibility

The inventory command stages and publishes its own seven reports using the shared
rollback publisher. Raw sales, weather, databases, feature CSV, saved models and
Phase 3 forecast reports remain unchanged. Outputs include the BOM, 110 item
forecasts, 110 material needs, snapshot, ten recommendations, summary and readable
report. All inventory parameters and artifact paths are in config/config.yaml.

Hand examples cover BOM/wastage, quantile conversion, covariance, safety stock,
lead-time consumption, receipt timing, late arrivals, rounding, minimum packs,
shelf-life conflicts and invalid input. Full verification is recorded in
reports/phase_4_verification.txt. Simulation and measured cost/waste/stockout
comparisons start only after the next continue instruction.
