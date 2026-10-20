from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyodbc


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and load the Walmart SQL Server reporting database.")
    parser.add_argument("--server", default="localhost", help="SQL Server name or instance.")
    parser.add_argument("--driver", default="ODBC Driver 17 for SQL Server", help="Installed ODBC driver name.")
    return parser.parse_args()


def connect(server: str, database: str, driver: str) -> pyodbc.Connection:
    connection_string = (
        f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
        "Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
    )
    return pyodbc.connect(connection_string, autocommit=True, timeout=15)


def execute_script(connection: pyodbc.Connection, path: Path) -> None:
    script = path.read_text(encoding="utf-8")
    batches = re.split(r"^\s*GO\s*$", script, flags=re.IGNORECASE | re.MULTILINE)
    cursor = connection.cursor()
    for batch in batches:
        if batch.strip():
            cursor.execute(batch)


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def insert_dataframe(connection: pyodbc.Connection, table: str, frame: pd.DataFrame, columns: list[str]) -> None:
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(f"[{column}]" for column in columns)
    statement = f"INSERT INTO dbo.{table} ({column_sql}) VALUES ({placeholders})"
    cursor = connection.cursor()
    cursor.fast_executemany = True
    batch_size = 5000
    for start in range(0, len(frame), batch_size):
        batch = frame.iloc[start : start + batch_size][columns]
        rows = [tuple(clean_value(value) for value in row) for row in batch.itertuples(index=False, name=None)]
        cursor.executemany(statement, rows)


def main() -> None:
    args = parse_args()
    try:
        master = connect(args.server, "master", args.driver)
    except pyodbc.Error as exc:
        raise SystemExit(
            "Could not connect to SQL Server. Verify the instance name and Windows/ODBC encryption configuration.\n"
            f"Original error: {exc}"
        ) from exc

    execute_script(master, SQL_DIR / "01_create_database.sql")
    master.close()
    database = connect(args.server, "WalmartRetailPerformance", args.driver)

    dim_store = pd.read_csv(PROCESSED_DIR / "dim_store.csv")
    dim_department = pd.read_csv(PROCESSED_DIR / "dim_department.csv")
    dim_date = pd.read_csv(PROCESSED_DIR / "dim_date.csv")
    fact = pd.read_csv(PROCESSED_DIR / "fact_weekly_sales.csv").rename(
        columns={"Fuel_Price": "FuelPrice"}
    )

    insert_dataframe(database, "DimStore", dim_store, ["Store", "StoreType", "StoreSize"])
    insert_dataframe(database, "DimDepartment", dim_department, ["Dept"])
    insert_dataframe(
        database,
        "DimDate",
        dim_date,
        ["DateKey", "Date", "Year", "Quarter", "MonthNumber", "MonthName", "WeekOfYear", "WeekEndingFriday"],
    )
    insert_dataframe(
        database,
        "FactWeeklySales",
        fact,
        [
            "Store", "Dept", "Date", "DateKey", "ActualSales", "IsHoliday", "Temperature", "FuelPrice",
            "MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5", "MarkDownTotal", "CPI",
            "Unemployment", "PlanSales", "ForecastSales", "ForecastMethod",
        ],
    )
    execute_script(database, SQL_DIR / "02_reporting_views.sql")
    count, total = database.cursor().execute(
        "SELECT COUNT(*), SUM(ActualSales) FROM dbo.FactWeeklySales"
    ).fetchone()
    print(f"Loaded {count:,} fact rows with ${total:,.2f} in actual sales.")
    database.close()


if __name__ == "__main__":
    main()

