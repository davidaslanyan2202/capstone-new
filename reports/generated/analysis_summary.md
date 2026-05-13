# EDA And Model Comparison Summary

## Dataset

- Source rows: 6070
- Source columns: 87
- Duplicate `row_id` count: 0
- Missing log target rows: 45
- Missing raw target rows: 45
- Missing contract rows: 195
- Rows under 300 minutes: 768

## Modeling Dataset

- Minimum minutes filter: `300`
- Modeling rows: 5271
- Train seasons: 21/22, 22/23
- Test seasons: 23/24
- Train rows: 3548
- Test rows: 1723
- Position rows: DF=1488, MF=2279, FW=1504

## Best Global Model

- Model: `hist_gradient_boosting`
- Test RMSE log: 0.7591
- Test MAE log: 0.5976
- Test R2: 0.6220
- Test MAE EUR: 6,857,255

## Main Conclusions

- The 300+ minute filter keeps broad coverage while excluding very small playing-time samples.
- The nonlinear hist-gradient boosting model performs best on the 2023/24 holdout season.
- Age, minutes, contract years remaining, league, and position are consistent valuation signals.
- Specialized position/league models improve hist-gradient RMSE in 0 of 8 tested segments.
- Global models remain the main benchmark; specialized models are diagnostics for segment-specific valuation patterns.
- Top permutation-importance features for the best model: Age, cleaned_comp, contract_years_remaining, 90s, goals_per90, Min.
- Sensitivity scenarios tested: 4.
- Bootstrap uncertainty rows: 2.

## Generated Files

- `data/processed/modeling_dataset.csv`
- `reports/generated/final_report.md`
- `reports/generated/tables/model_metrics.csv`
- `reports/generated/tables/error_by_group.csv`
- `reports/generated/tables/feature_importance.csv`
- `reports/generated/tables/specialized_model_comparison.csv`
- `reports/generated/tables/model_sensitivity.csv`
- `reports/generated/tables/bootstrap_intervals.csv`
- `reports/generated/tables/rolling_season_validation.csv`
- `reports/generated/tables/model_predictions.csv`
- `reports/generated/figures/model_comparison_test_rmse.png`
- `reports/generated/figures/predicted_vs_actual_best_model.png`
- `reports/generated/figures/residuals_by_league_position.png`
- `reports/generated/figures/position_model_comparison.png`
- `reports/generated/figures/league_model_comparison.png`
- `reports/generated/figures/specialized_vs_global_rmse.png`
- `paper/final/figures/*.png`
