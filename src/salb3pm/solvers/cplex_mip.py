"""CPLEX MIP adapter using DOcplex and the common time-indexed baseline."""

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
    solver_name = "cplex-mip"
    try:
        from docplex.mp.model import Model
    except ImportError as error:
        return result(
            instance, solver_name, None, "NOT_RUN", None, None, started, message=str(error)
        )

    log_stream = open_log(log_path)
    try:
        formulation, tasks = prepare(instance)
        model = Model(name="salb3pm")
        placed: dict[Placement, object] = model.binary_var_dict(formulation.placements, name="p")
        peak = model.integer_var(
            lb=formulation.lower_bound,
            ub=formulation.upper_bound,
            name="peak",
        )

        for task_id in tasks:
            model.add_constraint(model.sum(placed[p] for p in formulation.by_task[task_id]) == 1)
        for placements in formulation.by_station.values():
            model.add_constraint(
                model.sum(tasks[p[0]].duration * placed[p] for p in placements)
                <= instance.cycle_time
            )
        for placements in formulation.station_occupancy_rows():
            model.add_constraint(model.sum(placed[p] for p in placements) <= 1)
        for predecessor, successor in instance.precedence:
            model.add_constraint(
                model.sum(p[1] * placed[p] for p in formulation.by_task[predecessor])
                <= model.sum(p[1] * placed[p] for p in formulation.by_task[successor])
            )
        for first, second in formulation.precedence_same_station_pairs:
            model.add_constraint(placed[first] + placed[second] <= 1)
        for placements in formulation.power_rows():
            model.add_constraint(
                model.sum(tasks[p[0]].power * placed[p] for p in placements) <= peak
            )

        model.minimize(peak)
        if time_limit_seconds is not None:
            model.parameters.timelimit = time_limit_seconds
        solution = model.solve(log_output=log_stream)
        details = model.solve_details
        status_text = (details.status or "").lower()
        schedule = None
        objective = None
        if solution is not None:
            schedule = chosen_schedule(
                formulation.placements,
                {p: float(solution.get_value(var)) for p, var in placed.items()},
            )
            objective = round(solution.get_objective_value())
        if "optimal" in status_text:
            canonical = "OPTIMAL"
        elif "infeasible" in status_text:
            canonical = "UNSAT"
        elif "time limit" in status_text or "abort" in status_text:
            canonical = "FEASIBLE" if schedule else "TIMEOUT"
        else:
            canonical = "FEASIBLE" if schedule else "ERROR"
        raw_bound = getattr(details, "best_bound", None)
        bound = float(raw_bound) if raw_bound is not None else None
        return result(
            instance,
            solver_name,
            version("cplex"),
            canonical,
            objective,
            bound,
            started,
            schedule,
            None if canonical not in ("ERROR", "TIMEOUT") else details.status,
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
