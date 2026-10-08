# Modeling contract — Phase 3

The required models are implemented: yesterday naive, same-weekday-last-week seasonal
naive, seven-day moving average, Ridge, global LightGBM point regression and LightGBM
P10/P50/P90 quantile regressions. Saved artifacts use joblib and the explicit feature
manifest. Load trusted local artifacts only.

All training inputs come from observed-sales features. Quality/target/split metadata
never enters the predictor matrix. Stockout imputation, when explicitly enabled, applies
to training targets; reported validation/test scores use clean observed targets only.

The training period has five expanding folds by unique date, keeping all items on a
date together. Each fold fits numeric medians, category one-hot encoding and Ridge
scaling using its training rows only. Missing early lag/rolling values remain missing
until this fold-fitted preprocessing. Unknown item/categories are supported.

LightGBM searches the four configured learning-rate/leaf combinations. Pooled fold
absolute error divided by pooled actual units selects parameters. Ridge and all three
baselines are also scored on the same five folds. Validation WAPE chooses the ML point
model. The chosen model and fixed hyperparameters are refitted on train plus validation
before the final test evaluation. No test-driven retuning or generator changes occur.

The saved cutoff is 2025-07-19, before the default 2025-07-20 demo origin. Earlier demo
origins are rejected rather than served by a model trained on their future. Demo planned
prices/promotions come from the generated history and must cover the requested horizon.

Rolling one-day-ahead evaluation may use earlier observed test sales/weather that have
become available before each target date. Recursive evaluation uses 23 weekly origins,
with a frozen model and seven steps per origin. Plans are restricted to date/item/category,
price and planned promotion. Future actual sales, weather and quality are ignored.
Predicted counts are appended as synthetic history while origin weather persistence
stays frozen. Cold-start eligibility uses actual history available at origin, rather than
letting recursive predictions establish a new item's observed history.

Baselines use exact lags/rolling mean when available, then the configured prior-history
fallback columns, prior category mean, and finally training-category/overall means.
Items with fewer than 14 observed valid history rows use prior category averages for
point forecasts. Cold-start quantiles use empirical training-category quantiles; they
are a conservative fallback mechanism, not validated new-item intervals.

Three independent quantile models can cross. Predictions are clamped nonnegative and
sorted by row; raw crossing counts are reported. Coverage is measured afterward.
Point forecasts need not equal P50. The models do not promise that quantiles bracket
the separate point model. Recursive bands condition on predicted history and do not
propagate complete trajectory uncertainty.

WAPE is sum absolute error / sum absolute actual units, undefined for zero total demand.
MAE, RMSE and mean signed bias (prediction minus actual, in units) are also reported.
P10-P90 coverage includes both bounds and has nominal 80% coverage. This run measured
74.07% one-day coverage and about 74.97% recursive coverage, so intervals under-cover.
No post-test calibration was fitted to hide this limitation.

Validation-selected LightGBM achieved one-day WAPE 21.49%, against seasonal naive
28.91%: a 25.65% relative reduction, exceeding the requested 15%. Ridge had lower
test WAPE (20.67%) but was not selected after seeing test results. Seven-day recursive
LightGBM WAPE was 21.53%, against 28.83% seasonal naive. These synthetic-data results
do not establish real-shop generalization or inventory-policy benefits.

SHAP uses tree explanations for LightGBM and independent linear contributions around
training feature means for Ridge. Contributions add to the raw model output; nonnegative
clipping and cold-start overrides are explained separately. The top five drivers are
associations relative to a reference, not causal claims.

The optional SARIMAX extension remains disabled; enabling its flag raises a clear
NotImplementedError. It is not required for the model suite. Model outputs and reports
are staged and validated before publication; the original data/feature artifacts are
not overwritten. Inventory calculations and policy simulation remain later phases.
