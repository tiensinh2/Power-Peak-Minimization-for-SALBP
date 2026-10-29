"""OR-Tools CP-SAT adapter using the common time-indexed baseline."""

from __future__ import annotations

import time
from importlib.metadata import version
from pathlib import Path

from salb3pm.models.baseline_formulation import Placement
from salb3pm.schema import Instance
from salb3pm.solvers.common import chosen_schedule, failure_status, prepare, result


def solve(
    instance: Instance,
    time_limit_seconds: float | None = 3600,
    log_path: Path | None = None,
):
    started = time.perf_counter()
    solver_name = "cp-sat"
    try:
        from ortools.sat.python import cp_model
    except ImportError as error:
        return result(
            instance, solver_name, None, "NOT_RUN", None, None, started, message=str(error)
        )

    try:
        formulation, tasks = prepare(instance)
        model = cp_model.CpModel()
        placed: dict[Placement, cp_model.IntVar] = {
            placement: model.new_bool_var(f"p_{placement[0]}_{placement[1]}_{placement[2]}")
            for placement in formulation.placements
        }
        peak = model.new_int_var(formulation.lower_bound, formulation.upper_bound, "peak")

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
        model.minimize(peak)

        parameters = cp_model.CpSolver()
        if time_limit_seconds is not None:
            parameters.parameters.max_time_in_seconds = time_limit_seconds
        log_stream = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_stream = log_path.open("w", encoding="utf-8")
            parameters.parameters.log_search_progress = True
            parameters.log_callback = log_stream.write
        try:
            status = parameters.solve(model)
        finally:
            if log_stream is not None:
                log_stream.close()
        status_name = parameters.status_name(status)
        schedule = None
        objective = None
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            values = {p: float(parameters.value(var)) for p, var in placed.items()}
            schedule = chosen_schedule(formulation.placements, values)
            objective = round(parameters.objective_value)
            canonical = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        elif status == cp_model.INFEASIBLE:
            canonical = "UNSAT"
        elif status == cp_model.UNKNOWN:
            canonical = "TIMEOUT" if time_limit_seconds is not None else "ERROR"
        else:
            canonical = "ERROR"
        bound = (
            float(parameters.best_objective_bound)
            if status
            in (
                cp_model.OPTIMAL,
                cp_model.FEASIBLE,
            )
            else None
        )
        return result(
            instance,
            solver_name,
            version("ortools"),
            canonical,
            objective,
            bound,
            started,
            schedule,
            None if canonical != "ERROR" else status_name,
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
