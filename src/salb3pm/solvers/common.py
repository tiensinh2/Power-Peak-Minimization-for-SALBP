"""Shared helpers for solver adapters."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from salb3pm.models.baseline_formulation import BaselineFormulation, Placement
from salb3pm.schema import Assignment, Instance, Schedule, SolverResult
from salb3pm.validation import validate_instance, validate_schedule


def prepare(instance: Instance) -> tuple[BaselineFormulation, dict[int, Any]]:
    validate_instance(instance)
    return BaselineFormulation.build(instance), {task.id: task for task in instance.tasks}


def chosen_schedule(placements: tuple[Placement, ...], values: dict[Placement, float]) -> Schedule:
    assignments: dict[int, Assignment] = {}
    for task_id, station, start in placements:
        if values.get((task_id, station, start), 0.0) > 0.5:
            if task_id in assignments:
                raise ValueError(f"Solver returned multiple placements for task {task_id}")
            assignments[task_id] = Assignment(station=station, start=start)
    return Schedule(assignments)


def result(
    instance: Instance,
    solver: str,
    version: str | None,
    status: str,
    objective: int | None,
    best_bound: float | None,
    started: float,
    schedule: Schedule | None = None,
    message: str | None = None,
) -> SolverResult:
    if schedule is not None:
        recomputed = validate_schedule(instance, schedule)
        if objective is not None and objective != recomputed:
            return SolverResult(
                instance_id=instance.id,
                solver=solver,
                solver_version=version,
                status="ERROR",
                objective=objective,
                best_bound=best_bound,
                runtime_seconds=time.perf_counter() - started,
                schedule=schedule,
                message=f"Solver objective {objective} differs from validated peak {recomputed}",
            )
        objective = recomputed
    return SolverResult(
        instance_id=instance.id,
        solver=solver,
        solver_version=version,
        status=status,
        objective=objective,
        best_bound=best_bound,
        runtime_seconds=time.perf_counter() - started,
        schedule=schedule,
        message=message,
    )


def open_log(path: Path | None):
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8")


def failure_status(error: Exception) -> str:
    message = str(error).lower()
    unavailable_markers = (
        "license",
        "no cplex optimizer",
        "cp optimizer executable",
        "unable to locate",
        "not found",
        "community edition",
        "problem size limits exceeded",
    )
    return "NOT_RUN" if any(marker in message for marker in unavailable_markers) else "ERROR"
