# Business Requirements

## Project

Walmart Store Performance: Actual vs Plan vs Forecast

## Scenario

A retail reporting analyst is asked to evaluate 2012 weekly sales performance across Walmart stores and departments. Management needs a transparent planning benchmark, an independently evaluated forecast, and clear explanations for material performance differences.

The historical sales records were released through the Walmart Recruiting Store Sales Forecasting competition. The planning scenario is analyst-created and does not represent Walmart's internal budget.

## Reporting period

- Historical source period: February 5, 2010 through October 26, 2012
- Planning and forecast evaluation period: available weeks in 2012
- Planning baseline: comparable store-department week from 2011
- Planning target: baseline increased by 3%

## Business questions

1. Did 2012 actual sales exceed or miss the planning scenario?
2. Which stores and departments drove the largest favorable and unfavorable variances?
3. How accurately could weekly sales be forecast using only information available before 2012?
4. How did holiday weeks, markdowns, store size, and regional economic measures relate to sales performance?
5. Where should management investigate persistent underperformance or forecast error?

## Required deliverables

- Reproducible Python preparation and forecasting pipeline
- SQL Server dimensional reporting model and validation queries
- Excel reconciliation workbook
- Power BI report with executive, store/department, forecast, and methodology pages
- GitHub documentation, findings, dashboard preview, and resume-ready summary

## Guardrails

- Do not describe the planning scenario as Walmart's actual budget.
- Do not use future sales values when training forecasts.
- Retain negative net-sales rows as likely returns and flag them for review.
- Treat missing markdowns as unavailable promotion data, not automatically as data errors.
- Keep recent corporate financial statements separate from the historical store-level analysis.

