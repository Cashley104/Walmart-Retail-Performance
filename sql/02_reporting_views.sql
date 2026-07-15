USE WalmartRetailPerformance;
GO

CREATE OR ALTER VIEW dbo.vw_ExecutiveWeekly AS
SELECT
    f.[Date],
    d.[Year],
    d.MonthNumber,
    d.MonthName,
    f.IsHoliday,
    SUM(f.ActualSales) AS ActualSales,
    SUM(f.PlanSales) AS PlanSales,
    SUM(f.ForecastSales) AS ForecastSales,
    SUM(f.ActualSales) - SUM(f.PlanSales) AS PlanVariance,
    SUM(ABS(f.ActualSales - f.ForecastSales)) AS AbsoluteForecastError,
    COUNT(f.ForecastSales) AS ForecastRowCount
FROM dbo.FactWeeklySales AS f
INNER JOIN dbo.DimDate AS d ON d.DateKey = f.DateKey
GROUP BY f.[Date], d.[Year], d.MonthNumber, d.MonthName, f.IsHoliday;
GO

CREATE OR ALTER VIEW dbo.vw_StorePerformance2012 AS
SELECT
    f.Store,
    s.StoreType,
    s.StoreSize,
    SUM(f.ActualSales) AS ActualSales,
    SUM(f.PlanSales) AS PlanSales,
    SUM(f.ForecastSales) AS ForecastSales,
    SUM(f.ActualSales) - SUM(f.PlanSales) AS PlanVariance,
    CASE WHEN SUM(f.PlanSales) = 0 THEN NULL
         ELSE (SUM(f.ActualSales) - SUM(f.PlanSales)) / SUM(f.PlanSales) END AS PlanVariancePct,
    AVG(ABS(f.ActualSales - f.ForecastSales)) AS ForecastMAE
FROM dbo.FactWeeklySales AS f
INNER JOIN dbo.DimStore AS s ON s.Store = f.Store
WHERE YEAR(f.[Date]) = 2012 AND f.PlanSales IS NOT NULL
GROUP BY f.Store, s.StoreType, s.StoreSize;
GO

CREATE OR ALTER VIEW dbo.vw_DepartmentPerformance2012 AS
SELECT
    f.Dept,
    SUM(f.ActualSales) AS ActualSales,
    SUM(f.PlanSales) AS PlanSales,
    SUM(f.ForecastSales) AS ForecastSales,
    SUM(f.ActualSales) - SUM(f.PlanSales) AS PlanVariance,
    CASE WHEN SUM(f.PlanSales) = 0 THEN NULL
         ELSE (SUM(f.ActualSales) - SUM(f.PlanSales)) / SUM(f.PlanSales) END AS PlanVariancePct,
    AVG(ABS(f.ActualSales - f.ForecastSales)) AS ForecastMAE
FROM dbo.FactWeeklySales AS f
WHERE YEAR(f.[Date]) = 2012 AND f.PlanSales IS NOT NULL
GROUP BY f.Dept;
GO

CREATE OR ALTER VIEW dbo.vw_ForecastEvaluation AS
SELECT
    f.Store,
    s.StoreType,
    s.StoreSize,
    f.Dept,
    f.[Date],
    f.IsHoliday,
    f.ActualSales,
    f.PlanSales,
    f.ForecastSales,
    f.ForecastMethod,
    f.ActualSales - f.PlanSales AS PlanVariance,
    f.ActualSales - f.ForecastSales AS ForecastError,
    ABS(f.ActualSales - f.ForecastSales) AS AbsoluteForecastError,
    f.Temperature,
    f.FuelPrice,
    f.MarkDownTotal,
    f.CPI,
    f.Unemployment
FROM dbo.FactWeeklySales AS f
INNER JOIN dbo.DimStore AS s ON s.Store = f.Store
WHERE f.PlanSales IS NOT NULL;
GO

