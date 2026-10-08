"""Seven-screen coffee inventory dashboard backed by existing service contracts."""

from pathlib import Path
import json
from html import escape
import os
import sys
import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit executes this file by path; install the project root before imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.api.service import ConflictError
from src.dashboard.backend import DashboardBackend
from src.dashboard.views import forecast_chart, stock_table
from src.utils.config import load_config, resolve_path

SCREENS = (
    "Overview",
    "Demand Forecast",
    "Raw Materials",
    "Order Recommendations",
    "Insights",
    "Model Performance",
    "What-If",
)


@st.cache_resource
def backend(config_json: str) -> DashboardBackend:
    """Reuse one service/lock per application configuration."""
    return DashboardBackend(json.loads(config_json))


def app_config() -> dict:
    path = os.environ.get(load_config()["dashboard"]["config_environment_variable"])
    if "--config" in sys.argv:
        path = sys.argv[sys.argv.index("--config") + 1]
    return load_config(path)


def friendly(value: str) -> str:
    """Use café vocabulary without changing identifiers sent to the backend."""
    labels = {
        "lightgbm": "LightGBM · ML model",
        "ridge": "Ridge regression",
        "naive": "Yesterday's sales",
        "seasonal_naive": "Last week's sales",
        "moving_average": "7-day average",
        "quantile_p50": "Middle estimate (P50)",
        "manual": "Manual ordering",
        "ml": "ML ordering",
    }
    return labels.get(value, value.replace("_", " ").title())


def chart(figure, config: dict) -> None:
    """Give all interactive plots one legible, consistent visual language."""
    figure.update_layout(
        template="plotly_white",
        colorway=config["dashboard"]["colors"]["palette"],
        font={"family": "Arial, sans-serif", "size": 13, "color": "#65584e"},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        legend={"orientation": "h", "y": 1.12, "title_text": ""},
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#f1ece6", zerolinecolor="#e8dfd4")
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def go_to(screen: str) -> None:
    """Navigation callbacks run before widgets render on the next rerun."""
    st.session_state["navigation"] = screen


def table(frame: pd.DataFrame) -> None:
    """Show compact business labels while retaining full precision internally."""
    visible = frame.round(2).copy()
    for name in {
        "wape",
        "interval_coverage",
        "service_level",
        "stockout_rate",
        "item_day_stockout_rate",
    }.intersection(frame.columns):
        visible[name] = frame[name].map(lambda v: f"{v:.2%}" if pd.notna(v) else "")
    for name in {"material", "item", "model", "policy"}.intersection(frame.columns):
        visible[name] = frame[name].map(friendly)
    for name in {"date", "order_by_date", "expected_arrival", "arrival_date"}.intersection(
        frame.columns
    ):
        visible[name] = pd.to_datetime(frame[name]).dt.strftime("%d %b %Y").fillna("—")
    labels = {
        "forecast": "Expected sales",
        "p10": "Low estimate",
        "p50": "Middle estimate",
        "p90": "High estimate",
        "on_hand": "In stock",
        "on_order": "On the way",
        "mean_daily_need": "Needed / day",
        "days_of_cover": "Days left",
        "order_qty": "Buy quantity",
        "estimated_order_cost": "Cost (₹)",
        "expected_arrival": "Delivery date",
        "wape": "Forecast error",
        "mae": "Average error (units)",
        "service_level": "Demand served",
        "waste_cost": "Expired stock cost (₹)",
        "total_cost": "Modeled cost (₹)",
        "lost_units": "Lost sales (units)",
    }
    visible = visible.rename(columns=lambda n: labels.get(n, str(n).replace("_", " ").title()))
    st.dataframe(visible, use_container_width=True, hide_index=True)


def overview(data: DashboardBackend, days: int, config: dict) -> None:
    forecast, orders, stock = data.forecast(days), data.orders(), data.inventory()
    first = pd.to_datetime(forecast.date).min()
    rows = forecast.loc[pd.to_datetime(forecast.date).eq(first)].sort_values(
        "forecast", ascending=False
    )
    st.markdown(
        '<div class="welcome"><div class="eyebrow">A little planning. A smoother day.</div>'
        "<h2>Your café, ready for the next shift.</h2>"
        "<p>See what customers may order, check your ingredients, and build a shopping list — "
        "all in one place.</p></div>",
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    columns[0].metric(
        "☕ Expected sales · next day",
        f"{rows.forecast.sum():,.0f}",
        help="Total menu-item units, not customer count.",
    )
    columns[1].metric(
        "📦 Ingredients to reorder",
        int(orders.order_now.sum()),
        help="Materials with a proposed purchase in the supplier plan.",
    )
    columns[2].metric(
        "🛒 Estimated shopping cost",
        f"₹{orders.estimated_order_cost.sum():,.0f}",
        help="Proposed purchases at configured ingredient prices.",
    )
    st.caption(
        f"Next forecast day: {first.strftime('%d %b %Y')}. Shopping quantities use the supplier planning window."
    )
    if stock["illustrative"]:
        st.info(
            "Demo stock is illustrative. Add measured quantities in Raw Materials before using the shopping list."
        )
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        with st.container(border=True):
            st.subheader("What's likely to sell?")
            st.caption("Expected item sales for the next forecast day.")
            display = rows.assign(Menu=rows.item.map(friendly))
            figure = px.bar(
                display.sort_values("forecast"),
                x="forecast",
                y="Menu",
                orientation="h",
                color="Menu",
                color_discrete_sequence=config["dashboard"]["colors"]["palette"],
                labels={"forecast": "Expected units", "Menu": ""},
                text="forecast",
            )
            figure.update_traces(
                texttemplate="%{x:.0f}", textposition="outside", marker_line_width=0
            )
            figure.update_layout(showlegend=False, height=400)
            chart(figure, config)
    with right:
        with st.container(border=True):
            st.subheader("Your next steps")
            st.write(
                f"**{friendly(rows.iloc[0]['item'])}** leads the forecast. Check its ingredient stock first."
            )
            warnings = orders.loc[
                orders.pre_arrival_shortfall.gt(0) | orders.unmet_order_quantity.gt(0)
            ]
            if not warnings.empty:
                st.warning(
                    f"{len(warnings)} ingredients need attention: delivery timing or pack limits may leave a gap."
                )
                for row in warnings.head(3).itertuples():
                    issue = (
                        "Stock may run low before delivery"
                        if row.pre_arrival_shortfall > 0
                        else "Pack or expiry limit leaves a gap"
                    )
                    st.write(f"**{friendly(row.material)}** · {issue}")
            else:
                st.success("No projected delivery or supplier-pack shortages.")
            st.button(
                "📦 Check ingredient stock",
                on_click=go_to,
                args=("Raw Materials",),
                use_container_width=True,
            )
            st.button(
                "🛒 Open shopping list",
                on_click=go_to,
                args=("Order Recommendations",),
                type="primary",
                use_container_width=True,
            )
    with st.expander("See shortage quantities and planning details"):
        table(
            orders[["material", "unit", "pre_arrival_shortfall", "unmet_order_quantity", "reason"]]
        )
    st.caption(
        "Order recommendations are proposals. This dashboard does not place supplier purchases."
    )


def demand(data: DashboardBackend, days: int, config: dict) -> None:
    st.caption(
        "Pick a menu item to see its expected sales. The shaded area shows a lower and upper estimate."
    )
    item = st.selectbox("Menu item", list(config["menu"]), format_func=friendly, key="demand_item")
    forecast = data.forecast(days)
    rows = forecast.loc[forecast.item.eq(item)]
    columns = st.columns(3)
    columns[0].metric("Expected over this period", f"{rows.forecast.sum():,.0f} units")
    columns[1].metric("Daily average", f"{rows.forecast.mean():,.0f} units")
    peak = rows.loc[rows.forecast.idxmax()]
    columns[2].metric("Busiest forecast day", pd.Timestamp(peak.date).strftime("%a, %d %b"))
    chart(forecast_chart(forecast, data.history(), item, config["dashboard"]["colors"]), config)
    st.caption(
        "Past sales = recorded history. Expected sales = future prediction. Shading = P10–P90 estimates, not a guarantee."
    )
    with st.expander("View daily forecast numbers"):
        table(rows[["date", "forecast", "p10", "p50", "p90"]])
    st.caption(
        "Future actual sales are unavailable at this demo date. Bands are uncalibrated and do not capture every future uncertainty."
    )


def materials(data: DashboardBackend, days: int, config: dict) -> None:
    st.caption("See what is in stock, how long it may last, and which ingredients need attention.")
    snapshot = data.inventory()
    orders = data.orders()
    needs = data.materials(data.forecast(days))
    visible_stock = stock_table(snapshot, needs, orders)
    table(
        visible_stock[
            [
                "material",
                "unit",
                "on_hand",
                "on_order",
                "mean_daily_need",
                "days_of_cover",
                "status",
            ]
        ]
    )
    st.caption(
        "Days left = current stock ÷ average daily need. Each ingredient keeps its own g, ml or pieces unit."
    )
    st.caption(
        f"Inventory revision {snapshot['version']} · "
        + ("Illustrative stock" if snapshot["illustrative"] else "Caller-supplied stock")
        + " · Stock cover uses the selected horizon's mean expected need."
    )
    with st.expander("Update a material's stock"):
        material = st.selectbox(
            "Material", list(config["materials"]), format_func=friendly, key="stock_material"
        )
        row = next(r for r in snapshot["rows"] if r["material"] == material)
        if st.session_state.get("stock_loaded_material") != material:
            st.session_state["stock_loaded_material"] = material
            st.session_state["stock_edit_version"] = snapshot["version"]
            # Each ingredient must load its own quantities, not the previous form's.
            st.session_state["stock_on_hand"] = float(row["on_hand"])
            st.session_state["stock_on_order"] = float(row["on_order"])
            st.session_state["stock_arrival"] = pd.Timestamp(
                row["arrival_date"] or snapshot["as_of_date"]
            ).date()
        if st.button("Reload stock", key="reload_stock"):
            st.session_state.pop("stock_loaded_material", None)
            for key in ("stock_on_hand", "stock_on_order", "stock_arrival"):
                st.session_state.pop(key, None)
            st.rerun()
        with st.form("inventory_update"):
            on_hand = st.number_input(
                f"In stock ({config['materials'][material]['unit']})",
                min_value=0.0,
                key="stock_on_hand",
            )
            on_order = st.number_input(
                "Pending order quantity",
                min_value=0.0,
                key="stock_on_order",
            )
            arrival = st.date_input(
                "Pending arrival",
                min_value=pd.Timestamp(snapshot["as_of_date"]).date(),
                key="stock_arrival",
            )
            submitted = st.form_submit_button("Save measured stock", type="primary")
        if submitted:
            data.update(
                {
                    "expected_version": st.session_state["stock_edit_version"],
                    "rows": [
                        {
                            "material": material,
                            "on_hand": on_hand,
                            "on_order": on_order,
                            "arrival_date": arrival.isoformat() if on_order else None,
                        }
                    ],
                }
            )
            st.session_state["stock_saved_message"] = (
                "Stock saved; cover and recommendations refreshed."
            )
            st.session_state.pop("stock_loaded_material", None)
            st.rerun()
    material = st.selectbox(
        "Ingredient demand chart",
        list(config["materials"]),
        format_func=friendly,
        key="material_forecast",
    )
    rows = needs.loc[needs.material.eq(material)]
    chart(
        px.line(
            rows,
            x="date",
            y=["need", "need_p10", "need_p90"],
            color_discrete_sequence=config["dashboard"]["colors"]["palette"],
            labels={
                "value": config["materials"][material]["unit"],
                "date": "",
                "variable": "Estimate",
            },
        ),
        config,
    )


def orders_view(data: DashboardBackend) -> None:
    st.caption("Your proposed shopping list: what to buy, how much, and when it should arrive.")
    orders = data.orders()
    st.info(
        "Review these quantities before buying. Delivery delays, expiry and supplier packs can leave a shortage."
    )
    table(orders[["material", "unit", "order_qty", "expected_arrival", "estimated_order_cost"]])
    st.download_button(
        "⬇ Download shopping list (CSV)",
        orders.to_csv(index=False, lineterminator="\n"),
        "order_recommendations.csv",
        "text/csv",
        type="primary",
    )
    with st.expander("Why these orders? View dates and detailed reasons"):
        table(orders[["material", "order_now", "order_by_date", "expected_arrival", "reason"]])
    st.caption(
        "Prices come from the project configuration. Downloading a list does not place an order."
    )


def insights(data: DashboardBackend, config: dict) -> None:
    st.caption(
        "Understand why the model expects these sales, and explore patterns in the training data."
    )
    item = st.selectbox(
        "Explain menu item", list(config["menu"]), format_func=friendly, key="explain_item"
    )
    result = data.explanation(item)
    st.metric(
        f"Expected {friendly(item).lower()} sales · first day", f"{result['forecast']:.0f} units"
    )
    drivers_tab, patterns_tab = st.tabs(["💡 Prediction drivers", "📊 Sales patterns"])
    with drivers_tab:
        st.info(
            "Positive contributions raise the estimate; negative contributions lower it. These are model associations."
        )
        drivers = pd.DataFrame(result["drivers"]).dropna(subset=["contribution"])
        if not drivers.empty:
            drivers["Driver"] = drivers.feature.map(lambda value: friendly(value))
            figure = px.bar(
                drivers,
                x="contribution",
                y="Driver",
                orientation="h",
                color=drivers.contribution.ge(0).map(
                    {True: "Raises estimate", False: "Lowers estimate"}
                ),
                color_discrete_map={
                    "Raises estimate": config["dashboard"]["colors"]["secondary"],
                    "Lowers estimate": config["dashboard"]["colors"]["primary"],
                },
                labels={"contribution": "Contribution in menu units", "Driver": ""},
            )
            chart(figure, config)
        with st.expander("Read all five driver explanations"):
            for driver in result["drivers"]:
                st.write("• " + driver["explanation"])
            st.caption(result["method"])
    with patterns_tab:
        pattern = st.selectbox(
            "Explore a pattern", ["Weekday", "Festival", "Weather"], key="pattern"
        )
        name = {"Weekday": "weekly", "Festival": "festival", "Weather": "weather"}[pattern]
        st.image(
            str(resolve_path(config, "figures") / config["eda"]["figures"][name]),
            use_container_width=True,
        )
        st.caption(
            "Training-period patterns can also reflect seasons, promotions and trend. They do not establish cause and effect."
        )


def performance(data: DashboardBackend, config: dict) -> None:
    st.caption(
        "How accurate are the forecasts, and what happened when we tested the ordering policies?"
    )
    measurements = data.metrics()
    metrics = measurements["metrics"]
    rows = pd.DataFrame(metrics["one_day_test_metrics"])
    selected = rows.loc[rows.model.eq(metrics["selected_point_model"])].iloc[0]
    columns = st.columns(3)
    columns[0].metric(
        "Selected model's error",
        f"{selected.wape:.2%}",
        help="WAPE: total absolute forecast error divided by total actual sales. Lower is better.",
    )
    columns[1].metric(
        "Better than last week's forecast",
        f"{metrics['relative_wape_improvement']:.1%}",
        help="Relative WAPE improvement over seasonal naive.",
    )
    columns[2].metric("Clean test records", f"{metrics['test_rows']:,}")
    forecasting, simulation_tab = st.tabs(["🎯 Forecast accuracy", "♻️ Waste & service"])
    with forecasting:
        st.subheader("Lower forecast error is better")
        display = rows.assign(Model=rows.model.map(friendly)).sort_values("wape", ascending=False)
        figure = px.bar(
            display,
            x="wape",
            y="Model",
            orientation="h",
            text="wape",
            color=display.model.eq(metrics["selected_point_model"]),
            color_discrete_map={True: config["dashboard"]["colors"]["secondary"], False: "#c7bdb0"},
            labels={"wape": "Forecast error (WAPE)", "Model": ""},
        )
        figure.update_layout(showlegend=False)
        figure.update_xaxes(tickformat=".0%")
        figure.update_traces(texttemplate="%{x:.2%}", textposition="outside")
        chart(figure, config)
        st.caption(
            "LightGBM was selected using validation data. Ridge scored better on test, but we did not change selection after seeing test results."
        )
        table(rows[["model", "wape", "mae"]])
        with st.expander("More evaluation details"):
            table(rows)
            st.write(
                "P10–P90 test coverage is 74.07%, below its nominal 80%. Forecast bands are not calibrated guarantees."
            )
    with simulation_tab:
        simulation = measurements.get("simulation")
        if simulation:
            policies = pd.DataFrame(simulation["policies"])
            st.subheader("Less waste, with a service tradeoff")
            st.caption(
                f"{simulation['test_days']} replay days. All policies face the same synthetic demand and initial stock."
            )
            left, right = st.columns(2)
            for column, value, title in (
                (left, "waste_cost", "Expired ingredient cost (₹)"),
                (right, "lost_units", "Lost sales (menu units)"),
            ):
                with column:
                    display = policies.assign(Policy=policies.policy.map(friendly))
                    figure = px.bar(
                        display,
                        x="Policy",
                        y=value,
                        color="Policy",
                        color_discrete_sequence=config["dashboard"]["colors"]["palette"],
                        labels={value: title, "Policy": ""},
                    )
                    figure.update_layout(showlegend=False)
                    chart(figure, config)
            table(policies[["policy", "service_level", "lost_units", "waste_cost", "total_cost"]])
            st.warning(
                "ML wasted less stock than manual ordering, but lost more sales. Its small cost advantage reverses when remaining stock is fully credited."
            )
        else:
            st.info("Run the policy simulation to see waste and service comparisons.")


def whatif(data: DashboardBackend, days: int, config: dict) -> None:
    st.caption(
        "Try a different weather or promotion plan and see how expected sales change. This experiment does not save stock changes."
    )
    settings = config["dashboard"]["weather_controls"]
    with st.form("whatif"):
        st.subheader("1. Choose the weather")
        columns = st.columns(3)
        maximum = columns[0].slider(
            "Maximum temperature (°C)",
            settings["temperature_min"],
            settings["temperature_max"],
            settings["default_max"],
            key="scenario_max",
        )
        minimum = columns[1].slider(
            "Minimum temperature (°C)",
            settings["temperature_min"],
            settings["temperature_max"],
            settings["default_min"],
            key="scenario_min",
        )
        rain = columns[2].slider(
            "Rainfall (mm)",
            0,
            settings["rainfall_max"],
            settings["default_rain"],
            key="scenario_rain",
        )
        st.subheader("2. Try a promotion or festival")
        item = st.selectbox(
            "Promotion item", list(config["menu"]), format_func=friendly, key="scenario_item"
        )
        promotion = st.selectbox(
            "Promotion",
            ["Keep planned promotion", "Enable promotion", "Disable promotion"],
            key="scenario_promo",
        )
        festival = st.selectbox(
            "First-day festival",
            ["Keep calendar", "Add festival", "Remove festival"],
            key="scenario_festival",
        )
        submitted = st.form_submit_button("Compare scenario", type="primary")
    if submitted:
        if maximum < minimum:
            st.error(
                "Maximum temperature must be at least the minimum temperature. Adjust the sliders and try again."
            )
            return
        snapshot = data.inventory()
        body = {
            "days": days,
            "temp_max": maximum,
            "temp_min": minimum,
            "rainfall": rain,
            "promotions": {}
            if promotion == "Keep planned promotion"
            else {item: promotion == "Enable promotion"},
            "festivals": {}
            if festival == "Keep calendar"
            else {snapshot["as_of_date"]: festival == "Add festival"},
        }
        st.session_state["scenario_result"] = data.scenario(body)
        st.session_state["scenario_days"] = days
    if "scenario_result" not in st.session_state:
        st.info("Ready to explore? Set your conditions above and select Compare scenario.")
    if "scenario_result" in st.session_state:
        baseline, scenario = st.session_state["scenario_result"]
        if st.session_state["scenario_days"] != days:
            st.info(
                "Showing the last submitted horizon. Submit again to compare the selected horizon."
            )
        delta = float(scenario.forecast.sum() - baseline.forecast.sum())
        st.metric("Expected menu-unit change", f"{delta:+,.1f}")
        joined = (
            baseline.groupby("item")
            .forecast.sum()
            .rename("Baseline")
            .to_frame()
            .join(scenario.groupby("item").forecast.sum().rename("Scenario"))
        )
        display = joined.copy()
        display.index = display.index.map(friendly)
        chart(
            px.bar(
                display,
                barmode="group",
                color_discrete_sequence=config["dashboard"]["colors"]["palette"],
                labels={"value": "Expected menu units", "item": "", "variable": "Estimate"},
            ),
            config,
        )
        table(joined.reset_index())
        st.caption(
            "A scenario can increase or decrease predictions. The difference is a model association, not a causal uplift estimate."
        )


def main() -> None:
    config = app_config()
    st.set_page_config(
        page_title="Brew & Balance | Café Planner",
        page_icon="☕",
        layout="wide",
        initial_sidebar_state="auto",
    )
    colors = config["dashboard"]["colors"]
    css = resolve_path(config, "dashboard_styles").read_text(encoding="utf-8")
    css = css.replace("$primary", colors["primary"]).replace("$sidebar", colors["sidebar"])
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="brand"><span class="brand-icon">☕</span><div class="brand-name">Brew &amp; Balance</div>'
        '<div class="brand-tagline">Plan sales. Stock smarter.<br>Make every ingredient count.</div></div>',
        unsafe_allow_html=True,
    )
    st.title("Brew & Balance")
    try:
        data = backend(json.dumps(config, sort_keys=True))
        snapshot = data.inventory()
    except (ValueError, OSError, httpx.HTTPError) as error:
        st.error(f"Dashboard data unavailable: {error}")
        st.caption(
            "Load the project data and model, or start the API when using the API connection."
        )
        st.stop()
    st.caption(f"Planning date {snapshot['as_of_date']}")
    default = st.query_params.get("screen", "Overview")
    default = default if default in SCREENS else "Overview"
    icons = dict(zip(SCREENS, ("🏡", "📈", "📦", "🛒", "💡", "🎯", "🌤️")))
    screen = st.sidebar.radio(
        "Explore your café",
        SCREENS,
        index=SCREENS.index(default),
        format_func=lambda value: f"{icons[value]}  {value}",
        key="navigation",
    )
    st.sidebar.divider()
    st.sidebar.subheader("Your planning window")
    days = st.sidebar.slider(
        "Forecast days",
        1,
        config["api"]["max_forecast_days"],
        config["project"]["forecast_horizon_days"],
        key="forecast_days",
    )
    st.sidebar.caption(
        "Choose how many days to forecast. Shopping lists also account for supplier delivery time."
    )
    st.markdown(
        f'<span class="planning-pill">📅 Planning from {escape(pd.Timestamp(snapshot["as_of_date"]).strftime("%d %b %Y"))}'
        " · Synthetic shop demo</span>",
        unsafe_allow_html=True,
    )
    st.header(screen)
    st.sidebar.caption("College project · Synthetic sales  ☕")

    if "stock_saved_message" in st.session_state:
        st.success(st.session_state.pop("stock_saved_message"))
    try:
        if screen == "Overview":
            overview(data, days, config)
        elif screen == "Demand Forecast":
            demand(data, days, config)
        elif screen == "Raw Materials":
            materials(data, days, config)
        elif screen == "Order Recommendations":
            orders_view(data)
        elif screen == "Insights":
            insights(data, config)
        elif screen == "Model Performance":
            performance(data, config)
        else:
            whatif(data, days, config)
    except ConflictError:
        st.error("Stock changed since it was loaded. Use Reload stock and retry your update.")
    except (ValueError, OSError, httpx.HTTPError) as error:
        st.error(f"Unable to load this view: {error}")
        st.caption(
            "Check that data, model and reports exist. If using the API connection, start the local API first."
        )


if __name__ == "__main__":
    main()
