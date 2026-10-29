"""Command line entry point for setup and solver utilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from salb3pm.experiments.runner import run_one
from salb3pm.smoke import run_smoke
from salb3pm.solvers import SOLVERS


def main() -> None:
    parser = argparse.ArgumentParser(prog="salb3pm")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("smoke", help="check PySAT PB encoding and MaxSAT RC2 installation")
    solve_parser = commands.add_parser("solve", help="solve one JSON SALB3PM instance")
    solve_parser.add_argument("instance", type=Path)
    solve_parser.add_argument("--solver", choices=sorted(SOLVERS), required=True)
    solve_parser.add_argument("--time-limit", type=float, default=3600)
    solve_parser.add_argument("--output", type=Path)
    solve_parser.add_argument("--log", type=Path)
    args = parser.parse_args()

    if args.command == "smoke":
        run_smoke()
    elif args.command == "solve":
        if args.time_limit <= 0:
            solve_parser.error("--time-limit must be positive")
        output = run_one(
            args.instance,
            args.solver,
            args.time_limit,
            args.output,
            args.log,
        )
        print(json.dumps(output, indent=2))
        if output["result"]["status"] in {"ERROR", "NOT_RUN"}:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
