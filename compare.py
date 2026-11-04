"""
Benchmark and Comparison script: Inaugural MaxSAT vs Binary MaxSAT vs Iterative SAT (CaDiCaL).
Compares variable count, clause count, solving time, and optimal peak power across SALB3PM models.
"""

import sys
import glob
import os
import argparse
from typing import List

from common.instance import SALB3PMInstance
from common.visualizer import print_solution_details
from inaugural_model.encoder import InauguralMaxSATEncoder
from inaugural_model.solver import InauguralMaxSATSolver
from binary_model.encoder import BinaryMaxSATEncoder
from binary_model.solver import BinaryMaxSATSolver
from iterative_sat.solver import IterativeSATSolver


def run_comparison(instance: SALB3PMInstance, show_details: bool = False):
    print("=" * 95)
    print(f"BENCHMARK INSTANCE: {instance.name}")
    print(f"Tasks: {instance.num_tasks}, Stations: {instance.num_stations}, Cycle Time: {instance.cycle_time}")
    print(f"Lower Bound (LB): {instance.lower_bound}, Upper Bound (UB): {instance.upper_bound}")
    print("-" * 95)

    # 1. Inaugural Model
    inaug_enc = InauguralMaxSATEncoder(instance)
    inaug_wcnf = inaug_enc.encode()
    inaug_vars = inaug_enc.var_count
    inaug_hard = len(inaug_wcnf.hard)
    inaug_soft = len(inaug_wcnf.soft)

    inaug_solver = InauguralMaxSATSolver(instance)
    inaug_sol = inaug_solver.solve()

    # 2. Binary Model
    bin_enc = BinaryMaxSATEncoder(instance)
    bin_wcnf = bin_enc.encode()
    bin_vars = bin_enc.var_count
    bin_hard = len(bin_wcnf.hard)
    bin_soft = len(bin_wcnf.soft)

    bin_solver = BinaryMaxSATSolver(instance)
    bin_sol = bin_solver.solve()

    # 3. Iterative SAT Model (CaDiCaL)
    sat_solver = IterativeSATSolver(instance)
    sat_sol = sat_solver.solve(solver_name="cadical153")

    # Print comparison metrics
    header = f"{'Metric':<25} | {'Inaugural MaxSAT':<18} | {'Binary MaxSAT':<18} | {'Iterative SAT (CaDiCaL)':<24}"
    print(header)
    print("-" * len(header))
    print(f"{'Decision Variables':<25} | {inaug_vars:<18} | {bin_vars:<18} | {'N/A (Dynamic PB)':<24}")
    print(f"{'Hard Clauses':<25} | {inaug_hard:<18} | {bin_hard:<18} | {'N/A':<24}")
    print(f"{'Soft Clauses':<25} | {inaug_soft:<18} | {bin_soft:<18} | {'0 (Oracle)':<24}")
    print(f"{'Peak Power (W_peak)':<25} | {inaug_sol.peak_power if inaug_sol else 'N/A':<18} | {bin_sol.peak_power if bin_sol else 'N/A':<18} | {sat_sol.peak_power if sat_sol else 'N/A':<24}")
    print(f"{'Solving Time':<25} | {f'{inaug_sol.solving_time_sec:.4f}s' if inaug_sol else 'N/A':<18} | {f'{bin_sol.solving_time_sec:.4f}s' if bin_sol else 'N/A':<18} | {f'{sat_sol.solving_time_sec:.4f}s' if sat_sol else 'N/A':<24}")
    print("=" * 95)

    if show_details and bin_sol:
        print("\nOptimal Schedule and Profile (Binary Model):")
        print_solution_details(bin_sol)


def main():
    parser = argparse.ArgumentParser(description="Compare SALB3PM Solvers (Inaugural, Binary, Iterative SAT).")
    parser.add_argument("--file", "-f", type=str, default=None, help="Path to single JSON instance file")
    parser.add_argument("--dir", "-D", type=str, default="data/benchmarks/salb3pm-97", help="Directory of benchmark instances")
    parser.add_argument("--all", "-a", action="store_true", help="Run on all instances in benchmark directory")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Limit number of instances when running with --all")
    parser.add_argument("--details", "-d", action="store_true", help="Print schedule details")
    args = parser.parse_args()

    if args.file:
        inst = SALB3PMInstance.load_json(args.file)
        run_comparison(inst, show_details=args.details)
    elif args.all:
        files = sorted(glob.glob(os.path.join(args.dir, "*.json")))
        # Exclude manifest.json
        files = [f for f in files if not f.endswith("manifest.json")]
        if not files:
            print(f"No JSON files found in {args.dir}")
            return
        print(f"Found {len(files)} benchmark instances. Running first {args.limit}...")
        for f in files[:args.limit]:
            inst = SALB3PMInstance.load_json(f)
            run_comparison(inst, show_details=args.details)
    else:
        # Run paper example
        inst = SALB3PMInstance.create_paper_example()
        run_comparison(inst, show_details=True)


if __name__ == "__main__":
    main()
