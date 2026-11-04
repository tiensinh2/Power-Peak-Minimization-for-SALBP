"""
Script to generate Table I (Major Families Summary) and Table II (Hard Benchmark Results)
from the experiment results CSV.
Reference: Zheng et al., ICTAI 2024, Section IV-B.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict


def generate_tables(
    csv_path: str = "results/benchmark_summary.csv", output_dir: str = "results/tables"
):
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(csv_path):
        print(f"Results file '{csv_path}' not found.")
        return

    rows: list[dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # -------------------------------------------------------------
    # TABLE I: Major Families Summary
    # -------------------------------------------------------------
    # Group by family and solver
    families = sorted({r["family"] for r in rows})
    solvers = sorted({r["solver"] for r in rows})

    # count total instances per family
    inst_by_fam = defaultdict(set)
    for r in rows:
        inst_by_fam[r["family"]].add(r["instance_id"])

    # family -> solver -> (solved_count, total_time)
    fam_stats = defaultdict(lambda: defaultdict(lambda: {"solved": 0, "time": 0.0}))

    for r in rows:
        fam = r["family"]
        sol = r["solver"]
        if r["status"] == "OPTIMAL":
            fam_stats[fam][sol]["solved"] += 1
            fam_stats[fam][sol]["time"] += float(r["runtime_seconds"])

    print("\n" + "=" * 90)
    print("TABLE I: Number of Optimally Solved Instances and Accumulated Time (Major Families)")
    print("=" * 90)

    header = f"{'Family':<12} | {'#I':<4} | " + " | ".join(f"{s:<18}" for s in solvers)
    print(header)
    print("-" * len(header))

    table_1_rows = []
    for fam in families:
        num_i = len(inst_by_fam[fam])
        solver_cells = []
        for sol in solvers:
            cnt = fam_stats[fam][sol]["solved"]
            tm = fam_stats[fam][sol]["time"]
            solver_cells.append(f"{cnt} ({tm:.1f}s)")
        row_str = f"{fam:<12} | {num_i:<4} | " + " | ".join(f"{c:<18}" for c in solver_cells)
        print(row_str)
        table_1_rows.append(row_str)

    print("=" * 90)

    # Export Table 1 to Markdown & LaTeX
    md_t1_path = os.path.join(output_dir, "table_1_families.md")
    with open(md_t1_path, "w", encoding="utf-8") as f:
        f.write("# Table I: Major Families Summary\n\n")
        f.write("| Family | #I | " + " | ".join(solvers) + " |\n")
        f.write("| :--- | :---: | " + " | ".join([":---:"] * len(solvers)) + " |\n")
        for fam in families:
            num_i = len(inst_by_fam[fam])
            cells = [
                f"{fam_stats[fam][s]['solved']} ({fam_stats[fam][s]['time']:.1f}s)" for s in solvers
            ]
            f.write(f"| **{fam}** | {num_i} | " + " | ".join(cells) + " |\n")
    print(f"Exported Table I to: {md_t1_path}")

    # -------------------------------------------------------------
    # TABLE II: Hard Benchmarks Table
    # -------------------------------------------------------------
    # Filter instances where minimum runtime across solvers > 5s or marked hard
    inst_data = defaultdict(dict)
    for r in rows:
        inst_id = r["instance_id"]
        inst_data[inst_id]["n"] = r["num_tasks"]
        inst_data[inst_id]["m"] = r["num_stations"]
        inst_data[inst_id]["c"] = r["cycle_time"]
        inst_data[inst_id]["lb"] = r["lower_bound"]
        inst_data[inst_id]["ub"] = r["upper_bound"]
        if r["status"] == "OPTIMAL":
            inst_data[inst_id][r["solver"]] = f"{float(r['runtime_seconds']):.2f}s"
            inst_data[inst_id]["opt"] = r["objective"]
        else:
            inst_data[inst_id][r["solver"]] = "-"

    print("\n" + "=" * 90)
    print("TABLE II: Results on Representative/Hard Instances")
    print("=" * 90)
    t2_header = f"{'Instance':<15} | {'n':<3} | {'m':<3} | {'c':<4} | {'OPT.':<5} | " + " | ".join(
        f"{s:<18}" for s in solvers
    )
    print(t2_header)
    print("-" * len(t2_header))

    md_t2_path = os.path.join(output_dir, "table_2_hard_instances.md")
    with open(md_t2_path, "w", encoding="utf-8") as f:
        f.write("# Table II: Benchmark Instances Evaluation\n\n")
        f.write("| Instance | n | m | c | OPT. | " + " | ".join(solvers) + " |\n")
        f.write(
            "| :--- | :---: | :---: | :---: | :---: | "
            + " | ".join([":---:"] * len(solvers))
            + " |\n"
        )

        for inst_id, d in sorted(inst_data.items()):
            n, m, c = d.get("n", ""), d.get("m", ""), d.get("c", "")
            opt = d.get("opt", "-")
            cells = [d.get(s, "-") for s in solvers]
            print(
                f"{inst_id:<15} | {n:<3} | {m:<3} | {c:<4} | {opt:<5} | "
                + " | ".join(f"{c:<18}" for c in cells)
            )
            f.write(f"| **{inst_id}** | {n} | {m} | {c} | {opt} | " + " | ".join(cells) + " |\n")

    print(f"Exported Table II to: {md_t2_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate LaTeX and Markdown tables from results.")
    parser.add_argument("--csv", type=str, default="results/benchmark_summary.csv")
    parser.add_argument("--output-dir", "-o", type=str, default="results/tables")
    args = parser.parse_args()

    generate_tables(csv_path=args.csv, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
