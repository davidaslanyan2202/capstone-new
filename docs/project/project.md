# Capstone Project Proposal

A Data-Driven Analysis of Football Players’ Transfer Value Based on Performance and
Contract Characteristics

## Abstract:

Transfer values play a central role in modern football, influencing decisions related to
recruitment, squad planning, and contract negotiations. Despite their importance, the
relationship between a player’s on-field performance and market value is not fully transparent.
While detailed performance statistics are widely available, it remains unclear which aspects of a
player’s contribution are most strongly reflected in transfer value and how non-performance
factors influence valuation.


This project aims to develop a data-driven framework for predicting football players’ transfer
values using season-level performance data, while also analyzing the mechanisms that drive
valuation. In addition to performance metrics, the project investigates the impact of contract
expiry on player market value. Using publicly available performance, market value, and contract
data, the project combines predictive modeling with interpretability and positional analysis. The
final outcome is not only a transfer value prediction model, but also an analytical understanding
of valuation drivers, positional differences, and the role of contract characteristics.

## 1. Introduction

In professional football, player transfer values are widely used as indicators of sporting and
financial worth. These values are influenced by multiple factors, including on-field performance,
age, playing position, contractual situation, and broader market perception. Although transfer
values are closely followed particularly in top leagues the process through which performance
and contractual factors translate into market valuation is not always clear.
In practice, player evaluation often relies heavily on a limited set of visible performance metrics
such as goals and assists. While these indicators are important, they do not fully capture the
contribution of players in defensive or supporting roles, nor do they reflect overall involvement
across a season. Additionally, non-performance factors such as remaining contract length can
have a substantial impact on transfer value, yet these effects are rarely examined alongside
performance in a systematic way.

Previous academic studies and industry analyses have applied statistical and machine learning
methods to estimate player market value. These studies suggest that performance data can
explain a significant portion of valuation; however, many approaches rely on restricted feature
sets, focus on specific leagues, or prioritize predictive accuracy without sufficient interpretability.
Furthermore, the combined impact of performance and contract-related factors is often
underexplored.

This project addresses these limitations by examining football player valuation from both a
predictive and analytical perspective. Rather than focusing solely on transfer value estimation,
the project investigates which performance metrics drive valuation, how valuation mechanisms
differ across playing positions, and how contract expiry influences market value when controlling
for performance. By using publicly available season-level data, the project aims to provide a
transparent and reproducible analysis of the relationship between performance, contracts, and
transfer value.

## 2. Research Problems and Questions
The project addresses the following research problems and associated research questions:

1. Quantifying the relationship between performance and transfer value
To what extent can football players’ transfer values be predicted using season-level on-field performance data?

2.  Identifying valuation drivers
Which performance metrics contribute most to football players’ transfer values, and how do offensive, defensive, and involvement-based indicators differ in importance?

3.  Positional differences in valuation
Does the relationship between performance metrics and transfer value differ across playing positions, and do position-specific models provide improved insight or predictive performance?

4. Impact of contract expiry on valuation
How does remaining contract length or contract expiry influence transfer value, when controlling for player performance and position?

## 3. Methodology

1. Literature Review
A review of relevant academic literature and industry work on football analytics, player valuation,
and sports economics will be conducted. The review will cover traditional valuation approaches
as well as machine learning-based models, highlighting their strengths, limitations, and common
challenges, particularly with respect to feature selection, interpretability, and non-performance
factors such as contracts.

2. Data Collection
The project will use publicly available datasets containing football players’ season-level
performance statistics, market or transfer values, and contract-related information. Expected
variables include goals, assists, passes attempted and completed, defensive actions, minutes
played, player age, playing position, and remaining contract length. Data will be collected for a
defined set of leagues and seasons to ensure consistency and comparability.

3. Data Preprocessing and Exploratory Analysis
Data preprocessing will involve handling missing and inconsistent values, normalizing
performance metrics on a per-90-minutes basis, and encoding categorical variables such as
playing position. Exploratory data analysis will be conducted to examine distributions,
correlations between performance metrics, contract variables, and transfer value, as well as
differences across positions.

4. Model Development
Several regression-based machine learning models will be developed to predict football players’
transfer values. These will include a baseline linear regression model and more advanced
models such as tree-based or ensemble methods. Model performance will be evaluated using
metrics such as RMSE and R². Where appropriate, position-specific models will be developed
and compared with a global model.

5. Evaluation and Interpretation
Model outputs will be analyzed to identify the most influential performance and contract-related
features. Feature importance and model interpretation techniques will be applied to support
transparent analysis. Prediction errors will also be examined to identify patterns of over- or
undervaluation relative to performance and contractual characteristics.

## 4. Expected Results
The expected outcomes of the project include:

- A predictive model for estimating football players’ transfer values based on performance
and contract data
- Identification of key performance indicators that drive player valuation
- Empirical evidence of positional differences in valuation mechanisms
- Analysis of the impact of contract expiry on transfer value
- A transparent analytical framework describing how performance and contract factors
relate to transfer value


## 5. Risks and How They Will Be Addressed
- Data quality limitations:
Performance, contract, or market value data may be incomplete or inconsistent. How the risk will be addressed: Systematic data cleaning will be applied, and unreliable observations will be excluded where necessary.

- Model overfitting
More complex models may fit the training data too closely. How the risk will be addressed: Cross-validation will be used, and results will be compared with simpler baseline models.

- Influence of unobserved factors
Transfer values may be affected by factors not captured in the data, such as reputation or media exposure. How the risk will be addressed: These limitations will be clearly acknowledged, and conclusions will focus on performance- and contract-related insights.
