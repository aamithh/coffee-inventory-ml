"""Pure chart/table transformations, independent of Streamlit execution."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def stock_table(inventory: dict, needs: pd.DataFrame, orders: pd.DataFrame) -> pd.DataFrame:
    """Compute native-unit coverage without adding incompatible material quantities."""
    table = pd.DataFrame(inventory["rows"]).merge(
        needs.groupby("material", as_index=False).agg(
            mean_daily_need=("need", "mean"), forecast_need=("need", "sum")
        ),
        on="material",
    )
    table = table.merge(
        orders[["material", "unit", "order_now", "pre_arrival_shortfall", "unmet_order_quantity"]],
        on="material",
    )
    table["days_of_cover"] = np.where(
        table.mean_daily_need > 0, table.on_hand / table.mean_daily_need, np.nan
    )
    table["status"] = np.select(
        [table.pre_arrival_shortfall.gt(0), table.unmet_order_quantity.gt(0), table.order_now],
        ["Shortage before delivery", "Pack / shelf-life limit", "Order recommended"],
        default="Covered",
    )
    return table


def forecast_chart(
    forecast: pd.DataFrame, history: pd.DataFrame, item: str, colors: dict
) -> go.Figure:
    """Show valid prior observations and future marginal bands with clear separation."""
    rows = forecast.loc[forecast.item.eq(item)].sort_values("date")
    actual = history.loc[
        history.item.eq(item) & history.record_status.isin(["clean", "closed"])
    ].sort_values("date")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=actual.date,
            y=actual.sales,
            name="Past sales",
            mode="lines+markers",
            marker={"size": 4},
            line={"color": colors["muted"]},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=rows.date, y=rows.p10, name="P10", mode="lines", line={"width": 0}, showlegend=False
        )
    )
    figure.add_trace(
        go.Scatter(
            x=rows.date,
            y=rows.p90,
            name="Estimate range (P10–P90)",
            mode="lines",
            fill="tonexty",
            fillcolor=colors["band"],
            line={"width": 0},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=rows.date,
            y=rows.forecast,
            name="Expected sales",
            mode="lines+markers",
            marker={"size": 7},
            line={"color": colors["primary"], "width": 3},
        )
    )
    figure.update_layout(
        yaxis_title="Items sold per day",
        height=400,
        xaxis_title=None,
        template="plotly_white",
        legend={"orientation": "h"},
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
    )
    return figure
