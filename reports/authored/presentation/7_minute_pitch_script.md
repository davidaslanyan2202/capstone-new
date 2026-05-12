# 7-Minute Pitch Script: Football Player Market Value Prediction

## Introduction (1 minute - 150 words)
Good [morning/afternoon], everyone. Today, I'm excited to present my capstone project: "A Data-Driven Analysis of Football Players' Transfer Value Based on Performance and Contract Characteristics."

Imagine you're a football club manager deciding whether to buy or sell a player. How much is that midfielder really worth? Transfer values influence recruitment, squad planning, and contracts, but the process is often opaque. This project tackles that by predicting player market values using public data.

Our dataset covers over 5,000 player-season observations from the top five European leagues – Premier League, La Liga, Serie A, Bundesliga, and Ligue 1 – across three seasons: 2021/22, 2022/23, and 2023/24. We use Transfermarkt market values as our target, log-transformed to handle the extreme skew in valuations.

The key questions: How well can we predict market value from performance and contract data? Which variables matter most? Do relationships differ by position or league? And how does contract expiry affect value?

## Methodology (2 minutes - 300 words)
Let's dive into how we built this. Our final analytics table combines season-level performance stats, league and position info, age, and contract features. Key features include:

- Age and age squared
- Playing time: minutes, starts, 90s played
- Per-90 performance rates: goals, assists, crosses, etc.
- League and position group
- Contract years remaining and missing contract indicators
- Transfer history: count of previous transfers and days since last transfer

We excluded players with fewer than 300 minutes to focus on meaningful contributors, giving us a robust dataset.

For modeling, we used a chronological train/test split: training on 2021/22 and 2022/23 seasons, testing on the held-out 2023/24 season. This ensures we're predicting future values, not just fitting historical patterns.

We compared four global models:
1. Mean baseline (predicts average value)
2. Ordinary least squares linear regression
3. Ridge regression (with regularization)
4. Hist-gradient boosting (nonlinear ensemble method)

To explore differences, we also trained position-specific models (defenders, midfielders, forwards) and league-specific models for each of the five leagues.

Performance metrics: RMSE and MAE on the log scale, plus R² for explained variance. We also report errors in euros after inverse transformation.

## Results (2 minutes - 300 words)
The results are compelling. Our best global model – hist-gradient boosting – achieves:
- Test RMSE (log): 0.89
- Test MAE (log): 0.67
- R²: 0.61

This represents a 38% improvement in RMSE over the mean baseline, showing we can explain over 60% of the variance in market values.

Looking at the model comparison chart, hist-gradient boosting clearly outperforms linear and ridge models, indicating nonlinear relationships in valuation.

The predicted vs. actual scatter plot shows good alignment, though with some spread – especially for high-value players.

## Figure Explanations (0.5 minutes - 75 words)
The first figure is the log market value distribution. It shows how player values cluster after log transformation, with the largest groups in the mid-range and a long tail toward the highest values. This distribution confirms why we model the log target: it reduces skew and makes values easier for regression models to learn.

The second figure is the predicted-versus-actual scatter plot for the best hist-gradient boosting model. Each point is a player-season, colored by position group. The closer points are to the diagonal line, the better the prediction. The plot shows that most predictions are close to actual values, while some high-value players still have larger errors.

When we compare specialized models to the global model, the global model actually performs better in most cases. This suggests that training on the full dataset provides more robust predictions than splitting by position or league.

Position-wise: Forwards are easiest to value (R²=0.64), defenders hardest (R²=0.48). League-wise: Serie A most predictable (R²=0.58), La Liga least (R²=0.48).

Feature importance reveals the top drivers:
1. Age (18.5%) – younger players often valued higher for potential
2. Contract years remaining (15%) – shorter contracts increase market value
3. League (14.6%) – market context matters
4. Contract missing (13%) – free agents command premium
5. Transfer count (11.2%) – transfer history signals

## Analysis and Discussion (1.5 minutes - 225 words)
These findings tell us several important things. First, market values are meaningfully predictable from public data – a valuable tool for clubs and analysts.

The nonlinear model's success suggests complex interactions: a young forward in Serie A with an expiring contract might be valued differently than a veteran defender in La Liga.

Contract expiry's positive association makes sense – clubs can sell sooner, and buyers get immediate assets. Age's negative correlation reflects depreciation but also potential for younger players.

However, limitations remain. Transfermarkt values are estimates, not actual transfer fees. We lack injury data, exact wages, team strength, and reputation factors. These unobserved elements likely explain the remaining 39% of variance.

The chronological validation is a strength – we predict next season's values, not just fit current data.

Position and league differences highlight that valuation isn't universal. Forwards' values tie more directly to offensive stats, while defenders' valuations involve more subjective factors.

## Conclusion (0.5 minutes - 75 words)
In conclusion, this project demonstrates that football player market values can be estimated from public performance and contract data with moderate accuracy. The hist-gradient boosting model provides the best predictions, outperforming baselines by 38%.

Key insights: Age, contract status, and league are crucial drivers. Values are predictable but not fully explained by observables – reputation and market context play roles.

Future work should incorporate richer data and validate against real transfer fees.

Thank you for your attention. I'm happy to take questions.

(Word count: ~1,050. Speaking time: ~7 minutes at 150 wpm)