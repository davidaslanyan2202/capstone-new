#!/usr/bin/env python3
"""Batch scrape Transfermarkt transfer-history JSON by player ID.

The script reads unique `trmrkt_player_id` values from data/processed/metrics.csv,
requests one JSON endpoint per player, and saves successful non-empty JSON files.

Usage:
    python scrapper/test_scrapper.py
   
    
    

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "jsons"
DEFAULT_URL_TEMPLATE = "https://tmapi-alpha.transfermarkt.technology/transfer/history/player/{id}"
ID_COLUMN = "trmrkt_player_id"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
}


def read_unique_player_ids(input_path: Path) -> list[str]:
    player_ids: set[str] = set()

    with input_path.open("r", newline="", encoding="utf-8-sig", errors="replace") as file:
        reader = csv.DictReader(file)

        if ID_COLUMN not in (reader.fieldnames or []):
            raise ValueError(f"Missing required column `{ID_COLUMN}` in {input_path}")

        for row in reader:
            player_id = (row.get(ID_COLUMN) or "").strip()
            if player_id and player_id != "0":
                player_ids.add(player_id)

    return sorted(player_ids, key=lambda value: int(value) if value.isdigit() else value)


def parse_non_empty_json(text: str) -> Any | None:
    if not text.strip():
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    if data in ({}, [], None, ""):
        return None

    return data


def fetch_json(player_id: str, url_template: str, timeout: int) -> tuple[str, bool, str]:
    url = url_template.format(id=player_id)
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            encoding = response.headers.get_content_charset() or "utf-8"
            text = response.read().decode(encoding, errors="replace")
    except urllib.error.HTTPError as exc:
        return player_id, False, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return player_id, False, f"Request failed: {exc.reason}"
    except TimeoutError:
        return player_id, False, "Request timed out"

    if not 200 <= status < 300:
        return player_id, False, f"HTTP {status}"

    data = parse_non_empty_json(text)
    if data is None:
        return player_id, False, "Empty or invalid JSON"

    return player_id, True, json.dumps(data, ensure_ascii=False, indent=2)


def scrape_player_histories(
    player_ids: list[str],
    output_dir: Path,
    url_template: str,
    workers: int,
    timeout: int,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(fetch_json, player_id, url_template, timeout): player_id
            for player_id in player_ids
        }

        for index, future in enumerate(as_completed(futures), start=1):
            player_id, success, payload_or_error = future.result()

            if success:
                output_path = output_dir / f"{player_id}.json"
                output_path.write_text(payload_or_error, encoding="utf-8")
                success_count += 1
                print(f"[{index}/{len(player_ids)}] saved {output_path.name}")
            else:
                print(f"[{index}/{len(player_ids)}] skipped {player_id}: {payload_or_error}")

    return success_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape Transfermarkt transfer-history JSON files.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="CSV containing trmrkt_player_id")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder for downloaded JSON files")
    parser.add_argument("--url-template", default=DEFAULT_URL_TEMPLATE, help="URL template with `{id}` placeholder")
    parser.add_argument("--workers", type=int, default=50, help="Parallel request worker count")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for testing")
    args = parser.parse_args()

    if "{id}" not in args.url_template:
        print("FAIL: --url-template must contain `{id}` placeholder", file=sys.stderr)
        return 1

    try:
        player_ids = read_unique_player_ids(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.limit is not None:
        player_ids = player_ids[: args.limit]

    print(f"Unique player IDs to scrape: {len(player_ids)}")
    print(f"Output folder: {args.output_dir}")
    print(f"Workers: {args.workers}")

    success_count = scrape_player_histories(
        player_ids=player_ids,
        output_dir=args.output_dir,
        url_template=args.url_template,
        workers=max(1, args.workers),
        timeout=args.timeout,
    )

    print(f"Successful non-empty JSON files downloaded: {success_count}")
    return 0 if success_count == len(player_ids) else 1


if __name__ == "__main__":
    raise SystemExit(main())
