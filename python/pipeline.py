from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
EXCEL_DIR = ROOT / "excel"
PLAN_GROWTH_RATE = 0.03
EVALUATION_YEAR = 2012
RANDOM_STATE = 42

MARKDOWN_COLUMNS = [f"MarkDown{i}" for i in range(1, 6)]
MODEL_FEATURES = [
    "Store",
    "Dept",
    "TypeCode",
    "Size",
    "Month",
    "WeekOfYear",
    "IsHolidayInt",
    "Temperature",
    "Fuel_Price",
    "CPI",
    "Unemployment",
    *MARKDOWN_COLUMNS,
    *[f"{column}_Missing" for column in MARKDOWN_COLUMNS],
    "Lag52Sales",
]


def weighted_mae(actual: pd.Series, predicted: pd.Series, holiday: pd.Series) -> float:
    weights = np.where(holiday.astype(bool), 5.0, 1.0)
    return float(np.average(np.abs(actual - predicted), weights=weights))


def load_source_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = [RAW_DIR / "train.csv.zip", RAW_DIR / "features.csv.zip", RAW_DIR / "stores.csv"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files: {missing}")

    train = pd.read_csv(required[0], parse_dates=["Date"])
    features = pd.read_csv(required[1], parse_dates=["Date"])
    stores = pd.read_csv(required[2])
    return train, features, stores


def build_quality_report(
    train: pd.DataFrame, features: pd.DataFrame, stores: pd.DataFrame, merged: pd.DataFrame
) -> pd.DataFrame:
    checks = [
        ("Sales row count", len(train), "Informational"),
        ("Feature row count", len(features), "Informational"),
        ("Store row count", len(stores), "Informational"),
        ("Duplicate sales keys", train.duplicated(["Store", "Dept", "Date"]).sum(), "Must equal 0"),
        ("Duplicate feature keys", features.duplicated(["Store", "Date"]).sum(), "Must equal 0"),
        ("Unmatched sales-feature rows", merged["Temperature"].isna().sum(), "Must equal 0"),
        ("Rows missing store metadata", merged["Type"].isna().sum(), "Must equal 0"),
        ("Missing weekly sales", train["Weekly_Sales"].isna().sum(), "Must equal 0"),
        ("Negative net-sales rows", (train["Weekly_Sales"] < 0).sum(), "Flagged; retained as likely returns"),
        ("Zero-sales rows", (train["Weekly_Sales"] == 0).sum(), "Flagged; retained"),
        ("Rows with any missing markdown", features[MARKDOWN_COLUMNS].isna().any(axis=1).sum(), "Expected before/after rollout"),
        ("Rows missing CPI", features["CPI"].isna().sum(), "Expected in future feature dates"),
        ("Rows missing unemployment", features["Unemployment"].isna().sum(), "Expected in future feature dates"),
    ]
    return pd.DataFrame(checks, columns=["Check", "Result", "Expectation"])


def prepare_data(
    train: pd.DataFrame, features: pd.DataFrame, stores: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    merged = train.merge(
        features,
        on=["Store", "Date"],
        how="left",
        suffixes=("", "_Feature"),
        validate="many_to_one",
    ).merge(stores, on="Store", how="left", validate="many_to_one")

    quality = build_quality_report(train, features, stores, merged)
    merged["IsHoliday"] = merged["IsHoliday"].astype(bool)
    merged["IsHolidayInt"] = merged["IsHoliday"].astype(int)
    merged["Year"] = merged["Date"].dt.year
    merged["Month"] = merged["Date"].dt.month
    merged["WeekOfYear"] = merged["Date"].dt.isocalendar().week.astype(int)
    merged["DateKey"] = merged["Date"].dt.strftime("%Y%m%d").astype(int)
    merged["TypeCode"] = merged["Type"].map({"A": 0, "B": 1, "C": 2}).astype(int)

    for column in MARKDOWN_COLUMNS:
        merged[f"{column}_Missing"] = merged[column].isna().astype(int)
        merged[column] = merged[column].fillna(0.0)
    merged["MarkDownTotal"] = merged[MARKDOWN_COLUMNS].sum(axis=1)

    merged["CPI"] = merged["CPI"].fillna(merged.groupby("Store")["CPI"].transform("median"))
    merged["Unemployment"] = merged["Unemployment"].fillna(
        merged.groupby("Store")["Unemployment"].transform("median")
    )

    lag = merged[["Store", "Dept", "Date", "Weekly_Sales"]].copy()
    lag["Date"] = lag["Date"] + pd.Timedelta(days=364)
    lag = lag.rename(columns={"Weekly_Sales": "Lag52Sales"})
    merged = merged.merge(lag, on=["Store", "Dept", "Date"], how="left", validate="one_to_one")

    evaluation = merged.loc[merged["Year"].eq(EVALUATION_YEAR) & merged["Lag52Sales"].notna()].copy()
    evaluation["PlanSales"] = evaluation["Lag52Sales"] * (1.0 + PLAN_GROWTH_RATE)
    evaluation["SeasonalNaiveForecast"] = evaluation["Lag52Sales"]

    training = merged.loc[
        merged["Date"].lt(pd.Timestamp(f"{EVALUATION_YEAR}-01-01")) & merged["Lag52Sales"].notna()
    ].copy()

    return merged, training, evaluation, quality


def train_and_score(training: pd.DataFrame, evaluation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    model = HistGradientBoostingRegressor(
        loss="absolute_error",
        learning_rate=0.08,
        max_iter=140,
        max_leaf_nodes=31,
        min_samples_leaf=40,
        l2_regularization=1.0,
        random_state=RANDOM_STATE,
    )
    model.fit(training[MODEL_FEATURES], training["Weekly_Sales"])
    evaluation["ModelForecast"] = model.predict(evaluation[MODEL_FEATURES])

    benchmarks = {
        "Seasonal naive": "SeasonalNaiveForecast",
        "Planning scenario": "PlanSales",
        "Gradient boosting": "ModelForecast",
    }
    metric_rows = []
    for method, column in benchmarks.items():
        metric_rows.append(
            {
                "Method": method,
                "MAE": mean_absolute_error(evaluation["Weekly_Sales"], evaluation[column]),
                "WMAE": weighted_mae(evaluation["Weekly_Sales"], evaluation[column], evaluation["IsHoliday"]),
                "Bias": float((evaluation[column] - evaluation["Weekly_Sales"]).mean()),
                "EvaluationRows": len(evaluation),
            }
        )
    metrics = pd.DataFrame(metric_rows).sort_values("WMAE").reset_index(drop=True)
    forecast_candidates = metrics.loc[metrics["Method"].ne("Planning scenario")]
    selected_method = str(forecast_candidates.iloc[0]["Method"])
    selected_column = benchmarks[selected_method]
    evaluation["ForecastSales"] = evaluation[selected_column]
    evaluation["ForecastMethod"] = selected_method
    evaluation["PlanVariance"] = evaluation["Weekly_Sales"] - evaluation["PlanSales"]
    evaluation["PlanVariancePct"] = np.where(
        evaluation["PlanSales"].ne(0), evaluation["PlanVariance"] / evaluation["PlanSales"], np.nan
    )
    evaluation["ForecastError"] = evaluation["Weekly_Sales"] - evaluation["ForecastSales"]
    evaluation["AbsoluteForecastError"] = evaluation["ForecastError"].abs()
    return evaluation, metrics, selected_method


def build_dimensions(merged: pd.DataFrame, stores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dim_store = stores.rename(columns={"Type": "StoreType", "Size": "StoreSize"}).sort_values("Store")
    dim_department = pd.DataFrame({"Dept": sorted(merged["Dept"].unique())})
    dates = pd.date_range(merged["Date"].min(), merged["Date"].max(), freq="D")
    dim_date = pd.DataFrame({"Date": dates})
    dim_date["DateKey"] = dim_date["Date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["Year"] = dim_date["Date"].dt.year
    dim_date["Quarter"] = "Q" + dim_date["Date"].dt.quarter.astype(str)
    dim_date["MonthNumber"] = dim_date["Date"].dt.month
    dim_date["MonthName"] = dim_date["Date"].dt.month_name()
    dim_date["WeekOfYear"] = dim_date["Date"].dt.isocalendar().week.astype(int)
    dim_date["WeekEndingFriday"] = dim_date["Date"] + pd.to_timedelta((4 - dim_date["Date"].dt.weekday) % 7, unit="D")
    return dim_store, dim_department, dim_date


def aggregate_performance(evaluation: pd.DataFrame, group_column: str) -> pd.DataFrame:
    result = (
        evaluation.groupby(group_column, as_index=False)
        .agg(
            ActualSales=("Weekly_Sales", "sum"),
            PlanSales=("PlanSales", "sum"),
            ForecastSales=("ForecastSales", "sum"),
            AbsoluteForecastError=("AbsoluteForecastError", "sum"),
            EvaluationRows=("Weekly_Sales", "size"),
        )
    )
    result["PlanVariance"] = result["ActualSales"] - result["PlanSales"]
    result["PlanVariancePct"] = np.where(
        result["PlanSales"].ne(0), result["PlanVariance"] / result["PlanSales"], np.nan
    )
    result["ForecastMAE"] = result["AbsoluteForecastError"] / result["EvaluationRows"]
    return result.sort_values("PlanVariance", ascending=False)


def write_reconciliation_workbook(
    merged: pd.DataFrame,
    evaluation: pd.DataFrame,
    metrics: pd.DataFrame,
    quality: pd.DataFrame,
    store_summary: pd.DataFrame,
    department_summary: pd.DataFrame,
    selected_method: str,
) -> None:
    EXCEL_DIR.mkdir(parents=True, exist_ok=True)
    workbook_path = EXCEL_DIR / "walmart_reporting_reconciliation.xlsx"
    summary = pd.DataFrame(
        [
            ("Source rows", len(merged)),
            ("Source sales total", merged["Weekly_Sales"].sum()),
            ("Evaluation rows", len(evaluation)),
            ("Evaluation actual sales", evaluation["Weekly_Sales"].sum()),
            ("Evaluation plan sales", evaluation["PlanSales"].sum()),
            ("Evaluation forecast sales", evaluation["ForecastSales"].sum()),
            ("Plan growth assumption", PLAN_GROWTH_RATE),
            ("Selected forecast method", selected_method),
        ],
        columns=["Control", "Value"],
    )

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Control Summary", index=False)
        quality.to_excel(writer, sheet_name="Data Quality", index=False)
        metrics.to_excel(writer, sheet_name="Forecast Metrics", index=False)
        store_summary.to_excel(writer, sheet_name="Store Reconciliation", index=False)
        department_summary.to_excel(writer, sheet_name="Department Reconciliation", index=False)

        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1F4E78")
                cell.alignment = Alignment(horizontal="center")
            for column_cells in sheet.columns:
                max_length = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 42)
                sheet.column_dimensions[column_cells[0].column_letter].width = max_length


def export_outputs(
    merged: pd.DataFrame,
    evaluation: pd.DataFrame,
    metrics: pd.DataFrame,
    quality: pd.DataFrame,
    stores: pd.DataFrame,
    selected_method: str,
) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dim_store, dim_department, dim_date = build_dimensions(merged, stores)

    fact_columns = [
        "Store",
        "Dept",
        "Date",
        "DateKey",
        "Weekly_Sales",
        "IsHoliday",
        "Temperature",
        "Fuel_Price",
        *MARKDOWN_COLUMNS,
        "MarkDownTotal",
        "CPI",
        "Unemployment",
    ]
    fact = merged[fact_columns].copy()
    forecast_columns = evaluation[
        ["Store", "Dept", "Date", "PlanSales", "ForecastSales", "ForecastMethod"]
    ]
    fact = fact.merge(forecast_columns, on=["Store", "Dept", "Date"], how="left", validate="one_to_one")
    fact = fact.rename(columns={"Weekly_Sales": "ActualSales"})

    store_summary = aggregate_performance(evaluation, "Store")
    department_summary = aggregate_performance(evaluation, "Dept")

    fact.to_csv(PROCESSED_DIR / "fact_weekly_sales.csv", index=False, date_format="%Y-%m-%d")
    dim_store.to_csv(PROCESSED_DIR / "dim_store.csv", index=False)
    dim_department.to_csv(PROCESSED_DIR / "dim_department.csv", index=False)
    dim_date.to_csv(PROCESSED_DIR / "dim_date.csv", index=False, date_format="%Y-%m-%d")
    evaluation.to_csv(PROCESSED_DIR / "forecast_evaluation_2012.csv", index=False, date_format="%Y-%m-%d")
    store_summary.to_csv(PROCESSED_DIR / "store_performance_2012.csv", index=False)
    department_summary.to_csv(PROCESSED_DIR / "department_performance_2012.csv", index=False)
    metrics.to_csv(PROCESSED_DIR / "forecast_metrics.csv", index=False)
    quality.to_csv(PROCESSED_DIR / "data_quality_report.csv", index=False)

    metadata = {
        "source_rows": int(len(merged)),
        "source_start": merged["Date"].min().date().isoformat(),
        "source_end": merged["Date"].max().date().isoformat(),
        "evaluation_year": EVALUATION_YEAR,
        "evaluation_rows": int(len(evaluation)),
        "plan_growth_rate": PLAN_GROWTH_RATE,
        "selected_forecast_method": selected_method,
    }
    (PROCESSED_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_reconciliation_workbook(
        merged, evaluation, metrics, quality, store_summary, department_summary, selected_method
    )


def main() -> None:
    train, features, stores = load_source_data()
    merged, training, evaluation, quality = prepare_data(train, features, stores)
    evaluation, metrics, selected_method = train_and_score(training, evaluation)
    export_outputs(merged, evaluation, metrics, quality, stores, selected_method)
    print(metrics.to_string(index=False, float_format=lambda value: f"{value:,.2f}"))
    print(f"\nSelected forecast method: {selected_method}")
    print(f"Evaluation rows: {len(evaluation):,}")
    print(f"Outputs: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
