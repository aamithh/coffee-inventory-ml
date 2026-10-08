# Phase 4 inventory plan

Planning date: 2025-07-20; horizon: 11 days.
Stock snapshot: illustrative mean-demand coverage, not a measured shop inventory.

| Material | Unit | Order now | Quantity | Safety stock | Reason |
|---|---|---|---:|---:|---|
| coffee_beans | g | True | 51000.00 | 5169.16 | inventory position at/below reorder point or projected shortage |
| milk | ml | True | 55000.00 | 27355.04 | inventory position at/below reorder point or projected shortage; shelf-life capacity limits safety stock or pack rounding |
| sugar | g | True | 23000.00 | 2234.31 | inventory position at/below reorder point or projected shortage |
| chocolate_syrup | ml | True | 8000.00 | 674.68 | inventory position at/below reorder point or projected shortage |
| tea_leaves | g | True | 2500.00 | 201.59 | inventory position at/below reorder point or projected shortage |
| ice | g | True | 44000.00 | 6286.51 | inventory position at/below reorder point or projected shortage; shelf-life capacity limits safety stock or pack rounding |
| croissant_dough | pcs | True | 30.00 | 16.15 | inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu; shelf-life capacity limits safety stock or pack rounding |
| bread | pcs | True | 80.00 | 44.86 | inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu; shelf-life capacity limits safety stock or pack rounding |
| cup_hot | pcs | True | 3000.00 | 310.75 | inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu |
| cup_cold | pcs | True | 900.00 | 110.54 | inventory position at/below reorder point or projected shortage; stock shortage before new delivery; expedite or adjust menu |

Quantile totals and the normal-spread safety stock are planning proxies, not calibrated 95% guarantees.
Coverage starts at delivery. Pending arrivals are received before daily consumption.
Short shelf-life caps use receipt-window demand; longer shelf lives use mean demand times usable life.
Pack constraints can prevent a feasible order; unmet quantities and pre-delivery shortages are explicit.
Aggregate stock is assumed usable through the planning window. Lot expiry and FIFO belong to Phase 5.
Orders above the reorder point are reviewed again tomorrow; an unknown future order date is left blank.
No purchases are placed and no policy simulation or savings claim is made.
