#!/usr/bin/env python3
"""Validate core data-quality assumptions before modeling."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METRICS_PATH = REPO_ROOT / "data" / "interim" / "metrics.csv"
DEFAULT_VALUES_PATH = REPO_ROOT / "data" / "raw" / "player_values_old.csv"
DEFAULT_ANALYTICS_PATH = REPO_ROOT / "data" / "processed" / "player_season_analytics.csv"
MAX_MARKET_VALUE_DAYS_FROM_VALUATION = 120


def normalize_name(name: str) -> str:
    return name.strip().lower()


def ambiguous_value_names(values_path: Path) -> dict[str, set[str]]:
    candidate_ids_by_name: dict[str, set[str]] = {}
    with values_path.open("r", newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.DictReader(file)
        for row in reader:
            player_name = row.get("player_name", "")
            player_id = row.get("player_id", "")
            if not player_name or not player_id:
                continue
            candidate_ids_by_name.setdefault(normalize_name(player_name), set()).add(player_id.strip())

    return {
        name: candidate_ids
        for name, candidate_ids in candidate_ids_by_name.items()
        if len(candidate_ids) > 1
    }


def require(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run capstone data-quality checks.")
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--values", type=Path, default=DEFAULT_VALUES_PATH)
    parser.add_argument("--analytics", type=Path, default=DEFAULT_ANALYTICS_PATH)
    parser.add_argument("--max-target-days", type=int, default=MAX_MARKET_VALUE_DAYS_FROM_VALUATION)
    args = parser.parse_args()

    failures: list[str] = []

    metrics = pd.read_csv(args.metrics)
    analytics = pd.read_csv(args.analytics)

    ambiguous_names = ambiguous_value_names(args.values)
    metrics_names = metrics["Player"].fillna("").map(normalize_name)
    ambiguous_metric_rows = metrics_names.isin(ambiguous_names).sum()
    require(
        ambiguous_metric_rows == 0,
        failures,
        f"{ambiguous_metric_rows} metrics rows still use ambiguous Transfermarkt name matches.",
    )

    require(
        analytics["row_id"].duplicated().sum() == 0,
        failures,
        "Duplicate row_id values found in analytics table.",
    )
    grain_columns = ["trmrkt_player_id", "season", "Squad", "Comp"]
    require(
        analytics.duplicated(grain_columns).sum() == 0,
        failures,
        "Duplicate player-season-team grain rows found in analytics table.",
    )

    target_days = pd.to_numeric(analytics.get("market_value_days_from_valuation"), errors="coerce")
    market_missing = pd.to_numeric(analytics.get("market_value_missing"), errors="coerce").fillna(1)
    stale_labeled_rows = ((market_missing == 0) & (target_days > args.max_target_days)).sum()
    require(
        stale_labeled_rows == 0,
        failures,
        f"{stale_labeled_rows} labeled rows have market values more than {args.max_target_days} days from valuation.",
    )

    market_stale = pd.to_numeric(analytics.get("market_value_stale"), errors="coerce").fillna(0)
    stale_with_target = (
        (market_stale == 1)
        & analytics["market_value_eur"].notna()
        & analytics["log_market_value_eur"].notna()
    ).sum()
    require(
        stale_with_target == 0,
        failures,
        f"{stale_with_target} stale market-value rows still contain modeling targets.",
    )

    contract_years = pd.to_numeric(analytics.get("contract_years_remaining"), errors="coerce")
    negative_contract_rows = (contract_years < 0).sum()
    require(
        negative_contract_rows == 0,
        failures,
        f"{negative_contract_rows} rows have negative modeled contract_years_remaining.",
    )

    valuation_dates = pd.to_datetime(analytics["valuation_date"], errors="coerce")
    latest_transfer_dates = pd.to_datetime(
        analytics["latest_transfer_date_before_valuation"],
        errors="coerce",
    )
    future_transfer_rows = (latest_transfer_dates > valuation_dates).sum()
    require(
        future_transfer_rows == 0,
        failures,
        f"{future_transfer_rows} rows use transfer events after valuation_date.",
    )

    if failures:
        print("FAIL: data-quality checks failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS: data-quality checks passed.")
    print(f"Rows checked: metrics={len(metrics)}, analytics={len(analytics)}")
    print(f"Ambiguous value names excluded from metrics: {len(ambiguous_names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
