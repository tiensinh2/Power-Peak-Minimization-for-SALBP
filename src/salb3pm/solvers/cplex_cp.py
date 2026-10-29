"""IBM CP Optimizer adapter using DOcplex CP and the common formulation."""

from __future__ import annotations

import time
from importlib.metadata import version
from pathlib import Path

from salb3pm.models.baseline_formulation import Placement
from salb3pm.schema import Instance
from salb3pm.solvers.common import (
    chosen_schedule,
    failure_status,
    open_log,
    prepare,
    result,
)


def solve(
    instance: Instance,
    time_limit_seconds: float | None = 3600,
    log_path: Path | None = None,
):
    started = time.perf_counter()
    solver_name = "cplex-cp"
    try:
        from docplex.cp.expression import binary_var, integer_var
        from docplex.cp.model import CpoModel
    except ImportError as error:
        return result(
            instance, solver_name, None, "NOT_RUN", None, None, started, message=str(error)
        )

    log_stream = open_log(log_path)
    try:
        formulation, tasks = prepare(instance)
        model = CpoModel(name="salb3pm")
        placed: dict[Placement, object] = {
            placement: binary_var(name=f"p_{placement[0]}_{placement[1]}_{placement[2]}")
            for placement in formulation.placements
        }
        peak = integer_var(
            min=formulation.lower_bound,
            max=formulation.upper_bound,
            name="peak",
        )

        for task_id in tasks:
            model.add(sum(placed[p] for p in formulation.by_task[task_id]) == 1)
        for placements in formulation.by_station.values():
            model.add(
                sum(tasks[p[0]].duration * placed[p] for p in placements) <= instance.cycle_time
            )
        for placements in formulation.station_occupancy_rows():
            model.add(sum(placed[p] for p in placements) <= 1)
        for predecessor, successor in instance.precedence:
            model.add(
                sum(p[1] * placed[p] for p in formulation.by_task[predecessor])
                <= sum(p[1] * placed[p] for p in formulation.by_task[successor])
            )
        for first, second in formulation.precedence_same_station_pairs:
            model.add(placed[first] + placed[second] <= 1)
        for placements in formulation.power_rows():
            model.add(sum(tasks[p[0]].power * placed[p] for p in placements) <= peak)

        model.add(model.minimize(peak))
        options = {"TimeLimit": time_limit_seconds} if time_limit_seconds is not None else {}
        if log_stream is not None:
            options["LogOutput"] = log_stream
        solution = model.solve(**options)
        status_text = (solution.get_solve_status() if solution else "Unknown").lower()
        schedule = None
        objective = None
        bound = None
        has_solution = solution is not None and solution.is_solution()
        if has_solution:
            schedule = chosen_schedule(
                formulation.placements,
                {p: float(solution.get_value(var)) for p, var in placed.items()},
            )
            objectives = solution.get_objective_values()
            objective = round(objectives[0]) if objectives else None
            bounds = solution.get_objective_bounds()
            bound = float(bounds[0]) if bounds else None
        if "optimal" in status_text:
            canonical = "OPTIMAL"
        elif "infeasible" in status_text:
            canonical = "UNSAT"
        elif has_solution:
            canonical = "FEASIBLE"
        elif "unknown" in status_text or "stopped" in status_text:
            canonical = "TIMEOUT" if time_limit_seconds is not None else "ERROR"
        else:
            canonical = "ERROR"
        return result(
            instance,
            solver_name,
            version("docplex"),
            canonical,
            objective,
            bound,
            started,
            schedule,
            None if canonical not in ("ERROR", "TIMEOUT") else status_text,
        )
    except Exception as error:  # noqa: BLE001 - expose backend failures in the result record.
        return result(
            instance,
            solver_name,
            None,
            failure_status(error),
            None,
            None,
            started,
            message=str(error),
        )
    finally:
        if log_stream is not None:
            log_stream.close()
