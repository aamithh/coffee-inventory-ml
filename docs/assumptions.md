# Assumptions register

## Phase 1.5 current contract
This section supersedes the historical Phase 1 parameter snapshot below. Current values and comments are in config/config.yaml.

- A mean-one lognormal shop multiplier exp(N(-sigma²/2, sigma²)) is shared by every item on a date. Default sigma is 0.07; zero disables it. A dedicated stream isolates this effect.
- Default promotions are independent per item with probability 0.06. shop_day retains the earlier shop-wide 0.08 schedule. Planned discounts and demand lift remain unchanged. Stable SHA-256 item identities isolate demand and promotion streams from menu order.
- Promotion spillovers use a fixed configured peer_item_ids universe. Adding a menu item does not change existing demand histories; its promotions affect peers only after deliberately updating this universe. Editing the universe is a change to the generator assumptions.
- Automatic weather accepts a validated real cache, but retries the API when the previous cache was synthetic fallback. Metadata source is one string: open_meteo, synthetic_fallback, or synthetic. Explicit synthetic mode is offline. Start/end logs and the quality report identify the source.
- Chronological unique-date splits floor the train and validation fractions; remaining dates form test. A null project.as_of_date selects the first test date. forecast_horizon_days defaults to 7. Calendar validation includes the as-of date through as-of plus horizon and checks dated festival coverage.
- A null generator.drift.start_date selects validation start. The configured 180-day ramp and plateau are reported against split boundaries, including ramp days in test.
- Exclusive record_status precedence is closed > missing > stockout > outlier > clean. Raw flags remain available and may overlap. usable_for_training allows only clean rows by default; the explicit stockout override additionally allows censored rows. Neither field is a predictor.
- Exact reconciliation allocates all latent demand on missing rows to missing loss, including hidden stockout loss: latent minus observed equals stockout loss plus missing loss minus outlier excess. This is a mutually exclusive accounting decomposition.
- Observed SQLite has sales, calendar, weather, menu, materials and recipes. Evaluation truth is a separate simulation_truth.db with the simulation_truth table and a separate CSV. load_sales never attaches or reads truth. Source scans protect feature/model folders and can include future folders.
- DELETE journaling supports atomic transactions across attached observed/truth databases. Unrelated tables survive refreshes. SQLite read connections close explicitly for Windows file replacement.
- COFFEE_DB_DIR overrides both database directories while preserving filenames. The OneDrive warning recommends a non-synced location or excluding database files from sync; no project relocation occurs automatically.
- All generated artifacts are staged and validated before publication. Individual replacements are atomic and handled failures roll back. A process crash across multiple files is not globally atomic; the unchanged backup_pre_1_5 snapshot is the recovery point. Failed rollback retains recovery copies.
- Phase 1.5 originally left later commands guarded. Phases 2–7 subsequently implemented features, models, inventory, simulation, API and dashboard; all CLI tasks are now available.
- Clean weather comparisons are descriptive group means and can reflect trend, seasons and promotions. The report records actual directions without tuning parameters to force them.
- TODO: dated Holi/Diwali coverage currently ends in 2026. Pinned holidays data does not provide reliable Holi 2027 for this configuration, so unsupported years fail clearly instead of inventing dates. Extend both dated festivals with reviewed dates before requesting 2027 forecasts.

## Phase 2 feature assumptions
- Feature exports represent rolling one-day-ahead information, not fixed-origin multi-day forecasts.
- Weather persistence uses prior-day recorded weather as a simple forecast; archive availability delays are not modeled. Supplied weather requires issue timestamps before the target and origin.
- Clean sales and recorded closure zeros enter past histories. Stockout/missing/outlier rows do not; missing lags stay NaN.
- Stockout target treatment is controlled by features.censored_target_policy (exclude or impute). Imputation uses prior clean observations within features.imputation_window=7 days and never changes evaluation actuals.
- Rolling windows 7/28 allow partial histories and use sample standard deviation. Lag offsets 1/7/14/28 count calendar days; gaps must be explicit rows.
- Calendar cycle periods are fixed: weekday 7, month 12, day-of-month 31 and ISO week 53. These are encodings, not fitted transforms.
- Fewer than features.cold_start_days=14 prior valid item observations activates a past-only clean category mean for the later model fallback.
- Temperature bucket edges 20/28/35 degrees apply to forecast weather; values below/above receive open-ended buckets.
- Default EDA scope is training dates only. Figures use a 28-day descriptive trend window, 10x4 inches, 120 DPI, and configured filenames.
- Predictor columns are explicitly listed in feature_manifest.json. Quality, target, target-imputation and split metadata never belong in predictors.
- The feature switch takes precedence over generator stockout eligibility; both switches are documented to prevent silently training on censored counts.
- Feature artifacts publish only after staging; the Phase 1.5 sales/weather/database artifacts and backups are preserved.
See docs/feature_contract.md for the public interfaces, availability rules and recursive forecasting requirement.

## Phase 3 modeling assumptions
- Five expanding folds operate on training dates only. Numeric medians, scaling and category encoding fit separately in every fold.
- LightGBM searches the existing four learning_rate/num_leaves combinations; seed 42, 300 trees, deterministic CPU operation and two worker threads are fixed.
- Ridge alpha remains 1.0. ML point selection uses validation WAPE, then train+validation refitting freezes the test model.
- Baseline fallback columns are past seven-day item mean and category history. Cold-start threshold remains 14 prior valid observed item days.
- Targets are clean observed counts for validation/test scoring. Training can explicitly impute stockout targets using the Phase 2 switch.
- Quantiles are independently fitted at 0.1/0.5/0.9, clamped nonnegative and sorted if crossed. Coverage is empirical; no promised service level follows from these bands.
- Recursive origin stride is seven days, using the configured seven-day horizon. Predicted histories replace unknown lags; weather persistence stays frozen at origin.
- SHAP uses a deterministic 200-row test explanation sample, up to 15 displayed features and five local drivers. This does not select/tune the model.
- The requested WAPE improvement threshold is 0.15 and is reported as a measured comparison, never enforced by altering results.
- Recursive progress is printed every four origins. Notebook cells have a configured 120-second timeout.
- Optional SARIMAX remains disabled. Earlier-than-training-cutoff demo origins and unsupported training weather vintages fail clearly.
See docs/modeling_contract.md for scoring, publication, uncertainty and leakage limits.

## Phase 0 defaults
- Illustrative independent coffee shop in Bengaluru, India; timezone Asia/Kolkata.
- Daily synthetic history: 2023-01-01 through 2025-12-31 (1,096 days).
- Ten editable menu items and ten materials. Currency INR. Costs are illustrative,
  per g/ml/piece, not supplier quotations. Menu prices are illustrative per sale.
- Recipes list material amounts per sale; water and minor spices are excluded.
- Shelf lives assume suitable storage and apply to delivered stock. Ice has a
  seven-day planning limit under frozen storage; packaging has a 365-day planning life.
- Bakery shelf life two days, milk four days, beans ninety days.
- Wastage factors 3–8% cover preparation loss; simulation expiry loss is separate.
- Minimum order quantity will mean order multiples; if rounding conflicts with a
  perishable cap, reduce to a feasible multiple and report unmet need in Phase 4.
- Seed 42, chronological 70/15/15 splits by unique dates, five walk-forward folds.
- Phase 0 selected synthetic weather initially. Phase 1 now defaults to automatic
  Open-Meteo historical weather with a seeded synthetic fallback and cache. Historical
  weather is an idealized proxy, not a real day-ahead forecast.
- Promotions are planned in advance. Realized stockout flags are target-quality
  metadata, not known future predictors. Closed days are recorded explicitly.
- Exclude censored targets by default; shifted rolling imputation will be an option.
- Service level 95%, one-day shelf-life buffer, nominal seven-day target coverage.
- Inventory holding cost 0.1% of ingredient value/day; lost-sale penalty initially
  equals lost revenue. These are illustrative economics, not validated shop accounts.
- SARIMAX is optional and disabled; required models remain in scope.

## Historical pre-patch generator parameters
The YAML contains initial base demand/price per item, annual trend 6%, a gradual
12% shift over 180 days from July 2024, promotion probability 8% and lift 25%,
3% cannibalization, stockout probability 2.5%, missing/outlier probabilities 0.5%,
closure probability 0.8%, and negative-binomial dispersion 30.
Weekend lift starts at 15%, or 30% for cold drinks/bakery; payday lift 8%;
festival pre-lift 20% and some festival-day demand factor 0.85.
The equations were finalized and tested in Phase 1 below. See reports/data_summary.json
for actual generated statistics; these initial assumptions were not fitted to model results.

## Limits to preserve
Synthetic latent demand is available only for simulation evaluation, never model
training. Multi-step forecasts must recursively use predictions for unknown lags.
Forecast intervals are empirical model outputs, not guaranteed service levels.
Expiry and lead-time event ordering will be documented before simulation.

## Historical Phase 1 data-generating process (superseded above)

This is synthetic shop demand paired with Open-Meteo historical reanalysis when
available. It is not a real shop dataset. Automatic weather selection tries the
free historical endpoint, falls back with a logged reason, and records the source.
A matching, validated cache makes reruns independent of network availability.
Explicit open_meteo mode raises errors instead of falling back; synthetic mode
requires no network. Cached fallback weather remains in use until the cache is
removed or its input fingerprint changes.

Historical reanalysis is **not** weather available before the actual sales day.
It drives the synthetic demand process. Phase 2 must construct forecast weather inputs
from information available at prediction time, rather than feed future realized weather
into model features. Operational weather forecast errors remain a limitation. Phase 1
makes no claim that historical weather is a real day-ahead forecast.

### Demand equation and units
For each item/day, mean demand equals base_demand times the following factors:
- Linear trend: 1 + annual_trend × elapsed days / year_days.
- Gradual shift: 1 + drift_lift × clipped fraction of drift_duration_days since
  drift_start_date. This reaches a plateau, rather than a sudden jump.
- weekday_factors[Monday=0..Sunday=6], multiplied by the applicable weekend lift.
- monthly_factors[January..December] for the category.
- Temperature: exp(temperature_coefficient × (temp_max − demand_reference_temp)).
  Coefficients are per degree Celsius; negative coefficients reduce hot-drink demand.
- Rain: rain_lift when precipitation reaches rain_threshold_mm.
- Festival: festival_day_factor on the date, festival_pre_lift during the preceding
  festival_pre_days, otherwise other_holiday_factor on package holidays. This precedence
  prevents double-counting those three effects.
- promotion_lift for the selected item, cannibalization_factor for other items on
  a promotion day, otherwise 1.
- payday_lift for the first/last configured number of days of a month.
- long_weekend_lift on all days of a sufficiently long consecutive off-day run.

Negative-binomial customer demand has mean μ and variance μ + μ²/noise_dispersion.
Its size parameter is noise_dispersion; counts are nonnegative integer units.
These are generator assumptions fixed before model evaluation, not tuned to achieve
a desired model improvement.

### Observation quality and promotion scheduling
- The shop schedules a promotion on about 8% of days and chooses **one** menu item
  uniformly on each such day. This is a shop-day rate, not 8% of every item/day.
  A planned 10% price discount accompanies the configured demand lift; price is
  known in advance. Planned promotions can coincide with an unexpected closure.
- Shop closures are day-level and apply to all items. Demand and sales are zero.
  Realized closure flags are metadata, not automatically available future features.
- Stockouts are item/day events. Candidate stockout capacity is 35–75% of that
  day's realized uncapped demand, rounded down. Mark a stockout only when the cap
  actually reduces sales. This is a censoring simulation, not the Phase 5 inventory replay.
- POS outliers over-record uncensored, non-closure, positive sales by 2.5–4.5×,
  rounded to units. They do not increase latent customer demand.
- Missing sales are injected last, on open days. Missing and outlier/stockout
  flags can overlap, so quality counts are not necessarily mutually exclusive.
- No cleaning or target imputation is performed in Phase 1. NaN is retained in CSV,
  NULL in SQLite, and nullable floating sales still represent whole item counts.
- Weather, scheduling, and per-item demand use separate streams derived from
  config.project.seed and their stream identifiers. Menu iteration order is fixed
  by YAML. Reordering the menu changes which per-item stream applies.
- simulation_truth contains latent_demand and expected_demand. It is a separate CSV
  and SQLite table used only for simulation evaluation and controlled diagnostics.
  load_sales never joins it. Neither oracle value is an eligible model feature or
  training target.

### Weather assumptions
Synthetic maximum temperature uses a cosine seasonal cycle with Gaussian daily
noise. Minimum temperature subtracts a positive, bounded diurnal spread. Rain occurs
with the configured dry/monsoon Bernoulli probability and, when present, follows
a Gamma(shape, scale in mm) amount. The month set, cycle period/peak, all temperatures,
noise, threshold and output precision are configured below. These are illustrative
Bengaluru patterns, not fitted climatology. In the real-weather mode, precipitation_sum
is treated as rainfall, reasonable for this location; no separate snow model is used.
Daily maximum/minimum temperature and precipitation are Celsius/mm in Asia/Kolkata.
The archive request uses the endpoint's default best-match reanalysis model.

### Calendar assumptions
Karnataka public holidays come from pinned holidays==0.74 (observed=false).
Shop festivals add New Year, Christmas, Independence Day, Holi and Diwali.
Configured Holi/Diwali dates cover 2022–2026 and may differ by region or observance.
Extend the dated calendar before generating a new year; missing lunar festival
coverage raises an error rather than silently dropping festivals.
Festival distances refer to this configured shop festival list, not every public holiday.
Long weekends include configured festivals, public holidays and weekends. Calendar
runs are padded around the requested range. Every calendar input is knowable in advance.

### Persistence and data contracts
There is one row for every configured date/item pair; all shared date-level fields repeat
across menu items. The validator permits only explicitly flagged missing sales and
rejects duplicates, negative/nonfinite/fractional observed counts, unknown categories,
invalid flags and inconsistent closures. Weather validation rejects missing dates,
duplicates, missing values, inverted temperature ranges and negative precipitation.
SQLite refreshes seven generated tables transactionally, with unique date/item
or date indexes. Unrelated tables are preserved; a failed refresh restores previous
generated tables. Re-running the data command replaces the generated demo artifacts.
All artifact locations come from the paths section in config/config.yaml.

### Sources
- [Open-Meteo historical API](https://open-meteo.com/en/docs/historical-weather-api)
- [India holiday implementation](https://holidays.readthedocs.io/en/latest/auto_gen_docs/india/)

### Historical Phase 1 parameter snapshot (see YAML for current values)


#### data

```yaml
data:
  start_date: '2023-01-01'
  end_date: '2025-12-31'
  weather_provider: auto
  latitude: 12.9716
  longitude: 77.5946
  promotion_probability: 0.08
  promotion_lift: 1.25
  cannibalization_factor: 0.97
  stockout_probability: 0.025
  missing_probability: 0.005
  outlier_probability: 0.005
  closure_probability: 0.008
  annual_trend: 0.06
  drift_start_date: '2024-07-01'
  drift_duration_days: 180
  drift_lift: 0.12
  noise_dispersion: 30
  weekend_lift: 1.15
  cold_bakery_weekend_lift: 1.3
  payday_lift: 1.08
  festival_pre_lift: 1.2
  festival_day_factor: 0.85
  weather_timeout_seconds: 30
  random_stream: 1
  weekday_factors:
  - 0.95
  - 0.97
  - 1
  - 1
  - 1.08
  - 1
  - 1
  high_weekend_categories:
  - cold_drink
  - bakery
  promotion_discount: 0.1
  stockout_cap_min: 0.35
  stockout_cap_max: 0.75
  outlier_multiplier_min: 2.5
  outlier_multiplier_max: 4.5
  festival_pre_days: 2
  other_holiday_factor: 0.95
  long_weekend_lift: 1.1
  sample_rows: 20
```

#### weather

```yaml
weather:
  archive_url: https://archive-api.open-meteo.com/v1/archive
  cache_enabled: true
  random_stream: 2
  year_days: 365.25
  base_temp_max: 30
  temperature_amplitude: 4
  temperature_peak_day: 105
  temperature_noise_std: 1.8
  diurnal_spread: 9
  diurnal_spread_std: 1
  min_diurnal_spread: 5
  monsoon_months:
  - 6
  - 7
  - 8
  - 9
  - 10
  monsoon_rain_probability: 0.55
  dry_rain_probability: 0.12
  rain_gamma_shape: 1.8
  rain_gamma_scale: 4
  rain_threshold_mm: 0.5
  demand_reference_temp: 28
  decimals: 2
```

#### calendar

```yaml
calendar:
  country: IN
  subdivision: KA
  observed: false
  weekend_days:
  - 5
  - 6
  payday_first_days: 3
  payday_last_days: 3
  long_weekend_padding_days: 10
  long_weekend_min_days: 3
  required_dated_festivals:
  - Holi
  - Diwali
  recurring_festivals:
    New Year: 01-01
    Christmas: 12-25
    Independence Day: 08-15
  dated_festivals:
    '2022-03-18': Holi
    '2022-10-24': Diwali
    '2023-03-08': Holi
    '2023-11-12': Diwali
    '2024-03-25': Holi
    '2024-10-31': Diwali
    '2025-03-14': Holi
    '2025-10-20': Diwali
    '2026-03-04': Holi
    '2026-11-08': Diwali
```

#### demand_profiles

```yaml
demand_profiles:
  hot_drink:
    monthly_factors:
    - 1.1
    - 1.05
    - 1
    - 0.94
    - 0.95
    - 1
    - 1.06
    - 1.07
    - 1.05
    - 1.03
    - 1.07
    - 1.12
    temperature_coefficient: -0.025
    rain_lift: 1.03
  cold_drink:
    monthly_factors:
    - 0.9
    - 0.95
    - 1.06
    - 1.15
    - 1.15
    - 1.08
    - 1
    - 0.97
    - 0.96
    - 0.96
    - 0.94
    - 0.9
    temperature_coefficient: 0.055
    rain_lift: 0.9
  bakery:
    monthly_factors:
    - 1.05
    - 1
    - 1
    - 1
    - 0.98
    - 0.99
    - 1
    - 1.01
    - 1.02
    - 1.06
    - 1.1
    - 1.15
    temperature_coefficient: 0
    rain_lift: 1.02
  food:
    monthly_factors:
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    - 1
    temperature_coefficient: 0
    rain_lift: 0.98
```

#### item_effects

```yaml
item_effects:
  espresso:
    rain_lift: 1.15
  hot_chocolate:
    rain_lift: 1.25
    temperature_coefficient: -0.035
  masala_chai:
    rain_lift: 1.25
    temperature_coefficient: -0.03
```

#### paths

```yaml
paths:
  raw: data/raw
  processed: data/processed
  external: data/external
  database: data/processed/coffee.sqlite
  models: models
  figures: reports/figures
  metrics: reports/metrics.json
  simulation: reports/simulation.csv
  sales_csv: data/raw/sales.csv
  truth_csv: data/raw/simulation_truth.csv
  calendar_csv: data/external/calendar.csv
  weather_cache: data/external/weather.csv
  weather_metadata: data/external/weather_metadata.json
  data_summary: reports/data_summary.json
  sales_sample: reports/sales_sample.csv
  data_dictionary: docs/data_dictionary.md
  data_dictionary_json: docs/data_dictionary.json
  data_report: reports/data_quality.md
```

### Editable menu assumptions

| Item | Category | Base units/day | INR/sale |
|---|---|---:|---:|
| espresso | hot_drink | 40 | 90 |
| americano | hot_drink | 30 | 110 |
| latte | hot_drink | 50 | 160 |
| cappuccino | hot_drink | 45 | 150 |
| cold_coffee | cold_drink | 40 | 180 |
| iced_latte | cold_drink | 30 | 180 |
| hot_chocolate | hot_drink | 20 | 170 |
| masala_chai | hot_drink | 40 | 80 |
| croissant | bakery | 25 | 140 |
| sandwich | food | 30 | 180 |

### Editable material assumptions

| Material | Unit | Shelf life (days) | Lead time (days) | INR/unit | Order multiple | Prep loss fraction |
|---|---|---:|---:|---:|---:|---:|
| coffee_beans | g | 90 | 3 | 1.2 | 1000 | 0.03 |
| milk | ml | 4 | 1 | 0.06 | 1000 | 0.05 |
| sugar | g | 180 | 2 | 0.045 | 1000 | 0.03 |
| chocolate_syrup | ml | 30 | 2 | 0.3 | 500 | 0.04 |
| tea_leaves | g | 90 | 3 | 0.6 | 500 | 0.03 |
| ice | g | 7 | 1 | 0.01 | 1000 | 0.08 |
| croissant_dough | pcs | 2 | 1 | 45 | 10 | 0.08 |
| bread | pcs | 2 | 1 | 8 | 10 | 0.06 |
| cup_hot | pcs | 365 | 4 | 4 | 100 | 0.03 |
| cup_cold | pcs | 365 | 4 | 5 | 100 | 0.03 |

### Editable recipes (material units per sale)

```yaml
recipes:
  espresso:
    coffee_beans: 18
    cup_hot: 1
  americano:
    coffee_beans: 18
    cup_hot: 1
  latte:
    coffee_beans: 18
    milk: 200
    sugar: 8
    cup_hot: 1
  cappuccino:
    coffee_beans: 18
    milk: 150
    sugar: 8
    cup_hot: 1
  cold_coffee:
    coffee_beans: 18
    milk: 200
    sugar: 15
    ice: 100
    cup_cold: 1
  iced_latte:
    coffee_beans: 18
    milk: 180
    sugar: 10
    ice: 120
    cup_cold: 1
  hot_chocolate:
    milk: 220
    chocolate_syrup: 30
    sugar: 8
    cup_hot: 1
  masala_chai:
    tea_leaves: 4
    milk: 100
    sugar: 10
    cup_hot: 1
  croissant:
    croissant_dough: 1
  sandwich:
    bread: 2
```

## Phase 4 planning assumptions

- Forecast preparation wastage applies once, during BOM conversion.
- Stock snapshots are usable aggregate quantities; lot ages and FIFO belong to simulation.
- Existing pending stock is one batch per material, received before consumption on its date.
- Coverage begins on receipt, after supplier lead time. The forecast horizon expands accordingly.
- Material quantile sums and normal-spread sigma are uncalibrated planning proxies.
  The configured 95% target is not an empirical service guarantee.
- A forecast shortage can trigger a purchase above the mean-based reorder point.
- Binding shelf life uses receipt-window demand; longer shelf lives use a labeled
  mean-rate capacity proxy. Expected capacity does not guarantee zero realized waste.
- Supplier pack constraints take precedence over safety stock; infeasible packs and
  unmet quantities remain visible rather than silently exceeding the expiry cap.
- The CLI snapshot is illustrative. All ten demo recommendations are local outputs;
  no inventory savings or supplier purchase is claimed.
- Full formulas and API semantics: docs/inventory_contract.md.

## Phase 5 simulation assumptions

- Replay spans all 165 held-out test dates. The three policies have identical
  evaluation requests, prior-mean initial stock, supplier rules and item allocation.
- Forecast refreshes are weekly; inventory reviews are daily. Each origin uses
  strictly prior factual POS history. Simulated censored sales do not feed models.
- Evaluation-only demand is loaded after forecasts are frozen and affects only
  fulfillment/lost-sales measurement.
- Initial lots are fresh. FIFO expiry occurs at the start of receipt + shelf-life
  date. Multiple pending batches retain their own dates.
- Fulfillment serves whole recipes in alphabetical item order, without substitutions.
- Manual uses previous-week valid mean plus fixed buffer; forecast policies additionally
  impose demand-based expiry caps. Comparison covers complete ordering policies.
- Cost includes initial stock, commitments, end-day holding and lost-sales penalty.
  Waste cost is a procurement subset. Terminal inventory/pipeline have no assumed
  salvage; full-value salvage can change the ranking.
- ML materially reduces waste against manual but increases lost sales. Its small
  modeled-cost advantage is not a robust economic savings claim.
- All parameters were frozen before replay; no tuning to test outcomes.
- Complete mechanics and metrics: docs/simulation_contract.md.

## Phase 6 API assumptions

- The origin is the configured reproducible demo date, not wall-clock today.
- The API uses observed prior history and legitimate planned future metadata only;
  model loading is lazy and requires restart after artifact/config changes.
- Aggregate inventory snapshots support one pending batch per material and no lot-age
  expiry detail. Caller updates replace entire supplied rows and preserve other materials.
- A process-local lock plus expected_version protects the single-process JSON store.
  Multiple independent API processes sharing that file are unsupported.
- Initial inventory is illustrative. GET calls never persist it; caller updates save
  separate versioned JSON and leave generated data/model/simulation outputs unchanged.
- What-if scenarios alter weather, promotions and per-date festivals in isolated copies.
  Scenario issue times are hypothetical, and predictions describe associations.
- NaN/Infinity validation errors omit rejected raw values to keep error responses valid JSON.
- Health checks artifact presence/readability; forecast calls verify actual model behavior.
- Live verification uses a temporary loopback server and stops it afterward.
- Complete endpoint contracts and examples: docs/api_contract.md.

## Phase 7 dashboard assumptions

- Local mode reuses service modules; optional HTTP mode shares the running API's lock.
  Do not edit one JSON state concurrently from independent local writer processes.
- The visible planning date is the configured demo origin, not current wall-clock time.
- Stock cover is on-hand divided by selected-horizon mean material need; zero mean is
  undefined. Native g/ml/pcs requirements are not aggregated into one quantity.
- Forecast charts exclude defective historical actuals and do not show future realized
  sales at the demo origin. Quantile limitations remain visible.
- First-day SHAP drivers and training pattern charts describe associations.
- Stock forms retain their loaded revision; conflicts require Reload stock. Successful
  saves rerun the view. Tests write only isolated temporary stock snapshots.
- What-if results persist only in browser session state and retain their submitted horizon.
- Browser review found and fixed encoding/theme issues. The saved screenshots show
  the live app. Full instructions are in docs/dashboard_guide.md.

## Phase 8 final quality assumptions

- Final results refer to the preserved real-weather-cache dataset and validation-selected model.
- Final workflow checks regenerate all configured dates, the full tuning grid and replay
  into empty temporary output paths through the existing Windows venv/wrapper.
  Only validated weather inputs are copied; fitted models and replay forecasts are rebuilt.
- Fresh dependency installation and GNU Make execution are separate environment steps;
  neither is claimed as verified on this host. Exact fresh setup commands are in README.
- Final notebooks are validated as saved executed narratives with no error outputs;
  their prior phase execution evidence is retained rather than rerun to overwrite them.
- Presentation/report retain the waste/service and terminal-accounting tradeoffs.
  No generator, model selection or policy parameters changed to improve test outcomes.
- API verification now creates its configured schema directory and terminates the
  Windows process tree, so empty-path checks and temporary log cleanup work.

## Dashboard visual refresh

- Brew & Balance changes visual presentation and plain-language labels only;
  forecasting, inventory calculations and previously reported results stay fixed.
- Aggregate ingredient editing now loads quantities when the selected material
  changes, while keeping expected-version conflict checks.
- Navigation shortcuts and grouped details reduce the initial information load.
  Native material units, the synthetic demo/date labels and tradeoffs remain visible.
- Local theme and chart palette are configurable; no remote assets are loaded.
