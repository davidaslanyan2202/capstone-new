# Football Player Market Value Capstone

This project builds a reproducible player-season analytics workflow for predicting and explaining football player market value. It combines season-level performance data, Transfermarkt-derived market values, transfer-history features, and contract features for players in the top five European leagues.

## Objective

The main objective is to estimate `log_market_value_eur` from public football and contract signals, compare baseline and nonlinear regression models, and summarize valuation drivers by league and position.

## Project Structure

- `data/processed/player_season_analytics.csv` - final analytics table used for EDA and modeling.
- `analysis/eda_and_baseline.py` - one-command EDA, model comparison, diagnostics, and report generator.
- `analysis/eda_and_baseline.ipynb` - notebook version of the final analysis.
- `reports/figures/` - programmatically generated figures.
- `reports/tables/` - programmatically generated tables and model outputs.
- `reports/final_report.md` - Markdown report draft.
- `paper/main.tex` and `paper/references.bib` - IEEE/Overleaf-ready paper source files.

## Environment

Recommended environment:

- Python 3.10 or newer
- Packages listed in `requirements.txt`

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Reproduce Main Results

Run the final analysis, reports, figures, and paper source generation with one command:

```powershell
python analysis/eda_and_baseline.py --min-minutes 300 --include-position-models
```

The command regenerates:

- `data/processed/modeling_dataset.csv`
- `reports/eda_summary.md`
- `reports/final_report.md`
- `reports/tables/model_metrics.csv`
- `reports/tables/error_by_group.csv`
- `reports/tables/feature_importance.csv`
- `reports/figures/*.png`
- `paper/main.tex`
- `paper/references.bib`

## Notebook Execution

To execute the notebook from a clean kernel:

```powershell
jupyter nbconvert --to notebook --execute analysis/eda_and_baseline.ipynb --output eda_and_baseline.executed.ipynb --output-dir analysis
```

## Data Notes

The modeling target is `log_market_value_eur`, derived from `market_value_eur`. The final modeling filter keeps players with `Min >= 300`. The training seasons are `21/22` and `22/23`; the holdout test season is `23/24`.

The market value source is a proxy for player valuation rather than actual transfer fees. Contract fields are approximated from transfer-history events and should be interpreted as descriptive modeling features, not as causal proof.
