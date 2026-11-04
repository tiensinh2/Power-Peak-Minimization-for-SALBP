"""
Iterative SAT Solver for SALB3PM using SAT Oracle (CaDiCaL / Glucose / MiniSat).
Iteratively decreases the power peak bound until formula becomes UNSAT.
"""

import time

from common.instance import SALB3PMInstance, SALB3PMSolution
from pysat.solvers import Solver

from .encoder import IterativeSATEncoder


class IterativeSATSolver:
    """
    Solves SALB3PM by iteratively querying a SAT oracle with decreasing power upper bounds.
    """

    def __init__(self, instance: SALB3PMInstance):
        self.instance = instance
        self.encoder = IterativeSATEncoder(instance)

    def solve(
        self,
        solver_name: str = "cadical153",
        strategy: str = "linear",  # "linear" or "binary"
        verbose: bool = False,
    ) -> SALB3PMSolution | None:
        """
        Solve SALB3PM using iterative SAT oracle calls.

        Args:
            solver_name: SAT solver name in PySAT (e.g. 'cadical153', 'g4', 'm22')
            strategy: 'linear' (decrement peak by 1) or 'binary' (binary search on bounds)
            verbose: print iteration steps

        Returns:
            SALB3PMSolution if optimal solution found, None otherwise.
        """
        start_time = time.perf_counter()
        inst = self.instance
        lb = inst.lower_bound
        ub = inst.upper_bound

        # 1. Base Feasibility Encoding
        base_cnf = self.encoder.encode_base_feasibility()

        best_solution: SALB3PMSolution | None = None
        best_peak = ub + 1

        with Solver(name=solver_name, bootstrap_with=base_cnf.clauses) as sat:
            # First check: can we find ANY feasible assignment?
            if not sat.solve():
                if verbose:
                    print("Base problem is UNSAT (no feasible line balancing schedule exists).")
                return None

            model = sat.get_model()
            init_sol = self.encoder.decode_solution(model)
            best_solution = init_sol
            best_peak = init_sol.peak_power

            if verbose:
                print(
                    f"[Iterative SAT] Initial feasible solution found. Peak = {best_peak} (LB={lb})"
                )

            # If initial peak already matches lower bound, it's immediately optimal!
            if best_peak <= lb:
                best_solution.solving_time_sec = time.perf_counter() - start_time
                best_solution.is_optimal = True
                return best_solution

            # Iterative search loop
            curr_target = best_peak - 1
            iteration = 1

            while curr_target >= lb:
                if verbose:
                    print(
                        f"[Iterative SAT] Iteration {iteration}: Testing bound W_peak <= {curr_target} ..."
                    )

                # Encode PB constraint: sum(w_i * A_it) <= curr_target for all t
                bound_clauses, _ = self.encoder.encode_power_bound(curr_target)

                # Add new clauses to SAT solver
                for cl in bound_clauses:
                    sat.add_clause(cl)

                # Query SAT oracle
                is_sat = sat.solve()

                if is_sat:
                    model = sat.get_model()
                    sol = self.encoder.decode_solution(model)
                    best_solution = sol
                    best_peak = sol.peak_power
                    if verbose:
                        print(f"[Iterative SAT] -> SAT! New best peak = {best_peak}")

                    if best_peak <= lb:
                        if verbose:
                            print("[Iterative SAT] Lower bound reached. Optimal!")
                        break

                    curr_target = best_peak - 1
                else:
                    if verbose:
                        print(f"[Iterative SAT] -> UNSAT! Optimal peak is {best_peak}.")
                    break

                iteration += 1

        if best_solution:
            best_solution.solving_time_sec = time.perf_counter() - start_time
            best_solution.is_optimal = True

        return best_solution
