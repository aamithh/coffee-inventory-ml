# Phase 1.5 data-quality report

Range: 2023-01-01 to 2025-12-31.
Rows: **10,960**; days: **1,096**; items: **10**.
Weather source: open_meteo.

| Check | Measured result |
|---|---:|
| Duplicate or missing date/item pairs | 0 (validated) |
| Negative, nonfinite, or fractional observed sales | 0 (validated) |
| Missing sales | 56 |
| Injected POS outliers | 67 |
| Realized stockout rows | 266 |
| Shop closure days | 9 |
| Promotion days | 511 (46.62%) |
| Configured festival days | 15 |
| Recorded sales sum (includes POS outliers) | 484,112 |
| Uncapped latent demand sum (oracle) | 484,775 |

## Observed seasonality

Pattern means exclude missing, closure, stockout and injected outlier rows.
Weekday mean per item/day: 42.30460921843687.
Weekend mean per item/day: 50.6588785046729.
Weekend/weekday ratio: 1.197478937651908.

| Item | Recorded units | Mean/day | Missing | Stockouts | Clean weekend/weekday |
|---|---:|---:|---:|---:|---:|
| americano | 39,398 | 36.21 | 8 | 28 | 1.126 |
| cappuccino | 60,688 | 55.68 | 6 | 24 | 1.157 |
| cold_coffee | 56,560 | 51.70 | 2 | 20 | 1.319 |
| croissant | 35,408 | 32.51 | 7 | 28 | 1.307 |
| espresso | 56,862 | 52.31 | 9 | 27 | 1.151 |
| hot_chocolate | 29,307 | 26.79 | 2 | 32 | 1.174 |
| iced_latte | 42,621 | 39.07 | 5 | 31 | 1.329 |
| latte | 67,302 | 61.63 | 4 | 20 | 1.157 |
| masala_chai | 57,639 | 52.98 | 8 | 25 | 1.169 |
| sandwich | 38,327 | 35.13 | 5 | 31 | 1.140 |

## Exclusive record status

| Status | Rows |
|---|---:|
| closed | 90 |
| missing | 56 |
| stockout | 266 |
| outlier | 67 |
| clean | 10481 |
Training-eligible rows: 10481.

## As-of, splits and drift

- train_start: 2023-01-01
- train_end: 2025-02-05
- val_start: 2025-02-06
- val_end: 2025-07-19
- test_start: 2025-07-20
- test_end: 2025-12-31
- as_of_date: 2025-07-20
- forecast_horizon_days: 7
- calendar_required_through: 2025-07-27
- drift_start: 2025-02-06
- drift_plateau_date: 2025-08-05
- drift_start_split: val
- drift_ramp_overlap_days: {'train': 0, 'val': 164, 'test': 16}
- drift_appears_in_test: True
- test_contains_shifted_demand: True
- split_rule: floor(train*n), floor(validation*n), remainder to test; never shuffle

## Reconciliation (mutually exclusive status priority)

- latent_units: 484775
- observed_units: 484112
- gap: 663
- stockout_loss: 5020
- missing_loss: 2420
- outlier_excess: 6777
- unexplained_gap: 0

## Clean-row weather comparisons

Descriptive means; seasonality, promotions, trend and drift can confound these groups.
- cold_coffee: {'hot_mean': 66.72881355932203, 'normal_mean': 44.34893617021277, 'hot_rows': 354, 'normal_rows': 705}
- iced_latte: {'hot_mean': 49.68604651162791, 'normal_mean': 34.19027181688126, 'hot_rows': 344, 'normal_rows': 699}
- hot_chocolate: {'rainy_mean': 31.311377245508982, 'dry_mean': 23.111721611721613, 'rainy_rows': 501, 'dry_rows': 546}
- masala_chai: {'rainy_mean': 62.4859437751004, 'dry_mean': 45.78481012658228, 'rainy_rows': 498, 'dry_rows': 553}
Cross-item normalized residual correlation: 0.08218818233882166.

## Interpretation and limits

- Observed total retains injected POS over-recording errors and omits missing sales.
- Pattern means exclude closures, missing, stockout and POS outlier rows.
- Latent and expected demand are isolated oracle data, unavailable to the sales loader.
- Historical reanalysis weather is a proxy; it is not known day-ahead forecast weather.
- These are synthetic sales with real or synthetic weather, not observations from a real shop.
- Observed and latent totals need not match: censoring, missing sales and POS errors act differently.
- Raw weather/festival group comparisons are confounded; controlled effect tests hold other inputs fixed.
- No model accuracy, inventory-policy benefit or forecasting leakage test is claimed in Phase 1.

## Sources

- [Open-Meteo historical weather documentation](https://open-meteo.com/en/docs/historical-weather-api)
- [India holiday documentation](https://holidays.readthedocs.io/en/latest/auto_gen_docs/india/)
