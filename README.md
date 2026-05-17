# Football Player Market Value Capstone

This project builds a reproducible player-season analytics workflow for predicting and explaining football player market value. It combines season-level performance data, Transfermarkt-derived market values, transfer-history features, and contract features for players in the top five European leagues.

## Objective

Estimate `log_market_value_eur` from public football and contract signals, compare baseline and nonlinear regression models, and summarize valuation drivers by league and position.

## Supervisor Review Quick Start

Use these steps when reviewing the submission from a fresh checkout or downloaded ZIP.

1. Open a terminal in the repository root, the folder that contains this `README.md`.
2. Create and activate a Python virtual environment.

   Windows PowerShell:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies.

   Windows PowerShell:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   macOS/Linux:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Reproduce the project outputs without network access.

   ```powershell
   python code/reproduce.py
   ```

5. Run the automated checks.

   ```powershell
   python -m unittest discover -s tests -v
   ```

After these commands complete, review the generated analysis in `reports/generated/final_report.md`, the summary in `reports/generated/analysis_summary.md`, and the final paper PDF in `paper/final/main.pdf`.

## Project Structure

- `code/preprocessing/` - data preparation scripts that build interim and processed datasets.
- `code/analysis/` - EDA, model comparison, diagnostics, and generated report/paper draft logic.
- `code/scraping/` - optional Transfermarkt history scraper; the tracked JSON files are already included.
- `code/validation/` - lightweight data validation checks.
- `data/raw/` - original CSV inputs.
- `data/scraped/transfermarkt/history_json/` - tracked scraped Transfermarkt transfer-history JSON.
- `data/interim/` - inferred/intermediate CSVs used to assemble the final dataset.
- `data/processed/` - final analytics and modeling datasets.
- `reports/generated/` - programmatically generated tables, figures, and analysis reports.
- `reports/authored/` - hand/AI-written presentation and poster materials.
- `paper/final/` - canonical IEEE paper source, bibliography, figures, and compiled PDF.
- `docs/` - project notes, guidelines, and file classification manifest.

## Environment

Recommended runtime:

- Python 3.10 or newer
- Packages listed in `requirements.txt`

The reproduction workflow is designed to run offline because the required raw CSV files and scraped Transfermarkt JSON files are tracked in the repository. Network access is only needed for the optional scraping refresh.

If PowerShell blocks virtual-environment activation on Windows, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Reproduce Main Results

Run the full non-network reproduction workflow from the repository root:

```powershell
python code/reproduce.py
```

This command runs, in order:

1. `code/preprocessing/add_transfermarkt_ids.py`
2. `code/validation/check_transfermarkt_ids.py`
3. `code/preprocessing/build_player_season_analytics.py`
4. `code/validation/check_data_quality.py`
5. `code/analysis/eda_and_baseline.py --min-minutes 300 --include-position-models --include-league-models`

It rebuilds or refreshes:

- `data/interim/metrics.csv`
- `data/interim/unmatched_transfermarkt_id_rows.csv`
- `data/interim/ambiguous_transfermarkt_id_rows.csv`
- `data/interim/metrics_with_valuation_dates.csv`
- `data/interim/transfer_history_events.csv`
- `data/interim/player_season_market_values.csv`
- `data/interim/player_season_contract_features.csv`
- `data/processed/player_season_analytics.csv`
- `data/processed/modeling_dataset.csv`
- `reports/generated/analysis_summary.md`
- `reports/generated/final_report.md`
- `reports/generated/tables/*.csv`
- `reports/generated/figures/*.png`
- `paper/final/figures/*.png`

The final paper text in `paper/final/main.tex` is intentionally not overwritten by the reproduction command. The reproduction workflow refreshes the figures used by the paper, while the final PDF is compiled from the hand-edited source in `paper/final/`.

The reproduction workflow also runs validation gates for Transfermarkt IDs, stale market-value labels, future-dated transfer leakage, duplicate row grains, and negative modeled contract years.

## Tests

Run the unit tests from the repository root with:

```powershell
python -m unittest discover -s tests -v
```

The tests cover the preprocessing and validation rules that are easiest to regress: Transfermarkt ID ambiguity handling, valuation-date selection, stale-label handling, and contract-feature leakage prevention.

## Optional Scraping

The tracked scraped JSON files are sufficient for supervisor review and reproduction. To refresh them from the network, run:

```powershell
python code/scraping/scrape_transfer_history.py
```

This optional command contacts Transfermarkt-derived endpoints and can take longer than the offline reproduction workflow. It is not required to grade or verify the submitted results.

## Notebook Execution

To execute the notebook from a clean kernel:

```powershell
jupyter nbconvert --to notebook --execute code\analysis\eda_and_baseline.ipynb --output eda_and_baseline.executed.ipynb --output-dir code\analysis
```

The notebook is optional. The canonical reproducible path is `python code/reproduce.py`.

## Review Checklist

For a standard supervisor review, verify these items:

- `python code/reproduce.py` completes successfully.
- `python -m unittest discover -s tests -v` passes.
- `reports/generated/final_report.md` and `reports/generated/analysis_summary.md` are present after reproduction.
- `data/processed/modeling_dataset.csv` exists and reflects the modeling filter described below.
- `paper/final/main.pdf` is available for reading the final report; the reproduction command refreshes the paper figures but does not rewrite `paper/final/main.tex`.

## Data Notes

The modeling target is `log_market_value_eur`, derived from `market_value_eur`. Market-value observations more than 120 days from the season valuation date are flagged as stale and excluded from modeling. The final modeling filter keeps players with `Min >= 300`. The training seasons are `21/22` and `22/23`; the holdout test season is `23/24`.

The market value source is a proxy for player valuation rather than actual transfer fees. Contract fields are approximated from transfer-history events, expired contracts are modeled with an explicit flag, and contract features should be interpreted as descriptive modeling signals, not as causal proof.
