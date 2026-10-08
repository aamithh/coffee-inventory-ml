"""Read evaluation-only oracle demand from its isolated database."""

import sqlite3
from contextlib import closing
from typing import Any
import pandas as pd
from src.utils.config import resolve_path


def load_truth(config: dict[str, Any]) -> pd.DataFrame:
    """Load isolated simulation truth for diagnostics/simulation, never training."""
    database = resolve_path(config, "truth_database")
    if not database.exists():
        raise FileNotFoundError(f"Simulation truth database is missing: {database}")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
        return pd.read_sql_query(
            "SELECT * FROM simulation_truth ORDER BY date, item", connection, parse_dates=["date"]
        )
