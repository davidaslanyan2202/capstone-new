#!/usr/bin/env python3
"""Run the non-network reproduction workflow for the capstone project."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_step(args: list[str | Path]) -> None:
    command = [sys.executable, *[str(arg) for arg in args]]
    print(f"\n$ {' '.join(command)}")
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    run_step([Path("code") / "preprocessing" / "add_transfermarkt_ids.py"])
    run_step([Path("code") / "validation" / "check_transfermarkt_ids.py"])
    run_step([Path("code") / "preprocessing" / "build_player_season_analytics.py"])
    run_step([Path("code") / "validation" / "check_data_quality.py"])
    run_step(
        [
            Path("code") / "analysis" / "eda_and_baseline.py",
            "--min-minutes",
            "300",
            "--include-position-models",
            "--include-league-models",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
