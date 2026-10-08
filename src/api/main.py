"""Local FastAPI forecast, inventory and what-if application."""

import json
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.api.schemas import (
    HealthResponse,
    InventoryResponse,
    InventoryUpdate,
    ItemForecast,
    ItemResponse,
    MaterialForecast,
    MaterialResponse,
    MetricsResponse,
    OrderResponse,
    Recommendation,
    WhatIfRequest,
    WhatIfResponse,
)
from src.api.service import ConflictError, InventoryService, LIMITATIONS
from src.inventory.requirements import material_requirements
from src.utils.config import load_config, resolve_path

LOGGER = logging.getLogger(__name__)


def records(frame):
    """Pandas dates and missing values become ISO strings and JSON nulls."""
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def create_app(config: dict | None = None) -> FastAPI:
    """Construct independent service state; imports do not load models or write files."""
    settings = load_config() if config is None else config
    service = InventoryService(settings)
    app = FastAPI(
        title="Coffee Inventory ML",
        version="0.6.0",
        description="Past-only forecasts and local aggregate inventory planning. Scenario predictions are associations.",
    )
    app.state.service = service

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, error):
        # Echoing a rejected NaN/Infinity input would itself break strict JSON output.
        details = [
            {"type": entry["type"], "loc": list(entry["loc"]), "msg": entry["msg"]}
            for entry in error.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": details})

    def run(function, *args):
        try:
            return function(*args)
        except ConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except FileNotFoundError as error:
            LOGGER.warning("Required API artifact unavailable: %s", error)
            raise HTTPException(
                status_code=503,
                detail="Required data/model/report is unavailable. Run the completed project phases first.",
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except OSError as error:
            LOGGER.exception("API artifact access failed")
            raise HTTPException(
                status_code=503, detail="Artifact access failed; prior inventory remains available."
            ) from error

    def item_response(frame, days, scenario=False):
        rows = frame[["date", "item", "forecast", "p10", "p50", "p90", "horizon_day"]].copy()
        rows["date"] = rows.date.dt.strftime("%Y-%m-%d")
        return ItemResponse(
            as_of_date=service.origin.date(),
            days=days,
            model=service._artifact["selected_point"],
            scenario=scenario,
            forecasts=[ItemForecast.model_validate(row) for row in records(rows)],
            limitations=LIMITATIONS,
        )

    def material_response(frame, days):
        needs = material_requirements(frame, settings)
        needs["date"] = needs.date.dt.strftime("%Y-%m-%d")
        return MaterialResponse(
            as_of_date=service.origin.date(),
            days=days,
            requirements=[MaterialForecast.model_validate(row) for row in records(needs)],
            limitations=[
                LIMITATIONS[0],
                "Material quantile sums are planning proxies, not calibrated aggregate bands.",
            ],
        )

    @app.get("/health", response_model=HealthResponse)
    def health():
        available = {
            key: resolve_path(settings, key).is_file() for key in ("database", "model_bundle")
        }
        try:
            service.inventory()
            inventory_available = True
        except (ValueError, OSError):
            inventory_available = False
        ready = all(available.values()) and inventory_available
        return HealthResponse(
            status="ready" if ready else "degraded",
            as_of_date=service.origin.date(),
            model_available=available["model_bundle"],
            data_available=available["database"],
            inventory_available=inventory_available,
        )

    @app.get("/forecast/items", response_model=ItemResponse)
    def forecast_items(days: int = Query(default=7, ge=1)):
        frame = run(service.forecast, days)
        return item_response(frame, days)

    @app.get("/forecast/materials", response_model=MaterialResponse)
    def forecast_materials(days: int = Query(default=7, ge=1)):
        return material_response(run(service.forecast, days), days)

    @app.get("/recommendations/orders", response_model=OrderResponse)
    def recommendations():
        frame, snapshot, horizon = run(service.orders)
        allowed = set(Recommendation.model_fields)
        rows = frame[[key for key in frame.columns if key in allowed]]
        return OrderResponse(
            as_of_date=service.origin.date(),
            forecast_days=horizon,
            inventory_version=snapshot.version,
            illustrative_inventory=snapshot.illustrative,
            recommendations=[Recommendation.model_validate(row) for row in records(rows)],
            limitations=[
                LIMITATIONS[0],
                "Aggregate stock has no lot-age expiry detail; supplier packs may limit feasible service.",
            ],
        )

    @app.get("/inventory", response_model=InventoryResponse)
    def inventory():
        return run(service.inventory)

    @app.post("/inventory", response_model=InventoryResponse)
    def update_inventory(update: InventoryUpdate):
        return run(service.update_inventory, update)

    @app.post("/whatif", response_model=WhatIfResponse)
    def whatif(request: WhatIfRequest):
        run(service.check_days, request.days)
        changed = run(service.forecast, request.days, request)
        baseline = run(service.forecast, request.days)
        return WhatIfResponse(
            baseline=item_response(baseline, request.days),
            scenario=item_response(changed, request.days, True),
            material_requirements=material_response(changed, request.days),
            point_total_change=float(changed.forecast.sum() - baseline.forecast.sum()),
            interpretation="Hypothetical model association, not a causal uplift estimate. Inventory and baseline configuration are unchanged.",
        )

    @app.get("/model/metrics", response_model=MetricsResponse)
    def metrics():
        return run(service.metrics)

    return app


app = create_app()
