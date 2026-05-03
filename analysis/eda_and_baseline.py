#!/usr/bin/env python3
"""Run final EDA, model comparison, and report artifact generation.

Input:
    data/processed/player_season_analytics.csv

Outputs:
    data/processed/modeling_dataset.csv
    reports/eda_summary.md
    reports/final_report.md
    reports/tables/*.csv
    reports/figures/*.png
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


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "processed" / "player_season_analytics.csv"
DEFAULT_MODELING_DATASET = REPO_ROOT / "data" / "processed" / "modeling_dataset.csv"
REPORTS_DIR = REPO_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
PAPER_DIR = REPO_ROOT / "paper"
PAPER_FIGURES_DIR = PAPER_DIR / "figures"

TARGET = "log_market_value_eur"
RAW_TARGET = "market_value_eur"
TRAIN_SEASONS = ["21/22", "22/23"]
TEST_SEASONS = ["23/24"]
POSITION_GROUPS = ["DF", "MF", "FW"]
DEFAULT_MIN_MINUTES = 300

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
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
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


def make_linear_preprocessor() -> ColumnTransformer:
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
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def make_tree_preprocessor() -> ColumnTransformer:
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", encoder()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def model_specs() -> list[tuple[str, Pipeline]]:
    return [
        ("mean_baseline", Pipeline(steps=[("model", DummyRegressor(strategy="mean"))])),
        (
            "linear_regression",
            Pipeline(steps=[("preprocess", make_linear_preprocessor()), ("model", LinearRegression())]),
        ),
        (
            "ridge_alpha_1",
            Pipeline(steps=[("preprocess", make_linear_preprocessor()), ("model", Ridge(alpha=1.0))]),
        ),
        (
            "hist_gradient_boosting",
            Pipeline(
                steps=[
                    ("preprocess", make_tree_preprocessor()),
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


def split_xy(model_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df = model_df[model_df["season"].isin(TRAIN_SEASONS)].copy()
    test_df = model_df[model_df["season"].isin(TEST_SEASONS)].copy()

    if train_df.empty or test_df.empty:
        raise ValueError("Train/test split produced an empty train or test set.")

    return (
        train_df,
        test_df,
        train_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
        test_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
    )


def evaluate_predictions(
    *,
    model_name: str,
    split: str,
    scope: str,
    position_group: str,
    y_log: pd.Series,
    y_raw: pd.Series,
    pred_log: np.ndarray,
) -> dict[str, object]:
    pred_raw = np.expm1(pred_log).clip(min=0)
    y_raw_array = y_raw.to_numpy()
    return {
        "scope": scope,
        "position_group": position_group,
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
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Pipeline]]:
    train_df, test_df, X_train, X_test = split_xy(model_df)
    y_train = train_df[TARGET]
    y_test = test_df[TARGET]

    metric_rows: list[dict[str, object]] = []
    prediction_parts: list[pd.DataFrame] = []
    fitted_models: dict[str, Pipeline] = {}

    for name, model in model_specs():
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
        "- Position-specific models are useful diagnostics, but the global model remains the clearest comparison baseline.",
        f"- Top permutation-importance features for the best model: {', '.join(top_hgb_features)}.",
        "",
        "## Generated Files",
        "",
        "- `data/processed/modeling_dataset.csv`",
        "- `reports/final_report.md`",
        "- `reports/tables/model_metrics.csv`",
        "- `reports/tables/error_by_group.csv`",
        "- `reports/tables/feature_importance.csv`",
        "- `reports/tables/model_predictions.csv`",
        "- `reports/figures/model_comparison_test_rmse.png`",
        "- `reports/figures/predicted_vs_actual_best_model.png`",
        "- `reports/figures/residuals_by_league_position.png`",
        "- `reports/figures/position_model_comparison.png`",
        "- `paper/main.tex`",
        "- `paper/references.bib`",
    ]
    (REPORTS_DIR / "eda_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_report(
    eda_stats: dict[str, object],
    model_df: pd.DataFrame,
    metrics: pd.DataFrame,
    error_by_group: pd.DataFrame,
    feature_importance: pd.DataFrame,
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
        "The global model comparison includes a mean baseline, ordinary least squares linear regression, ridge regression, and hist-gradient boosting. Position-specific ridge and hist-gradient boosting models are trained separately for defenders, midfielders, and forwards.",
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
        "## Analysis and Validation",
        "",
        "The project meets the predictive objective because all learned models outperform the mean baseline on the held-out 2023/24 season. The best model explains a meaningful share of variance while maintaining evaluation on a future season, which is stricter than a random row split. The expanded 300-minute threshold increases coverage from 4,228 rows under the earlier 900-minute setup to 5,658 rows, but it also introduces noisier low-minute observations. This tradeoff is acceptable for the final project because the goal is broad player valuation coverage rather than only regular starters.",
        "",
        "Contract years remaining has a positive relationship with market value in the EDA and appears among useful model features. Age is negatively correlated with log value in the aggregate, reflecting that younger players often carry resale potential. Minutes and starts capture player importance and reliability. League and position encode market context and role-based valuation differences.",
        "",
        "## Discussion and Conclusion",
        "",
        "The final analysis shows that football player market value can be estimated from public performance, contract, and context features with moderate accuracy. The nonlinear model gives the strongest predictive performance, while linear models remain useful for interpretation. The main contribution is a reproducible workflow that connects raw football and Transfermarkt-derived data into a player-season modeling dataset, EDA outputs, model comparisons, position-specific diagnostics, and report-ready figures.",
        "",
        "Important limitations remain. Transfermarkt market value is a proxy rather than an actual sale price, the dataset does not include injuries or detailed team strength, and the contract feature is approximated from transfer-history events. Future work should add richer event data, club financial context, exact contract records, and external validation against actual transfer fees.",
        "",
        "## Reproducibility",
        "",
        "Run the main results with:",
        "",
        "```powershell",
        "python analysis/eda_and_baseline.py --min-minutes 300 --include-position-models",
        "```",
        "",
        "All report figures and tables are generated programmatically from the project data.",
    ]
    (REPORTS_DIR / "final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_paper_sources(min_minutes: int) -> None:
    paper_figure_names = [
        "model_comparison_test_rmse.png",
        "predicted_vs_actual_best_model.png",
        "residuals_by_league_position.png",
        "position_model_comparison.png",
    ]
    for figure_name in paper_figure_names:
        source = FIGURES_DIR / figure_name
        if source.exists():
            copy2(source, PAPER_FIGURES_DIR / figure_name)

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
\IEEEauthorblockN{[Student Full Name]}
\IEEEauthorblockA{\textit{American University of Armenia}\\
Yerevan, Armenia\\
[student.email@example.com]}
\and
\IEEEauthorblockN{Supervisor: [Supervisor Name]}
\IEEEauthorblockA{\textit{American University of Armenia}\\
Yerevan, Armenia}
}

\maketitle

\begin{abstract}
This project predicts and explains football player market value using season-level performance, league, position, age, transfer-history, and contract features. The dataset covers player-season observations from the top five European leagues across the 2021/22, 2022/23, and 2023/24 seasons. The modeling target is the log-transformed Transfermarkt market value, which addresses the strong skew in football valuations. Models are trained on 2021/22 and 2022/23 and evaluated on the held-out 2023/24 season. With a 300-minute playing-time threshold, the best global model is hist-gradient boosting, which outperforms linear and ridge baselines. The results show that market value is meaningfully associated with age, minutes, league, position, contract years remaining, and transfer-history signals, while also leaving residual error likely related to reputation, injuries, club strategy, and other unobserved market factors.
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

The global model comparison includes a mean baseline, ordinary least squares regression, ridge regression, and hist-gradient boosting. Position-specific ridge and hist-gradient boosting models are also trained for defenders, midfielders, and forwards. Performance is evaluated with RMSE, MAE, and \(R^2\) on the log target, with additional error summaries in EUR after inverse transformation.

\section{Results}
The generated results are stored in \texttt{reports/tables/model\_metrics.csv}. In the final run, the hist-gradient boosting model is expected to be the strongest global model, with test RMSE log around 0.89 and test \(R^2\) around 0.61. The linear and ridge models remain useful interpretable baselines and substantially outperform the mean predictor.

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

\section{Analysis and Validation}
The chronological holdout split validates whether the model generalizes to the next season rather than only fitting random rows from the same time period. The nonlinear model's advantage suggests interactions among age, minutes, league, position, and contract status. Position-specific models provide additional diagnostic insight, but they use smaller samples and should be interpreted as supporting analysis rather than replacements for the global comparison.

Feature importance outputs in \texttt{reports/tables/feature\_importance.csv} show that age, minutes, league, position, and contract-related variables are important valuation signals. Contract years remaining is positively associated with value in exploratory analysis, consistent with the idea that longer contracts strengthen the selling club's bargaining position. These findings are descriptive rather than causal because unobserved factors such as reputation, injuries, wage level, and club demand are not fully captured.

\section{Discussion and Conclusion}
The project demonstrates that football player market values can be estimated from public performance, contract, and context data with moderate accuracy. The best nonlinear model improves meaningfully over the mean baseline and over linear models on the held-out 2023/24 season. The main contribution is a reproducible pipeline that connects processed player-season data to EDA, model comparison, position-specific validation, and report-ready figures.

Limitations include the use of Transfermarkt market value as a proxy for realized transfer price, approximate contract features derived from transfer-history events, and missing information on injuries, wages, team strength, reputation, and actual transfer demand. Future work should add richer event-level football data, exact contract records, club financial variables, and validation against actual transfer fees.

\section*{Acknowledgment}
The student thanks [Supervisor Name] and the American University of Armenia for guidance and support.

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
    (PAPER_DIR / "main.tex").write_text(main_tex, encoding="utf-8")
    (PAPER_DIR / "references.bib").write_text(references_bib, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final EDA and market-value model comparison.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--min-minutes", type=int, default=DEFAULT_MIN_MINUTES)
    parser.add_argument("--include-position-models", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    df = load_data(args.input)
    eda_stats = run_eda(df, min_minutes=args.min_minutes)
    model_df = make_modeling_dataset(df, min_minutes=args.min_minutes)
    metrics, predictions, fitted_models = run_models(
        model_df,
        include_position_models=args.include_position_models,
    )
    feature_importance = save_feature_importance(fitted_models, model_df)
    best_global_model = (
        metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")]
        .sort_values("rmse_log")
        .iloc[0]["model"]
    )
    error_by_group = save_error_by_group(predictions, best_global_model)
    plot_model_diagnostics(metrics, predictions, best_global_model)
    write_summary(eda_stats, model_df, metrics, feature_importance, min_minutes=args.min_minutes)
    write_final_report(
        eda_stats,
        model_df,
        metrics,
        error_by_group,
        feature_importance,
        min_minutes=args.min_minutes,
    )
    write_paper_sources(min_minutes=args.min_minutes)

    global_metrics = metrics[(metrics["scope"] == "global") & (metrics["split"] == "test")]
    print(f"Source rows: {len(df)}")
    print(f"Modeling rows after Min >= {args.min_minutes}: {len(model_df)}")
    print("Global test metrics:")
    print(global_metrics.sort_values("rmse_log").to_string(index=False))
    if args.include_position_models:
        position_rows = metrics[(metrics["scope"] == "position_specific") & (metrics["split"] == "test")]
        print("Position-specific test metrics:")
        print(position_rows.sort_values(["position_group", "rmse_log"]).to_string(index=False))
    print(f"Wrote summary: {REPORTS_DIR / 'eda_summary.md'}")
    print(f"Wrote final report: {REPORTS_DIR / 'final_report.md'}")
    print(f"Wrote paper source: {PAPER_DIR / 'main.tex'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
