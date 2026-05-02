# EDA And Baseline Modeling Summary

## Dataset

- Source rows: 6471
- Source columns: 84
- Duplicate `row_id` count: 0
- Missing log target rows: 0
- Missing raw target rows: 0
- Missing contract rows: 321
- Rows under 900 minutes: 2243

## Modeling Dataset

- Minimum minutes filter: `900`
- Modeling rows: 4228
- Train seasons: 21/22, 22/23
- Test seasons: 23/24
- Train rows: 2840
- Test rows: 1388

## Best Baseline

- Model: `linear_regression`
- Test RMSE log: 0.9990
- Test MAE log: 0.7208
- Test R2: 0.5061

## Generated Files

- `data/processed/modeling_dataset.csv`
- `reports/tables/missingness.csv`
- `reports/tables/market_value_by_group.csv`
- `reports/tables/numeric_correlations.csv`
- `reports/tables/target_correlations.csv`
- `reports/tables/baseline_model_metrics.csv`
- `reports/tables/ridge_alpha_1_coefficients.csv`
- `reports/tables/ridge_alpha_10_coefficients.csv`
- `reports/figures/*.png`
