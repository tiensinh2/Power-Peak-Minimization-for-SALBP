"""
Visualizer and Pretty-Printer for SALB3PM Solutions.
Displays Gantt chart schedules and power consumption profiles.
"""

from common.instance import SALB3PMSolution


def print_solution_details(sol: SALB3PMSolution) -> None:
    """
    Print comprehensive details of an SALB3PM solution.
    """
    inst = sol.instance
    print("=" * 70)
    print(f"  SALB3PM SOLUTION REPORT: {inst.name}")
    print("=" * 70)
    print(
        f"Tasks (n): {inst.num_tasks} | Stations (m): {inst.num_stations} | Cycle Time (c): {inst.cycle_time}"
    )
    print(
        f"Optimal Peak Power (W_peak): {sol.peak_power}  (Lower Bound: {inst.lower_bound}, Upper Bound: {inst.upper_bound})"
    )
    print(
        f"Status: {'OPTIMAL' if sol.is_optimal else 'FEASIBLE'} | Solving Time: {sol.solving_time_sec:.4f} s"
    )
    print("-" * 70)

    # 1. Task Assignments and Schedule Table
    print(
        f"{'Task':<6} {'Station':<10} {'Start':<8} {'End':<8} {'Duration':<10} {'Power (w_i)':<12}"
    )
    print("-" * 70)
    for i in range(1, inst.num_tasks + 1):
        s = sol.task_station.get(i, -1)
        st = sol.task_start.get(i, -1)
        dur = inst.processing_times[i]
        pw = inst.power_consumptions[i]
        print(f"{i:<6} {s:<10} {st:<8} {st + dur:<8} {dur:<10} {pw:<12}")

    print("-" * 70)

    # 2. ASCII Gantt Chart for Stations
    print("SCHEDULE GANTT CHART (By Station):")
    time_header = "Station | " + "".join(f"{t:^5}" for t in range(inst.cycle_time))
    print(time_header)
    print("-" * len(time_header))

    for s in range(1, inst.num_stations + 1):
        timeline = ["  .  "] * inst.cycle_time
        station_tasks = [i for i in range(1, inst.num_tasks + 1) if sol.task_station.get(i) == s]
        for i in station_tasks:
            st = sol.task_start[i]
            dur = inst.processing_times[i]
            for t in range(st, st + dur):
                timeline[t] = f" T{i}  "
        print(f"  S{s:<4} | " + "".join(timeline))

    print("-" * 70)

    # 3. Power Consumption Profile Over Time
    print("TOTAL POWER PROFILE OVER TIME:")
    p_header = "Time    | " + "".join(f"{t:^5}" for t in range(inst.cycle_time))
    print(p_header)
    print("-" * len(p_header))
    p_values = "Power   | " + "".join(f"{sol.power_at_time[t]:^5}" for t in range(inst.cycle_time))
    print(p_values)

    # Visual power indicator
    print(
        "Peak?   | "
        + "".join(
            f"{'PEAK' if sol.power_at_time[t] == sol.peak_power else ' -- ':^5}"
            for t in range(inst.cycle_time)
        )
    )
    print("=" * 70)
