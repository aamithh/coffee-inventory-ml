"""FIFO quantities with receipt-date expiry and conservation-friendly events."""

from dataclasses import dataclass
import math
import pandas as pd


@dataclass
class Lot:
    quantity: float
    received: pd.Timestamp
    expires: pd.Timestamp


class Stock:
    """FIFO lots; expiry at start of expires date, before consumption."""

    def __init__(self) -> None:
        self.lots: list[Lot] = []

    @property
    def quantity(self) -> float:
        return sum(lot.quantity for lot in self.lots)

    def receive(self, quantity: float, day: pd.Timestamp, shelf_life: int) -> None:
        if not math.isfinite(quantity) or quantity < 0 or shelf_life < 1:
            raise ValueError("Invalid lot quantity or shelf life.")
        if quantity:
            self.lots.append(Lot(quantity, day, day + pd.Timedelta(days=shelf_life)))
            self.lots.sort(key=lambda lot: lot.received)

    def expire(self, day: pd.Timestamp) -> float:
        waste = sum(lot.quantity for lot in self.lots if lot.expires <= day)
        self.lots = [lot for lot in self.lots if lot.expires > day]
        return waste

    def consume(self, quantity: float) -> float:
        if not math.isfinite(quantity) or quantity < 0:
            raise ValueError("Consumption must be finite and nonnegative.")
        requested = quantity
        for lot in self.lots:
            used = min(quantity, lot.quantity)
            lot.quantity -= used
            quantity -= used
            if quantity <= 1e-9:
                break
        self.lots = [lot for lot in self.lots if lot.quantity > 1e-9]
        return requested - quantity

    def copy(self) -> "Stock":
        result = Stock()
        result.lots = [Lot(lot.quantity, lot.received, lot.expires) for lot in self.lots]
        return result
