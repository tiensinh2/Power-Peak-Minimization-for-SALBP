"""
Entry point to run the Iterative SAT model (Py et al. 2024 / CaDiCaL) on SALB3PM instances.
Usage:
  python -m iterative_sat.main [--file path/to/instance.json] [--solver cadical153]
"""

import argparse

from common.instance import SALB3PMInstance
from common.visualizer import print_solution_details

from iterative_sat.solver import IterativeSATSolver


def main():
    parser = argparse.ArgumentParser(
        description="Solve SALB3PM using Iterative SAT Model (CaDiCaL)."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="Path to JSON instance file (default: Paper Example Fig 1)",
    )
    parser.add_argument(
        "--solver",
        "-s",
        type=str,
        default="cadical153",
        help="SAT solver name (default: cadical153)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print iterative search progression"
    )
    args = parser.parse_args()

    if args.file:
        instance = SALB3PMInstance.load_json(args.file)
    else:
        print("No input file provided. Running with Example from Paper (Figure 1)...")
        instance = SALB3PMInstance.create_paper_example()

    print(
        f"Loaded instance: {instance.name} (n={instance.num_tasks}, m={instance.num_stations}, c={instance.cycle_time})"
    )
    print(f"LB={instance.lower_bound}, UB={instance.upper_bound}")

    print(f"Solving with Iterative SAT (Oracle: {args.solver})...")
    solver = IterativeSATSolver(instance)
    solution = solver.solve(solver_name=args.solver, verbose=args.verbose)

    if solution:
        valid, errors = solution.validate()
        if not valid:
            print("WARNING: Solution validation errors found:")
            for err in errors:
                print(f"  - {err}")
        else:
            print("Solution successfully verified (Valid = True)!")

        print_solution_details(solution)
    else:
        print("No feasible/optimal solution found (UNSAT).")


if __name__ == "__main__":
    main()
