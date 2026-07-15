# Power BI Build Guide

## Recommended source

Connect Power BI to the SQL Server database `WalmartRetailPerformance` after running the SQL load. The processed CSV files can be used as a fallback.

## Relationships

- `DimStore[Store]` one-to-many `FactWeeklySales[Store]`
- `DimDepartment[Dept]` one-to-many `FactWeeklySales[Dept]`
- `DimDate[DateKey]` one-to-many `FactWeeklySales[DateKey]`

## Core DAX measures

```DAX
Actual Sales = SUM(FactWeeklySales[ActualSales])

Plan Sales = SUM(FactWeeklySales[PlanSales])

Forecast Sales = SUM(FactWeeklySales[ForecastSales])

Plan Variance = [Actual Sales] - [Plan Sales]

Plan Variance % = DIVIDE([Plan Variance], [Plan Sales])

Forecast Error = [Actual Sales] - [Forecast Sales]

Absolute Forecast Error =
SUMX(
    FactWeeklySales,
    ABS(FactWeeklySales[ActualSales] - FactWeeklySales[ForecastSales])
)

Forecast MAE =
DIVIDE(
    [Absolute Forecast Error],
    COUNTROWS(FILTER(FactWeeklySales, NOT ISBLANK(FactWeeklySales[ForecastSales])))
)

Holiday Actual Sales =
CALCULATE([Actual Sales], FactWeeklySales[IsHoliday] = TRUE())
```

## Page 1: Executive Summary

- KPI cards: Actual Sales, Plan Sales, Plan Variance, Plan Variance %, Forecast MAE
- Line chart: Actual, Plan, and Forecast by week
- Bar chart: Plan Variance by store
- Bar chart: Plan Variance by department
- Slicers: Store Type, Store, Department, Month, Holiday

## Page 2: Store and Department Performance

- Matrix: Store > Department with Actual, Plan, Variance, Variance %, Forecast MAE
- Scatter plot: Store Size vs Actual Sales, colored by Store Type
- Bar chart: Top/bottom stores by Plan Variance
- Drill-through page for a selected store

## Page 3: Forecast and Drivers

- Line chart: Actual vs Forecast by week
- Bar chart: Forecast MAE by store
- Bar chart: Forecast MAE by department
- Scatter plots for sales versus markdown total and selected economic measures
- Holiday/non-holiday comparison

## Page 4: Methodology and Quality

- Source period and record counts
- Planning formula and 3% assumption
- Forecast methods and WMAE results
- Data-quality checks
- Notes on negative sales and missing markdowns
- Statement that the plan is illustrative and not Walmart's internal budget

