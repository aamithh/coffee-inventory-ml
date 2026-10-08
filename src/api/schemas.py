"""Strict API payloads and JSON-safe forecast/inventory response contracts."""

from datetime import date
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, StrictBool, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ItemForecast(Schema):
    date: date
    item: str
    forecast: FiniteFloat
    p10: FiniteFloat
    p50: FiniteFloat
    p90: FiniteFloat
    horizon_day: int


class ItemResponse(Schema):
    as_of_date: date
    days: int
    model: str
    scenario: bool = False
    forecasts: list[ItemForecast]
    limitations: list[str]


class MaterialForecast(Schema):
    date: date
    material: str
    need: FiniteFloat
    need_p10: FiniteFloat
    need_p50: FiniteFloat
    need_p90: FiniteFloat
    unit: str
    expected_cost: FiniteFloat


class MaterialResponse(Schema):
    as_of_date: date
    days: int
    requirements: list[MaterialForecast]
    limitations: list[str]


class InventoryRow(Schema):
    material: str = Field(min_length=1)
    on_hand: FiniteFloat = Field(ge=0, strict=True)
    on_order: FiniteFloat = Field(default=0, ge=0, strict=True)
    arrival_date: date | None = None

    @model_validator(mode="after")
    def pending_date(self) -> "InventoryRow":
        if self.on_order > 0 and self.arrival_date is None:
            raise ValueError("Positive on_order requires arrival_date.")
        if self.on_order == 0 and self.arrival_date is not None:
            raise ValueError("arrival_date must be null when on_order is zero.")
        return self


class InventoryResponse(Schema):
    as_of_date: date
    version: int
    illustrative: bool
    rows: list[InventoryRow]


class InventoryUpdate(Schema):
    expected_version: int = Field(ge=0, strict=True)
    rows: list[InventoryRow] = Field(min_length=1)


class Recommendation(Schema):
    material: str
    unit: str
    order_now: bool
    order_qty: FiniteFloat
    order_by_date: date | None
    expected_arrival: date | None
    planning_arrival_date: date
    safety_stock: FiniteFloat
    reorder_point: FiniteFloat
    coverage_days: int
    pre_arrival_shortfall: FiniteFloat
    unmet_order_quantity: FiniteFloat
    estimated_order_cost: FiniteFloat
    reason: str


class OrderResponse(Schema):
    as_of_date: date
    forecast_days: int
    inventory_version: int
    illustrative_inventory: bool
    recommendations: list[Recommendation]
    limitations: list[str]


class WhatIfRequest(Schema):
    days: int = Field(default=7, ge=1, strict=True)
    temp_max: FiniteFloat | None = None
    temp_min: FiniteFloat | None = None
    rainfall: FiniteFloat | None = Field(default=None, ge=0)
    promotions: dict[str, StrictBool] = Field(default_factory=dict)
    festivals: dict[date, StrictBool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def temperature_order(self) -> "WhatIfRequest":
        if (
            self.temp_max is not None
            and self.temp_min is not None
            and self.temp_min > self.temp_max
        ):
            raise ValueError("temp_min must not exceed temp_max.")
        return self


class WhatIfResponse(Schema):
    baseline: ItemResponse
    scenario: ItemResponse
    material_requirements: MaterialResponse
    point_total_change: FiniteFloat
    interpretation: str


class HealthResponse(Schema):
    status: str
    as_of_date: date
    model_available: bool
    data_available: bool
    inventory_available: bool


class MetricsResponse(Schema):
    metrics: dict[str, Any]
    simulation: dict[str, Any] | None = None
