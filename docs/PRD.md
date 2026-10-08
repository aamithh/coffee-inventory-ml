# Product requirements

## Problem and users
A shop manager needs daily menu forecasts, ingredient requirements and explained
orders that account for uncertainty, delivery delays and expiry.

## Scope
Ten menu items; configurable BOM; synthetic India calendar/weather history;
chronological ML evaluation; three-policy FIFO simulation; FastAPI; Streamlit.
Free local operation, editable configuration, reproducible seed 42.

## Acceptance
All core calculations have pytest coverage. Report WAPE, MAE, RMSE, bias and
interval coverage overall and per item. Seek 15% relative WAPE improvement versus
seasonal naive; honestly explain results if not attained. Compare manual, baseline
and ML policies using expiry waste, stockouts, service, holding and total cost.

## Delivery
Phases 0–8 follow the supplied specification. Each phase ends with verified checks,
updated progress and a stop until the user says "continue".
