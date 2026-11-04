"""
MaxSAT and SAT solver adapters for SALB3PM.
Supports:
  - maxsat-inaugural / maxsat-unary (Section III-A)
  - maxsat-binary (Section III-B)
  - sat-iterative (Py et al. 2024 / CaDiCaL)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
curr = Path(__file__).resolve()
while curr != curr.parent:
    if (curr / "pyproject.toml").exists() or (curr / "inaugural_model").exists():
        if str(curr) not in sys.path:
            sys.path.insert(0, str(curr))
        break
    curr = curr.parent
if str(Path.cwd()) not in sys.path:
    sys.path.insert(0, str(Path.cwd()))

from binary_model.solver import BinaryMaxSATSolver
from common.instance import SALB3PMInstance
from inaugural_model.solver import InauguralMaxSATSolver
from iterative_sat.solver import IterativeSATSolver

from salb3pm.schema import Assignment, Instance, Schedule, SolverResult


def _to_common_instance(instance: Instance) -> SALB3PMInstance:
    """Convert schema.Instance to common.instance.SALB3PMInstance."""
    return SALB3PMInstance.from_dict(instance.to_dict())


def _to_solver_result(
    instance_id: str, solver_name: str, sol, elapsed: float, status: str = "OPTIMAL"
) -> SolverResult:
    if sol is None:
        return SolverResult(
            instance_id=instance_id,
            solver=solver_name,
            solver_version="pysat-rc2",
            status="UNSAT_OR_TIMEOUT",
            objective=None,
            best_bound=None,
            runtime_seconds=elapsed,
            schedule=None,
            message="No solution found within resource limits.",
        )

    assignments = {
        task_id: Assignment(station=sol.task_station[task_id], start=sol.task_start[task_id])
        for task_id in range(1, sol.instance.num_tasks + 1)
        if task_id in sol.task_station and task_id in sol.task_start
    }

    return SolverResult(
        instance_id=instance_id,
        solver=solver_name,
        solver_version="pysat",
        status=status,
        objective=sol.peak_power,
        best_bound=float(sol.instance.lower_bound),
        runtime_seconds=elapsed,
        schedule=Schedule(assignments=assignments),
        message="Optimal solution found.",
    )


def solve_maxsat_inaugural(
    instance: Instance,
    time_limit_seconds: float | None = 3600,
    log_path: Path | None = None,
) -> SolverResult:
    """Solve using Inaugural MaxSAT model (Unary threshold)."""
    common_inst = _to_common_instance(instance)
    solver = InauguralMaxSATSolver(common_inst)
    start = time.perf_counter()
    sol = solver.solve()
    elapsed = time.perf_counter() - start
    return _to_solver_result(instance.id, "maxsat-inaugural", sol, elapsed)


def solve_maxsat_binary(
    instance: Instance,
    time_limit_seconds: float | None = 3600,
    log_path: Path | None = None,
) -> SolverResult:
    """Solve using Binary Representation MaxSAT model."""
    common_inst = _to_common_instance(instance)
    solver = BinaryMaxSATSolver(common_inst)
    start = time.perf_counter()
    sol = solver.solve()
    elapsed = time.perf_counter() - start
    return _to_solver_result(instance.id, "maxsat-binary", sol, elapsed)


def solve_sat_iterative(
    instance: Instance,
    time_limit_seconds: float | None = 3600,
    log_path: Path | None = None,
) -> SolverResult:
    """Solve using Iterative SAT with CaDiCaL oracle."""
    common_inst = _to_common_instance(instance)
    solver = IterativeSATSolver(common_inst)
    start = time.perf_counter()
    sol = solver.solve(solver_name="cadical153")
    elapsed = time.perf_counter() - start
    return _to_solver_result(instance.id, "sat-iterative", sol, elapsed)
