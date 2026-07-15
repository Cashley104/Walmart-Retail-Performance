# Initial Findings

These findings are generated from the reproducible pipeline and should be reviewed in Power BI before they are treated as final management recommendations.

## Reconciliation

- Historical source rows: 421,570
- Historical source sales: $6,737,218,987.11
- Evaluation rows: 123,905
- Evaluation period: January 6 through October 26, 2012
- Duplicate store-department-week keys: 0
- Unmatched store or weekly-feature records: 0

## Actual versus plan

- Evaluation-period actual sales: $1,999,265,475.88
- Illustrative 3% plan: $2,008,222,674.93
- Total variance: -$8,957,199.05
- Total variance rate: -0.45%

The overall result was close to plan, but aggregated performance conceals meaningful store and department differences.

### Store variance

Largest favorable variances:

1. Store 39: +$4.67M (+7.63%)
2. Store 41: +$2.34M (+4.30%)
3. Store 4: +$1.90M (+2.09%)

Largest unfavorable variances:

1. Store 14: -$9.80M (-11.23%)
2. Store 27: -$4.15M (-5.45%)
3. Store 36: -$3.30M (-19.90%)

Store 36 had the largest percentage shortfall, while Store 14 had the largest dollar shortfall. They should not be treated as the same type of management problem.

### Department variance

Largest favorable variances:

1. Department 92: +$6.11M (+4.20%)
2. Department 87: +$3.42M (+13.28%)
3. Department 9: +$1.66M (+4.31%)

Largest unfavorable variances:

1. Department 72: -$4.34M (-5.12%)
2. Department 5: -$2.41M (-6.72%)
3. Department 55: -$2.27M (-15.01%)

## Forecast evaluation

| Method | MAE | Holiday-weighted MAE | Bias |
|---|---:|---:|---:|
| Planning scenario (benchmark only) | $1,784.39 | $1,779.27 | +$72.29 |
| Seasonal prior-year forecast | $1,811.56 | $1,818.03 | -$399.78 |
| Gradient boosting | $1,857.78 | $1,864.71 | -$564.80 |

The seasonal prior-year method was selected as the forecast because it outperformed gradient boosting on holiday-weighted error. The planning scenario had lower error but remains a management target, not an independently selected forecast.

The result is a useful reminder that model complexity does not guarantee better forecasting. The gradient-boosting implementation may require stronger time-series features, department-specific behavior, or additional tuning before it can outperform the seasonal baseline.

## Holiday performance

- Average total sales during available non-holiday weeks: $46.37M
- Average total sales during available holiday weeks: $49.13M
- Unadjusted holiday-week lift: approximately 5.95%

This comparison is descriptive. It does not prove that the holiday indicator caused the increase because department mix, markdown availability, and seasonal timing also differ.

## Data limitations

- Store and department identifiers are anonymized.
- Markdown fields are unavailable before November 2011 and remain incomplete afterward.
- Negative weekly sales are retained as likely net returns but cannot be confirmed from the supplied fields.
- The 2012 evaluation period ends October 26 and is not a complete fiscal or calendar year.
- The 3% plan is illustrative and does not represent Walmart's internal budget.
- Observed relationships with economic variables or markdowns should not be described as causal without a stronger research design.

## Dashboard investigation priorities

1. Separate dollar variance from percentage variance when ranking stores.
2. Drill into Store 14 by department and week to locate its $9.80M shortfall.
3. Compare Stores 36 and 39 by store type, size, department mix, and weekly trend.
4. Determine whether Departments 72, 5, and 55 underperformed broadly or only in selected stores.
5. Map forecast error by store and department to find series where a prior-year forecast is insufficient.

