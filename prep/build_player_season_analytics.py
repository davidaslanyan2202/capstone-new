#!/usr/bin/env python3
"""Build the analytics-ready player-season dataset described in data.md.

Outputs:
    data/processed/metrics_with_valuation_dates.csv
    data/processed/transfer_history_events.csv
    data/processed/player_season_market_values.csv
    data/processed/player_season_contract_features.csv
    data/processed/player_season_analytics.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"
DEFAULT_VALUES_PATH = REPO_ROOT / "data" / "raw" / "player_values_old.csv"
DEFAULT_JSON_DIR = REPO_ROOT / "jsons"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "processed"

SEASON_VALUATION_DATES = {
    "21/22": date(2022, 6, 30),
    "22/23": date(2023, 6, 30),
    "23/24": date(2024, 6, 30),
}

METRICS_WITH_DATES = "metrics_with_valuation_dates.csv"
TRANSFER_EVENTS = "transfer_history_events.csv"
MARKET_VALUES = "player_season_market_values.csv"
CONTRACT_FEATURES = "player_season_contract_features.csv"
ANALYTICS_TABLE = "player_season_analytics.csv"

COUNT_STAT_COLUMNS = {
    "Gls": "goals_per90",
    "Ast": "assists_per90",
    "Sh": "shots_per90",
    "SoT": "shots_on_target_per90",
    "Crs": "crosses_per90",
    "Int": "interceptions_per90",
    "TklW": "tackles_won_per90",
    "Fls": "fouls_per90",
    "Fld": "fouled_per90",
}


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.DictReader(file)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    number = parse_float(value)
    if number is None:
        return None
    return int(number)


def parse_us_date(value: str) -> date | None:
    text = (value or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def clean_text(value: str) -> str:
    text = (value or "").replace("\xa0", " ").strip()
    return " ".join(text.split())


def clean_comp(value: str) -> str:
    text = clean_text(value)
    parts = text.split()
    if len(parts) > 1 and len(parts[0]) <= 5:
        return " ".join(parts[1:])
    return text


def clean_nation(value: str) -> str:
    text = clean_text(value)
    parts = text.split()
    return parts[-1] if parts else ""


def position_group(value: str) -> str:
    positions = {part.strip() for part in (value or "").split(",")}
    if "GK" in positions:
        return "GK"
    if "FW" in positions:
        return "FW"
    if "MF" in positions:
        return "MF"
    if "DF" in positions:
        return "DF"
    return clean_text(value)


def season_end_year(season: str) -> int | None:
    valuation_date = SEASON_VALUATION_DATES.get(season)
    return valuation_date.year if valuation_date else None


def safe_filename_part(value: str) -> str:
    return (
        clean_text(value)
        .replace("/", "-")
        .replace("\\", "-")
        .replace(",", "")
        .replace(" ", "_")
    )


def add_metrics_row_ids_and_features(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        result: dict[str, Any] = dict(row)
        player_id = clean_text(row.get("trmrkt_player_id", ""))
        season = clean_text(row.get("season", ""))
        squad = safe_filename_part(row.get("Squad", ""))
        comp = safe_filename_part(row.get("Comp", ""))
        valuation_date = SEASON_VALUATION_DATES.get(season)

        result["row_id"] = f"{player_id}_{season}_{squad}_{comp}_{index}"
        result["valuation_date"] = valuation_date.isoformat() if valuation_date else ""
        result["season_end_year"] = season_end_year(season) or ""
        result["position_group"] = position_group(row.get("Pos", ""))
        result["cleaned_comp"] = clean_comp(row.get("Comp", ""))
        result["cleaned_nation"] = clean_nation(row.get("Nation", ""))

        age = parse_float(row.get("Age"))
        result["age_squared"] = round(age * age, 4) if age is not None else ""

        minutes = parse_float(row.get("Min"))
        result["low_minutes_flag"] = "1" if minutes is not None and minutes < 900 else "0"
        if minutes is None:
            result["minutes_bucket"] = ""
        elif minutes < 450:
            result["minutes_bucket"] = "under_450"
        elif minutes < 900:
            result["minutes_bucket"] = "450_to_899"
        elif minutes < 1800:
            result["minutes_bucket"] = "900_to_1799"
        else:
            result["minutes_bucket"] = "1800_plus"

        nineties = parse_float(row.get("90s"))
        for source_column, output_column in COUNT_STAT_COLUMNS.items():
            value = parse_float(row.get(source_column))
            if value is None or nineties is None or nineties <= 0:
                result[output_column] = ""
            else:
                result[output_column] = round(value / nineties, 6)

        enriched.append(result)

    return enriched


def compact_content(value: dict[str, Any] | None) -> str:
    if not isinstance(value, dict):
        return ""
    compact = value.get("compact")
    if not isinstance(compact, dict):
        return ""
    return str(compact.get("content") or "")


def jsonish(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def parse_transfer_history(json_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for path in sorted(json_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        data = payload.get("data") or {}
        player_id = clean_text(str(data.get("playerId") or path.stem))
        history = data.get("history") or {}

        for bucket in ("terminated", "pending"):
            events = history.get(bucket) or []
            if not isinstance(events, list):
                continue

            for event in events:
                details = event.get("details") or {}
                market_value = details.get("marketValue") or {}
                fee = details.get("fee") or {}
                source = event.get("transferSource") or {}
                destination = event.get("transferDestination") or {}
                type_details = event.get("typeDetails") or {}

                transfer_date = parse_iso_date(details.get("date"))
                contract_until = parse_iso_date(details.get("contractUntilDate"))

                rows.append(
                    {
                        "trmrkt_player_id": clean_text(str(details.get("playerId") or player_id)),
                        "transfer_id": clean_text(str(event.get("id") or "")),
                        "event_bucket": bucket,
                        "is_pending": "1" if bucket == "pending" or details.get("isPending") else "0",
                        "transfer_type": clean_text(str(type_details.get("type") or "")),
                        "transfer_date": transfer_date.isoformat() if transfer_date else "",
                        "season_id": details.get("seasonId") or "",
                        "season_display": ((details.get("season") or {}).get("display") or ""),
                        "contract_until_date": contract_until.isoformat() if contract_until else "",
                        "remaining_contract_period_raw": jsonish(details.get("remainingContractPeriod")),
                        "age_at_transfer": details.get("age") or "",
                        "market_value_eur_at_transfer": (market_value.get("value") if isinstance(market_value, dict) else "") or "",
                        "fee_eur": (fee.get("value") if isinstance(fee, dict) else "") or "",
                        "fee_text": compact_content(fee),
                        "source_club_id": source.get("clubId") or "",
                        "source_competition_id": source.get("competitionId") or "",
                        "source_country_id": source.get("countryId") or "",
                        "destination_club_id": destination.get("clubId") or "",
                        "destination_competition_id": destination.get("competitionId") or "",
                        "destination_country_id": destination.get("countryId") or "",
                        "relative_url": event.get("relativeUrl") or "",
                    }
                )

    return rows


def load_market_values(values_path: Path, target_ids: set[str]) -> dict[str, list[tuple[date, int]]]:
    values_by_player: dict[str, list[tuple[date, int]]] = defaultdict(list)

    with values_path.open("r", newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.DictReader(file)
        for row in reader:
            player_id = clean_text(row.get("player_id", ""))
            if player_id not in target_ids:
                continue

            value_date = parse_us_date(row.get("date_unix", ""))
            value = parse_int(row.get("value"))
            if value_date is None or value is None or value <= 0:
                continue

            values_by_player[player_id].append((value_date, value))

    for player_values in values_by_player.values():
        player_values.sort(key=lambda item: item[0])

    return values_by_player


def market_window(valuation_date: date) -> tuple[date, date]:
    return date(valuation_date.year, 5, 15), date(valuation_date.year, 8, 31)


def choose_market_value(
    player_values: list[tuple[date, int]],
    valuation_date: date,
) -> tuple[date | None, int | None, bool]:
    if not player_values:
        return None, None, False

    start, end = market_window(valuation_date)
    in_window = [item for item in player_values if start <= item[0] <= end]
    candidates = in_window if in_window else player_values
    chosen_date, chosen_value = min(candidates, key=lambda item: abs((item[0] - valuation_date).days))
    return chosen_date, chosen_value, bool(in_window)


def build_market_value_rows(
    metrics_rows: list[dict[str, Any]],
    values_by_player: dict[str, list[tuple[date, int]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row in metrics_rows:
        player_id = clean_text(row.get("trmrkt_player_id", ""))
        valuation_date = parse_us_date(row.get("valuation_date", ""))
        if valuation_date is None:
            rows.append(
                {
                    "row_id": row["row_id"],
                    "trmrkt_player_id": player_id,
                    "season": row.get("season", ""),
                    "Squad": row.get("Squad", ""),
                    "Comp": row.get("Comp", ""),
                    "valuation_date": row.get("valuation_date", ""),
                    "market_value_eur": "",
                    "market_value_date": "",
                    "market_value_days_from_valuation": "",
                    "log_market_value_eur": "",
                    "market_value_in_window": "0",
                    "market_value_missing": "1",
                }
            )
            continue

        value_date, market_value, in_window = choose_market_value(values_by_player.get(player_id, []), valuation_date)
        missing = market_value is None or value_date is None
        rows.append(
            {
                "row_id": row["row_id"],
                "trmrkt_player_id": player_id,
                "season": row.get("season", ""),
                "Squad": row.get("Squad", ""),
                "Comp": row.get("Comp", ""),
                "valuation_date": row.get("valuation_date", ""),
                "market_value_eur": market_value or "",
                "market_value_date": value_date.isoformat() if value_date else "",
                "market_value_days_from_valuation": abs((value_date - valuation_date).days) if value_date else "",
                "log_market_value_eur": round(math.log1p(market_value), 8) if market_value else "",
                "market_value_in_window": "1" if in_window else "0",
                "market_value_missing": "1" if missing else "0",
            }
        )

    return rows


def group_events_by_player(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        transfer_date = parse_us_date(event.get("transfer_date", ""))
        if transfer_date is None:
            continue
        enriched = dict(event)
        enriched["_transfer_date_obj"] = transfer_date
        grouped[clean_text(event.get("trmrkt_player_id", ""))].append(enriched)

    for player_events in grouped.values():
        player_events.sort(key=lambda item: item["_transfer_date_obj"])

    return grouped


def is_loan_event(event: dict[str, Any]) -> bool:
    transfer_type = clean_text(str(event.get("transfer_type", ""))).upper()
    fee_text = clean_text(str(event.get("fee_text", ""))).lower()
    return "LOAN" in transfer_type or "loan" in fee_text


def is_free_event(event: dict[str, Any]) -> bool:
    fee_text = clean_text(str(event.get("fee_text", ""))).lower()
    fee = parse_float(event.get("fee_eur"))
    return fee_text == "free transfer" or fee == 0


def build_contract_feature_rows(
    metrics_rows: list[dict[str, Any]],
    events_by_player: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row in metrics_rows:
        player_id = clean_text(row.get("trmrkt_player_id", ""))
        valuation_date = parse_us_date(row.get("valuation_date", ""))
        player_events = events_by_player.get(player_id, [])
        before_events = [
            event for event in player_events
            if valuation_date is not None and event["_transfer_date_obj"] <= valuation_date
        ]
        terminated_before = [event for event in before_events if event.get("event_bucket") == "terminated"]
        eligible_events = terminated_before or before_events
        latest = eligible_events[-1] if eligible_events else None

        contract_until = parse_us_date(latest.get("contract_until_date", "")) if latest else None
        latest_transfer_date = latest["_transfer_date_obj"] if latest else None

        if valuation_date and contract_until:
            contract_days_remaining: int | str = (contract_until - valuation_date).days
            contract_years_remaining: float | str = round(contract_days_remaining / 365.25, 4)
            expiring_1y = "1" if contract_days_remaining <= 365 else "0"
            expiring_2y = "1" if contract_days_remaining <= 730 else "0"
            contract_missing = "0"
        else:
            contract_days_remaining = ""
            contract_years_remaining = ""
            expiring_1y = ""
            expiring_2y = ""
            contract_missing = "1"

        days_since_last_transfer = (
            (valuation_date - latest_transfer_date).days
            if valuation_date and latest_transfer_date
            else ""
        )

        transfer_count = len(before_events)
        loan_count = sum(1 for event in before_events if is_loan_event(event))

        rows.append(
            {
                "row_id": row["row_id"],
                "trmrkt_player_id": player_id,
                "season": row.get("season", ""),
                "Squad": row.get("Squad", ""),
                "Comp": row.get("Comp", ""),
                "valuation_date": row.get("valuation_date", ""),
                "latest_transfer_id_before_valuation": latest.get("transfer_id", "") if latest else "",
                "latest_transfer_date_before_valuation": latest_transfer_date.isoformat() if latest_transfer_date else "",
                "latest_transfer_type_before_valuation": latest.get("transfer_type", "") if latest else "",
                "contract_until_date": contract_until.isoformat() if contract_until else "",
                "contract_days_remaining": contract_days_remaining,
                "contract_years_remaining": contract_years_remaining,
                "contract_expiring_within_1y": expiring_1y,
                "contract_expiring_within_2y": expiring_2y,
                "contract_missing": contract_missing,
                "days_since_last_transfer": days_since_last_transfer,
                "last_transfer_market_value_eur": latest.get("market_value_eur_at_transfer", "") if latest else "",
                "last_transfer_fee_eur": latest.get("fee_eur", "") if latest else "",
                "last_transfer_fee_text": latest.get("fee_text", "") if latest else "",
                "last_transfer_was_loan": "1" if latest and is_loan_event(latest) else "0",
                "last_transfer_was_free": "1" if latest and is_free_event(latest) else "0",
                "transfer_count_before_valuation": transfer_count,
                "loan_count_before_valuation": loan_count,
            }
        )

    return rows


def fieldnames_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key.startswith("_"):
                continue
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    return fieldnames


def ordered_analytics_fieldnames(rows: list[dict[str, Any]], metrics_fieldnames: list[str]) -> list[str]:
    priority_fields = [
        "row_id",
        "trmrkt_player_id",
        "Player",
        "Nation",
        "cleaned_nation",
        "Pos",
        "position_group",
        "Squad",
        "Comp",
        "cleaned_comp",
        "season",
        "season_end_year",
        "valuation_date",
    ]
    generated_fields = [
        "age_squared",
        "low_minutes_flag",
        "minutes_bucket",
        *COUNT_STAT_COLUMNS.values(),
        "market_value_eur",
        "market_value_date",
        "market_value_days_from_valuation",
        "log_market_value_eur",
        "market_value_in_window",
        "market_value_missing",
        "latest_transfer_id_before_valuation",
        "latest_transfer_date_before_valuation",
        "latest_transfer_type_before_valuation",
        "contract_until_date",
        "contract_days_remaining",
        "contract_years_remaining",
        "contract_expiring_within_1y",
        "contract_expiring_within_2y",
        "contract_missing",
        "days_since_last_transfer",
        "last_transfer_market_value_eur",
        "last_transfer_fee_eur",
        "last_transfer_fee_text",
        "last_transfer_was_loan",
        "last_transfer_was_free",
        "transfer_count_before_valuation",
        "loan_count_before_valuation",
    ]

    all_fields = fieldnames_from_rows(rows)
    ordered: list[str] = []
    seen: set[str] = set()

    for field in [*priority_fields, *metrics_fieldnames, *generated_fields, *all_fields]:
        if field in all_fields and field not in seen:
            ordered.append(field)
            seen.add(field)

    return ordered


def join_by_row_id(
    metrics_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    market_by_row_id = {row["row_id"]: row for row in market_rows}
    contract_by_row_id = {row["row_id"]: row for row in contract_rows}
    join_key_columns = {"row_id", "trmrkt_player_id", "season", "Squad", "Comp", "valuation_date"}
    analytics_rows: list[dict[str, Any]] = []

    for metrics_row in metrics_rows:
        result = dict(metrics_row)
        for source in (market_by_row_id.get(metrics_row["row_id"], {}), contract_by_row_id.get(metrics_row["row_id"], {})):
            for key, value in source.items():
                if key not in join_key_columns:
                    result[key] = value
        analytics_rows.append(result)

    return analytics_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build player-season analytics tables.")
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--values", type=Path, default=DEFAULT_VALUES_PATH)
    parser.add_argument("--json-dir", type=Path, default=DEFAULT_JSON_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    metrics_raw, metrics_fieldnames = read_csv(args.metrics)
    metrics_rows = add_metrics_row_ids_and_features(metrics_raw)
    target_ids = {clean_text(row.get("trmrkt_player_id", "")) for row in metrics_rows if row.get("trmrkt_player_id")}

    print(f"Metrics rows: {len(metrics_rows)}")
    print(f"Unique Transfermarkt IDs in metrics: {len(target_ids)}")

    metrics_extra_fields = [
        "row_id",
        "valuation_date",
        "season_end_year",
        "position_group",
        "cleaned_comp",
        "cleaned_nation",
        "age_squared",
        "low_minutes_flag",
        "minutes_bucket",
        *COUNT_STAT_COLUMNS.values(),
    ]
    write_csv(
        args.output_dir / METRICS_WITH_DATES,
        metrics_rows,
        ["row_id", *metrics_fieldnames, *[field for field in metrics_extra_fields if field != "row_id"]],
    )

    transfer_events = parse_transfer_history(args.json_dir)
    transfer_event_fields = [
        "trmrkt_player_id",
        "transfer_id",
        "event_bucket",
        "is_pending",
        "transfer_type",
        "transfer_date",
        "season_id",
        "season_display",
        "contract_until_date",
        "remaining_contract_period_raw",
        "age_at_transfer",
        "market_value_eur_at_transfer",
        "fee_eur",
        "fee_text",
        "source_club_id",
        "source_competition_id",
        "source_country_id",
        "destination_club_id",
        "destination_competition_id",
        "destination_country_id",
        "relative_url",
    ]
    write_csv(args.output_dir / TRANSFER_EVENTS, transfer_events, transfer_event_fields)
    print(f"Transfer-history events: {len(transfer_events)}")

    values_by_player = load_market_values(args.values, target_ids)
    market_rows = build_market_value_rows(metrics_rows, values_by_player)
    market_fields = [
        "row_id",
        "trmrkt_player_id",
        "season",
        "Squad",
        "Comp",
        "valuation_date",
        "market_value_eur",
        "market_value_date",
        "market_value_days_from_valuation",
        "log_market_value_eur",
        "market_value_in_window",
        "market_value_missing",
    ]
    write_csv(args.output_dir / MARKET_VALUES, market_rows, market_fields)
    print(f"Market-value rows: {len(market_rows)}")
    print(f"Market-value missing rows: {sum(1 for row in market_rows if row['market_value_missing'] == '1')}")

    events_by_player = group_events_by_player(transfer_events)
    contract_rows = build_contract_feature_rows(metrics_rows, events_by_player)
    contract_fields = [
        "row_id",
        "trmrkt_player_id",
        "season",
        "Squad",
        "Comp",
        "valuation_date",
        "latest_transfer_id_before_valuation",
        "latest_transfer_date_before_valuation",
        "latest_transfer_type_before_valuation",
        "contract_until_date",
        "contract_days_remaining",
        "contract_years_remaining",
        "contract_expiring_within_1y",
        "contract_expiring_within_2y",
        "contract_missing",
        "days_since_last_transfer",
        "last_transfer_market_value_eur",
        "last_transfer_fee_eur",
        "last_transfer_fee_text",
        "last_transfer_was_loan",
        "last_transfer_was_free",
        "transfer_count_before_valuation",
        "loan_count_before_valuation",
    ]
    write_csv(args.output_dir / CONTRACT_FEATURES, contract_rows, contract_fields)
    print(f"Contract-feature rows: {len(contract_rows)}")
    print(f"Contract missing rows: {sum(1 for row in contract_rows if row['contract_missing'] == '1')}")

    analytics_rows = join_by_row_id(metrics_rows, market_rows, contract_rows)
    analytics_fields = ordered_analytics_fieldnames(analytics_rows, metrics_fieldnames)
    write_csv(args.output_dir / ANALYTICS_TABLE, analytics_rows, analytics_fields)
    print(f"Analytics rows: {len(analytics_rows)}")
    print(f"Wrote final table: {args.output_dir / ANALYTICS_TABLE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
