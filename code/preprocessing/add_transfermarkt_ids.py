#!/usr/bin/env python3
"""Add Transfermarkt player IDs to matched top-five-leagues performance rows.

Matching rule:
    lower(trim(top5.Player)) == lower(trim(player_values_old.player_name))

Rows with no unambiguous ID match are skipped and written to review files.

Output:
    data/interim/metrics.csv
    data/interim/unmatched_transfermarkt_id_rows.csv
    data/interim/ambiguous_transfermarkt_id_rows.csv
"""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOP5_PATH = REPO_ROOT / "data" / "raw" / "top5.csv"
PLAYER_VALUES_PATH = REPO_ROOT / "data" / "raw" / "player_values_old.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "interim" / "metrics.csv"
UNMATCHED_REVIEW_PATH = REPO_ROOT / "data" / "interim" / "unmatched_transfermarkt_id_rows.csv"
AMBIGUOUS_REVIEW_PATH = REPO_ROOT / "data" / "interim" / "ambiguous_transfermarkt_id_rows.csv"


def normalize_name(name: str) -> str:
    return name.strip().lower()


def build_player_id_lookup(path: Path) -> tuple[dict[str, str], dict[str, set[str]]]:
    candidate_ids_by_name: dict[str, set[str]] = {}

    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.DictReader(file)

        for row in reader:
            player_name = row.get("player_name", "")
            player_id = row.get("player_id", "")

            if not player_name or not player_id:
                continue

            key = normalize_name(player_name)
            player_id = player_id.strip()
            candidate_ids_by_name.setdefault(key, set()).add(player_id)

    lookup = {
        name: next(iter(candidate_ids))
        for name, candidate_ids in candidate_ids_by_name.items()
        if len(candidate_ids) == 1
    }
    ambiguous_candidates = {
        name: candidate_ids
        for name, candidate_ids in candidate_ids_by_name.items()
        if len(candidate_ids) > 1
    }

    return lookup, ambiguous_candidates


def write_review_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def add_transfermarkt_ids() -> None:
    player_id_by_name, ambiguous_candidates = build_player_id_lookup(PLAYER_VALUES_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    matched_rows = 0
    ambiguous_rows = 0
    skipped_rows = 0
    total_rows = 0
    unmatched_review_rows: list[dict[str, str]] = []
    ambiguous_review_rows: list[dict[str, str]] = []

    with TOP5_PATH.open("r", newline="", encoding="utf-8-sig", errors="replace") as input_file:
        reader = csv.DictReader(input_file)
        fieldnames = list(reader.fieldnames or [])
        review_fieldnames = [
            *fieldnames,
            "match_status",
            "candidate_transfermarkt_ids",
        ]

        if "trmrkt_player_id" not in fieldnames:
            fieldnames.append("trmrkt_player_id")

        with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                total_rows += 1
                player_key = normalize_name(row.get("Player", ""))

                if player_key in ambiguous_candidates:
                    ambiguous_rows += 1
                    review_row = dict(row)
                    review_row["match_status"] = "ambiguous_name"
                    review_row["candidate_transfermarkt_ids"] = ";".join(
                        sorted(
                            ambiguous_candidates[player_key],
                            key=lambda value: (0, int(value)) if value.isdigit() else (1, value),
                        )
                    )
                    ambiguous_review_rows.append(review_row)
                    continue

                player_id = player_id_by_name.get(player_key, "")

                if not player_id:
                    skipped_rows += 1
                    review_row = dict(row)
                    review_row["match_status"] = "unmatched_name"
                    review_row["candidate_transfermarkt_ids"] = ""
                    unmatched_review_rows.append(review_row)
                    continue

                matched_rows += 1

                row["trmrkt_player_id"] = player_id
                writer.writerow(row)

    write_review_rows(UNMATCHED_REVIEW_PATH, unmatched_review_rows, review_fieldnames)
    write_review_rows(AMBIGUOUS_REVIEW_PATH, ambiguous_review_rows, review_fieldnames)

    print(f"Wrote: {OUTPUT_PATH}")
    print(f"Rows processed: {total_rows}")
    print(f"Rows written with matches: {matched_rows}")
    print(f"Rows skipped without matches: {skipped_rows}")
    print(f"Rows skipped due to ambiguous names: {ambiguous_rows}")
    print(f"Ambiguous names in value data: {len(ambiguous_candidates)}")
    print(f"Wrote unmatched review rows: {UNMATCHED_REVIEW_PATH}")
    print(f"Wrote ambiguous review rows: {AMBIGUOUS_REVIEW_PATH}")


if __name__ == "__main__":
    add_transfermarkt_ids()
