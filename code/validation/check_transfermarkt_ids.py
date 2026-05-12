#!/usr/bin/env python3
"""Validate that every interim metrics row has a non-empty Transfermarkt ID."""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = REPO_ROOT / "data" / "interim" / "metrics.csv"
ID_COLUMN = "trmrkt_player_id"


def is_invalid_player_id(value: str | None) -> bool:
    if value is None:
        return True

    cleaned = value.strip()
    return cleaned == "" or cleaned == "0"


def main() -> int:
    invalid_rows: list[dict[str, str]] = []
    total_rows = 0

    with INPUT_PATH.open("r", newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.DictReader(file)

        if ID_COLUMN not in (reader.fieldnames or []):
            print(f"FAIL: missing required column `{ID_COLUMN}` in {INPUT_PATH}")
            return 1

        for row_number, row in enumerate(reader, start=2):
            total_rows += 1
            if is_invalid_player_id(row.get(ID_COLUMN)):
                invalid_rows.append(
                    {
                        "row_number": str(row_number),
                        "Player": row.get("Player", ""),
                        "Squad": row.get("Squad", ""),
                        "season": row.get("season", ""),
                        ID_COLUMN: row.get(ID_COLUMN, ""),
                    }
                )

    if invalid_rows:
        print(f"FAIL: {len(invalid_rows)} of {total_rows} rows have missing, blank, or 0 `{ID_COLUMN}`.")
        print("First 25 invalid rows:")
        for row in invalid_rows[:25]:
            print(
                f"row={row['row_number']}, "
                f"Player={row['Player']}, "
                f"Squad={row['Squad']}, "
                f"season={row['season']}, "
                f"{ID_COLUMN}={row[ID_COLUMN]!r}"
            )
        return 1

    print(f"PASS: all {total_rows} rows have a non-empty, non-zero `{ID_COLUMN}`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
