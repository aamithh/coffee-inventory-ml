"""Validated item-to-material recipe contracts in configured native units."""

from typing import Any
import numpy as np
import pandas as pd


def bom_matrix(config: dict[str, Any]) -> pd.DataFrame:
    """Rows are menu items, columns materials; no recipe multiplier is applied twice."""
    menu, materials, recipes = config["menu"], config["materials"], config["recipes"]
    if not menu or not materials or set(recipes) != set(menu):
        raise ValueError("Every menu item needs a recipe and materials must be nonempty.")
    matrix = pd.DataFrame(0.0, index=list(menu), columns=list(materials))
    for item, recipe in recipes.items():
        if not recipe:
            raise ValueError(f"Recipe is empty: {item}")
        for material, quantity in recipe.items():
            if (
                material not in materials
                or isinstance(quantity, bool)
                or not np.isfinite(quantity)
                or quantity <= 0
            ):
                raise ValueError(f"Invalid recipe quantity: {item}/{material}")
            matrix.loc[item, material] = float(quantity)
    for name, settings in materials.items():
        for key in ("unit_cost", "wastage_factor", "min_order_qty"):
            value = settings[key]
            if isinstance(value, bool) or not np.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {name}/{key}")
        if settings["min_order_qty"] <= 0 or not settings["unit"]:
            raise ValueError(f"Invalid material unit/order multiple: {name}")
        for key in ("lead_time_days", "shelf_life_days"):
            value = settings[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name}/{key} must be a nonnegative integer.")
        if settings["shelf_life_days"] < 1:
            raise ValueError("Shelf life must be positive.")
    matrix.index.name = "item"
    matrix.columns.name = "material"
    return matrix
