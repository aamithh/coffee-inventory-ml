# Feature contract — Phase 2

The export contains 40 explicitly named predictors. Always select
FeatureDataset.feature_columns, or the feature_manifest.json list. Numeric target,
quality and split metadata are not predictors.

Calendar predictors are rebuilt from the configured calendar: weekday/weekend, day,
week, month, month end, holiday/festival flags and distances, payday and long weekend.
Four calendar fields have sine/cosine encodings with fixed configured periods. Planned
item/category, price and promotion are available in advance.

Weather policy defaults to persistence: yesterday's observed max/min temperature and
rainfall approximate a forecast for today. Rain flag and temperature bucket derive
from these forecast inputs. This is a simple forecast with errors, not future realized
weather. Supplied forecasts require one row/date, timezone-free local issued_at strictly
before target date, finite valid weather values and coverage of every target row.
Fixed-origin predictions additionally require issued_at strictly before the origin.

For each item, lags 1/7/14/28 and rolling means/sample standard deviations 7/28 use only
prior daily rows. Gaps are rejected; retain explicit missing rows. Closed-day zero counts
can enter later histories. Stockout, missing and outlier observations never enter lag
history. Rolling windows allow partial histories; single-observation standard deviation
and unavailable lags remain NaN. There is no backward filling or dataset-wide scaling.

Targets default to clean rows only, independent of the generator's stockout eligibility
override. The explicit features.censored_target_policy switch can choose impute:
replace stockout targets with the prior clean rolling mean over imputation_window calendar
days. No available clean history means the target stays excluded. Missing/outlier/closure
targets remain excluded. Imputed target flags remain metadata and are not silently
substituted into lag histories or held-out actuals. Phase 3 should score clean actual
targets separately from any imputed training targets.

history_days counts prior valid observed item rows. cold_start_flag marks fewer than
14 prior usable observations. category_past_mean pools only clean category sales from
strictly earlier dates; it is a fallback input for the cold-start prediction policy in
Phase 3. No-history categories retain NaN.

Date splits share src/utils/dates.py boundaries. Historical exports represent rolling
one-day-ahead evaluation, where yesterday's actuals have become available. Fixed-origin
multi-day forecasts must call build_prediction_features with history strictly before
origin and planned future rows. Future actual sales and raw weather in plans are ignored.
Unknown lags stay NaN. Phase 3 must recursively append predicted counts when advancing
the horizon. The feature pipeline itself does not claim to implement a forecasting model.

Leakage tests mutate current/future sales, observation quality and realized weather,
compare all predictors through the cutoff, and verify prefix equivalence after truncating
future rows. Additional tests reject late forecast vintages, unavailable coverage,
duplicate keys and daily gaps. Known calendar and planned promotion/price may vary at
the target date; they are legitimate planned inputs.

Core EDA is src/eda/report.py; notebook cells call modules. Default plots use train dates
only. Descriptive EDA uses realized weather to study synthetic demand and does not feed
that weather into target-day model predictors. Charts were executed and visually checked.
