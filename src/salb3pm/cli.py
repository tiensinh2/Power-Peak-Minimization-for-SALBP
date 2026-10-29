"""Command line entry point for setup and solver utilities."""

from __future__ import annotations

import argparse

from salb3pm.smoke import run_smoke


def main() -> None:
    parser = argparse.ArgumentParser(prog="salb3pm")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("smoke", help="check PySAT PB encoding and MaxSAT RC2 installation")
    args = parser.parse_args()

    if args.command == "smoke":
        run_smoke()


if __name__ == "__main__":
    main()
