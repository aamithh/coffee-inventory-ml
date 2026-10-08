# Six-slide presentation outline

Target four minutes; use the saved results without claiming real-shop savings.

## Slide 1 — Purchasing problem (0:00–0:30)
- Changing demand causes expired ingredients or lost sales.
- Goal: item forecasts → ingredient needs → feasible order proposals.
- Local API and seven-screen dashboard.
Visual: Overview screenshot with planning date and illustrative-stock label.

## Slide 2 — Data and leakage controls (0:30–1:10)
- Ten items/materials, 10,960 item-days across 2023–2025.
- Synthetic demand with trend, weather, promotions and defective observations.
- Separate observed data and evaluation truth; prior-only features.
- Chronological 70/15/15 split; five expanding folds.
Visual: simplified README architecture with truth → replay branch only.

## Slide 3 — Forecast results (1:10–1:50)
- Selected LightGBM WAPE 21.49% versus seasonal naive 28.91%.
- Relative improvement 25.65%; Ridge test WAPE 20.67% reported honestly.
- Recursive WAPE 21.53%; interval coverage 74.07% vs nominal 80%.
- SHAP contributions describe associations.
Visual: reports/figures/model_wape.png and forecast-band screenshot.

## Slide 4 — From predictions to orders (1:50–2:30)
- BOM/preparation wastage converts menu units to native ingredient quantities.
- Lead time, safety stock, minimum packs and shelf-life capacity.
- Explicit shortages; exports are proposals, not purchases.
Visual: order quantity, arrival and reason table.

## Slide 5 — Simulation tradeoff (2:30–3:20)
- 165 days, common 88,436 requests and FIFO accounting.
- ML expiry INR 1,731 vs manual INR 44,868: 96.14% lower.
- Lost units 1,383 vs manual 762: 81.50% higher.
- Service ML 98.44%, manual 99.14%, seasonal naive 97.03%.
- Gross-cost advantage 0.205%; full terminal credit reverses ranking.
Visual: reports/figures/simulation_comparison.png.
Note: comparison is of complete ordering policies.

## Slide 6 — Demo, verification and future work (3:20–4:00)
- Versioned stock edits and isolated what-if form.
- Full tests/lint; isolated complete rebuild and live server startup.
- Synthetic data, uncertain intervals and assumed economics limit claims.
- Next: real POS/lots, calibration, robust policy evaluation and pilot.
Visual: dashboard screenshot and actual final test count from PROGRESS.md.
