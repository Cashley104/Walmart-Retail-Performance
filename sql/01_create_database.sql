IF DB_ID(N'WalmartRetailPerformance') IS NULL
BEGIN
    CREATE DATABASE WalmartRetailPerformance;
END;
GO

USE WalmartRetailPerformance;
GO

DROP VIEW IF EXISTS dbo.vw_ForecastEvaluation;
DROP VIEW IF EXISTS dbo.vw_DepartmentPerformance2012;
DROP VIEW IF EXISTS dbo.vw_StorePerformance2012;
DROP VIEW IF EXISTS dbo.vw_ExecutiveWeekly;
DROP TABLE IF EXISTS dbo.FactWeeklySales;
DROP TABLE IF EXISTS dbo.DimDate;
DROP TABLE IF EXISTS dbo.DimDepartment;
DROP TABLE IF EXISTS dbo.DimStore;
GO

CREATE TABLE dbo.DimStore (
    Store int NOT NULL PRIMARY KEY,
    StoreType char(1) NOT NULL,
    StoreSize int NOT NULL,
    CONSTRAINT CK_DimStore_Type CHECK (StoreType IN ('A', 'B', 'C'))
);

CREATE TABLE dbo.DimDepartment (
    Dept int NOT NULL PRIMARY KEY
);

CREATE TABLE dbo.DimDate (
    DateKey int NOT NULL PRIMARY KEY,
    [Date] date NOT NULL UNIQUE,
    [Year] smallint NOT NULL,
    [Quarter] char(2) NOT NULL,
    MonthNumber tinyint NOT NULL,
    MonthName varchar(9) NOT NULL,
    WeekOfYear tinyint NOT NULL,
    WeekEndingFriday date NOT NULL
);

CREATE TABLE dbo.FactWeeklySales (
    WeeklySalesKey bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    Store int NOT NULL,
    Dept int NOT NULL,
    [Date] date NOT NULL,
    DateKey int NOT NULL,
    ActualSales decimal(19,2) NOT NULL,
    IsHoliday bit NOT NULL,
    Temperature decimal(9,3) NULL,
    FuelPrice decimal(9,4) NULL,
    MarkDown1 decimal(19,2) NOT NULL,
    MarkDown2 decimal(19,2) NOT NULL,
    MarkDown3 decimal(19,2) NOT NULL,
    MarkDown4 decimal(19,2) NOT NULL,
    MarkDown5 decimal(19,2) NOT NULL,
    MarkDownTotal decimal(19,2) NOT NULL,
    CPI decimal(12,6) NULL,
    Unemployment decimal(9,4) NULL,
    PlanSales decimal(19,2) NULL,
    ForecastSales decimal(19,2) NULL,
    ForecastMethod varchar(40) NULL,
    CONSTRAINT UQ_FactWeeklySales UNIQUE (Store, Dept, [Date]),
    CONSTRAINT FK_FactWeeklySales_Store FOREIGN KEY (Store) REFERENCES dbo.DimStore(Store),
    CONSTRAINT FK_FactWeeklySales_Department FOREIGN KEY (Dept) REFERENCES dbo.DimDepartment(Dept),
    CONSTRAINT FK_FactWeeklySales_Date FOREIGN KEY (DateKey) REFERENCES dbo.DimDate(DateKey)
);

CREATE INDEX IX_FactWeeklySales_Date ON dbo.FactWeeklySales(DateKey);
CREATE INDEX IX_FactWeeklySales_StoreDate ON dbo.FactWeeklySales(Store, DateKey);
CREATE INDEX IX_FactWeeklySales_DepartmentDate ON dbo.FactWeeklySales(Dept, DateKey);
GO

