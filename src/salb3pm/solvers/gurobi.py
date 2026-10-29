"""Gurobi MIP adapter using the common time-indexed baseline."""

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
    solver_name = "gurobi"
    try:
        import gurobipy as gp
    except ImportError as error:
        return result(
            instance, solver_name, None, "NOT_RUN", None, None, started, message=str(error)
        )

    try:
        formulation, tasks = prepare(instance)
        model = gp.Model("salb3pm")
        model.Params.OutputFlag = int(log_path is not None)
        if time_limit_seconds is not None:
            model.Params.TimeLimit = time_limit_seconds
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            model.Params.LogFile = str(log_path)

        placed: dict[Placement, gp.Var] = {
            placement: model.addVar(
                vtype=gp.GRB.BINARY, name=f"p_{placement[0]}_{placement[1]}_{placement[2]}"
            )
            for placement in formulation.placements
        }
        peak = model.addVar(
            lb=formulation.lower_bound,
            ub=formulation.upper_bound,
            vtype=gp.GRB.INTEGER,
            name="peak",
        )
        for task_id in tasks:
            model.addConstr(gp.quicksum(placed[p] for p in formulation.by_task[task_id]) == 1)
        for placements in formulation.by_station.values():
            model.addConstr(
                gp.quicksum(tasks[p[0]].duration * placed[p] for p in placements)
                <= instance.cycle_time
            )
        for placements in formulation.station_occupancy_rows():
            model.addConstr(gp.quicksum(placed[p] for p in placements) <= 1)
        for predecessor, successor in instance.precedence:
            model.addConstr(
                gp.quicksum(p[1] * placed[p] for p in formulation.by_task[predecessor])
                <= gp.quicksum(p[1] * placed[p] for p in formulation.by_task[successor])
            )
        for first, second in formulation.precedence_same_station_pairs:
            model.addConstr(placed[first] + placed[second] <= 1)
        for time_unit, placements in formulation.by_power_time.items():
            if not placements:
                continue
            model.addConstr(
                gp.quicksum(tasks[p[0]].power * placed[p] for p in placements) <= peak,
                name=f"peak_at_{time_unit}",
            )

        model.setObjective(peak, gp.GRB.MINIMIZE)
        model.optimize()
        schedule = None
        objective = None
        bound = None
        if model.SolCount:
            values = {p: var.X for p, var in placed.items()}
            schedule = chosen_schedule(formulation.placements, values)
            objective = round(model.ObjVal)
            bound = float(model.ObjBound)
        if model.Status == gp.GRB.OPTIMAL:
            canonical = "OPTIMAL"
        elif model.Status == gp.GRB.TIME_LIMIT:
            canonical = "FEASIBLE" if schedule else "TIMEOUT"
        elif model.Status == gp.GRB.INFEASIBLE:
            canonical = "UNSAT"
        elif schedule is not None:
            canonical = "FEASIBLE"
        else:
            canonical = "ERROR"
        return result(
            instance,
            solver_name,
            version("gurobipy"),
            canonical,
            objective,
            bound,
            started,
            schedule,
            None if canonical != "ERROR" else f"Gurobi status {model.Status}",
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
