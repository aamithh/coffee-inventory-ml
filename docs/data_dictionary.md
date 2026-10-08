# Data dictionary

One observed row per local date/item; daily fields repeat across items.

Weather values use Celsius and mm. No oracle column belongs in model inputs.

## sales

| Field | Type | Meaning | Unit | Availability |
|---|---|---|---|---|
| date | date | Local sales day; one row per date/item. | day | known calendar |
| item | string | Editable menu identifier. |  | known in advance |
| category | string | Menu category. |  | known in advance |
| price | float | Planned selling price, including promotion discount. | INR/sale | known in advance |
| promo_flag | int | This item is the selected promotion for this day. | 0/1 | planned in advance |
| sales | nullable float | Observed units sold; censored on stockouts, may contain POS errors. | items | after day ends; target |
| stockout_flag | int | Realized item demand exceeded the simulated sales cap. | 0/1 | after day ends; target-quality metadata |
| closure_flag | int | Shop was closed; observed and latent demand set to zero. | 0/1 | after day ends; metadata |
| missing_flag | int | Observed sales was deliberately made missing. | 0/1 | after day ends; metadata |
| outlier_flag | int | Injected POS over-recording error, not latent customer demand. | 0/1 | after day ends; metadata |
| day_of_week | int | Monday=0 through Sunday=6. |  | known calendar |
| weekend_flag | int | Configured weekend weekday. | 0/1 | known calendar |
| day_of_month | int | Day number within month. | day | known calendar |
| week_of_year | int | ISO week number. | week | known calendar |
| month | int | Calendar month number. | month | known calendar |
| month_end_flag | int | Final day of the calendar month. | 0/1 | known calendar |
| holiday_flag | int | India/Karnataka holiday from the pinned holidays package. | 0/1 | known calendar |
| holiday_name | string | Holiday name or empty string. |  | known calendar |
| festival_flag | int | Configured shop-relevant festival date. | 0/1 | known calendar |
| festival_name | string | Configured festival name or empty string. |  | known calendar |
| days_to_next_festival | int | Days to next configured festival; zero on event day. | days | known calendar |
| days_since_last_festival | int | Days since last configured festival; zero on event day. | days | known calendar |
| payday_flag | int | First/last configured days of a month. | 0/1 | known calendar |
| long_weekend_flag | int | Part of a consecutive holiday/weekend run of configured length. | 0/1 | known calendar |
| temp_max | float | Daily maximum temperature. | degrees C | synthetic proxy or historical reanalysis |
| temp_min | float | Daily minimum temperature. | degrees C | synthetic proxy or historical reanalysis |
| rainfall | float | Daily precipitation; treated as rain in this demo. | mm | synthetic proxy or historical reanalysis |
| rain_flag | int | Precipitation meets configured threshold. | 0/1 | same availability as weather |
| weather_source | string | synthetic or open_meteo; source is retained. |  | provider metadata |
| record_status | string | Single precedence: closed > missing > stockout > outlier > clean. |  | after day ends; target-quality metadata |
| usable_for_training | bool | Clean rows, plus stockouts only when explicitly configured. | true/false | after day ends; target eligibility, never a predictor |

## simulation_truth

| Field | Type | Meaning | Unit | Availability |
|---|---|---|---|---|
| date | date | Local sales day; one row per date/item. | day | known calendar |
| item | string | Editable menu identifier. |  | known in advance |
| latent_demand | int | Uncapped realized customer demand; zero on closure days. | items | oracle; simulation evaluation only |
| expected_demand | float | Generator mean before demand noise; zero on closure days. | items | oracle; data diagnostics only |
| expected_demand_without_shop_shock | float | Mean demand excluding the shared shock; residual diagnostic only. | items | oracle; never training |
| shop_daily_multiplier | float | Same mean-one daily lognormal draw across all items. | multiplier | oracle; never training |

simulation_truth is in the separate configured truth_database SQLite file, never the observed database.
Raw quality flags may overlap; reports count record_status exactly once using closed > missing > stockout > outlier > clean.
usable_for_training is metadata for filtering targets, never a feature.
Missing-priority reconciliation assigns all latent demand on missing rows to missing loss, including any hidden stockout loss.
project.as_of_date and forecast_horizon_days define the demo date; split/drift dates are reported, not oracle predictors.

## Other observed-database SQLite tables

- calendar: one row/day, calendar fields above.
- weather: one row/day, weather fields above.
- menu: item, category, base_demand (items/day), price (INR/sale).
- materials: material, unit, shelf_life_days, lead_time_days, unit_cost (INR/unit), min_order_qty (units), wastage_factor (fraction).
- recipes: item, material, quantity (material units/sale).
