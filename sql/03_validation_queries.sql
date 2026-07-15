USE WalmartRetailPerformance;
GO

-- Expected: 421,570 rows and $6,737,218,987.11 in source actual sales.
SELECT COUNT(*) AS FactRows, SUM(ActualSales) AS ActualSalesTotal
FROM dbo.FactWeeklySales;

-- Expected: zero duplicate business keys.
SELECT Store, Dept, [Date], COUNT(*) AS DuplicateCount
FROM dbo.FactWeeklySales
GROUP BY Store, Dept, [Date]
HAVING COUNT(*) > 1;

-- Expected: zero orphaned dimension references.
SELECT COUNT(*) AS MissingStoreRows
FROM dbo.FactWeeklySales AS f
LEFT JOIN dbo.DimStore AS s ON s.Store = f.Store
WHERE s.Store IS NULL;

SELECT COUNT(*) AS MissingDepartmentRows
FROM dbo.FactWeeklySales AS f
LEFT JOIN dbo.DimDepartment AS d ON d.Dept = f.Dept
WHERE d.Dept IS NULL;

SELECT COUNT(*) AS MissingDateRows
FROM dbo.FactWeeklySales AS f
LEFT JOIN dbo.DimDate AS d ON d.DateKey = f.DateKey
WHERE d.DateKey IS NULL;

-- Negative weekly net sales are retained for analysis as likely net returns.
SELECT COUNT(*) AS NegativeSalesRows, SUM(ActualSales) AS NegativeSalesTotal
FROM dbo.FactWeeklySales
WHERE ActualSales < 0;

-- Evaluation coverage and reconciliation.
SELECT
    COUNT(*) AS EvaluationRows,
    MIN([Date]) AS EvaluationStart,
    MAX([Date]) AS EvaluationEnd,
    SUM(ActualSales) AS ActualSales,
    SUM(PlanSales) AS PlanSales,
    SUM(ForecastSales) AS ForecastSales
FROM dbo.FactWeeklySales
WHERE PlanSales IS NOT NULL;
GO

