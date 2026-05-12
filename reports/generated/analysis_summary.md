# EDA And Model Comparison Summary

## Dataset

- Source rows: 6471
- Source columns: 84
- Duplicate `row_id` count: 0
- Missing log target rows: 0
- Missing raw target rows: 0
- Missing contract rows: 321
- Rows under 300 minutes: 813

## Modeling Dataset

- Minimum minutes filter: `300`
- Modeling rows: 5658
- Train seasons: 21/22, 22/23
- Test seasons: 23/24
- Train rows: 3818
- Test rows: 1840
- Position rows: DF=1614, MF=2443, FW=1601

## Best Global Model

- Model: `hist_gradient_boosting`
- Test RMSE log: 0.8877
- Test MAE log: 0.6663
- Test R2: 0.6146
- Test MAE EUR: 6,871,178

## Main Conclusions

- The 300+ minute filter keeps broad coverage while excluding very small playing-time samples.
- The nonlinear hist-gradient boosting model performs best on the 2023/24 holdout season.
- Age, minutes, contract years remaining, league, and position are consistent valuation signals.
- Specialized position/league models improve hist-gradient RMSE in 0 of 8 tested segments.
- Global models remain the main benchmark; specialized models are diagnostics for segment-specific valuation patterns.
- Top permutation-importance features for the best model: Age, contract_years_remaining, cleaned_comp, contract_missing, transfer_count_before_valuation, crosses_per90.

## Generated Files

- `data/processed/modeling_dataset.csv`
- `reports/generated/final_report.md`
- `reports/generated/tables/model_metrics.csv`
- `reports/generated/tables/error_by_group.csv`
- `reports/generated/tables/feature_importance.csv`
- `reports/generated/tables/specialized_model_comparison.csv`
- `reports/generated/tables/model_predictions.csv`
- `reports/generated/figures/model_comparison_test_rmse.png`
- `reports/generated/figures/predicted_vs_actual_best_model.png`
- `reports/generated/figures/residuals_by_league_position.png`
- `reports/generated/figures/position_model_comparison.png`
- `reports/generated/figures/league_model_comparison.png`
- `reports/generated/figures/specialized_vs_global_rmse.png`
- `paper/generated/main.tex`
- `paper/generated/references.bib`
- `paper/final/figures/*.png`
