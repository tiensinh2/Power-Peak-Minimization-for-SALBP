"""
Entry point to run the Binary MaxSAT model on SALB3PM instances.
Usage:
  python -m binary_model.main [--file path/to/instance.json] [--export output.wcnf]
"""

import argparse

from common.instance import SALB3PMInstance
from common.visualizer import print_solution_details

from binary_model.solver import BinaryMaxSATSolver


def main():
    parser = argparse.ArgumentParser(
        description="Solve SALB3PM using Enhanced Binary MaxSAT Model."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="Path to JSON instance file (default: Paper Example Fig 1)",
    )
    parser.add_argument(
        "--export", "-e", type=str, default=None, help="Export encoded WCNF formula to file"
    )
    parser.add_argument(
        "--solver", "-s", type=str, default="g4", help="Underlying SAT solver for RC2 (default: g4)"
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

    solver = BinaryMaxSATSolver(instance)

    if args.export:
        solver.export_wcnf(args.export)
        print(f"WCNF formula exported to {args.export}")

    print("Encoding and solving with Binary MaxSAT model...")
    solution = solver.solve(solver_name=args.solver)

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
