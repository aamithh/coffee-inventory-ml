"""Past-only forecast service and versioned aggregate inventory persistence."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
import json
import pandas as pd
from src.api.schemas import InventoryResponse, InventoryRow, InventoryUpdate, WhatIfRequest
from src.data.artifacts import publish_artifacts
from src.data.loader import load_sales
from src.inventory.bom import bom_matrix
from src.inventory.requirements import material_requirements
from src.inventory.reorder import planning_horizon, recommend_orders
from src.models.predict import load_artifact, recursive_forecast
from src.utils.config import resolve_path
from src.utils.dates import get_as_of_date, validate_forecast_calendar

LIMITATIONS = [
    "Quantile bands are uncalibrated; nominal service levels are not guarantees.",
    "Forecast origin follows configured demo date; weather defaults to past persistence.",
]


class ConflictError(Exception):
    """Stale inventory revision supplied by a caller."""


class InventoryService:
    """One local process; locks serialize model use and atomic snapshot revisions."""

    def __init__(self, config: dict) -> None:
        self.config = deepcopy(config)
        self.origin = get_as_of_date(config)
        self.lock = RLock()
        self._artifact = None

    def check_days(self, days: int) -> None:
        if not 1 <= days <= self.config["api"]["max_forecast_days"]:
            raise ValueError(
                f"days must be between 1 and {self.config['api']['max_forecast_days']}."
            )
        config = deepcopy(self.config)
        config["project"]["forecast_horizon_days"] = days
        validate_forecast_calendar(config)

    def forecast(self, days: int, scenario: WhatIfRequest | None = None) -> pd.DataFrame:
        """Pass only legitimate planned metadata and strictly prior observed history."""
        self.check_days(days)
        config = deepcopy(self.config)
        origin = self.origin
        dates = pd.date_range(origin, periods=days)
        history = load_sales(config, end_date=str((origin - pd.Timedelta(days=1)).date()))
        if history.empty:
            raise ValueError("No observed history before requested forecast origin.")
        plans = load_sales(config, start_date=str(origin.date()), end_date=str(dates[-1].date()))[
            ["date", "item", "category", "price", "promo_flag"]
        ]
        missing = dates.difference(plans.date.unique())
        if len(missing):
            plans = pd.concat(
                [
                    plans,
                    pd.DataFrame(
                        [
                            dict(
                                date=d,
                                item=item,
                                category=m["category"],
                                price=m["price"],
                                promo_flag=0,
                            )
                            for d in missing
                            for item, m in config["menu"].items()
                        ]
                    ),
                ],
                ignore_index=True,
            )
        weather = None
        if scenario is not None:
            unknown = set(scenario.promotions) - set(config["menu"])
            if unknown:
                raise ValueError(f"Unknown promotion items: {sorted(unknown)}")
            if any(pd.Timestamp(day) not in dates for day in scenario.festivals):
                raise ValueError(
                    "Festival scenario dates must lie in the requested forecast horizon."
                )
            config["calendar"]["scenario_festivals"] = {
                str(day): config["api"]["scenario_festival_name"] if enabled else ""
                for day, enabled in scenario.festivals.items()
            }
            for item, enabled in scenario.promotions.items():
                mask = plans.item.eq(item)
                plans.loc[mask, "promo_flag"] = int(enabled)
                plans.loc[mask, "price"] = config["menu"][item]["price"] * (
                    1 - config["data"]["promotion_discount"] if enabled else 1
                )
            if any(
                value is not None
                for value in (scenario.temp_max, scenario.temp_min, scenario.rainfall)
            ):
                last = history.sort_values("date").iloc[-1]
                values = {
                    key: getattr(scenario, key)
                    if getattr(scenario, key) is not None
                    else float(last[key])
                    for key in ("temp_max", "temp_min", "rainfall")
                }
                if values["temp_min"] > values["temp_max"]:
                    raise ValueError(
                        "Scenario temperatures, including persistence defaults, must be ordered."
                    )
                weather = pd.DataFrame(
                    [
                        dict(
                            date=day,
                            issued_at=origin
                            - pd.Timedelta(minutes=config["api"]["scenario_issue_lead_minutes"]),
                            **values,
                        )
                        for day in dates
                    ]
                )
                config["features"]["weather_policy"] = "supplied"
        with self.lock:
            if self._artifact is None:
                self._artifact = load_artifact(self.config)
            return recursive_forecast(
                self._artifact, history, plans, origin, config, weather_forecasts=weather
            )

    def inventory(self) -> InventoryResponse:
        """Read persistent revision or return the explicitly illustrative fallback."""
        with self.lock:
            path = resolve_path(self.config, "api_inventory_state")
            if path.exists():
                result = InventoryResponse.model_validate_json(path.read_text(encoding="utf-8"))
                if pd.Timestamp(result.as_of_date) != self.origin:
                    raise ValueError(
                        "Inventory snapshot date differs from the configured forecast origin."
                    )
                if set(row.material for row in result.rows) != set(self.config["materials"]) or len(
                    result.rows
                ) != len(self.config["materials"]):
                    raise ValueError(
                        "Stored inventory must contain exactly every configured material."
                    )
                self.validate_rows(result.rows)
                return result
            demo = resolve_path(self.config, "inventory_snapshot")
            if demo.exists():
                frame = pd.read_csv(demo)
            else:
                history = load_sales(
                    self.config, end_date=str((self.origin - pd.Timedelta(days=1)).date())
                )
                valid = history.loc[history.record_status.isin(["clean", "closed"])]
                means = valid.groupby("item").sales.mean().reindex(self.config["menu"]).fillna(0)
                matrix = bom_matrix(self.config)
                quantities = means.to_numpy() @ matrix.to_numpy()
                frame = pd.DataFrame(
                    [
                        dict(
                            material=m,
                            on_hand=float(q)
                            * (1 + s["wastage_factor"])
                            * min(
                                self.config["inventory"]["initial_coverage_days"],
                                s["shelf_life_days"] - self.config["inventory"]["buffer_days"],
                            ),
                            on_order=0,
                            arrival_date=None,
                        )
                        for (m, s), q in zip(self.config["materials"].items(), quantities)
                    ]
                )
            frame["arrival_date"] = (
                pd.to_datetime(frame.arrival_date)
                .dt.strftime("%Y-%m-%d")
                .where(frame.arrival_date.notna(), None)
            )
            rows = [InventoryRow.model_validate(row) for row in frame.to_dict(orient="records")]
            self.validate_rows(rows)
            return InventoryResponse(
                as_of_date=self.origin.date(), version=0, illustrative=True, rows=rows
            )

    def validate_rows(self, rows: list[InventoryRow]) -> None:
        if len({row.material for row in rows}) != len(rows):
            raise ValueError("Duplicate inventory materials.")
        for row in rows:
            if row.material not in self.config["materials"]:
                raise ValueError(f"Unknown material: {row.material}")
            if row.arrival_date is not None and pd.Timestamp(row.arrival_date) < self.origin:
                raise ValueError("Pending arrivals cannot precede inventory as_of_date.")

    def update_inventory(self, update: InventoryUpdate) -> InventoryResponse:
        """Patch full material rows with optimistic revision checking and atomic publication."""
        self.validate_rows(update.rows)
        with self.lock:
            current = self.inventory()
            if update.expected_version != current.version:
                raise ConflictError(
                    f"Inventory revision changed; expected version {current.version}."
                )
            mapping = {row.material: row for row in current.rows}
            mapping.update({row.material: row for row in update.rows})
            result = InventoryResponse(
                as_of_date=current.as_of_date,
                version=current.version + 1,
                illustrative=False,
                rows=[mapping[m] for m in self.config["materials"]],
            )
            target = resolve_path(self.config, "api_inventory_state")
            staging = resolve_path(self.config, "pipeline_staging")
            staging.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=staging, prefix="api_inventory_") as directory:
                source = Path(directory) / "snapshot.json"
                source.write_text(result.model_dump_json(indent=2), encoding="utf-8")
                publish_artifacts([(source, target)])
            return result

    def orders(self) -> tuple[pd.DataFrame, InventoryResponse, int]:
        horizon = planning_horizon(self.config)
        needs = material_requirements(self.forecast(horizon), self.config)
        snapshot = self.inventory()
        frame = pd.DataFrame([row.model_dump(mode="json") for row in snapshot.rows])
        return recommend_orders(needs, frame, self.origin, self.config), snapshot, horizon

    def metrics(self) -> dict:
        result = json.loads(resolve_path(self.config, "metrics").read_text(encoding="utf-8"))
        simulation_path = resolve_path(self.config, "simulation_metrics")
        return {
            "metrics": result,
            "simulation": json.loads(simulation_path.read_text(encoding="utf-8"))
            if simulation_path.exists()
            else None,
        }
