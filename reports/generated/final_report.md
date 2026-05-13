# A Data-Driven Analysis of Football Players' Transfer Value

## Abstract

This project predicts and explains football player market value using season-level performance, league, position, age, transfer-history, and contract features. The final analytics table contains player-season observations from the top five European leagues across 2021/22, 2022/23, and 2023/24. The target is the natural log transform `log1p(market_value_eur)`, which reduces the extreme skew in player valuation. With a minimum playing-time filter of 300 minutes, the modeling dataset contains 5,271 rows, including 3,548 training rows and 1,723 test rows. The best global model is `hist_gradient_boosting`, with test RMSE log 0.759, MAE log 0.598, and R2 0.622. The results show that market value is predictable from observable football and contract signals, but valuation remains partly driven by unobserved reputation, club strategy, and market context.

## Introduction

Transfer values influence recruitment, squad planning, and contract negotiation. However, the process by which performance statistics and contract status translate into market valuation is not fully transparent. This project studies whether football player market values can be predicted from public season-level data and which variables are most informative for that prediction task.

The main research questions are: how well can market value be predicted from performance and contract data, which variables drive valuation, whether relationships differ by position, and how contract expiry relates to value after controlling for other signals.

## Literature Review

Prior work supports the use of Transfermarkt values as a structured proxy for market valuation, while also noting that the values reflect collective market perception rather than direct transaction prices. Studies on football valuation have used econometric models, machine learning, and ensemble methods to estimate player value from age, performance, contract, and contextual variables. The present project follows this applied modeling direction but emphasizes reproducibility, explicit train/test separation by season, and interpretable diagnostics.

## Methodology

The analysis uses `data/processed/player_season_analytics.csv` as the final table. Each row represents a player-season/team record. The feature set includes age, minutes, starts, per-90 performance rates, league, season, position group, contract years remaining, missing-contract indicators, and transfer-history counts. The target is `log_market_value_eur`.

Players with fewer than 300 minutes are excluded. This threshold keeps substantially more observations than the earlier 900-minute filter while still removing the smallest samples. The final modeling rows by position are DF=1,488, MF=2,279, and FW=1,504. Models are trained on 2021/22 and 2022/23 and evaluated only on 2023/24.

The global model comparison includes a mean baseline, ordinary least squares linear regression, ridge regression, and hist-gradient boosting. Separate position-specific and league-specific models are also trained. These specialized models are compared against the global model evaluated on the same subgroup, which shows whether segmentation actually improves predictive accuracy.

## Results

### Global Model Metrics

| model | rows | rmse_log | mae_log | r2 | mae_eur |
| --- | --- | --- | --- | --- | --- |
| hist_gradient_boosting | 1723 | 0.7591 | 0.5976 | 0.6220 | 6857254.5747 |
| linear_regression | 1723 | 0.7898 | 0.6309 | 0.5909 | 7475934.5469 |
| ridge_alpha_1 | 1723 | 0.7900 | 0.6312 | 0.5907 | 7470605.8308 |
| mean_baseline | 1723 | 1.2380 | 1.0237 | -0.0052 | 10993746.6806 |

The best model improves test RMSE log by 38.7% relative to the mean baseline. The nonlinear hist-gradient boosting model performs best, indicating that football valuation is not purely linear in the available features.

### Position-Specific Models

| position_group | model | rows | rmse_log | mae_log | r2 |
| --- | --- | --- | --- | --- | --- |
| DF | ridge_alpha_1 | 488 | 0.7941 | 0.6420 | 0.5704 |
| DF | hist_gradient_boosting | 488 | 0.8367 | 0.6560 | 0.5230 |
| FW | ridge_alpha_1 | 481 | 0.7540 | 0.5989 | 0.6546 |
| FW | hist_gradient_boosting | 481 | 0.7606 | 0.6039 | 0.6486 |
| MF | hist_gradient_boosting | 754 | 0.7925 | 0.6263 | 0.5696 |
| MF | ridge_alpha_1 | 754 | 0.7992 | 0.6329 | 0.5623 |

The position-specific results are useful for diagnosing how model behavior changes by role. They should be interpreted cautiously because each position model has fewer training examples than the global model.

### League-Specific Models

| cleaned_comp | model | rows | rmse_log | mae_log | r2 |
| --- | --- | --- | --- | --- | --- |
| Bundesliga | ridge_alpha_1 | 319 | 0.7927 | 0.6420 | 0.5890 |
| Bundesliga | hist_gradient_boosting | 319 | 0.8190 | 0.6492 | 0.5612 |
| La Liga | ridge_alpha_1 | 345 | 0.8279 | 0.6648 | 0.5300 |
| La Liga | hist_gradient_boosting | 345 | 0.8631 | 0.6812 | 0.4891 |
| Ligue 1 | hist_gradient_boosting | 325 | 0.8498 | 0.6781 | 0.4214 |
| Ligue 1 | ridge_alpha_1 | 325 | 0.8504 | 0.6770 | 0.4206 |
| Premier League | hist_gradient_boosting | 362 | 0.7410 | 0.5664 | 0.5983 |
| Premier League | ridge_alpha_1 | 362 | 0.7809 | 0.5936 | 0.5539 |
| Serie A | ridge_alpha_1 | 372 | 0.7125 | 0.5817 | 0.5811 |
| Serie A | hist_gradient_boosting | 372 | 0.7689 | 0.6115 | 0.5122 |

League-specific models test whether each league has enough distinct valuation structure to justify a separate estimator. These models are especially useful because league context is one of the strongest valuation signals.

### Global Vs Specialized Models

| group_column | group_value | rows | global_rmse_log | specialized_rmse_log | rmse_log_delta_specialized_minus_global | result |
| --- | --- | --- | --- | --- | --- | --- |
| cleaned_comp | Bundesliga | 319 | 0.7948 | 0.8190 | 0.0243 | global better |
| cleaned_comp | Premier League | 362 | 0.7063 | 0.7410 | 0.0347 | global better |
| cleaned_comp | Serie A | 372 | 0.7248 | 0.7689 | 0.0441 | global better |
| cleaned_comp | Ligue 1 | 325 | 0.7947 | 0.8498 | 0.0551 | global better |
| cleaned_comp | La Liga | 345 | 0.7804 | 0.8631 | 0.0827 | global better |
| position_group | MF | 754 | 0.7669 | 0.7925 | 0.0256 | global better |
| position_group | FW | 481 | 0.7344 | 0.7606 | 0.0261 | global better |
| position_group | DF | 488 | 0.7709 | 0.8367 | 0.0658 | global better |

Negative deltas mean the specialized model has lower RMSE than the global model on the same subgroup. Positive deltas mean the global model generalizes better, usually because it benefits from a larger training sample.

### Feature Importance

| feature | importance | importance_std |
| --- | --- | --- |
| Age | 0.2851 | 0.0135 |
| cleaned_comp | 0.1608 | 0.0071 |
| contract_years_remaining | 0.0738 | 0.0041 |
| 90s | 0.0527 | 0.0055 |
| goals_per90 | 0.0459 | 0.0031 |
| Min | 0.0417 | 0.0045 |
| assists_per90 | 0.0359 | 0.0047 |
| shots_per90 | 0.0317 | 0.0078 |
| days_since_last_transfer | 0.0282 | 0.0085 |
| crosses_per90 | 0.0241 | 0.0052 |

Permutation importance for the best nonlinear model highlights context and availability variables such as league, position, age, minutes, and contract status. Ridge coefficients provide a complementary linear view, but neither method should be interpreted as causal evidence.

### Error Diagnostics

| group_column | group_value | rows | mae_log | rmse_log | mae_eur |
| --- | --- | --- | --- | --- | --- |
| cleaned_comp | Premier League | 362 | 0.5386 | 0.7063 | 10392688.3176 |
| cleaned_comp | Serie A | 372 | 0.5765 | 0.7248 | 5437541.9386 |
| cleaned_comp | La Liga | 345 | 0.6147 | 0.7804 | 6763659.4121 |
| cleaned_comp | Ligue 1 | 325 | 0.6287 | 0.7947 | 5041915.9483 |
| cleaned_comp | Bundesliga | 319 | 0.6387 | 0.7948 | 6451553.8547 |
| position_group | FW | 481 | 0.5842 | 0.7344 | 8121330.2677 |
| position_group | MF | 754 | 0.6007 | 0.7669 | 6523069.4707 |
| position_group | DF | 488 | 0.6057 | 0.7709 | 6127654.4928 |
| season | 23/24 | 1723 | 0.5976 | 0.7591 | 6857254.5747 |

Residual diagnostics show where the model is more or less reliable across leagues and positions. Large errors remain expected for players whose valuation is affected by reputation, transfer demand, injuries, academy status, or unusual contract situations not captured in the data.

### Robustness And Sensitivity

| variant | model | rows | rmse_log | mae_log | r2 | target_filter | feature_set |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_features_min_300 | hist_gradient_boosting | 1723 | 0.7591 | 0.5976 | 0.6220 | max_120_days | all_features |
| all_features_min_300 | linear_regression | 1723 | 0.7898 | 0.6309 | 0.5909 | max_120_days | all_features |
| all_features_min_300 | ridge_alpha_1 | 1723 | 0.7900 | 0.6312 | 0.5907 | max_120_days | all_features |
| all_features_min_300 | mean_baseline | 1723 | 1.2380 | 1.0237 | -0.0052 | max_120_days | all_features |
| all_features_min_900 | hist_gradient_boosting | 1303 | 0.7347 | 0.5788 | 0.6201 | max_120_days | all_features |
| all_features_min_900 | linear_regression | 1303 | 0.7635 | 0.6055 | 0.5897 | max_120_days | all_features |
| all_features_min_900 | ridge_alpha_1 | 1303 | 0.7638 | 0.6060 | 0.5894 | max_120_days | all_features |
| all_features_min_900 | mean_baseline | 1303 | 1.1943 | 0.9789 | -0.0039 | max_120_days | all_features |
| in_window_targets_min_300 | hist_gradient_boosting | 1722 | 0.7605 | 0.5988 | 0.6200 | in_window_only | all_features |
| in_window_targets_min_300 | linear_regression | 1722 | 0.7891 | 0.6304 | 0.5909 | in_window_only | all_features |
| in_window_targets_min_300 | ridge_alpha_1 | 1722 | 0.7894 | 0.6306 | 0.5906 | in_window_only | all_features |
| in_window_targets_min_300 | mean_baseline | 1722 | 1.2368 | 1.0228 | -0.0049 | in_window_only | all_features |
| no_contract_transfer_features_min_300 | hist_gradient_boosting | 1723 | 0.8150 | 0.6453 | 0.5643 | max_120_days | no_contract_transfer_features |
| no_contract_transfer_features_min_300 | linear_regression | 1723 | 0.8306 | 0.6641 | 0.5475 | max_120_days | no_contract_transfer_features |
| no_contract_transfer_features_min_300 | ridge_alpha_1 | 1723 | 0.8308 | 0.6640 | 0.5473 | max_120_days | no_contract_transfer_features |
| no_contract_transfer_features_min_300 | mean_baseline | 1723 | 1.2380 | 1.0237 | -0.0052 | max_120_days | no_contract_transfer_features |

The sensitivity table compares the headline setup against variants that remove contract/transfer-history features, require in-window market-value targets, and use a stricter 900-minute playing-time threshold.

### Bootstrap Uncertainty

| model | metric | estimate | ci_lower_95 | ci_upper_95 | bootstrap_samples |
| --- | --- | --- | --- | --- | --- |
| hist_gradient_boosting | rmse_log | 0.7591 | 0.7317 | 0.7868 | 500 |
| hist_gradient_boosting | mae_log | 0.5976 | 0.5775 | 0.6203 | 500 |

Bootstrap intervals resample the 2023/24 test residuals for the best global model and give a simple uncertainty range around headline error metrics.

### Rolling Season Validation

| train_seasons | test_season | model | rows | rmse_log | mae_log | r2 |
| --- | --- | --- | --- | --- | --- | --- |
| 21/22 | 22/23 | hist_gradient_boosting | 1764 | 0.7594 | 0.6072 | 0.6111 |
| 21/22 | 22/23 | ridge_alpha_1 | 1764 | 0.7808 | 0.6255 | 0.5889 |
| 21/22 | 22/23 | linear_regression | 1764 | 0.7823 | 0.6261 | 0.5873 |
| 21/22 | 22/23 | mean_baseline | 1764 | 1.2218 | 1.0094 | -0.0067 |
| 21/22,22/23 | 23/24 | hist_gradient_boosting | 1723 | 0.7591 | 0.5976 | 0.6220 |
| 21/22,22/23 | 23/24 | linear_regression | 1723 | 0.7898 | 0.6309 | 0.5909 |
| 21/22,22/23 | 23/24 | ridge_alpha_1 | 1723 | 0.7900 | 0.6312 | 0.5907 |
| 21/22,22/23 | 23/24 | mean_baseline | 1723 | 1.2380 | 1.0237 | -0.0052 |

Rolling validation is limited by the three available seasons, but it checks whether conclusions are stable when testing 2022/23 after training on 2021/22 and when testing 2023/24 after training on the first two seasons.

## Analysis and Validation

The project meets the predictive objective because all learned global models outperform the mean baseline on the held-out 2023/24 season. The best model explains a meaningful share of variance while maintaining evaluation on a future season, which is stricter than a random row split. The expanded 300-minute threshold increases coverage relative to a 900-minute regular-starter filter, but it also introduces noisier low-minute observations. This tradeoff is acceptable for the final project because the goal is broad player valuation coverage rather than only regular starters.

The segmented modeling results show that specialization is not automatically better. Some simpler ridge models improve in selected league or position segments, but the specialized hist-gradient boosting models perform worse than the global hist-gradient model on every tested subgroup. This makes the global hist-gradient boosting model the best headline model, with segment-specific models used for interpretation and robustness checks.

Contract years remaining has a positive relationship with market value in the EDA and appears among useful model features, but expired contracts are now modeled as a separate flag and negative remaining years are capped at zero. Age is negatively correlated with log value in the aggregate, reflecting that younger players often carry resale potential. Minutes and starts capture player importance and reliability. League and position encode market context and role-based valuation differences.

## Discussion and Conclusion

The final analysis shows that football player market value can be estimated from public performance, contract, and context features with moderate accuracy. The nonlinear model gives the strongest predictive performance, while linear models remain useful for interpretation. The main contribution is a reproducible workflow that connects raw football and Transfermarkt-derived data into a player-season modeling dataset, EDA outputs, global models, position-specific models, league-specific models, and report-ready figures.

Important limitations remain. Transfermarkt market value is a proxy rather than an actual sale price, the dataset does not include injuries or detailed team strength, and the contract feature is approximated from transfer-history events. Future work should add richer event data, club financial context, exact contract records, and external validation against actual transfer fees.

## Reproducibility

Run the main results with:

```powershell
python code/reproduce.py
```

All report figures and tables are generated programmatically from the project data.
