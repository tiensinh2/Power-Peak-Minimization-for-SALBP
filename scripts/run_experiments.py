"""
Batch Experiment Runner for SALB3PM Benchmarks.
Runs multiple solvers across the 97 benchmark instances, enforces cutoff timeout,
records results in CSV & JSON, and prepares data for Figure 5, Figure 6, Table I, and Table II.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
from pathlib import Path
from typing import Any

from salb3pm.experiments.runner import run_one
from salb3pm.solvers import SOLVERS

DEFAULT_SOLVERS = [
    "maxsat-binary",
    "maxsat-inaugural",
    "sat-iterative",
    "cp-sat",
]


def run_benchmark_suite(
    instance_dir: str = "data/benchmarks/salb3pm-97",
    solvers: list[str] = DEFAULT_SOLVERS,
    timeout_seconds: float = 60.0,
    limit: int | None = None,
    output_csv: str = "results/benchmark_summary.csv",
) -> None:
    os.makedirs("results/raw", exist_ok=True)
    os.makedirs("results/logs", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    instance_files = sorted(glob.glob(os.path.join(instance_dir, "*.json")))
    instance_files = [f for f in instance_files if not f.endswith("manifest.json")]

    if limit is not None:
        instance_files = instance_files[:limit]

    print("=" * 105)
    print("SALB3PM BENCHMARK EXECUTION SUITE")
    print(f"Total Instances: {len(instance_files)} | Timeout per run: {timeout_seconds}s")
    print(f"Solvers: {', '.join(solvers)}")
    print("=" * 105)

    fieldnames = [
        "instance_id",
        "family",
        "num_tasks",
        "num_stations",
        "cycle_time",
        "lower_bound",
        "upper_bound",
        "solver",
        "status",
        "objective",
        "best_bound",
        "runtime_seconds",
    ]

    records: list[dict[str, Any]] = []

    # Resume from existing CSV if available
    completed_keys = set()
    if os.path.exists(output_csv):
        with open(output_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                completed_keys.add((row["instance_id"], row["solver"]))
                records.append(row)

    for idx, inst_file in enumerate(instance_files, 1):
        inst_path = Path(inst_file)
        with open(inst_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        inst_id = raw_data.get("id", raw_data.get("name", inst_path.stem))
        family = raw_data.get("family", inst_id.split("-")[0])
        n = raw_data["num_tasks"]
        m = raw_data.get("num_stations", raw_data.get("stations", 1))
        c = raw_data["cycle_time"]
        lb = raw_data.get("lower_bound", max(raw_data.get("power_consumptions", [0])))
        ub = raw_data.get(
            "upper_bound", sum(sorted(raw_data.get("power_consumptions", [0]), reverse=True)[:m])
        )

        print(f"\n[{idx}/{len(instance_files)}] Instance: {inst_id} (n={n}, m={m}, c={c})")

        for solver_name in solvers:
            if (inst_id, solver_name) in completed_keys:
                print(f"  -> {solver_name:<20}: (cached)")
                continue

            try:
                out = run_one(
                    instance_path=inst_path,
                    solver_name=solver_name,
                    time_limit_seconds=timeout_seconds,
                )
                res = out["result"]
                status = res["status"]
                obj = res["objective"]
                rt = res["runtime_seconds"]
                print(
                    f"  -> {solver_name:<20}: {status:<10} | W_peak = {obj!s:<5} | time = {rt:.4f}s"
                )
            except Exception as e:  # noqa: BLE001
                status = "ERROR"
                obj = None
                rt = timeout_seconds
                print(f"  -> {solver_name:<20}: ERROR ({e})")

            row = {
                "instance_id": inst_id,
                "family": family,
                "num_tasks": n,
                "num_stations": m,
                "cycle_time": c,
                "lower_bound": lb,
                "upper_bound": ub,
                "solver": solver_name,
                "status": status,
                "objective": obj if obj is not None else "",
                "best_bound": lb,
                "runtime_seconds": f"{rt:.4f}",
            }
            records.append(row)

            # Write incrementally to CSV
            with open(output_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)

    print("\n" + "=" * 105)
    print(f"Benchmark finished! Summary written to: {output_csv}")
    print("=" * 105)


def main():
    parser = argparse.ArgumentParser(description="Run SALB3PM benchmark suite across solvers.")
    parser.add_argument("--dir", "-D", type=str, default="data/benchmarks/salb3pm-97")
    parser.add_argument(
        "--solvers", "-s", nargs="+", default=DEFAULT_SOLVERS, choices=sorted(SOLVERS.keys())
    )
    parser.add_argument("--timeout", "-t", type=float, default=60.0)
    parser.add_argument("--limit", "-l", type=int, default=None)
    parser.add_argument("--output", "-o", type=str, default="results/benchmark_summary.csv")
    args = parser.parse_args()

    run_benchmark_suite(
        instance_dir=args.dir,
        solvers=args.solvers,
        timeout_seconds=args.timeout,
        limit=args.limit,
        output_csv=args.output,
    )


if __name__ == "__main__":
    main()
