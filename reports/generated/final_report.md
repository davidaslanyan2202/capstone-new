# A Data-Driven Analysis of Football Players' Transfer Value

## Abstract

This project predicts and explains football player market value using season-level performance, league, position, age, transfer-history, and contract features. The final analytics table contains player-season observations from the top five European leagues across 2021/22, 2022/23, and 2023/24. The target is the natural log transform `log1p(market_value_eur)`, which reduces the extreme skew in player valuation. With a minimum playing-time filter of 300 minutes, the modeling dataset contains 5,658 rows, including 3,818 training rows and 1,840 test rows. The best global model is `hist_gradient_boosting`, with test RMSE log 0.888, MAE log 0.666, and R2 0.615. The results show that market value is predictable from observable football and contract signals, but valuation remains partly driven by unobserved reputation, club strategy, and market context.

## Introduction

Transfer values influence recruitment, squad planning, and contract negotiation. However, the process by which performance statistics and contract status translate into market valuation is not fully transparent. This project studies whether football player market values can be predicted from public season-level data and which variables are most informative for that prediction task.

The main research questions are: how well can market value be predicted from performance and contract data, which variables drive valuation, whether relationships differ by position, and how contract expiry relates to value after controlling for other signals.

## Literature Review

Prior work supports the use of Transfermarkt values as a structured proxy for market valuation, while also noting that the values reflect collective market perception rather than direct transaction prices. Studies on football valuation have used econometric models, machine learning, and ensemble methods to estimate player value from age, performance, contract, and contextual variables. The present project follows this applied modeling direction but emphasizes reproducibility, explicit train/test separation by season, and interpretable diagnostics.

## Methodology

The analysis uses `data/processed/player_season_analytics.csv` as the final table. Each row represents a player-season/team record. The feature set includes age, minutes, starts, per-90 performance rates, league, season, position group, contract years remaining, missing-contract indicators, and transfer-history counts. The target is `log_market_value_eur`.

Players with fewer than 300 minutes are excluded. This threshold keeps substantially more observations than the earlier 900-minute filter while still removing the smallest samples. The final modeling rows by position are DF=1,614, MF=2,443, and FW=1,601. Models are trained on 2021/22 and 2022/23 and evaluated only on 2023/24.

The global model comparison includes a mean baseline, ordinary least squares linear regression, ridge regression, and hist-gradient boosting. Separate position-specific and league-specific models are also trained. These specialized models are compared against the global model evaluated on the same subgroup, which shows whether segmentation actually improves predictive accuracy.

## Results

### Global Model Metrics

| model | rows | rmse_log | mae_log | r2 | mae_eur |
| --- | --- | --- | --- | --- | --- |
| hist_gradient_boosting | 1840 | 0.8877 | 0.6663 | 0.6146 | 6871178.1624 |
| ridge_alpha_1 | 1840 | 0.9925 | 0.7341 | 0.5183 | 7665130.2120 |
| linear_regression | 1840 | 0.9925 | 0.7341 | 0.5183 | 7668460.5645 |
| mean_baseline | 1840 | 1.4320 | 1.1333 | -0.0027 | 11046357.1685 |

The best model improves test RMSE log by 38.0% relative to the mean baseline. The nonlinear hist-gradient boosting model performs best, indicating that football valuation is not purely linear in the available features.

### Position-Specific Models

| position_group | model | rows | rmse_log | mae_log | r2 |
| --- | --- | --- | --- | --- | --- |
| DF | hist_gradient_boosting | 529 | 1.0218 | 0.7499 | 0.4826 |
| DF | ridge_alpha_1 | 529 | 1.0279 | 0.7672 | 0.4765 |
| FW | hist_gradient_boosting | 507 | 0.8695 | 0.6652 | 0.6352 |
| FW | ridge_alpha_1 | 507 | 0.9350 | 0.6867 | 0.5782 |
| MF | hist_gradient_boosting | 804 | 0.9360 | 0.7041 | 0.5636 |
| MF | ridge_alpha_1 | 804 | 0.9999 | 0.7353 | 0.5019 |

The position-specific results are useful for diagnosing how model behavior changes by role. They should be interpreted cautiously because each position model has fewer training examples than the global model.

### League-Specific Models

| cleaned_comp | model | rows | rmse_log | mae_log | r2 |
| --- | --- | --- | --- | --- | --- |
| Bundesliga | ridge_alpha_1 | 326 | 0.9064 | 0.7045 | 0.5226 |
| Bundesliga | hist_gradient_boosting | 326 | 0.9226 | 0.7172 | 0.5055 |
| La Liga | hist_gradient_boosting | 389 | 1.0391 | 0.7627 | 0.4766 |
| La Liga | ridge_alpha_1 | 389 | 1.0539 | 0.7718 | 0.4616 |
| Ligue 1 | hist_gradient_boosting | 341 | 0.9229 | 0.7066 | 0.5009 |
| Ligue 1 | ridge_alpha_1 | 341 | 0.9607 | 0.7394 | 0.4592 |
| Premier League | hist_gradient_boosting | 393 | 0.9830 | 0.7056 | 0.5301 |
| Premier League | ridge_alpha_1 | 393 | 1.0134 | 0.7073 | 0.5005 |
| Serie A | hist_gradient_boosting | 391 | 0.8597 | 0.6500 | 0.5836 |
| Serie A | ridge_alpha_1 | 391 | 0.9241 | 0.6697 | 0.5189 |

League-specific models test whether each league has enough distinct valuation structure to justify a separate estimator. These models are especially useful because league context is one of the strongest valuation signals.

### Global Vs Specialized Models

| group_column | group_value | rows | global_rmse_log | specialized_rmse_log | rmse_log_delta_specialized_minus_global | result |
| --- | --- | --- | --- | --- | --- | --- |
| cleaned_comp | Serie A | 391 | 0.8256 | 0.8597 | 0.0340 | global better |
| cleaned_comp | Bundesliga | 326 | 0.8687 | 0.9226 | 0.0539 | global better |
| cleaned_comp | Ligue 1 | 341 | 0.8677 | 0.9229 | 0.0552 | global better |
| cleaned_comp | La Liga | 389 | 0.9824 | 1.0391 | 0.0568 | global better |
| cleaned_comp | Premier League | 393 | 0.8815 | 0.9830 | 0.1016 | global better |
| position_group | MF | 804 | 0.8938 | 0.9360 | 0.0422 | global better |
| position_group | FW | 507 | 0.8022 | 0.8695 | 0.0673 | global better |
| position_group | DF | 529 | 0.9539 | 1.0218 | 0.0679 | global better |

Negative deltas mean the specialized model has lower RMSE than the global model on the same subgroup. Positive deltas mean the global model generalizes better, usually because it benefits from a larger training sample.

### Feature Importance

| feature | importance | importance_std |
| --- | --- | --- |
| Age | 0.1845 | 0.0141 |
| contract_years_remaining | 0.1497 | 0.0167 |
| cleaned_comp | 0.1464 | 0.0075 |
| contract_missing | 0.1301 | 0.0117 |
| transfer_count_before_valuation | 0.1123 | 0.0090 |
| crosses_per90 | 0.0435 | 0.0063 |
| days_since_last_transfer | 0.0383 | 0.0057 |
| goals_per90 | 0.0379 | 0.0039 |
| 90s | 0.0378 | 0.0079 |
| assists_per90 | 0.0335 | 0.0058 |

Permutation importance for the best nonlinear model highlights context and availability variables such as league, position, age, minutes, and contract status. Ridge coefficients provide a complementary linear view, but neither method should be interpreted as causal evidence.

### Error Diagnostics

| group_column | group_value | rows | mae_log | rmse_log | mae_eur |
| --- | --- | --- | --- | --- | --- |
| cleaned_comp | Premier League | 393 | 0.6186 | 0.8815 | 10498859.8927 |
| cleaned_comp | Serie A | 391 | 0.6325 | 0.8256 | 5350644.1297 |
| cleaned_comp | Ligue 1 | 341 | 0.6821 | 0.8677 | 5086252.7112 |
| cleaned_comp | Bundesliga | 326 | 0.6889 | 0.8687 | 6427194.5320 |
| cleaned_comp | La Liga | 389 | 0.7156 | 0.9824 | 6671301.8879 |
| position_group | FW | 507 | 0.6271 | 0.8022 | 8081882.9584 |
| position_group | MF | 804 | 0.6692 | 0.8938 | 6607319.0532 |
| position_group | DF | 529 | 0.6994 | 0.9539 | 6111849.9814 |
| season | 23/24 | 1840 | 0.6663 | 0.8877 | 6871178.1624 |

Residual diagnostics show where the model is more or less reliable across leagues and positions. Large errors remain expected for players whose valuation is affected by reputation, transfer demand, injuries, academy status, or unusual contract situations not captured in the data.

## Analysis and Validation

The project meets the predictive objective because all learned global models outperform the mean baseline on the held-out 2023/24 season. The best model explains a meaningful share of variance while maintaining evaluation on a future season, which is stricter than a random row split. The expanded 300-minute threshold increases coverage from 4,228 rows under the earlier 900-minute setup to 5,658 rows, but it also introduces noisier low-minute observations. This tradeoff is acceptable for the final project because the goal is broad player valuation coverage rather than only regular starters.

The segmented modeling results show that specialization is not automatically better. Some simpler ridge models improve in selected league or position segments, but the specialized hist-gradient boosting models perform worse than the global hist-gradient model on every tested subgroup. This makes the global hist-gradient boosting model the best headline model, with segment-specific models used for interpretation and robustness checks.

Contract years remaining has a positive relationship with market value in the EDA and appears among useful model features. Age is negatively correlated with log value in the aggregate, reflecting that younger players often carry resale potential. Minutes and starts capture player importance and reliability. League and position encode market context and role-based valuation differences.

## Discussion and Conclusion

The final analysis shows that football player market value can be estimated from public performance, contract, and context features with moderate accuracy. The nonlinear model gives the strongest predictive performance, while linear models remain useful for interpretation. The main contribution is a reproducible workflow that connects raw football and Transfermarkt-derived data into a player-season modeling dataset, EDA outputs, global models, position-specific models, league-specific models, and report-ready figures.

Important limitations remain. Transfermarkt market value is a proxy rather than an actual sale price, the dataset does not include injuries or detailed team strength, and the contract feature is approximated from transfer-history events. Future work should add richer event data, club financial context, exact contract records, and external validation against actual transfer fees.

## Reproducibility

Run the main results with:

```powershell
python code/reproduce.py
```

All report figures and tables are generated programmatically from the project data.
