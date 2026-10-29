"""Typed input and output objects shared by SALB3PM solver backends."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    duration: int
    power: int


@dataclass(frozen=True, slots=True)
class Instance:
    id: str
    cycle_time: int
    stations: int
    tasks: tuple[Task, ...]
    precedence: tuple[tuple[int, int], ...]
    dataset_version: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Instance:
        tasks = tuple(
            Task(
                id=_integer(task["id"], "task id"),
                duration=_integer(task["duration"], "task duration"),
                power=_integer(task["power"], "task power"),
            )
            for task in data["tasks"]
        )
        precedence = tuple(
            tuple(_integer(task_id, "precedence task ID") for task_id in arc)
            for arc in data.get("precedence", [])
        )
        if any(len(arc) != 2 for arc in precedence):
            raise ValueError("Each precedence arc must contain predecessor and successor IDs")
        return cls(
            id=str(data["id"]),
            cycle_time=_integer(data["cycle_time"], "cycle_time"),
            stations=_integer(data["stations"], "stations"),
            tasks=tasks,
            precedence=precedence,  # type: ignore[arg-type]
            dataset_version=data.get("dataset_version"),
        )

    @classmethod
    def read_json(cls, path: str | Path) -> Instance:
        with Path(path).open(encoding="utf-8") as stream:
            return cls.from_dict(json.load(stream))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["precedence"] = [list(arc) for arc in self.precedence]
        return data


@dataclass(frozen=True, slots=True)
class Assignment:
    station: int
    start: int


@dataclass(frozen=True, slots=True)
class Schedule:
    assignments: dict[int, Assignment]

    def to_dict(self) -> dict[str, Any]:
        return {
            str(task_id): asdict(assignment)
            for task_id, assignment in sorted(self.assignments.items())
        }


@dataclass(frozen=True, slots=True)
class SolverResult:
    instance_id: str
    solver: str
    solver_version: str | None
    status: str
    objective: int | None
    best_bound: float | None
    runtime_seconds: float
    schedule: Schedule | None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "solver": self.solver,
            "solver_version": self.solver_version,
            "status": self.status,
            "objective": self.objective,
            "best_bound": self.best_bound,
            "runtime_seconds": self.runtime_seconds,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "message": self.message,
        }


def _integer(value: Any, field: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{field} must be an integer")
    return value
