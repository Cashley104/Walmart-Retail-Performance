# Metric Definitions

| Metric | Definition |
|---|---|
| Actual Sales | Recorded weekly sales for a store and department. |
| Comparable Prior-Year Sales | Sales for the same store and department 364 days earlier. |
| Plan Sales | Comparable prior-year sales multiplied by 1.03. This is an illustrative planning scenario. |
| Plan Variance | Actual Sales minus Plan Sales. Positive is favorable. |
| Plan Variance % | Plan Variance divided by Plan Sales. |
| Forecast Sales | Prediction from the best genuine forecasting method using only pre-2012 sales history for model training. The planning scenario is reported as a benchmark but cannot be selected as the forecast. |
| Forecast Error | Actual Sales minus Forecast Sales. |
| Absolute Forecast Error | Absolute value of Forecast Error. |
| MAE | Average Absolute Forecast Error across evaluation rows. |
| WMAE | Average Absolute Forecast Error using weight 5 for holiday weeks and 1 otherwise. |
| Forecast Bias | Average Forecast Sales minus Actual Sales. Positive indicates overforecasting. |
| Holiday Sales Lift | Holiday-period sales compared with an appropriate non-holiday baseline. |
| MarkDown Total | Sum of the five anonymized markdown fields after missing values are represented as unavailable/zero for modeling. |
