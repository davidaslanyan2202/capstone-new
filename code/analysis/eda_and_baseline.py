#!/usr/bin/env python3
"""Run final EDA, model comparison, and report artifact generation.

Input:
    data/processed/player_season_analytics.csv

Outputs:
    data/processed/modeling_dataset.csv
    reports/generated/analysis_summary.md
    reports/generated/final_report.md
    reports/generated/tables/*.csv
    reports/generated/figures/*.png
    paper/final/figures/*.png
"""

from __future__ import annotations

import argparse
import math
from shutil import copy2
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "data" / "processed" / "player_season_analytics.csv"
DEFAULT_MODELING_DATASET = REPO_ROOT / "data" / "processed" / "modeling_dataset.csv"
REPORTS_DIR = REPO_ROOT / "reports" / "generated"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
SUMMARY_PATH = REPORTS_DIR / "analysis_summary.md"
GENERATED_REPORT_PATH = REPORTS_DIR / "final_report.md"
PAPER_FINAL_FIGURES_DIR = REPO_ROOT / "paper" / "final" / "figures"

TARGET = "log_market_value_eur"
RAW_TARGET = "market_value_eur"
TRAIN_SEASONS = ["21/22", "22/23"]
TEST_SEASONS = ["23/24"]
POSITION_GROUPS = ["DF", "MF", "FW"]
DEFAULT_MIN_MINUTES = 300
MAX_MARKET_VALUE_DAYS_FROM_VALUATION = 120

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
    "contract_expired",
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
    "contract_expired",
    "market_value_days_from_valuation",
    "market_value_stale",
    "days_since_last_transfer",
    "transfer_count_before_valuation",
]

CONTRACT_AND_TRANSFER_FEATURES = [
    "contract_years_remaining",
    "contract_expired",
    "contract_missing",
    "days_since_last_transfer",
    "transfer_count_before_valuation",
    "loan_count_before_valuation",
]


def ensure_dirs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_FINAL_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
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


def encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def make_linear_preprocessor(
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> ColumnTransformer:
    numeric_features = numeric_features or NUMERIC_FEATURES
    categorical_features = categorical_features or CATEGORICAL_FEATURES
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", encoder()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )


def make_tree_preprocessor(
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> ColumnTransformer:
    numeric_features = numeric_features or NUMERIC_FEATURES
    categorical_features = categorical_features or CATEGORICAL_FEATURES
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", encoder()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )


def model_specs(
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> list[tuple[str, Pipeline]]:
    numeric_features = numeric_features or NUMERIC_FEATURES
    categorical_features = categorical_features or CATEGORICAL_FEATURES
    return [
        ("mean_baseline", Pipeline(steps=[("model", DummyRegressor(strategy="mean"))])),
        (
            "linear_regression",
            Pipeline(
                steps=[
                    ("preprocess", make_linear_preprocessor(numeric_features, categorical_features)),
                    ("model", LinearRegression()),
                ]
            ),
        ),
        (
            "ridge_alpha_1",
            Pipeline(
                steps=[
                    ("preprocess", make_linear_preprocessor(numeric_features, categorical_features)),
                    ("model", Ridge(alpha=1.0)),
                ]
            ),
        ),
        (
            "hist_gradient_boosting",
            Pipeline(
                steps=[
                    ("preprocess", make_tree_preprocessor(numeric_features, categorical_features)),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            random_state=42,
                            max_iter=300,
                            learning_rate=0.05,
                            l2_regularization=0.01,
                        ),
                    ),
                ]
            ),
        ),
    ]


def make_modeling_dataset(
    df: pd.DataFrame,
    min_minutes: int,
    *,
    output_path: Path | None = DEFAULT_MODELING_DATASET,
    in_window_only: bool = False,
) -> pd.DataFrame:
    required = [TARGET, RAW_TARGET, "season", *NUMERIC_FEATURES, *CATEGORICAL_FEATURES]
    missing_columns = [column for column in required if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required modeling columns: {missing_columns}")

    model_df = df.copy()
    if "market_value_stale" in model_df.columns:
        model_df = model_df[model_df["market_value_stale"].fillna(0) == 0]
    if "market_value_days_from_valuation" in model_df.columns:
        model_df = model_df[
            model_df["market_value_days_from_valuation"].isna()
            | (model_df["market_value_days_from_valuation"] <= MAX_MARKET_VALUE_DAYS_FROM_VALUATION)
        ]
    if in_window_only and "market_value_in_window" in model_df.columns:
        model_df = model_df[model_df["market_value_in_window"].fillna(0) == 1]
    model_df = model_df[model_df[TARGET].notna() & model_df[RAW_TARGET].notna()]
    model_df = model_df[model_df["season"].isin(TRAIN_SEASONS + TEST_SEASONS)]
    model_df = model_df[model_df["Min"].fillna(0) >= min_minutes]

    for column in CATEGORICAL_FEATURES:
        model_df[column] = model_df[column].fillna("Unknown").astype(str)

    if output_path is not None:
        model_df.to_csv(output_path, index=False)
    return model_df


def run_eda(df: pd.DataFrame, min_minutes: int) -> dict[str, object]:
    missingness = (
        df.isna()
        .sum()
        .rename("missing_count")
        .to_frame()
        .assign(missing_pct=lambda x: x["missing_count"] / len(df))
        .sort_values(["missing_count", "missing_pct"], ascending=False)
    )
    missingness.to_csv(TABLES_DIR / "missingness.csv")

    for column in ["season", "cleaned_comp", "position_group", "contract_missing", "minutes_bucket"]:
        if column in df.columns:
            counts = df[column].value_counts(dropna=False).rename_axis(column).reset_index(name="rows")
            counts.to_csv(TABLES_DIR / f"{column}_counts.csv", index=False)

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
    position_order = [group for group in ["DF", "MF", "FW", "GK"] if group in set(df["position_group"].dropna())]
    sns.boxplot(data=df, x="position_group", y=TARGET, order=position_order)
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
        "rows_under_min_minutes": int((df["Min"].fillna(0) < min_minutes).sum()) if "Min" in df.columns else None,
    }


def feature_columns(
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> list[str]:
    return (numeric_features or NUMERIC_FEATURES) + (categorical_features or CATEGORICAL_FEATURES)


def split_xy(
    model_df: pd.DataFrame,
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df = model_df[model_df["season"].isin(TRAIN_SEASONS)].copy()
    test_df = model_df[model_df["season"].isin(TEST_SEASONS)].copy()

    if train_df.empty or test_df.empty:
        raise ValueError("Train/test split produced an empty train or test set.")

    columns = feature_columns(numeric_features, categorical_features)
    return (
        train_df,
        test_df,
        train_df[columns],
        test_df[columns],
    )


def evaluate_predictions(
    *,
    model_name: str,
    split: str,
    scope: str,
    position_group: str,
    cleaned_comp: str,
    y_log: pd.Series,
    y_raw: pd.Series,
    pred_log: np.ndarray,
) -> dict[str, object]:
    pred_raw = np.expm1(pred_log).clip(min=0)
    y_raw_array = y_raw.to_numpy()
    return {
        "scope": scope,
        "position_group": position_group,
        "cleaned_comp": cleaned_comp,
        "model": model_name,
        "split": split,
        "rows": len(y_log),
        "rmse_log": math.sqrt(mean_squared_error(y_log, pred_log)),
        "mae_log": mean_absolute_error(y_log, pred_log),
        "r2": r2_score(y_log, pred_log),
        "rmse_eur": math.sqrt(mean_squared_error(y_raw_array, pred_raw)),
        "mae_eur": mean_absolute_error(y_raw_array, pred_raw),
    }


def make_prediction_rows(
    *,
    df_part: pd.DataFrame,
    model_name: str,
    split: str,
    scope: str,
    pred_log: np.ndarray,
) -> pd.DataFrame:
    identity_columns = [
        "row_id",
        "Player",
        "position_group",
        "cleaned_comp",
        "season",
        "Min",
        RAW_TARGET,
        TARGET,
    ]
    available_columns = [column for column in identity_columns if column in df_part.columns]
    predictions = df_part[available_columns].copy()
    predictions["scope"] = scope
    predictions["model"] = model_name
    predictions["split"] = split
    predictions["pred_log_market_value_eur"] = pred_log
    predictions["pred_market_value_eur"] = np.expm1(pred_log).clip(min=0)
    predictions["residual_log"] = predictions[TARGET] - predictions["pred_log_market_value_eur"]
    predictions["abs_error_log"] = predictions["residual_log"].abs()
    predictions["residual_eur"] = predictions[RAW_TARGET] - predictions["pred_market_value_eur"]
    predictions["abs_error_eur"] = predictions["residual_eur"].abs()
    return predictions


def fit_model_set(
    model_df: pd.DataFrame,
    *,
    scope: str,
    position_group: str,
    cleaned_comp: str = "ALL",
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Pipeline]]:
    train_df, test_df, X_train, X_test = split_xy(model_df, numeric_features, categorical_features)
    return fit_model_set_on_frames(
        train_df,
        test_df,
        X_train,
        X_test,
        scope=scope,
        position_group=position_group,
        cleaned_comp=cleaned_comp,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )


def fit_model_set_on_frames(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    *,
    scope: str,
    position_group: str,
    cleaned_comp: str = "ALL",
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Pipeline]]:
    y_train = train_df[TARGET]
    y_test = test_df[TARGET]

    metric_rows: list[dict[str, object]] = []
    prediction_parts: list[pd.DataFrame] = []
    fitted_models: dict[str, Pipeline] = {}

    for name, model in model_specs(numeric_features, categorical_features):
        model.fit(X_train, y_train)
        fitted_models[name] = model

        for split, df_part, X_part, y_part in [
            ("train", train_df, X_train, y_train),
            ("test", test_df, X_test, y_test),
        ]:
            predictions = model.predict(X_part)
            metric_rows.append(
                evaluate_predictions(
                    model_name=name,
                    split=split,
                    scope=scope,
                    position_group=position_group,
                    cleaned_comp=cleaned_comp,
                    y_log=y_part,
                    y_raw=df_part[RAW_TARGET],
                    pred_log=predictions,
                )
            )
            prediction_parts.append(
                make_prediction_rows(
                    df_part=df_part,
                    model_name=name,
                    split=split,
                    scope=scope,
                    pred_log=predictions,
                )
            )

    return pd.DataFrame(metric_rows), pd.concat(prediction_parts, ignore_index=True), fitted_models


def run_models(
    model_df: pd.DataFrame,
    *,
    include_position_models: bool,
    include_league_models: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Pipeline]]:
    global_metrics, global_predictions, fitted_models = fit_model_set(
        model_df,
        scope="global",
        position_group="ALL",
    )
    metric_parts = [global_metrics]
    prediction_parts = [global_predictions]

    if include_position_models:
        for position_group in POSITION_GROUPS:
            position_df = model_df[model_df["position_group"] == position_group].copy()
            train_rows = position_df["season"].isin(TRAIN_SEASONS).sum()
            test_rows = position_df["season"].isin(TEST_SEASONS).sum()
            if train_rows == 0 or test_rows == 0:
                raise ValueError(f"Position group {position_group} has empty train or test rows.")

            metrics, predictions, _ = fit_model_set(
                position_df,
                scope="position_specific",
                position_group=position_group,
            )
            metric_parts.append(metrics)
            prediction_parts.append(predictions)

    if include_league_models:
        league_groups = sorted(model_df["cleaned_comp"].dropna().unique())
        for league in league_groups:
            league_df = model_df[model_df["cleaned_comp"] == league].copy()
            train_rows = league_df["season"].isin(TRAIN_SEASONS).sum()
            test_rows = league_df["season"].isin(TEST_SEASONS).sum()
            if train_rows == 0 or test_rows == 0:
                raise ValueError(f"League {league} has empty train or test rows.")

            metrics, predictions, _ = fit_model_set(
                league_df,
                scope="league_specific",
                position_group="ALL",
                cleaned_comp=league,
            )
            metric_parts.append(metrics)
            prediction_parts.append(predictions)

    metrics = pd.concat(metric_parts, ignore_index=True)
    predictions = pd.concat(prediction_parts, ignore_index=True)

    metrics.to_csv(TABLES_DIR / "model_metrics.csv", index=False)
    metrics.to_csv(TABLES_DIR / "baseline_model_metrics.csv", index=False)
    predictions.to_csv(TABLES_DIR / "model_predictions.csv", index=False)
    return metrics, predictions, fitted_models


def save_ridge_coefficients(model: Pipeline) -> pd.DataFrame:
    preprocessor = model.named_steps["preprocess"]
    estimator = model.named_steps["model"]
    coefficients = pd.DataFrame(
        {
            "scope": "global",
            "model": "ridge_alpha_1",
            "feature": preprocessor.get_feature_names_out(),
            "importance": estimator.coef_,
            "abs_importance": np.abs(estimator.coef_),
            "importance_type": "standardized_coefficient",
        }
    ).sort_values("abs_importance", ascending=False)
    coefficients.to_csv(TABLES_DIR / "ridge_alpha_1_coefficients.csv", index=False)
    return coefficients


def save_permutation_importance(
    model: Pipeline,
    model_df: pd.DataFrame,
    *,
    sample_size: int = 1000,
) -> pd.DataFrame:
    test_df = model_df[model_df["season"].isin(TEST_SEASONS)].copy()
    if len(test_df) > sample_size:
        test_df = test_df.sample(sample_size, random_state=42)

    X_test = test_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test_df[TARGET]
    result = permutation_importance(
        model,
        X_test,
        y_test,
        n_repeats=8,
        random_state=42,
        scoring="neg_root_mean_squared_error",
        n_jobs=1,
    )
    importance = pd.DataFrame(
        {
            "scope": "global",
            "model": "hist_gradient_boosting",
            "feature": NUMERIC_FEATURES + CATEGORICAL_FEATURES,
            "importance": result.importances_mean,
            "importance_std": result.importances_std,
            "abs_importance": np.abs(result.importances_mean),
            "importance_type": "permutation_rmse_drop",
        }
    ).sort_values("importance", ascending=False)
    importance.to_csv(TABLES_DIR / "hist_gradient_boosting_permutation_importance.csv", index=False)
    return importance


def save_feature_importance(fitted_models: dict[str, Pipeline], model_df: pd.DataFrame) -> pd.DataFrame:
    parts = [save_ridge_coefficients(fitted_models["ridge_alpha_1"])]
    parts.append(save_permutation_importance(fitted_models["hist_gradient_boosting"], model_df))
    feature_importance = pd.concat(parts, ignore_index=True, sort=False)
    feature_importance.to_csv(TABLES_DIR / "feature_importance.csv", index=False)
    return feature_importance


def save_error_by_group(predictions: pd.DataFrame, best_model_name: str) -> pd.DataFrame:
    best_predictions = predictions[
        (predictions["scope"] == "global")
        & (predictions["model"] == best_model_name)
        & (predictions["split"] == "test")
    ].copy()
    group_rows = []
    for group_column in ["cleaned_comp", "position_group", "season"]:
        grouped = (
            best_predictions.groupby(group_column, dropna=False)
            .agg(
                rows=("abs_error_log", "size"),
                mae_log=("abs_error_log", "mean"),
                rmse_log=("residual_log", lambda x: math.sqrt(np.mean(np.square(x)))),
                mae_eur=("abs_error_eur", "mean"),
            )
            .reset_index()
            .rename(columns={group_column: "group_value"})
        )
        grouped["group_column"] = group_column
        group_rows.append(grouped)

    error_by_group = pd.concat(group_rows, ignore_index=True)
    error_by_group.to_csv(TABLES_DIR / "error_by_group.csv", index=False)
    return error_by_group


def summarize_prediction_errors(prediction_rows: pd.DataFrame) -> dict[str, float | int]:
    return {
        "rows": len(prediction_rows),
        "mae_log": prediction_rows["abs_error_log"].mean(),
        "rmse_log": math.sqrt(np.mean(np.square(prediction_rows["residual_log"]))),
        "mae_eur": prediction_rows["abs_error_eur"].mean(),
    }


def save_specialized_model_comparison(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    comparisons = [
        ("position_group", "position_specific", POSITION_GROUPS),
        ("cleaned_comp", "league_specific", sorted(predictions["cleaned_comp"].dropna().unique())),
    ]
    model_names = ["ridge_alpha_1", "hist_gradient_boosting"]

    for group_column, local_scope, group_values in comparisons:
        for group_value in group_values:
            for model_name in model_names:
                global_rows = predictions[
                    (predictions["scope"] == "global")
                    & (predictions["model"] == model_name)
                    & (predictions["split"] == "test")
                    & (predictions[group_column] == group_value)
                ]
                local_rows = predictions[
                    (predictions["scope"] == local_scope)
                    & (predictions["model"] == model_name)
                    & (predictions["split"] == "test")
                    & (predictions[group_column] == group_value)
                ]
                if global_rows.empty or local_rows.empty:
                    continue

                global_metrics = summarize_prediction_errors(global_rows)
                local_metrics = summarize_prediction_errors(local_rows)
                rows.append(
                    {
                        "group_column": group_column,
                        "group_value": group_value,
                        "model": model_name,
                        "rows": local_metrics["rows"],
                        "global_rmse_log": global_metrics["rmse_log"],
                        "specialized_rmse_log": local_metrics["rmse_log"],
                        "rmse_log_delta_specialized_minus_global": (
                            local_metrics["rmse_log"] - global_metrics["rmse_log"]
                        ),
                        "global_mae_log": global_metrics["mae_log"],
                        "specialized_mae_log": local_metrics["mae_log"],
                        "mae_log_delta_specialized_minus_global": (
                            local_metrics["mae_log"] - global_metrics["mae_log"]
                        ),
                        "global_mae_eur": global_metrics["mae_eur"],
                        "specialized_mae_eur": local_metrics["mae_eur"],
                    }
                )

    comparison = pd.DataFrame(rows).sort_values(["group_column", "group_value", "model"])
    comparison.to_csv(TABLES_DIR / "specialized_model_comparison.csv", index=False)
    return comparison


def save_bootstrap_intervals(
    predictions: pd.DataFrame,
    best_model_name: str,
    *,
    n_bootstrap: int = 500,
) -> pd.DataFrame:
    best_predictions = predictions[
        (predictions["scope"] == "global")
        & (predictions["model"] == best_model_name)
        & (predictions["split"] == "test")
    ].copy()
    if best_predictions.empty:
        intervals = pd.DataFrame()
        intervals.to_csv(TABLES_DIR / "bootstrap_intervals.csv", index=False)
        return intervals

    rng = np.random.default_rng(42)
    rows: list[dict[str, object]] = []
    indices = np.arange(len(best_predictions))
    residuals = best_predictions["residual_log"].to_numpy()
    abs_errors = best_predictions["abs_error_log"].to_numpy()

    bootstrap_rmse = []
    bootstrap_mae = []
    for _ in range(n_bootstrap):
        sample_indices = rng.choice(indices, size=len(indices), replace=True)
        bootstrap_rmse.append(math.sqrt(np.mean(np.square(residuals[sample_indices]))))
        bootstrap_mae.append(np.mean(abs_errors[sample_indices]))

    for metric, values in [("rmse_log", bootstrap_rmse), ("mae_log", bootstrap_mae)]:
        rows.append(
            {
                "model": best_model_name,
                "metric": metric,
                "estimate": (
                    math.sqrt(np.mean(np.square(residuals)))
                    if metric == "rmse_log"
                    else np.mean(abs_errors)
                ),
                "ci_lower_95": np.quantile(values, 0.025),
                "ci_upper_95": np.quantile(values, 0.975),
                "bootstrap_samples": n_bootstrap,
            }
        )

    intervals = pd.DataFrame(rows)
    intervals.to_csv(TABLES_DIR / "bootstrap_intervals.csv", index=False)
    return intervals


def save_rolling_season_validation(model_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    seasons = sorted(model_df["season"].dropna().unique())
    columns = feature_columns()

    for index in range(1, len(seasons)):
        train_seasons = seasons[:index]
        test_season = seasons[index]
        train_df = model_df[model_df["season"].isin(train_seasons)].copy()
        test_df = model_df[model_df["season"] == test_season].copy()
        if train_df.empty or test_df.empty:
            continue

        metrics, _, _ = fit_model_set_on_frames(
            train_df,
            test_df,
            train_df[columns],
            test_df[columns],
            scope="rolling_season",
            position_group="ALL",
        )
        test_metrics = metrics[metrics["split"] == "test"].copy()
        test_metrics["train_seasons"] = ",".join(train_seasons)
        test_metrics["test_season"] = test_season
        rows.append(test_metrics)

    rolling = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    rolling.to_csv(TABLES_DIR / "rolling_season_validation.csv", index=False)
    return rolling


def save_model_sensitivity(source_df: pd.DataFrame, base_min_minutes: int) -> pd.DataFrame:
    variants = [
        {
            "variant": f"all_features_min_{base_min_minutes}",
            "min_minutes": base_min_minutes,
            "in_window_only": False,
            "numeric_features": NUMERIC_FEATURES,
            "feature_set": "all_features",
        },
        {
            "variant": f"no_contract_transfer_features_min_{base_min_minutes}",
            "min_minutes": base_min_minutes,
            "in_window_only": False,
            "numeric_features": [
                feature for feature in NUMERIC_FEATURES if feature not in CONTRACT_AND_TRANSFER_FEATURES
            ],
            "feature_set": "no_contract_transfer_features",
        },
        {
            "variant": f"in_window_targets_min_{base_min_minutes}",
            "min_minutes": base_min_minutes,
            "in_window_only": True,
            "numeric_features": NUMERIC_FEATURES,
            "feature_set": "all_features",
        },
        {
            "variant": "all_features_min_900",
            "min_minutes": 900,
            "in_window_only": False,
            "numeric_features": NUMERIC_FEATURES,
            "feature_set": "all_features",
        },
    ]

    rows: list[pd.DataFrame] = []
    for variant in variants:
        model_df = make_modeling_dataset(
            source_df,
            int(variant["min_minutes"]),
            output_path=None,
            in_window_only=bool(variant["in_window_only"]),
        )
        if model_df.empty:
            continue

        metrics, _, _ = fit_model_set(
            model_df,
            scope="sensitivity",
            position_group="ALL",
            numeric_features=list(variant["numeric_features"]),
        )
        test_metrics = metrics[metrics["split"] == "test"].copy()
        test_metrics["variant"] = variant["variant"]
        test_metrics["min_minutes"] = variant["min_minutes"]
        test_metrics["target_filter"] = "in_window_only" if variant["in_window_only"] else "max_120_days"
        test_metrics["feature_set"] = variant["feature_set"]
        rows.append(test_metrics)

    sensitivity = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    sensitivity.to_csv(TABLES_DIR / "model_sensitivity.csv", index=False)
    return sensitivity


def plot_model_diagnostics(metrics: pd.DataFrame, predictions: pd.DataFrame, best_model_name: str) -> None:
    test_metrics = metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")].copy()
    test_metrics = test_metrics.sort_values("rmse_log")

    plt.figure(figsize=(9, 5))
    sns.barplot(data=test_metrics, x="model", y="rmse_log", color="#4C78A8")
    plt.title("Global Model Comparison On 2023/24 Test Season")
    plt.xlabel("Model")
    plt.ylabel("Test RMSE log")
    plt.xticks(rotation=20, ha="right")
    save_plot(FIGURES_DIR / "model_comparison_test_rmse.png")

    best_predictions = predictions[
        (predictions["scope"] == "global")
        & (predictions["model"] == best_model_name)
        & (predictions["split"] == "test")
    ].copy()

    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=best_predictions,
        x=TARGET,
        y="pred_log_market_value_eur",
        hue="position_group",
        alpha=0.6,
    )
    min_value = min(best_predictions[TARGET].min(), best_predictions["pred_log_market_value_eur"].min())
    max_value = max(best_predictions[TARGET].max(), best_predictions["pred_log_market_value_eur"].max())
    plt.plot([min_value, max_value], [min_value, max_value], color="#333333", linestyle="--", linewidth=1)
    plt.title(f"Predicted Vs Actual Log Market Value ({best_model_name})")
    plt.xlabel("Actual log1p(market value EUR)")
    plt.ylabel("Predicted log1p(market value EUR)")
    save_plot(FIGURES_DIR / "predicted_vs_actual_best_model.png")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.boxplot(data=best_predictions, x="cleaned_comp", y="residual_log", ax=axes[0])
    axes[0].axhline(0, color="#333333", linestyle="--", linewidth=1)
    axes[0].set_title("Residuals By League")
    axes[0].set_xlabel("League")
    axes[0].set_ylabel("Actual - predicted log value")
    axes[0].tick_params(axis="x", rotation=25)

    sns.boxplot(data=best_predictions, x="position_group", y="residual_log", ax=axes[1], order=POSITION_GROUPS)
    axes[1].axhline(0, color="#333333", linestyle="--", linewidth=1)
    axes[1].set_title("Residuals By Position")
    axes[1].set_xlabel("Position group")
    axes[1].set_ylabel("Actual - predicted log value")
    save_plot(FIGURES_DIR / "residuals_by_league_position.png")

    position_metrics = metrics[(metrics["scope"] == "position_specific") & (metrics["split"] == "test")].copy()
    if not position_metrics.empty:
        position_metrics = position_metrics[position_metrics["model"].isin(["ridge_alpha_1", "hist_gradient_boosting"])]
        plt.figure(figsize=(9, 5))
        sns.barplot(
            data=position_metrics,
            x="position_group",
            y="rmse_log",
            hue="model",
            order=POSITION_GROUPS,
        )
        plt.title("Position-Specific Model Comparison")
        plt.xlabel("Position group")
        plt.ylabel("Test RMSE log")
        save_plot(FIGURES_DIR / "position_model_comparison.png")

    league_metrics = metrics[(metrics["scope"] == "league_specific") & (metrics["split"] == "test")].copy()
    if not league_metrics.empty:
        league_metrics = league_metrics[league_metrics["model"].isin(["ridge_alpha_1", "hist_gradient_boosting"])]
        plt.figure(figsize=(11, 5))
        sns.barplot(
            data=league_metrics,
            x="cleaned_comp",
            y="rmse_log",
            hue="model",
            order=sorted(league_metrics["cleaned_comp"].unique()),
        )
        plt.title("League-Specific Model Comparison")
        plt.xlabel("League")
        plt.ylabel("Test RMSE log")
        plt.xticks(rotation=25, ha="right")
        save_plot(FIGURES_DIR / "league_model_comparison.png")


def plot_specialized_vs_global(specialized_comparison: pd.DataFrame) -> None:
    if specialized_comparison.empty:
        return

    plot_df = specialized_comparison[
        specialized_comparison["model"] == "hist_gradient_boosting"
    ].copy()
    plot_df["comparison_label"] = plot_df["group_column"].map(
        {"position_group": "Position", "cleaned_comp": "League"}
    ) + ": " + plot_df["group_value"].astype(str)
    plot_df = plot_df.sort_values("rmse_log_delta_specialized_minus_global")

    plt.figure(figsize=(11, 6))
    colors = np.where(plot_df["rmse_log_delta_specialized_minus_global"] <= 0, "#2E7D32", "#B23B3B")
    plt.barh(plot_df["comparison_label"], plot_df["rmse_log_delta_specialized_minus_global"], color=colors)
    plt.axvline(0, color="#333333", linewidth=1)
    plt.title("Specialized Vs Global Hist-Gradient Boosting")
    plt.xlabel("Specialized RMSE log minus global RMSE log")
    plt.ylabel("Segment")
    save_plot(FIGURES_DIR / "specialized_vs_global_rmse.png")


def format_eur(value: float) -> str:
    return f"{value:,.0f}"


def dataframe_to_markdown(df: pd.DataFrame, *, floatfmt: str = ".4f") -> str:
    """Render a compact GitHub-style Markdown table without optional dependencies."""
    if df.empty:
        return "_No rows._"

    display_df = df.copy()
    for column in display_df.columns:
        if pd.api.types.is_float_dtype(display_df[column]):
            display_df[column] = display_df[column].map(lambda value: format(value, floatfmt))
        else:
            display_df[column] = display_df[column].astype(str)

    headers = list(display_df.columns)
    rows = display_df.values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def write_summary(
    eda_stats: dict[str, object],
    model_df: pd.DataFrame,
    metrics: pd.DataFrame,
    feature_importance: pd.DataFrame,
    specialized_comparison: pd.DataFrame,
    sensitivity: pd.DataFrame,
    bootstrap_intervals: pd.DataFrame,
    min_minutes: int,
) -> None:
    global_test = metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")]
    best_test = global_test.sort_values("rmse_log").iloc[0]
    train_rows = len(model_df[model_df["season"].isin(TRAIN_SEASONS)])
    test_rows = len(model_df[model_df["season"].isin(TEST_SEASONS)])
    position_counts = model_df["position_group"].value_counts().reindex(POSITION_GROUPS).fillna(0).astype(int)

    hgb_importance = feature_importance[
        (feature_importance["model"] == "hist_gradient_boosting")
        & (feature_importance["importance_type"] == "permutation_rmse_drop")
    ].copy()
    top_hgb_features = hgb_importance.head(6)["feature"].tolist()
    if specialized_comparison.empty:
        improved_segments = 0
        total_segments = 0
    else:
        hgb_specialized = specialized_comparison[
            specialized_comparison["model"] == "hist_gradient_boosting"
        ].copy()
        improved_segments = int((hgb_specialized["rmse_log_delta_specialized_minus_global"] < 0).sum())
        total_segments = len(hgb_specialized)

    lines = [
        "# EDA And Model Comparison Summary",
        "",
        "## Dataset",
        "",
        f"- Source rows: {eda_stats['rows']}",
        f"- Source columns: {eda_stats['columns']}",
        f"- Duplicate `row_id` count: {eda_stats['duplicate_row_ids']}",
        f"- Missing log target rows: {eda_stats['target_missing']}",
        f"- Missing raw target rows: {eda_stats['raw_target_missing']}",
        f"- Missing contract rows: {eda_stats['contract_missing_rows']}",
        f"- Rows under {min_minutes} minutes: {eda_stats['rows_under_min_minutes']}",
        "",
        "## Modeling Dataset",
        "",
        f"- Minimum minutes filter: `{min_minutes}`",
        f"- Modeling rows: {len(model_df)}",
        f"- Train seasons: {', '.join(TRAIN_SEASONS)}",
        f"- Test seasons: {', '.join(TEST_SEASONS)}",
        f"- Train rows: {train_rows}",
        f"- Test rows: {test_rows}",
        f"- Position rows: DF={position_counts['DF']}, MF={position_counts['MF']}, FW={position_counts['FW']}",
        "",
        "## Best Global Model",
        "",
        f"- Model: `{best_test['model']}`",
        f"- Test RMSE log: {best_test['rmse_log']:.4f}",
        f"- Test MAE log: {best_test['mae_log']:.4f}",
        f"- Test R2: {best_test['r2']:.4f}",
        f"- Test MAE EUR: {format_eur(best_test['mae_eur'])}",
        "",
        "## Main Conclusions",
        "",
        f"- The {min_minutes}+ minute filter keeps broad coverage while excluding very small playing-time samples.",
        "- The nonlinear hist-gradient boosting model performs best on the 2023/24 holdout season.",
        "- Age, minutes, contract years remaining, league, and position are consistent valuation signals.",
        f"- Specialized position/league models improve hist-gradient RMSE in {improved_segments} of {total_segments} tested segments.",
        "- Global models remain the main benchmark; specialized models are diagnostics for segment-specific valuation patterns.",
        f"- Top permutation-importance features for the best model: {', '.join(top_hgb_features)}.",
        f"- Sensitivity scenarios tested: {sensitivity['variant'].nunique() if not sensitivity.empty else 0}.",
        f"- Bootstrap uncertainty rows: {len(bootstrap_intervals)}.",
        "",
        "## Generated Files",
        "",
        "- `data/processed/modeling_dataset.csv`",
        "- `reports/generated/final_report.md`",
        "- `reports/generated/tables/model_metrics.csv`",
        "- `reports/generated/tables/error_by_group.csv`",
        "- `reports/generated/tables/feature_importance.csv`",
        "- `reports/generated/tables/specialized_model_comparison.csv`",
        "- `reports/generated/tables/model_sensitivity.csv`",
        "- `reports/generated/tables/bootstrap_intervals.csv`",
        "- `reports/generated/tables/rolling_season_validation.csv`",
        "- `reports/generated/tables/model_predictions.csv`",
        "- `reports/generated/figures/model_comparison_test_rmse.png`",
        "- `reports/generated/figures/predicted_vs_actual_best_model.png`",
        "- `reports/generated/figures/residuals_by_league_position.png`",
        "- `reports/generated/figures/position_model_comparison.png`",
        "- `reports/generated/figures/league_model_comparison.png`",
        "- `reports/generated/figures/specialized_vs_global_rmse.png`",
        "- `paper/final/figures/*.png`",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_report(
    eda_stats: dict[str, object],
    model_df: pd.DataFrame,
    metrics: pd.DataFrame,
    error_by_group: pd.DataFrame,
    feature_importance: pd.DataFrame,
    specialized_comparison: pd.DataFrame,
    sensitivity: pd.DataFrame,
    bootstrap_intervals: pd.DataFrame,
    rolling_validation: pd.DataFrame,
    min_minutes: int,
) -> None:
    global_test = metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")].sort_values("rmse_log")
    best_test = global_test.iloc[0]
    mean_test = global_test[global_test["model"] == "mean_baseline"].iloc[0]
    improvement = 1 - (best_test["rmse_log"] / mean_test["rmse_log"])

    train_rows = len(model_df[model_df["season"].isin(TRAIN_SEASONS)])
    test_rows = len(model_df[model_df["season"].isin(TEST_SEASONS)])
    position_counts = model_df["position_group"].value_counts().reindex(POSITION_GROUPS).fillna(0).astype(int)

    metrics_md = dataframe_to_markdown(global_test[["model", "rows", "rmse_log", "mae_log", "r2", "mae_eur"]])

    position_test = metrics[
        (metrics["scope"] == "position_specific")
        & (metrics["split"] == "test")
        & (metrics["model"].isin(["ridge_alpha_1", "hist_gradient_boosting"]))
    ].copy()
    position_md = dataframe_to_markdown(
        position_test[["position_group", "model", "rows", "rmse_log", "mae_log", "r2"]].sort_values(
            ["position_group", "rmse_log"]
        )
    )

    league_test = metrics[
        (metrics["scope"] == "league_specific")
        & (metrics["split"] == "test")
        & (metrics["model"].isin(["ridge_alpha_1", "hist_gradient_boosting"]))
    ].copy()
    league_md = dataframe_to_markdown(
        league_test[["cleaned_comp", "model", "rows", "rmse_log", "mae_log", "r2"]].sort_values(
            ["cleaned_comp", "rmse_log"]
        )
    )

    specialized_hgb = specialized_comparison[
        specialized_comparison["model"] == "hist_gradient_boosting"
    ].copy()
    specialized_hgb["result"] = np.where(
        specialized_hgb["rmse_log_delta_specialized_minus_global"] < 0,
        "specialized better",
        "global better",
    )
    specialized_md = dataframe_to_markdown(
        specialized_hgb[
            [
                "group_column",
                "group_value",
                "rows",
                "global_rmse_log",
                "specialized_rmse_log",
                "rmse_log_delta_specialized_minus_global",
                "result",
            ]
        ].sort_values(["group_column", "rmse_log_delta_specialized_minus_global"])
    )

    top_features = feature_importance[
        (feature_importance["model"] == "hist_gradient_boosting")
        & (feature_importance["importance_type"] == "permutation_rmse_drop")
    ].head(10)
    top_features_md = dataframe_to_markdown(top_features[["feature", "importance", "importance_std"]])

    group_error_md = dataframe_to_markdown(
        error_by_group.sort_values(["group_column", "mae_log"])[
            ["group_column", "group_value", "rows", "mae_log", "rmse_log", "mae_eur"]
        ]
    )
    sensitivity_md = dataframe_to_markdown(
        sensitivity[
            [
                "variant",
                "model",
                "rows",
                "rmse_log",
                "mae_log",
                "r2",
                "target_filter",
                "feature_set",
            ]
        ].sort_values(["variant", "rmse_log"])
        if not sensitivity.empty
        else sensitivity
    )
    bootstrap_md = dataframe_to_markdown(bootstrap_intervals) if not bootstrap_intervals.empty else "_No rows._"
    rolling_md = dataframe_to_markdown(
        rolling_validation[
            ["train_seasons", "test_season", "model", "rows", "rmse_log", "mae_log", "r2"]
        ].sort_values(["test_season", "rmse_log"])
        if not rolling_validation.empty
        else rolling_validation
    )

    lines = [
        "# A Data-Driven Analysis of Football Players' Transfer Value",
        "",
        "## Abstract",
        "",
        "This project predicts and explains football player market value using season-level performance, league, position, age, transfer-history, and contract features. The final analytics table contains player-season observations from the top five European leagues across 2021/22, 2022/23, and 2023/24. The target is the natural log transform `log1p(market_value_eur)`, which reduces the extreme skew in player valuation. With a minimum playing-time filter of 300 minutes, the modeling dataset contains "
        f"{len(model_df):,} rows, including {train_rows:,} training rows and {test_rows:,} test rows. The best global model is `{best_test['model']}`, with test RMSE log {best_test['rmse_log']:.3f}, MAE log {best_test['mae_log']:.3f}, and R2 {best_test['r2']:.3f}. The results show that market value is predictable from observable football and contract signals, but valuation remains partly driven by unobserved reputation, club strategy, and market context.",
        "",
        "## Introduction",
        "",
        "Transfer values influence recruitment, squad planning, and contract negotiation. However, the process by which performance statistics and contract status translate into market valuation is not fully transparent. This project studies whether football player market values can be predicted from public season-level data and which variables are most informative for that prediction task.",
        "",
        "The main research questions are: how well can market value be predicted from performance and contract data, which variables drive valuation, whether relationships differ by position, and how contract expiry relates to value after controlling for other signals.",
        "",
        "## Literature Review",
        "",
        "Prior work supports the use of Transfermarkt values as a structured proxy for market valuation, while also noting that the values reflect collective market perception rather than direct transaction prices. Studies on football valuation have used econometric models, machine learning, and ensemble methods to estimate player value from age, performance, contract, and contextual variables. The present project follows this applied modeling direction but emphasizes reproducibility, explicit train/test separation by season, and interpretable diagnostics.",
        "",
        "## Methodology",
        "",
        "The analysis uses `data/processed/player_season_analytics.csv` as the final table. Each row represents a player-season/team record. The feature set includes age, minutes, starts, per-90 performance rates, league, season, position group, contract years remaining, missing-contract indicators, and transfer-history counts. The target is `log_market_value_eur`.",
        "",
        f"Players with fewer than {min_minutes} minutes are excluded. This threshold keeps substantially more observations than the earlier 900-minute filter while still removing the smallest samples. The final modeling rows by position are DF={position_counts['DF']:,}, MF={position_counts['MF']:,}, and FW={position_counts['FW']:,}. Models are trained on 2021/22 and 2022/23 and evaluated only on 2023/24.",
        "",
        "The global model comparison includes a mean baseline, ordinary least squares linear regression, ridge regression, and hist-gradient boosting. Separate position-specific and league-specific models are also trained. These specialized models are compared against the global model evaluated on the same subgroup, which shows whether segmentation actually improves predictive accuracy.",
        "",
        "## Results",
        "",
        "### Global Model Metrics",
        "",
        metrics_md,
        "",
        f"The best model improves test RMSE log by {improvement:.1%} relative to the mean baseline. The nonlinear hist-gradient boosting model performs best, indicating that football valuation is not purely linear in the available features.",
        "",
        "### Position-Specific Models",
        "",
        position_md,
        "",
        "The position-specific results are useful for diagnosing how model behavior changes by role. They should be interpreted cautiously because each position model has fewer training examples than the global model.",
        "",
        "### League-Specific Models",
        "",
        league_md,
        "",
        "League-specific models test whether each league has enough distinct valuation structure to justify a separate estimator. These models are especially useful because league context is one of the strongest valuation signals.",
        "",
        "### Global Vs Specialized Models",
        "",
        specialized_md,
        "",
        "Negative deltas mean the specialized model has lower RMSE than the global model on the same subgroup. Positive deltas mean the global model generalizes better, usually because it benefits from a larger training sample.",
        "",
        "### Feature Importance",
        "",
        top_features_md,
        "",
        "Permutation importance for the best nonlinear model highlights context and availability variables such as league, position, age, minutes, and contract status. Ridge coefficients provide a complementary linear view, but neither method should be interpreted as causal evidence.",
        "",
        "### Error Diagnostics",
        "",
        group_error_md,
        "",
        "Residual diagnostics show where the model is more or less reliable across leagues and positions. Large errors remain expected for players whose valuation is affected by reputation, transfer demand, injuries, academy status, or unusual contract situations not captured in the data.",
        "",
        "### Robustness And Sensitivity",
        "",
        sensitivity_md,
        "",
        "The sensitivity table compares the headline setup against variants that remove contract/transfer-history features, require in-window market-value targets, and use a stricter 900-minute playing-time threshold.",
        "",
        "### Bootstrap Uncertainty",
        "",
        bootstrap_md,
        "",
        "Bootstrap intervals resample the 2023/24 test residuals for the best global model and give a simple uncertainty range around headline error metrics.",
        "",
        "### Rolling Season Validation",
        "",
        rolling_md,
        "",
        "Rolling validation is limited by the three available seasons, but it checks whether conclusions are stable when testing 2022/23 after training on 2021/22 and when testing 2023/24 after training on the first two seasons.",
        "",
        "## Analysis and Validation",
        "",
        f"The project meets the predictive objective because all learned global models outperform the mean baseline on the held-out 2023/24 season. The best model explains a meaningful share of variance while maintaining evaluation on a future season, which is stricter than a random row split. The expanded {min_minutes}-minute threshold increases coverage relative to a 900-minute regular-starter filter, but it also introduces noisier low-minute observations. This tradeoff is acceptable for the final project because the goal is broad player valuation coverage rather than only regular starters.",
        "",
        "The segmented modeling results show that specialization is not automatically better. Some simpler ridge models improve in selected league or position segments, but the specialized hist-gradient boosting models perform worse than the global hist-gradient model on every tested subgroup. This makes the global hist-gradient boosting model the best headline model, with segment-specific models used for interpretation and robustness checks.",
        "",
        "Contract years remaining has a positive relationship with market value in the EDA and appears among useful model features, but expired contracts are now modeled as a separate flag and negative remaining years are capped at zero. Age is negatively correlated with log value in the aggregate, reflecting that younger players often carry resale potential. Minutes and starts capture player importance and reliability. League and position encode market context and role-based valuation differences.",
        "",
        "## Discussion and Conclusion",
        "",
        "The final analysis shows that football player market value can be estimated from public performance, contract, and context features with moderate accuracy. The nonlinear model gives the strongest predictive performance, while linear models remain useful for interpretation. The main contribution is a reproducible workflow that connects raw football and Transfermarkt-derived data into a player-season modeling dataset, EDA outputs, global models, position-specific models, league-specific models, and report-ready figures.",
        "",
        "Important limitations remain. Transfermarkt market value is a proxy rather than an actual sale price, the dataset does not include injuries or detailed team strength, and the contract feature is approximated from transfer-history events. Future work should add richer event data, club financial context, exact contract records, and external validation against actual transfer fees.",
        "",
        "## Reproducibility",
        "",
        "Run the main results with:",
        "",
        "```powershell",
        "python code/reproduce.py",
        "```",
        "",
        "All report figures and tables are generated programmatically from the project data.",
    ]
    GENERATED_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_paper_sources(min_minutes: int, model_df: pd.DataFrame, metrics: pd.DataFrame) -> None:
    global_test = metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")].sort_values("rmse_log")
    best_test = global_test.iloc[0]
    best_model_label = str(best_test["model"]).replace("_", "-")

    paper_figure_names = [
        "model_comparison_test_rmse.png",
        "predicted_vs_actual_best_model.png",
        "residuals_by_league_position.png",
        "position_model_comparison.png",
        "league_model_comparison.png",
        "specialized_vs_global_rmse.png",
    ]
    for figure_name in paper_figure_names:
        source = FIGURES_DIR / figure_name
        if source.exists():
            copy2(source, PAPER_FINAL_FIGURES_DIR / figure_name)

    main_tex = r"""\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts

\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{url}

\begin{document}

\title{A Data-Driven Analysis of Football Players' Transfer Value Based on Performance and Contract Characteristics}

\author{
\IEEEauthorblockN{David Aslanyan}
\IEEEauthorblockA{\textit{American University of Armenia}\\
Yerevan, Armenia\\
david\_aslanyan@edu.auau.am}
\and
\IEEEauthorblockN{Supervisor: Arman Asryan}
\IEEEauthorblockA{\textit{American University of Armenia}\\
Yerevan, Armenia}
}

\maketitle

\begin{abstract}
This project predicts and explains football player market value using season-level performance, league, position, age, transfer-history, and contract features. The dataset covers player-season observations from the top five European leagues across the 2021/22, 2022/23, and 2023/24 seasons. The modeling target is the log-transformed Transfermarkt market value, which addresses the strong skew in football valuations. Models are trained on 2021/22 and 2022/23 and evaluated on the held-out 2023/24 season. With a """ + str(min_minutes) + r"""-minute playing-time threshold, the modeling dataset contains """ + f"{len(model_df):,}" + r""" rows. The best global model is """ + best_model_label + r""", with test RMSE log """ + f"{best_test['rmse_log']:.2f}" + r""" and test \(R^2\) """ + f"{best_test['r2']:.2f}" + r""". The results show that market value is meaningfully associated with age, minutes, league, position, contract years remaining, and transfer-history signals, while also leaving residual error likely related to reputation, injuries, club strategy, and other unobserved market factors.
\end{abstract}

\begin{IEEEkeywords}
football analytics, market value prediction, Transfermarkt, machine learning, regression, contract analysis
\end{IEEEkeywords}

\section{Introduction}
Transfer values play a central role in professional football because they influence recruitment, squad planning, and contract negotiation. Although goals and assists are often emphasized in public discussion, market valuation also reflects age, position, playing time, contract situation, league context, and market expectations. This project examines whether public season-level data can predict player market value and which feature groups are most informative.

The research questions are: (1) how well can football players' market values be predicted from season-level performance and contract data; (2) which variables are most associated with valuation; (3) whether the relationship differs by position; and (4) how contract expiry relates to value after controlling for other signals.

\section{Literature Review}
Transfermarkt has been widely used in football economics and analytics as a proxy for player market value. Herm et al. studied the accuracy and attributes of crowd-generated Transfermarkt valuations \cite{herm2014crowd}. Muller et al. proposed data-driven player valuation methods beyond crowd judgment \cite{muller2017beyond}. More recent machine-learning studies compare regression and ensemble approaches for predicting European football player values \cite{aydemir2022ensemble,tamim2025football}. Contract duration and transfer-market economics are also important because remaining contract length changes bargaining power and expected transfer fees \cite{poli2022contract}. This project builds on these directions with a reproducible player-season pipeline and explicit holdout-season validation.

\section{Methodology}
The final analytics table is \texttt{data/processed/player\_season\_analytics.csv}. Each row is a player-season/team observation. Features include age, squared age, minutes, starts, 90s, per-90 performance rates, league, season, position group, contract years remaining, missing-contract indicators, and transfer-history counts. The target is \texttt{log\_market\_value\_eur}, defined as \(\log(1 + \text{market value in EUR})\).

Players with fewer than """ + str(min_minutes) + r""" minutes are excluded. This threshold increases coverage compared with a 900-minute regular-starter filter while still removing very small playing-time samples. The train/test split is chronological: 2021/22 and 2022/23 are used for training, and 2023/24 is held out for testing.

The global model comparison includes a mean baseline, ordinary least squares regression, ridge regression, and hist-gradient boosting. Position-specific models are trained for defenders, midfielders, and forwards. League-specific models are trained for each top-five league. Specialized models are compared with the global model on the same subgroup to test whether segmentation improves prediction or whether the global model benefits from its larger training sample. Performance is evaluated with RMSE, MAE, and \(R^2\) on the log target, with additional error summaries in EUR after inverse transformation.

\section{Results}
The generated results are stored in \texttt{reports/generated/tables/model\_metrics.csv}. In the final run, the strongest global model is """ + best_model_label + r""", with test RMSE log """ + f"{best_test['rmse_log']:.2f}" + r""" and test \(R^2\) """ + f"{best_test['r2']:.2f}" + r""". The linear and ridge models remain useful interpretable baselines and substantially outperform the mean predictor.

\begin{figure}[htbp]
\centerline{\includegraphics[width=\linewidth]{figures/model_comparison_test_rmse.png}}
\caption{Global model comparison on the 2023/24 test season.}
\label{fig:model_comparison}
\end{figure}

\begin{figure}[htbp]
\centerline{\includegraphics[width=\linewidth]{figures/predicted_vs_actual_best_model.png}}
\caption{Predicted versus actual log market value for the best global model.}
\label{fig:predicted_actual}
\end{figure}

\begin{figure}[htbp]
\centerline{\includegraphics[width=\linewidth]{figures/specialized_vs_global_rmse.png}}
\caption{Segment-specific hist-gradient boosting models compared with the global model on the same subgroup. Negative values favor specialized models.}
\label{fig:specialized_global}
\end{figure}

\section{Analysis and Validation}
The chronological holdout split validates whether the model generalizes to the next season rather than only fitting random rows from the same time period. The nonlinear model's advantage suggests interactions among age, minutes, league, position, and contract status. Position-specific and league-specific models provide diagnostic insight, but they use smaller samples and should be interpreted as supporting analysis rather than replacements for the global comparison.

Feature importance outputs in \texttt{reports/generated/tables/feature\_importance.csv} show that age, minutes, league, position, and contract-related variables are important valuation signals. Contract years remaining is positively associated with value in exploratory analysis, consistent with the idea that longer contracts strengthen the selling club's bargaining position. These findings are descriptive rather than causal because unobserved factors such as reputation, injuries, wage level, and club demand are not fully captured.

\section{Discussion and Conclusion}
The project demonstrates that football player market values can be estimated from public performance, contract, and context data with moderate accuracy. The best nonlinear model improves meaningfully over the mean baseline and over linear models on the held-out 2023/24 season. The main contribution is a reproducible pipeline that connects processed player-season data to EDA, model comparison, position-specific validation, and report-ready figures.

Limitations include the use of Transfermarkt market value as a proxy for realized transfer price, approximate contract features derived from transfer-history events, and missing information on injuries, wages, team strength, reputation, and actual transfer demand. Future work should add richer event-level football data, exact contract records, club financial variables, and validation against actual transfer fees.

\section*{Acknowledgment}
The student thanks Arman Asryan and the American University of Armenia for guidance and support.

\bibliographystyle{IEEEtran}
\bibliography{references}

\end{document}
"""

    references_bib = r"""@article{herm2014crowd,
  author = {Herm, Steffen and Callsen-Bracker, Hans-Martin and Kreis, Henning},
  title = {When the Crowd Evaluates Soccer Players' Market Values: Accuracy and Evaluation Attributes of an Online Community},
  journal = {Sport Management Review},
  volume = {17},
  number = {4},
  pages = {484--492},
  year = {2014},
  doi = {10.1016/j.smr.2013.12.006}
}

@article{muller2017beyond,
  author = {Muller, Oliver and Simons, Alexander and Weinmann, Markus},
  title = {Beyond Crowd Judgments: Data-Driven Estimation of Market Value in Association Football},
  journal = {European Journal of Operational Research},
  volume = {263},
  number = {2},
  pages = {611--624},
  year = {2017},
  doi = {10.1016/j.ejor.2017.05.005}
}

@article{aydemir2022ensemble,
  author = {Aydemir, Berke and Batar, Mehmet Ali and Sevi, Rukiye},
  title = {An Ensemble Learning Approach to Predict the Transfer Values of Football Players},
  journal = {SN Computer Science},
  volume = {3},
  number = {227},
  year = {2022},
  doi = {10.1007/s42979-022-01095-z}
}

@article{poli2022contract,
  author = {Poli, Raffaele and Ravenel, Loic and Besson, Roger},
  title = {Econometric Approach to Assessing the Transfer Fees and Values of Professional Football Players},
  journal = {Economies},
  volume = {10},
  number = {1},
  pages = {4},
  year = {2022},
  doi = {10.3390/economies10010004}
}

@article{tamim2025football,
  author = {Tamim, Mohamed and Abdessalem, Talel and Kacem, Imed},
  title = {Market Value Prediction of European Football Players: A Machine Learning Approach},
  journal = {Journal of Computational Mathematics and Data Science},
  volume = {14},
  pages = {100118},
  year = {2025},
  doi = {10.1016/j.jcmds.2025.100118}
}
"""
    # The final paper text is hand-edited in paper/final/main.tex.
    # Reproduction refreshes only the figure copies used by that source.


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final EDA and market-value model comparison.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--min-minutes", type=int, default=DEFAULT_MIN_MINUTES)
    parser.add_argument("--include-position-models", action="store_true")
    parser.add_argument("--include-league-models", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    df = load_data(args.input)
    eda_stats = run_eda(df, min_minutes=args.min_minutes)
    model_df = make_modeling_dataset(df, min_minutes=args.min_minutes)
    metrics, predictions, fitted_models = run_models(
        model_df,
        include_position_models=args.include_position_models,
        include_league_models=args.include_league_models,
    )
    feature_importance = save_feature_importance(fitted_models, model_df)
    best_global_model = (
        metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")]
        .sort_values("rmse_log")
        .iloc[0]["model"]
    )
    error_by_group = save_error_by_group(predictions, best_global_model)
    specialized_comparison = save_specialized_model_comparison(predictions)
    bootstrap_intervals = save_bootstrap_intervals(predictions, best_global_model)
    rolling_validation = save_rolling_season_validation(model_df)
    sensitivity = save_model_sensitivity(df, args.min_minutes)
    plot_model_diagnostics(metrics, predictions, best_global_model)
    plot_specialized_vs_global(specialized_comparison)
    write_summary(
        eda_stats,
        model_df,
        metrics,
        feature_importance,
        specialized_comparison,
        sensitivity,
        bootstrap_intervals,
        min_minutes=args.min_minutes,
    )
    write_final_report(
        eda_stats,
        model_df,
        metrics,
        error_by_group,
        feature_importance,
        specialized_comparison,
        sensitivity,
        bootstrap_intervals,
        rolling_validation,
        min_minutes=args.min_minutes,
    )
    write_paper_sources(min_minutes=args.min_minutes, model_df=model_df, metrics=metrics)

    global_metrics = metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")]
    print(f"Source rows: {len(df)}")
    print(f"Modeling rows after Min >= {args.min_minutes}: {len(model_df)}")
    print("Global test metrics:")
    print(global_metrics.sort_values("rmse_log").to_string(index=False))
    if args.include_position_models:
        position_rows = metrics[(metrics["scope"] == "position_specific") & (metrics["split"] == "test")]
        print("Position-specific test metrics:")
        print(position_rows.sort_values(["position_group", "rmse_log"]).to_string(index=False))
    if args.include_league_models:
        league_rows = metrics[(metrics["scope"] == "league_specific") & (metrics["split"] == "test")]
        print("League-specific test metrics:")
        print(league_rows.sort_values(["cleaned_comp", "rmse_log"]).to_string(index=False))
    print(f"Wrote summary: {SUMMARY_PATH}")
    print(f"Wrote final report: {GENERATED_REPORT_PATH}")
    print(f"Refreshed final paper figures: {PAPER_FINAL_FIGURES_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
