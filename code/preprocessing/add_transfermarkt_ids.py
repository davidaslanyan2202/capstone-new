#!/usr/bin/env python3
"""Add Transfermarkt player IDs to matched top-five-leagues performance rows.

Matching rule:
    lower(trim(top5.Player)) == lower(trim(player_values_old.player_name))

Unmatched rows are skipped.

Output:
    data/interim/metrics.csv
"""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOP5_PATH = REPO_ROOT / "data" / "raw" / "top5.csv"
PLAYER_VALUES_PATH = REPO_ROOT / "data" / "raw" / "player_values_old.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "interim" / "metrics.csv"


def normalize_name(name: str) -> str:
    return name.strip().lower()


def build_player_id_lookup(path: Path) -> tuple[dict[str, str], set[str]]:
    lookup: dict[str, str] = {}
    ambiguous_names: set[str] = set()

    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.DictReader(file)

        for row in reader:
            player_name = row.get("player_name", "")
            player_id = row.get("player_id", "")

            if not player_name or not player_id:
                continue

            key = normalize_name(player_name)
            player_id = player_id.strip()

            if key in lookup and lookup[key] != player_id:
                ambiguous_names.add(key)
                continue

            lookup.setdefault(key, player_id)

    return lookup, ambiguous_names


def add_transfermarkt_ids() -> None:
    player_id_by_name, ambiguous_names = build_player_id_lookup(PLAYER_VALUES_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    matched_rows = 0
    skipped_rows = 0
    total_rows = 0

    with TOP5_PATH.open("r", newline="", encoding="utf-8-sig", errors="replace") as input_file:
        reader = csv.DictReader(input_file)
        fieldnames = list(reader.fieldnames or [])

        if "trmrkt_player_id" not in fieldnames:
            fieldnames.append("trmrkt_player_id")

        with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                total_rows += 1
                player_key = normalize_name(row.get("Player", ""))
                player_id = player_id_by_name.get(player_key, "")

                if not player_id:
                    skipped_rows += 1
                    continue

                matched_rows += 1

                row["trmrkt_player_id"] = player_id
                writer.writerow(row)

    print(f"Wrote: {OUTPUT_PATH}")
    print(f"Rows processed: {total_rows}")
    print(f"Rows written with matches: {matched_rows}")
    print(f"Rows skipped without matches: {skipped_rows}")
    print(f"Ambiguous names in value data: {len(ambiguous_names)}")


if __name__ == "__main__":
    add_transfermarkt_ids()
