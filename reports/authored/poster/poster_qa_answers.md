# Poster Presentation Q&A Answer Sheet

This document provides prepared answers to potential questions judges or audience members might ask after your football player market value prediction poster presentation.

## Project Overview Questions

### What is the main objective of your project?
Our project builds a reproducible analytics workflow to predict and explain football player market values using season-level performance data, league context, position, age, transfer history, and contract features from the top five European leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1) across seasons 2021/22 to 2023/24.

### Why is this topic important?
Transfer values influence recruitment, squad planning, and contract negotiations in professional football. Understanding what drives market valuation helps clubs make informed decisions and provides transparency in an otherwise opaque process.

### What makes your approach unique?
We emphasize reproducibility with a chronological train/test split (training on 2021/22-2022/23, testing on 2023/24), explicit holdout validation, and comprehensive diagnostics comparing global vs. position/league-specific models.

## Methodology Questions

### How did you collect the data?
We scraped player transfer history data from Transfermarkt's API (tmapi-alpha.transfermarkt.technology) using Python scripts. The scraper reads unique player IDs from processed metrics data, makes concurrent HTTP requests to fetch JSON transfer histories, and saves the results to local JSON files. This was combined with season-level performance statistics from football analytics sources.

### What preprocessing steps did you take?
- Filtered players with minimum 300 minutes played to focus on meaningful contributors
- Handled missing values using median imputation for numeric features and most frequent for categorical
- Log-transformed the target (market_value_eur) to address extreme skewness
- Created features like contract years remaining, transfer counts, and age squared

### Why did you choose a chronological train/test split?
This ensures we're predicting future market values rather than just fitting historical patterns. It's more realistic for real-world application where you'd predict next season's values using current data.

### What features did you include in your models?
Numeric: Age, age squared, minutes, starts, 90s, per-90 performance rates (goals, assists, shots, etc.), contract years remaining, transfer counts, days since last transfer.
Categorical: Position group, league, season.

## Model Selection Questions

### Why did you choose these specific models?
- **Mean baseline**: Simple benchmark to show any learned model improves over predicting the average
- **Linear regression**: Interpretable baseline for understanding linear relationships
- **Ridge regression**: Regularized linear model to handle potential multicollinearity
- **Hist-gradient boosting**: Nonlinear ensemble method for capturing complex interactions, which proved most effective

### Why hist-gradient boosting over other nonlinear methods?
Hist-gradient boosting is efficient with large datasets, handles mixed data types well, and provides good performance without extensive hyperparameter tuning. It outperformed other tree-based methods we tested and showed the best balance of accuracy and computational efficiency.

### Why evaluate on RMSE, MAE, and R²?
- **RMSE (Root Mean Squared Error)**: Penalizes large errors more heavily, good for understanding overall prediction accuracy
- **MAE (Mean Absolute Error)**: Shows average absolute error, more interpretable in euros
- **R²**: Measures proportion of variance explained, standard goodness-of-fit metric

We report both log-scale and euro-scale metrics since the target is log-transformed.

### Why not use more advanced models like neural networks?
We prioritized interpretability and computational efficiency. Hist-gradient boosting provided excellent performance without the complexity of neural networks, which would require more data and computational resources.

## Data Questions

### How reliable is Transfermarkt data?
Transfermarkt values are crowd-sourced estimates rather than actual transaction prices. While not perfect, they're widely used in football economics research and correlate well with real transfer values. We acknowledge this limitation and note that our predictions are estimates of estimated values.

### Why exclude players with fewer than 300 minutes?
This threshold balances coverage (keeping 5,658 observations) with quality, excluding players with very limited playing time who may not have established market values.

### How did you handle missing contract data?
We created a "contract_missing" binary feature and imputed missing values appropriately. About 13% of players had missing contract information.

## Results Questions

### Why does the global model outperform specialized models?
The global model benefits from a larger training sample (all players) compared to position/league-specific models trained on subsets. While some specialized models improve slightly, the global approach provides more robust generalization.

### What explains the differences between leagues and positions?
League context captures market maturity and competition level. Positions differ because offensive metrics (goals/assists) more directly correlate with value than defensive stats.

### How do your results compare to existing literature?
Our R² of 0.61 aligns with similar studies using machine learning for player valuation. The nonlinear model's advantage supports recent findings that valuation involves complex interactions.

## Tools and Libraries Questions

### What programming language and libraries did you use?
- **Python**: Main language for data processing, modeling, and automation
- **pandas/numpy**: Data manipulation and analysis
- **scikit-learn**: Machine learning models and evaluation metrics
- **matplotlib/seaborn**: Data visualization and plotting
- **jupyter**: Interactive development and notebook-based analysis
- **urllib/concurrent.futures**: Web scraping with multi-threading

### Why Python over R or other languages?
Python has excellent libraries for both data science (pandas, scikit-learn) and web scraping, plus strong support for reproducible workflows.

### How did you ensure reproducibility?
All analysis is scripted in Python with fixed random seeds. The workflow regenerates all results, figures, and reports from raw data with a single command.

## Validation and Robustness Questions

### How confident are you in your results?
The chronological holdout validation provides strong evidence of generalizability. Cross-validation on training data showed consistent performance, and the model's feature importance aligns with football domain knowledge.

### What are the main limitations?
- Transfermarkt values are estimates, not actual sales prices
- Missing data on injuries, wages, team strength, and reputation
- Limited to top European leagues; may not generalize to other football contexts
- Contract features are approximated from transfer history

### How would you improve the model with more data?
Add injury records, exact contract details, club financial data, and player reputation metrics. External validation against actual transfer fees would be valuable.

## Future Work Questions

### What are your next steps?
- Validate predictions against real transfer data
- Add richer event-level football statistics
- Explore deep learning approaches with larger datasets
- Develop a web application for real-time player valuation

### How could this be applied in practice?
Clubs could use the model for transfer target evaluation, contract negotiations, and squad planning. Agents might use it to justify player values to clubs.

## General Questions

### How long did this project take?
Approximately [X months/weeks] of part-time work, including data collection, preprocessing, modeling, and report writing.

### What was the most challenging part?
[Data preprocessing/cleaning, model selection, or interpretation - choose based on your experience]

### What did you learn from this project?
- Importance of chronological validation in time-series prediction
- Balance between model complexity and interpretability
- Value of reproducible workflows in data science

### Do you have any questions for us?
[Prepare 1-2 thoughtful questions about their work or the field]

---

Remember to:
- Speak confidently but acknowledge uncertainties
- Use the poster visuals to illustrate points
- Keep answers concise (1-2 minutes each)
- Practice delivering answers naturally
- Have business cards or contact info ready