"""Transactional observed/truth persistence with separate SQLite files."""

import sqlite3
from contextlib import closing
from typing import Any
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from src.data.quality import validate_sales, validate_truth
from src.utils.config import resolve_path


def _sql_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Serialize dates consistently for portable range queries."""
    result = frame.copy()
    if "date" in result:
        result["date"] = pd.to_datetime(result["date"]).dt.strftime("%Y-%m-%d")
    return result


def save_dataset(
    sales: pd.DataFrame,
    truth: pd.DataFrame,
    calendar: pd.DataFrame,
    weather: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    """Refresh public tables and attached oracle tables in one DELETE-journal transaction."""
    validate_sales(sales, config)
    validate_truth(truth, sales)
    database = resolve_path(config, "database").resolve()
    truth_database = resolve_path(config, "truth_database").resolve()
    if database == truth_database:
        raise ValueError("Observed and simulation truth databases must be different files.")
    mode = config["sqlite"]["journal_mode"].upper()
    if mode != "DELETE":
        raise ValueError("Use DELETE journaling for atomic commits across the attached databases.")
    for path in (database, truth_database):
        path.parent.mkdir(parents=True, exist_ok=True)
    tables = {
        "sales": sales,
        "calendar": calendar,
        "weather": weather,
        "menu": pd.DataFrame([{"item": item, **value} for item, value in config["menu"].items()]),
        "materials": pd.DataFrame(
            [{"material": name, **value} for name, value in config["materials"].items()]
        ),
        "recipes": pd.DataFrame(
            [
                {"item": item, "material": material, "quantity": quantity}
                for item, recipe in config["recipes"].items()
                for material, quantity in recipe.items()
            ]
        ),
    }
    engine = create_engine(URL.create("sqlite", database=str(database)))
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("ATTACH DATABASE ? AS oracle", (str(truth_database),))
            connection.exec_driver_sql(f"PRAGMA main.journal_mode={mode}")
            connection.exec_driver_sql(f"PRAGMA oracle.journal_mode={mode}")
            connection.commit()
            with connection.begin():
                connection.exec_driver_sql("BEGIN")
                for table, frame in tables.items():
                    _sql_frame(frame).to_sql(table, connection, if_exists="replace", index=False)
                _sql_frame(truth).to_sql(
                    "simulation_truth",
                    connection,
                    schema="oracle",
                    if_exists="replace",
                    index=False,
                )
                # Migration removes legacy oracle data only inside the successful transaction.
                connection.exec_driver_sql("DROP TABLE IF EXISTS main.simulation_truth")
                connection.exec_driver_sql(
                    'CREATE UNIQUE INDEX sales_date_item ON sales ("date", "item")'
                )
                connection.exec_driver_sql(
                    'CREATE UNIQUE INDEX oracle.simulation_truth_date_item ON simulation_truth ("date", "item")'
                )
                for table in ("calendar", "weather"):
                    connection.exec_driver_sql(
                        f'CREATE UNIQUE INDEX "{table}_date" ON "{table}" ("date")'
                    )
    finally:
        engine.dispose()


def load_sales(
    config: dict[str, Any], start_date: str | None = None, end_date: str | None = None
) -> pd.DataFrame:
    """Read only the observed database; do not attach any other database."""
    database = resolve_path(config, "database").resolve()
    if not database.exists():
        raise FileNotFoundError(f"Generate data first; database missing: {database}")
    query = "SELECT * FROM sales"
    conditions, parameters = [], []
    for value, operator in ((start_date, ">="), (end_date, "<=")):
        if value is not None:
            conditions.append(f"date {operator} ?")
            parameters.append(pd.Timestamp(value).strftime("%Y-%m-%d"))
    if (
        start_date is not None
        and end_date is not None
        and pd.Timestamp(start_date) > pd.Timestamp(end_date)
    ):
        raise ValueError("start_date must be <= end_date.")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date, item"
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
        frame = pd.read_sql_query(query, connection, params=parameters, parse_dates=["date"])
    frame["usable_for_training"] = frame["usable_for_training"].astype(bool)
    return frame
