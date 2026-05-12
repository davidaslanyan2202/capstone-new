# Graph Report - C:\Users\GBM\Documents\Dev\repos\capstone  (2026-05-13)

## Corpus Check
- 37 files · ~69,145 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 354 nodes · 552 edges · 27 communities (22 shown, 5 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 119 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_EDA Modeling Pipeline|EDA Modeling Pipeline]]
- [[_COMMUNITY_Player Analytics Build|Player Analytics Build]]
- [[_COMMUNITY_League Model RMSE|League Model RMSE]]
- [[_COMMUNITY_Residual Diagnostics|Residual Diagnostics]]
- [[_COMMUNITY_Data Build Plan|Data Build Plan]]
- [[_COMMUNITY_Research Report Context|Research Report Context]]
- [[_COMMUNITY_Transfermarkt Integration|Transfermarkt Integration]]
- [[_COMMUNITY_Presentation Findings|Presentation Findings]]
- [[_COMMUNITY_Specialized Global RMSE|Specialized Global RMSE]]
- [[_COMMUNITY_Prediction Calibration|Prediction Calibration]]
- [[_COMMUNITY_Position Model RMSE|Position Model RMSE]]
- [[_COMMUNITY_Segment RMSE Comparison|Segment RMSE Comparison]]
- [[_COMMUNITY_League Value Distribution|League Value Distribution]]
- [[_COMMUNITY_Global Model Benchmark|Global Model Benchmark]]
- [[_COMMUNITY_Contract Value Pattern|Contract Value Pattern]]
- [[_COMMUNITY_Position Value Distribution|Position Value Distribution]]
- [[_COMMUNITY_Log Value Histogram|Log Value Histogram]]
- [[_COMMUNITY_Model Numeric Features|Model Numeric Features]]
- [[_COMMUNITY_Raw Value Distribution|Raw Value Distribution]]
- [[_COMMUNITY_Per 90 Performance|Per 90 Performance]]
- [[_COMMUNITY_Transfer ID Helpers|Transfer ID Helpers]]
- [[_COMMUNITY_Transfer ID Tests|Transfer ID Tests]]
- [[_COMMUNITY_Correlation Heatmap|Correlation Heatmap]]
- [[_COMMUNITY_Error Diagnostics|Error Diagnostics]]
- [[_COMMUNITY_Assist Rate Feature|Assist Rate Feature]]
- [[_COMMUNITY_Cross Rate Feature|Cross Rate Feature]]

## God Nodes (most connected - your core abstractions)
1. `League-Specific Model Comparison` - 24 edges
2. `main()` - 14 edges
3. `clean_text()` - 14 edges
4. `Residuals By Position Boxplots` - 13 edges
5. `main()` - 12 edges
6. `Residuals By League Boxplots` - 12 edges
7. `Global Model Lower RMSE Across Shown Segments` - 11 edges
8. `add_metrics_row_ids_and_features()` - 9 edges
9. `Final Report Results` - 8 edges
10. `Test RMSE log` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Poster PDF Results Summary` --semantically_similar_to--> `Final Report Results`  [INFERRED] [semantically similar]
  A Data-Driven Analysis of Football Players’ Transfer Value Based on Performance and Contract Characteristics (1).pdf → reports/generated/final_report.md
- `Seven Minute Pitch Script PDF` --semantically_similar_to--> `Seven Minute Presentation Narrative`  [INFERRED] [semantically similar]
  7_minute_pitch_script.pdf → 7_minute_pitch_script.md
- `Poster Q&A Answers PDF` --semantically_similar_to--> `Poster Q&A Methodology Answers`  [INFERRED] [semantically similar]
  poster_qa_answers.pdf → poster_qa_answers.md
- `Player Valuation Research Questions` --rationale_for--> `Global Model Comparison`  [INFERRED]
  project.md → code\\analysis\\eda_and_baseline.py
- `Project Risks And Mitigations` --semantically_similar_to--> `Final Report Limitations`  [INFERRED] [semantically similar]
  project.md → reports/generated/final_report.md

## Hyperedges (group relationships)
- **Player Season Data Pipeline Tables** — metrics_csv, build_player_season_analytics_transfer_history_events_table, build_player_season_analytics_market_values_table, build_player_season_analytics_contract_features_table, build_player_season_analytics_analytics_table [EXTRACTED 1.00]
- **Market Value Modeling Workflow** — eda_and_baseline_final_analytics_input, eda_and_baseline_modeling_dataset, eda_and_baseline_chronological_train_test_split, eda_and_baseline_global_model_comparison, eda_and_baseline_feature_importance_analysis, eda_and_baseline_error_diagnostics, eda_and_baseline_report_artifact_generation [EXTRACTED 1.00]
- **Capstone Presentation Artifacts** — pitch_script_presentation_narrative, poster_qa_methodology, presentation_cheat_sheet_key_findings, poster_pdf_capstone_poster, poster_general_structure_guidelines [INFERRED 0.86]
- **Model performance comparison by league** — league_model_comparison_chart, league_model_comparison_test_rmse_log_metric, league_model_comparison_ridge_alpha_1_model, league_model_comparison_hist_gradient_boosting_model, league_model_comparison_bundesliga_league, league_model_comparison_la_liga_league, league_model_comparison_ligue_1_league, league_model_comparison_premier_league_league, league_model_comparison_serie_a_league [EXTRACTED 1.00]
- **hist_gradient_boosting lower RMSE majority pattern** — league_model_comparison_hist_gradient_boosting_model, league_model_comparison_ridge_alpha_1_model, league_model_comparison_hist_gradient_boosting_lower_rmse_most_leagues, league_model_comparison_la_liga_result, league_model_comparison_ligue_1_result, league_model_comparison_premier_league_result, league_model_comparison_serie_a_result [INFERRED 0.85]
- **League-specific RMSE result set** — league_model_comparison_bundesliga_result, league_model_comparison_la_liga_result, league_model_comparison_ligue_1_result, league_model_comparison_premier_league_result, league_model_comparison_serie_a_result, league_model_comparison_test_rmse_log_metric [EXTRACTED 1.00]
- **Global Model RMSE Comparison** — model_comparison_test_rmse_hist_gradient_boosting, model_comparison_test_rmse_ridge_alpha_1, model_comparison_test_rmse_linear_regression, model_comparison_test_rmse_mean_baseline, model_comparison_test_rmse_test_rmse_log, model_comparison_test_rmse_2023_24_test_season [EXTRACTED 1.00]
- **Position-Specific Model Benchmark** — position_model_comparison_chart, position_model_comparison_test_rmse_log, position_model_comparison_position_group, position_model_comparison_ridge_alpha_1, position_model_comparison_hist_gradient_boosting [EXTRACTED 1.00]
- **Compared Position Groups** — position_model_comparison_df, position_model_comparison_mf, position_model_comparison_fw [EXTRACTED 1.00]
- **Model and Position Error Patterns** — position_model_comparison_hgb_lower_rmse_pattern, position_model_comparison_position_error_gradient, position_model_comparison_test_rmse_log, position_model_comparison_hist_gradient_boosting, position_model_comparison_ridge_alpha_1 [EXTRACTED 1.00]
- **Position Group Stratification in Prediction Chart** — predicted_vs_actual_best_model_chart, predicted_vs_actual_best_model_position_group, predicted_vs_actual_best_model_df, predicted_vs_actual_best_model_fw, predicted_vs_actual_best_model_mf [EXTRACTED 1.00]
- **Model Calibration View** — predicted_vs_actual_best_model_chart, predicted_vs_actual_best_model_hist_gradient_boosting, predicted_vs_actual_best_model_actual_log_market_value, predicted_vs_actual_best_model_predicted_log_market_value, predicted_vs_actual_best_model_ideal_reference_line, predicted_vs_actual_best_model_prediction_alignment [INFERRED 0.86]
- **Residual Diagnostics By Categorical Group** — residuals_by_league_position_figure, residuals_by_league_position_actual_minus_predicted_log_value, residuals_by_league_position_league_boxplots, residuals_by_league_position_position_boxplots, residuals_by_league_position_zero_residual_baseline [EXTRACTED 1.00]
- **League Residual Comparison** — residuals_by_league_position_league_boxplots, residuals_by_league_position_premier_league, residuals_by_league_position_bundesliga, residuals_by_league_position_ligue_1, residuals_by_league_position_la_liga, residuals_by_league_position_serie_a [EXTRACTED 1.00]
- **Position Residual Comparison** — residuals_by_league_position_position_boxplots, residuals_by_league_position_defenders, residuals_by_league_position_midfielders, residuals_by_league_position_forwards [EXTRACTED 1.00]
- **Positive RMSE Gap Ranking Across Segments** — specialized_vs_global_rmse_chart, specialized_vs_global_rmse_log_rmse_difference, specialized_vs_global_rmse_premier_league_segment, specialized_vs_global_rmse_defender_forward_segments, specialized_vs_global_rmse_mid_tier_leagues, specialized_vs_global_rmse_midfielder_segment, specialized_vs_global_rmse_serie_a_segment [EXTRACTED 1.00]
- **Position Group Color Encoding** — contract_years_vs_log_market_value_position_group, contract_years_vs_log_market_value_forward_group, contract_years_vs_log_market_value_midfielder_group, contract_years_vs_log_market_value_defender_group [EXTRACTED 1.00]
- **Contract Market Value Measurement Frame** — contract_years_vs_log_market_value_scatterplot, contract_years_vs_log_market_value_contract_years_remaining, contract_years_vs_log_market_value_log_market_value_eur, contract_years_vs_log_market_value_position_group [EXTRACTED 1.00]
- **League-specific RMSE comparison across five football leagues** — league_model_comparison_chart, league_model_comparison_test_rmse_log, league_model_comparison_ridge_alpha_1, league_model_comparison_hist_gradient_boosting, league_model_comparison_bundesliga_rmse, league_model_comparison_la_liga_rmse, league_model_comparison_ligue_1_rmse, league_model_comparison_premier_league_rmse, league_model_comparison_serie_a_rmse [EXTRACTED 1.00]
- **League Market Value Distribution Comparison** — log_market_value_by_league_chart, log_market_value_by_league_log10_market_value_eur, log_market_value_by_league_boxplot_distribution, log_market_value_by_league_premier_league, log_market_value_by_league_bundesliga, log_market_value_by_league_serie_a, log_market_value_by_league_ligue_1, log_market_value_by_league_la_liga [EXTRACTED 1.00]
- **Position Group Market Value Distribution Comparison** — log_market_value_by_position_chart, log_market_value_by_position_log1p_market_value_eur, log_market_value_by_position_position_group, log_market_value_by_position_df, log_market_value_by_position_mf, log_market_value_by_position_fw [EXTRACTED 1.00]
- **Log Market Value Distribution Histogram Summary** — log_market_value_distribution_chart, log_market_value_distribution_log1p_market_value_eur, log_market_value_distribution_count, log_market_value_distribution_histogram_bins, log_market_value_distribution_central_mass, log_market_value_distribution_peak_near_16, log_market_value_distribution_sparse_tails [EXTRACTED 1.00]
- **Market Value Histogram Interpretation** — market_value_distribution_histogram, market_value_distribution_market_value_eur, market_value_distribution_count, market_value_distribution_low_value_concentration, market_value_distribution_high_value_outliers, market_value_distribution_right_skew [EXTRACTED 0.90]
- **Global Model RMSE Comparison** — model_comparison_test_rmse_hist_gradient_boosting, model_comparison_test_rmse_ridge_alpha_1, model_comparison_test_rmse_linear_regression, model_comparison_test_rmse_mean_baseline, model_comparison_test_rmse_test_rmse_log, model_comparison_test_rmse_2023_24_test_season [EXTRACTED 1.00]
- **All Numeric Features in Correlation Matrix** — numeric_correlation_heatmap_market_value_eur, numeric_correlation_heatmap_log_market_value_eur, numeric_correlation_heatmap_age, numeric_correlation_heatmap_min, numeric_correlation_heatmap_90s, numeric_correlation_heatmap_goals_per90, numeric_correlation_heatmap_assists_per90, numeric_correlation_heatmap_shots_per90, numeric_correlation_heatmap_shots_on_target_per90, numeric_correlation_heatmap_crosses_per90, numeric_correlation_heatmap_interceptions_per90, numeric_correlation_heatmap_tackles_won_per90, numeric_correlation_heatmap_contract_years_remaining, numeric_correlation_heatmap_days_since_last_transfer, numeric_correlation_heatmap_transfer_count_before_valuation [EXTRACTED 1.00]
- **Attacking Output Feature Cluster** — numeric_correlation_heatmap_goals_per90, numeric_correlation_heatmap_assists_per90, numeric_correlation_heatmap_shots_per90, numeric_correlation_heatmap_shots_on_target_per90, numeric_correlation_heatmap_crosses_per90 [EXTRACTED 1.00]
- **Valuation, Contract, and Transfer Timing Features** — numeric_correlation_heatmap_market_value_eur, numeric_correlation_heatmap_log_market_value_eur, numeric_correlation_heatmap_age, numeric_correlation_heatmap_contract_years_remaining, numeric_correlation_heatmap_days_since_last_transfer, numeric_correlation_heatmap_transfer_count_before_valuation [EXTRACTED 1.00]
- **Position-specific RMSE comparison across football position groups** — position_model_comparison_chart, position_model_comparison_test_rmse_log, position_model_comparison_position_group, position_model_comparison_ridge_alpha_1, position_model_comparison_hist_gradient_boosting, position_model_comparison_df_rmse, position_model_comparison_mf_rmse, position_model_comparison_fw_rmse [EXTRACTED 1.00]
- **Position-group model error pattern** — position_model_comparison_hgb_lower_rmse_all_positions, position_model_comparison_fw_lowest_rmse, position_model_comparison_df_highest_rmse, position_model_comparison_df_rmse, position_model_comparison_mf_rmse, position_model_comparison_fw_rmse [INFERRED 0.86]
- **Best Model Prediction Evaluation View** — predicted_vs_actual_best_model_hist_gradient_boosting, predicted_vs_actual_best_model_actual_log_market_value, predicted_vs_actual_best_model_predicted_log_market_value, predicted_vs_actual_best_model_position_group, predicted_vs_actual_best_model_perfect_prediction_line [EXTRACTED 1.00]
- **Position Group Overlay** — predicted_vs_actual_best_model_df, predicted_vs_actual_best_model_fw, predicted_vs_actual_best_model_mf, predicted_vs_actual_best_model_position_group [EXTRACTED 1.00]
- **Residual diagnostic figure structure** — residuals_by_league_position_chart, residuals_by_league_position_residual_log_metric, residuals_by_league_position_league_boxplots, residuals_by_league_position_position_boxplots, residuals_by_league_position_zero_reference_line [EXTRACTED 1.00]
- **League and position residual grouping facets** — residuals_by_league_position_premier_league, residuals_by_league_position_bundesliga, residuals_by_league_position_ligue_1, residuals_by_league_position_la_liga, residuals_by_league_position_serie_a, residuals_by_league_position_df, residuals_by_league_position_mf, residuals_by_league_position_fw [EXTRACTED 1.00]
- **Mostly centered residuals with asymmetric negative outliers** — residuals_by_league_position_near_zero_medians, residuals_by_league_position_negative_outliers, residuals_by_league_position_overprediction_interpretation, residuals_by_league_position_league_extreme_outliers, residuals_by_league_position_position_extreme_outliers [INFERRED 0.86]
- **Specialized and Global Model RMSE Scope Comparison** — reports_specialized_vs_global_rmse_chart, reports_specialized_vs_global_rmse_hist_gradient_boosting_model, reports_specialized_vs_global_rmse_log_delta_metric, reports_specialized_vs_global_rmse_specialized_model, reports_specialized_vs_global_rmse_global_model [EXTRACTED 1.00]
- **Positive RMSE Gap Ranking Across Segments** — reports_specialized_vs_global_rmse_log_delta_metric, reports_specialized_vs_global_rmse_premier_league_gap, reports_specialized_vs_global_rmse_df_gap, reports_specialized_vs_global_rmse_fw_gap, reports_specialized_vs_global_rmse_la_liga_gap, reports_specialized_vs_global_rmse_ligue_1_gap, reports_specialized_vs_global_rmse_bundesliga_gap, reports_specialized_vs_global_rmse_mf_gap, reports_specialized_vs_global_rmse_serie_a_gap [EXTRACTED 1.00]
- **Segmented Model Underperformance Pattern** — reports_specialized_vs_global_rmse_global_lower_error_insight, reports_specialized_vs_global_rmse_league_segments, reports_specialized_vs_global_rmse_position_segments, reports_specialized_vs_global_rmse_premier_league_largest_gap, reports_specialized_vs_global_rmse_serie_a_smallest_gap [INFERRED 0.84]

## Communities (27 total, 5 thin omitted)

### Community 0 - "EDA Modeling Pipeline"
Cohesion: 0.13
Nodes (30): clean_numeric_columns(), dataframe_to_markdown(), encoder(), ensure_dirs(), evaluate_predictions(), fit_model_set(), format_eur(), load_data() (+22 more)

### Community 1 - "Player Analytics Build"
Cohesion: 0.18
Nodes (28): add_metrics_row_ids_and_features(), build_contract_feature_rows(), build_market_value_rows(), choose_market_value(), clean_comp(), clean_nation(), clean_text(), compact_content() (+20 more)

### Community 2 - "League Model RMSE"
Cohesion: 0.14
Nodes (28): Bundesliga, Bundesliga RMSE: ridge ~0.90, hist_gradient_boosting ~0.92, Bundesliga is the visible exception where ridge_alpha_1 has slightly lower RMSE, Bundesliga RMSE: ridge_alpha_1 ~0.90, hist_gradient_boosting ~0.92, League-Specific Model Comparison, hist_gradient_boosting lower RMSE in four of five leagues, hist_gradient_boosting, hist_gradient_boosting lower RMSE in most leagues (+20 more)

### Community 3 - "Residual Diagnostics"
Cohesion: 0.13
Nodes (27): Actual Minus Predicted Log Value Residual, Bundesliga, Residual Diagnostics by League and Position, Defenders Position Group, DF position group, Residuals By League And Position Figure, Forwards Position Group, FW position group (+19 more)

### Community 4 - "Data Build Plan"
Cohesion: 0.09
Nodes (26): Add Metrics Row IDs And Features, Player Season Analytics Table, Build Contract Feature Rows, Build Market Value Rows, Choose Market Value, Contract Feature Rule, Player Season Contract Features Table, Join By Row ID (+18 more)

### Community 5 - "Research Report Context"
Cohesion: 0.08
Nodes (25): Aydemir et al. 2022 Ensemble Valuation Study, Chronological Train/Test Split, EDA And Diagnostic Visualizations, Minimum 300 Minutes Filter, Modeling Dataset, IEEE Paper Source Generation, EDA And Baseline Pipeline, Herm et al. 2014 Crowd Valuation Study (+17 more)

### Community 6 - "Transfermarkt Integration"
Cohesion: 0.1
Nodes (23): Add Transfermarkt IDs, Build Player ID Lookup, Normalize Player Name, Load Market Values, Parse Transfer History, Transfer History Events Table, Transfer History JSON Files, Processed Metrics CSV (+15 more)

### Community 7 - "Presentation Findings"
Cohesion: 0.13
Nodes (20): Feature Importance Analysis, Global Model Comparison, Hist-Gradient Boosting Model, League-Specific Models, Linear Regression Model, Mean Baseline Model, Permutation Importance, Position-Specific Models (+12 more)

### Community 8 - "Specialized Global RMSE"
Cohesion: 0.16
Nodes (19): Bundesliga Specialized RMSE log gap (~0.054), Specialized Vs Global Hist-Gradient Boosting RMSE Chart, Defender Specialized RMSE log gap (~0.068), Forward Specialized RMSE log gap (~0.067), Global Model Lower RMSE Across Shown Segments, Global Model, Hist-Gradient Boosting Model, La Liga Specialized RMSE log gap (~0.057) (+11 more)

### Community 9 - "Prediction Calibration"
Cohesion: 0.21
Nodes (17): Actual log1p Market Value EUR, Predicted Vs Actual Log Market Value Chart, DF Position Group, Predicted Vs Actual Log Market Value Figure, FW Position Group, Hist Gradient Boosting Best Model, Ideal Prediction Reference Line, Market Value EUR (+9 more)

### Community 10 - "Position Model RMSE"
Cohesion: 0.24
Nodes (16): Position-Specific Model Comparison, DF Position Group, DF has highest visible test RMSE among position groups, DF RMSE: ridge_alpha_1 ~1.03, hist_gradient_boosting ~1.02, FW Position Group, FW has lowest visible test RMSE among position groups, FW RMSE: ridge_alpha_1 ~0.93, hist_gradient_boosting ~0.90, hist_gradient_boosting lower RMSE across all shown position groups (+8 more)

### Community 11 - "Segment RMSE Comparison"
Cohesion: 0.21
Nodes (14): Specialized Vs Global Hist-Gradient Boosting RMSE Chart, Defender and Forward Position Segments (~0.067 RMSE log gap), Global Model Lower RMSE Across Shown Segments, Global Model, Hist-Gradient Boosting Model, League Segments, Specialized RMSE log minus Global RMSE log, La Liga, Ligue 1, and Bundesliga Segments (~0.054-0.057 RMSE log gap) (+6 more)

### Community 12 - "League Value Distribution"
Cohesion: 0.27
Nodes (11): League Boxplot Market Value Distribution, Bundesliga, Log Market Value By League Chart, La Liga, Ligue 1, log10p Market Value EUR, Lower Market Value Outliers Across Leagues, Premier League (+3 more)

### Community 13 - "Global Model Benchmark"
Cohesion: 0.42
Nodes (9): 2023/24 Test Season, Global Model Comparison On 2023/24 Test Season, Mean Baseline Highest Test RMSE, hist_gradient_boosting, linear_regression, Histogram Gradient Boosting Lowest Test RMSE, mean_baseline, ridge_alpha_1 (+1 more)

### Community 14 - "Contract Value Pattern"
Cohesion: 0.39
Nodes (9): Contract Years Remaining, DF, Dense 0-6 Contract Year Cluster, FW, log1p(market value EUR), MF, Position Group, Positive Contract Duration And Market Value Pattern (+1 more)

### Community 15 - "Position Value Distribution"
Cohesion: 0.44
Nodes (9): Log Market Value By Position Group Boxplot, DF Position Group, FW Position Group, FW Slightly Higher Median Log Market Value, log1p(market value EUR), MF Position Group, Position Group, Lower Market Value Outliers Across Position Groups (+1 more)

### Community 16 - "Log Value Histogram"
Cohesion: 0.31
Nodes (9): Central Mass Around Log Market Value 14-17, Log Market Value Distribution Histogram, Count, Market Value Histogram Bins, log1p(market value EUR), Sparse Lower Tail Around Log Market Value 9-12, Highest Frequency Near Log Market Value 16, Sparse Low and High Market Value Tails (+1 more)

### Community 17 - "Model Numeric Features"
Cohesion: 0.39
Nodes (8): 90s, Age, contract_years_remaining, days_since_last_transfer, log_market_value_eur, market_value_eur, Min, transfer_count_before_valuation

### Community 18 - "Raw Value Distribution"
Cohesion: 0.47
Nodes (6): Count, High Market Value Outliers, Market Value Distribution Histogram, Low Market Value Concentration, Market Value EUR, Right-Skewed Market Value Distribution

### Community 19 - "Per 90 Performance"
Cohesion: 0.7
Nodes (5): goals_per90, interceptions_per90, shots_on_target_per90, shots_per90, tackles_won_per90

### Community 20 - "Transfer ID Helpers"
Cohesion: 1.0
Nodes (3): add_transfermarkt_ids(), build_player_id_lookup(), normalize_name()

## Ambiguous Edges - Review These
- `Processed Metrics CSV` → `Top5 With Transfermarkt ID Table`  [AMBIGUOUS]
  code/validation/check_transfermarkt_ids.py · relation: semantically_similar_to

## Knowledge Gaps
- **67 isolated node(s):** `Render a compact GitHub-style Markdown table without optional dependencies.`, `Top Five League Performance Rows`, `Season Valuation Dates`, `Per-90 Feature Engineering`, `Player Season Team Row Grain` (+62 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Processed Metrics CSV` and `Top5 With Transfermarkt ID Table`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `EDA And Baseline Pipeline` connect `Research Report Context` to `Data Build Plan`, `Presentation Findings`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `Final Analytics Input` connect `Data Build Plan` to `Research Report Context`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `League-Specific Model Comparison` (e.g. with `hist_gradient_boosting lower RMSE in most leagues` and `ridge_alpha_1 lower RMSE in Bundesliga`) actually correct?**
  _`League-Specific Model Comparison` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Residuals By Position Boxplots` (e.g. with `Near-Zero Residual Medians Across Groups` and `Residuals By League Boxplots`) actually correct?**
  _`Residuals By Position Boxplots` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Render a compact GitHub-style Markdown table without optional dependencies.`, `Top Five League Performance Rows`, `Season Valuation Dates` to the rest of the system?**
  _67 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `EDA Modeling Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._