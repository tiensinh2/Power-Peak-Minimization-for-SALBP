"""Exact and MaxSAT/SAT solver adapters for SALB3PM."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from salb3pm.schema import Instance, SolverResult
from salb3pm.solvers.cp_sat import solve as solve_cp_sat
from salb3pm.solvers.cplex_cp import solve as solve_cplex_cp
from salb3pm.solvers.cplex_mip import solve as solve_cplex_mip
from salb3pm.solvers.gurobi import solve as solve_gurobi
from salb3pm.solvers.maxsat import (
    solve_maxsat_binary,
    solve_maxsat_inaugural,
    solve_sat_iterative,
)

Solver = Callable[[Instance, float | None, Path | None], SolverResult]

SOLVERS: dict[str, Solver] = {
    "cp-sat": solve_cp_sat,
    "cplex-cp": solve_cplex_cp,
    "cplex-mip": solve_cplex_mip,
    "gurobi": solve_gurobi,
    "maxsat-inaugural": solve_maxsat_inaugural,
    "maxsat-unary": solve_maxsat_inaugural,
    "maxsat-binary": solve_maxsat_binary,
    "sat-iterative": solve_sat_iterative,
    "cadical": solve_sat_iterative,
}


def solve_instance(
    solver_name: str,
    instance: Instance,
    time_limit_seconds: float | None = 3600,
    log_path: Path | None = None,
) -> SolverResult:
    try:
        solver = SOLVERS[solver_name]
    except KeyError as error:
        raise ValueError(
            f"Unknown solver {solver_name!r}; choose from {sorted(SOLVERS)}"
        ) from error
    return solver(instance, time_limit_seconds, log_path)
