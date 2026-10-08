"""Dashboard access to existing services with optional HTTP transport."""

from copy import deepcopy
import json
import httpx
import pandas as pd
from src.api.schemas import InventoryUpdate, WhatIfRequest
from src.api.service import InventoryService
from src.data.loader import load_sales
from src.features.build_features import build_prediction_features
from src.inventory.requirements import material_requirements
from src.models.explain import explain_prediction
from src.models.predict import load_artifact
from src.utils.config import resolve_path


class DashboardBackend:
    """Use existing module contracts locally, or the same contracts over the API."""

    def __init__(self, config: dict) -> None:
        self.config = deepcopy(config)
        self.service = InventoryService(config)
        self.http = (
            httpx.Client(
                base_url=config["dashboard"]["api_url"],
                timeout=config["dashboard"]["request_timeout_seconds"],
                trust_env=False,
            )
            if config["dashboard"]["backend"] == "http"
            else None
        )
        if config["dashboard"]["backend"] not in ("local", "http"):
            raise ValueError("Dashboard backend must be local or http.")

    def request(self, method: str, path: str, body: dict | None = None) -> dict:
        response = self.http.request(method, path, json=body)
        if response.is_error:
            raise ValueError(
                f"API HTTP {response.status_code}: {response.json().get('detail', 'Request failed')}"
            )
        return response.json()

    def forecast(self, days: int) -> pd.DataFrame:
        if self.http:
            frame = pd.DataFrame(self.request("GET", f"/forecast/items?days={days}")["forecasts"])
            frame["date"] = pd.to_datetime(frame.date)
            return frame
        return self.service.forecast(days)

    def inventory(self) -> dict:
        return (
            self.request("GET", "/inventory")
            if self.http
            else self.service.inventory().model_dump(mode="json")
        )

    def update(self, body: dict) -> dict:
        return (
            self.request("POST", "/inventory", body)
            if self.http
            else self.service.update_inventory(InventoryUpdate.model_validate(body)).model_dump(
                mode="json"
            )
        )

    def orders(self) -> pd.DataFrame:
        if self.http:
            return pd.DataFrame(self.request("GET", "/recommendations/orders")["recommendations"])
        return self.service.orders()[0]

    def metrics(self) -> dict:
        return self.request("GET", "/model/metrics") if self.http else self.service.metrics()

    def scenario(self, body: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
        if self.http:
            data = self.request("POST", "/whatif", body)
            return pd.DataFrame(data["baseline"]["forecasts"]), pd.DataFrame(
                data["scenario"]["forecasts"]
            )
        request = WhatIfRequest.model_validate(body)
        return self.service.forecast(request.days), self.service.forecast(request.days, request)

    def history(self) -> pd.DataFrame:
        start = self.service.origin - pd.Timedelta(days=self.config["dashboard"]["history_days"])
        return load_sales(
            self.config,
            start_date=str(start.date()),
            end_date=str((self.service.origin - pd.Timedelta(days=1)).date()),
        )

    def explanation(self, item: str) -> dict:
        """Explain the first forecast day from the same past-only feature contract."""
        origin = self.service.origin
        history = load_sales(self.config, end_date=str((origin - pd.Timedelta(days=1)).date()))
        plans = load_sales(self.config, start_date=str(origin.date()), end_date=str(origin.date()))[
            ["date", "item", "category", "price", "promo_flag"]
        ]
        if plans.empty:
            plans = pd.DataFrame(
                [
                    dict(
                        date=origin, item=i, category=m["category"], price=m["price"], promo_flag=0
                    )
                    for i, m in self.config["menu"].items()
                ]
            )
        row = build_prediction_features(history, plans, origin, self.config).frame
        row = row.loc[row.item.eq(item)]
        artifact = load_artifact(self.config)
        return explain_prediction(
            artifact["point_models"][artifact["selected_point"]],
            row,
            self.config["models"]["explanation_top_n"],
        )

    def eda(self) -> dict:
        return json.loads(resolve_path(self.config, "eda_summary").read_text(encoding="utf-8"))

    def materials(self, forecast: pd.DataFrame) -> pd.DataFrame:
        return material_requirements(forecast, self.config)
