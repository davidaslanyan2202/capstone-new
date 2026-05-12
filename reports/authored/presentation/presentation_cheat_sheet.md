# Football Player Market Value Prediction: Key Insights Cheat Sheet

## Project Overview
- **Objective**: Predict football player market value using season-level performance, league, position, age, transfer history, and contract features
- **Dataset**: 5,658 player-season observations from top 5 European leagues (2021/22-2023/24), minimum 300 minutes played
- **Target**: Log-transformed market value (log1p(market_value_eur)) to handle extreme skew
- **Train/Test Split**: Train on 2021/22 & 2022/23, test on 2023/24

## Key Findings
- **Market value is predictable**: Best model explains 61.5% of variance in log market value
- **Nonlinear relationships**: Hist-gradient boosting outperforms linear models, indicating complex valuation dynamics
- **Contract status matters**: Players with expiring contracts have higher values (resale potential)
- **Age effect**: Negative correlation - younger players often valued higher for future potential
- **League differences**: Serie A players easiest to value (R²=0.58), La Liga hardest (R²=0.48)
- **Position differences**: Forwards best predicted (R²=0.64), Defenders worst (R²=0.48)
- **Global model wins**: Single model for all players performs better than position/league-specific models

## Model Performance
- **Best Model**: Hist-gradient boosting
  - Test RMSE (log): 0.888
  - Test MAE (log): 0.666
  - R²: 0.615
  - Improvement over baseline: 38% reduction in RMSE
- **Comparison**:
  - Ridge regression: R²=0.52
  - Linear regression: R²=0.52
  - Mean baseline: R²=-0.003

## Top Predictive Features
1. **Age** (18.5% importance) - Younger = higher value potential
2. **Contract years remaining** (15.0%) - Shorter contracts = higher market value
3. **League** (14.6%) - Market context drives valuation
4. **Contract missing** (13.0%) - Free agents/out-of-contract players
5. **Transfer count before valuation** (11.2%) - Transfer history
6. **Crosses per 90** (4.4%)
7. **Days since last transfer** (3.8%)
8. **Goals per 90** (3.8%)
9. **90s played** (3.8%)
10. **Assists per 90** (3.4%)

## Position-Specific Insights
- **Forwards (FW)**: Best prediction accuracy (RMSE=0.80, R²=0.64)
- **Midfielders (MF)**: Middle performance (RMSE=0.89, R²=0.56)
- **Defenders (DF)**: Worst prediction (RMSE=0.95, R²=0.48)
- **Why?**: Offensive metrics (goals/assists) more directly tied to value than defensive stats

## League-Specific Insights
- **Serie A**: Most predictable (RMSE=0.83, R²=0.58) - Stable, tactical league
- **Bundesliga**: Good prediction (RMSE=0.87, R²=0.51)
- **Ligue 1**: Moderate (RMSE=0.87, R²=0.50)
- **Premier League**: Moderate (RMSE=0.88, R²=0.53)
- **La Liga**: Least predictable (RMSE=0.98, R²=0.48) - High variance, star-driven

## Limitations & Future Work
- **Data gaps**: No injury data, exact contract details, club finances
- **Proxy measure**: Transfermarkt values ≠ actual transfer fees
- **Unobserved factors**: Reputation, demand, academy status not captured
- **Future**: Add richer event data, external validation against real transfers

## Main Takeaway
Football player market values can be estimated from public data with moderate accuracy, but valuation remains partly driven by unobserved market context and reputation factors.