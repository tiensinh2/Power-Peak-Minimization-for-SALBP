"""
Visualization script to generate Figure 5 (Cactus Plot) and Figure 6 (Scatter Log-Log Comparison)
from benchmark results CSV.
Reference: Zheng et al., ICTAI 2024, Section IV-B, IV-C.
"""

from __future__ import annotations

import argparse
import csv
import os

import matplotlib.pyplot as plt


def generate_plots(
    csv_path: str = "results/benchmark_summary.csv", output_dir: str = "results/figures"
):
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(csv_path):
        print(f"Results file '{csv_path}' not found. Please run experiments first.")
        return

    # Read data
    rows: list[dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    solvers = sorted({row["solver"] for row in rows})
    print(f"Loaded {len(rows)} execution records across solvers: {solvers}")

    # -------------------------------------------------------------
    # FIGURE 5: Cactus Plot (Cumulative solved instances vs runtime)
    # -------------------------------------------------------------
    plt.figure(figsize=(9, 6))

    colors = {
        "maxsat-binary": "#2ca02c",  # Green
        "maxsat-inaugural": "#1f77b4",  # Blue
        "sat-iterative": "#ff7f0e",  # Orange
        "cp-sat": "#9467bd",  # Purple
        "gurobi": "#d62728",  # Red
        "cplex-mip": "#8c564b",  # Brown
    }
    line_styles = {
        "maxsat-binary": "-",
        "maxsat-inaugural": "--",
        "sat-iterative": "-.",
        "cp-sat": ":",
        "gurobi": "-",
        "cplex-mip": "--",
    }

    for solver in solvers:
        solver_times = [
            float(r["runtime_seconds"])
            for r in rows
            if r["solver"] == solver and r["status"] == "OPTIMAL"
        ]
        solver_times.sort()

        if not solver_times:
            continue

        cum_solved = list(range(1, len(solver_times) + 1))

        c = colors.get(solver, "#333333")
        ls = line_styles.get(solver, "-")
        plt.plot(cum_solved, solver_times, label=solver, color=c, linestyle=ls, linewidth=2.0)

    plt.xlabel("Cumulative Solved Number of Instances", fontsize=12)
    plt.ylabel("Solving Time in Seconds (Log Scale)", fontsize=12)
    plt.yscale("log")
    plt.title(
        "Figure 5: Cumulative Solved Instances vs. Runtime (SALB3PM)",
        fontsize=13,
        fontweight="bold",
    )
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend(loc="upper left", fontsize=10)
    plt.tight_layout()

    fig5_path = os.path.join(output_dir, "figure_5_cactus.png")
    plt.savefig(fig5_path, dpi=300)
    plt.close()
    print(f"Generated Figure 5 (Cactus Plot): {fig5_path}")

    # -------------------------------------------------------------
    # FIGURE 6: Scatter Plot Log-Log (Binary Model vs Inaugural Model)
    # -------------------------------------------------------------
    inaug_times: dict[str, float] = {}
    binary_times: dict[str, float] = {}

    for r in rows:
        inst_id = r["instance_id"]
        t = float(r["runtime_seconds"]) if r["status"] == "OPTIMAL" else 3600.0
        if r["solver"] in {"maxsat-inaugural", "maxsat-unary"}:
            inaug_times[inst_id] = t
        elif r["solver"] == "maxsat-binary":
            binary_times[inst_id] = t

    common_insts = set(inaug_times.keys()) & set(binary_times.keys())
    if common_insts:
        plt.figure(figsize=(7, 7))
        x_vals = [binary_times[i] for i in common_insts]
        y_vals = [inaug_times[i] for i in common_insts]

        plt.scatter(x_vals, y_vals, color="#1f77b4", alpha=0.8, edgecolors="k", s=50)

        # Diagonal y = x line
        min_val = min(min(x_vals), min(y_vals), 0.001)
        max_val = max(max(x_vals), max(y_vals), 10.0)
        plt.plot([min_val, max_val], [min_val, max_val], "r--", label="y = x (Equality)")

        plt.xscale("log")
        plt.yscale("log")
        plt.xlabel("Binary Model Runtime (s) [Log Scale]", fontsize=12)
        plt.ylabel("Inaugural Model Runtime (s) [Log Scale]", fontsize=12)
        plt.title(
            "Figure 6: Binary vs. Inaugural MaxSAT Runtime Comparison",
            fontsize=13,
            fontweight="bold",
        )
        plt.grid(True, which="both", linestyle="--", alpha=0.5)
        plt.legend(loc="upper left", fontsize=10)
        plt.tight_layout()

        fig6_path = os.path.join(output_dir, "figure_6_scatter.png")
        plt.savefig(fig6_path, dpi=300)
        plt.close()
        print(f"Generated Figure 6 (Scatter Plot): {fig6_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark evaluation plots.")
    parser.add_argument("--csv", type=str, default="results/benchmark_summary.csv")
    parser.add_argument("--output-dir", "-o", type=str, default="results/figures")
    args = parser.parse_args()

    generate_plots(csv_path=args.csv, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
