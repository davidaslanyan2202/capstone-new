#!/usr/bin/env python3
"""Run first-pass EDA and baseline market-value models.

Input:
    data/processed/player_season_analytics.csv

Outputs:
    data/processed/modeling_dataset.csv
    reports/eda_summary.md
    reports/tables/*.csv
    reports/figures/*.png
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "processed" / "player_season_analytics.csv"
DEFAULT_MODELING_DATASET = REPO_ROOT / "data" / "processed" / "modeling_dataset.csv"
REPORTS_DIR = REPO_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

TARGET = "log_market_value_eur"
RAW_TARGET = "market_value_eur"
TRAIN_SEASONS = ["21/22", "22/23"]
TEST_SEASONS = ["23/24"]

NUMERIC_FEATURES = [
    "Age",
    "age_squared",
    "Min",
    "Starts",
    "90s",
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "shots_on_target_per90",
    "crosses_per90",
    "interceptions_per90",
    "tackles_won_per90",
    "fouls_per90",
    "fouled_per90",
    "contract_years_remaining",
    "contract_missing",
    "days_since_last_transfer",
    "transfer_count_before_valuation",
    "loan_count_before_valuation",
]

CATEGORICAL_FEATURES = [
    "position_group",
    "cleaned_comp",
    "season",
]

EDA_NUMERIC_COLUMNS = [
    RAW_TARGET,
    TARGET,
    "Age",
    "Min",
    "90s",
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "shots_on_target_per90",
    "crosses_per90",
    "interceptions_per90",
    "tackles_won_per90",
    "contract_years_remaining",
    "days_since_last_transfer",
    "transfer_count_before_valuation",
]


def ensure_dirs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_MODELING_DATASET.parent.mkdir(parents=True, exist_ok=True)


def clean_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    numeric_columns = sorted(set(NUMERIC_FEATURES + EDA_NUMERIC_COLUMNS + [RAW_TARGET, TARGET]))
    df = clean_numeric_columns(df, numeric_columns)
    return df


def save_plot(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def run_eda(df: pd.DataFrame) -> dict[str, object]:
    missingness = (
        df.isna()
        .sum()
        .rename("missing_count")
        .to_frame()
        .assign(missing_pct=lambda x: x["missing_count"] / len(df))
        .sort_values(["missing_count", "missing_pct"], ascending=False)
    )
    missingness.to_csv(TABLES_DIR / "missingness.csv")

    group_counts = []
    for column in ["season", "cleaned_comp", "position_group", "contract_missing", "minutes_bucket"]:
        if column in df.columns:
            counts = df[column].value_counts(dropna=False).rename_axis(column).reset_index(name="rows")
            counts.to_csv(TABLES_DIR / f"{column}_counts.csv", index=False)
            group_counts.append((column, counts))

    target_by_group_parts = []
    for column in ["season", "cleaned_comp", "position_group", "minutes_bucket"]:
        if column in df.columns:
            grouped = (
                df.groupby(column, dropna=False)[RAW_TARGET]
                .agg(["count", "median", "mean"])
                .reset_index()
                .assign(group_column=column)
            )
            target_by_group_parts.append(grouped)

    if target_by_group_parts:
        pd.concat(target_by_group_parts, ignore_index=True).to_csv(
            TABLES_DIR / "market_value_by_group.csv",
            index=False,
        )

    correlations = df[[column for column in EDA_NUMERIC_COLUMNS if column in df.columns]].corr(numeric_only=True)
    correlations.to_csv(TABLES_DIR / "numeric_correlations.csv")
    if TARGET in correlations.columns:
        correlations[TARGET].sort_values(ascending=False).to_csv(TABLES_DIR / "target_correlations.csv")

    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(9, 5))
    sns.histplot(df[RAW_TARGET].dropna(), bins=60)
    plt.title("Market Value Distribution")
    plt.xlabel("Market value EUR")
    save_plot(FIGURES_DIR / "market_value_distribution.png")

    plt.figure(figsize=(9, 5))
    sns.histplot(df[TARGET].dropna(), bins=60)
    plt.title("Log Market Value Distribution")
    plt.xlabel("log1p(market value EUR)")
    save_plot(FIGURES_DIR / "log_market_value_distribution.png")

    plt.figure(figsize=(10, 5))
    order = df.groupby("cleaned_comp")[RAW_TARGET].median().sort_values(ascending=False).index
    sns.boxplot(data=df, x="cleaned_comp", y=TARGET, order=order)
    plt.title("Log Market Value By League")
    plt.xlabel("League")
    plt.ylabel("log1p(market value EUR)")
    plt.xticks(rotation=25, ha="right")
    save_plot(FIGURES_DIR / "log_market_value_by_league.png")

    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x="position_group", y=TARGET, order=["DF", "MF", "FW", "GK"])
    plt.title("Log Market Value By Position Group")
    plt.xlabel("Position group")
    plt.ylabel("log1p(market value EUR)")
    save_plot(FIGURES_DIR / "log_market_value_by_position.png")

    plt.figure(figsize=(8, 5))
    sns.scatterplot(
        data=df.sample(min(len(df), 2500), random_state=42),
        x="contract_years_remaining",
        y=TARGET,
        hue="position_group",
        alpha=0.55,
    )
    plt.title("Contract Years Remaining Vs Log Market Value")
    plt.xlabel("Contract years remaining")
    plt.ylabel("log1p(market value EUR)")
    save_plot(FIGURES_DIR / "contract_years_vs_log_market_value.png")

    if not correlations.empty:
        plt.figure(figsize=(11, 8))
        sns.heatmap(correlations, cmap="vlag", center=0, linewidths=0.2)
        plt.title("Numeric Feature Correlations")
        save_plot(FIGURES_DIR / "numeric_correlation_heatmap.png")

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_row_ids": int(df["row_id"].duplicated().sum()) if "row_id" in df.columns else None,
        "target_missing": int(df[TARGET].isna().sum()),
        "raw_target_missing": int(df[RAW_TARGET].isna().sum()),
        "contract_missing_rows": int((df["contract_missing"] == 1).sum()) if "contract_missing" in df.columns else None,
        "low_minutes_rows": int((df["Min"] < 900).sum()) if "Min" in df.columns else None,
    }


def make_modeling_dataset(df: pd.DataFrame, min_minutes: int) -> pd.DataFrame:
    required = [TARGET, RAW_TARGET, "season", *NUMERIC_FEATURES, *CATEGORICAL_FEATURES]
    missing_columns = [column for column in required if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required modeling columns: {missing_columns}")

    model_df = df.copy()
    model_df = model_df[model_df[TARGET].notna() & model_df[RAW_TARGET].notna()]
    model_df = model_df[model_df["season"].isin(TRAIN_SEASONS + TEST_SEASONS)]
    model_df = model_df[model_df["Min"].fillna(0) >= min_minutes]

    for column in CATEGORICAL_FEATURES:
        model_df[column] = model_df[column].fillna("Unknown").astype(str)

    model_df.to_csv(DEFAULT_MODELING_DATASET, index=False)
    return model_df


def make_preprocessor() -> ColumnTransformer:
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", encoder),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def evaluate_model(name: str, model: Pipeline, X: pd.DataFrame, y: pd.Series, split: str) -> dict[str, float | str]:
    predictions = model.predict(X)
    rmse = math.sqrt(mean_squared_error(y, predictions))
    return {
        "model": name,
        "split": split,
        "rows": len(y),
        "rmse_log": rmse,
        "mae_log": mean_absolute_error(y, predictions),
        "r2": r2_score(y, predictions),
    }


def run_models(model_df: pd.DataFrame) -> pd.DataFrame:
    train_df = model_df[model_df["season"].isin(TRAIN_SEASONS)].copy()
    test_df = model_df[model_df["season"].isin(TEST_SEASONS)].copy()

    if train_df.empty or test_df.empty:
        raise ValueError("Train/test split produced an empty train or test set.")

    X_train = train_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train_df[TARGET]
    X_test = test_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test_df[TARGET]

    models: list[tuple[str, Pipeline]] = [
        ("mean_baseline", Pipeline(steps=[("model", DummyRegressor(strategy="mean"))])),
        ("linear_regression", Pipeline(steps=[("preprocess", make_preprocessor()), ("model", LinearRegression())])),
        ("ridge_alpha_1", Pipeline(steps=[("preprocess", make_preprocessor()), ("model", Ridge(alpha=1.0))])),
        ("ridge_alpha_10", Pipeline(steps=[("preprocess", make_preprocessor()), ("model", Ridge(alpha=10.0))])),
    ]

    metric_rows: list[dict[str, float | str]] = []

    for name, model in models:
        model.fit(X_train, y_train)
        metric_rows.append(evaluate_model(name, model, X_train, y_train, "train"))
        metric_rows.append(evaluate_model(name, model, X_test, y_test, "test"))

        if name.startswith("ridge"):
            save_ridge_coefficients(name, model)

    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(TABLES_DIR / "baseline_model_metrics.csv", index=False)
    return metrics


def save_ridge_coefficients(name: str, model: Pipeline) -> None:
    preprocessor = model.named_steps["preprocess"]
    estimator = model.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    coefficients = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": estimator.coef_,
            "abs_coefficient": np.abs(estimator.coef_),
        }
    ).sort_values("abs_coefficient", ascending=False)
    coefficients.to_csv(TABLES_DIR / f"{name}_coefficients.csv", index=False)


def write_summary(eda_stats: dict[str, object], model_df: pd.DataFrame, metrics: pd.DataFrame, min_minutes: int) -> None:
    best_test = metrics[metrics["split"] == "test"].sort_values("rmse_log").iloc[0]
    lines = [
        "# EDA And Baseline Modeling Summary",
        "",
        "## Dataset",
        "",
        f"- Source rows: {eda_stats['rows']}",
        f"- Source columns: {eda_stats['columns']}",
        f"- Duplicate `row_id` count: {eda_stats['duplicate_row_ids']}",
        f"- Missing log target rows: {eda_stats['target_missing']}",
        f"- Missing raw target rows: {eda_stats['raw_target_missing']}",
        f"- Missing contract rows: {eda_stats['contract_missing_rows']}",
        f"- Rows under 900 minutes: {eda_stats['low_minutes_rows']}",
        "",
        "## Modeling Dataset",
        "",
        f"- Minimum minutes filter: `{min_minutes}`",
        f"- Modeling rows: {len(model_df)}",
        f"- Train seasons: {', '.join(TRAIN_SEASONS)}",
        f"- Test seasons: {', '.join(TEST_SEASONS)}",
        f"- Train rows: {len(model_df[model_df['season'].isin(TRAIN_SEASONS)])}",
        f"- Test rows: {len(model_df[model_df['season'].isin(TEST_SEASONS)])}",
        "",
        "## Best Baseline",
        "",
        f"- Model: `{best_test['model']}`",
        f"- Test RMSE log: {best_test['rmse_log']:.4f}",
        f"- Test MAE log: {best_test['mae_log']:.4f}",
        f"- Test R2: {best_test['r2']:.4f}",
        "",
        "## Generated Files",
        "",
        "- `data/processed/modeling_dataset.csv`",
        "- `reports/tables/missingness.csv`",
        "- `reports/tables/market_value_by_group.csv`",
        "- `reports/tables/numeric_correlations.csv`",
        "- `reports/tables/target_correlations.csv`",
        "- `reports/tables/baseline_model_metrics.csv`",
        "- `reports/tables/ridge_alpha_1_coefficients.csv`",
        "- `reports/tables/ridge_alpha_10_coefficients.csv`",
        "- `reports/figures/*.png`",
    ]
    (REPORTS_DIR / "eda_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EDA and baseline modeling.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--min-minutes", type=int, default=900)
    args = parser.parse_args()

    ensure_dirs()
    df = load_data(args.input)
    eda_stats = run_eda(df)
    model_df = make_modeling_dataset(df, min_minutes=args.min_minutes)
    metrics = run_models(model_df)
    write_summary(eda_stats, model_df, metrics, min_minutes=args.min_minutes)

    print(f"Source rows: {len(df)}")
    print(f"Modeling rows after Min >= {args.min_minutes}: {len(model_df)}")
    print("Baseline metrics:")
    print(metrics.to_string(index=False))
    print(f"Wrote summary: {REPORTS_DIR / 'eda_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
