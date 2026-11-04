"""
MaxSAT Solver interface for the Inaugural Model using PySAT RC2 or exporting WCNF.
"""

import time

from common.instance import SALB3PMInstance, SALB3PMSolution
from pysat.examples.rc2 import RC2

from .encoder import InauguralMaxSATEncoder


class InauguralMaxSATSolver:
    """
    Solver for the Inaugural MaxSAT model.
    """

    def __init__(self, instance: SALB3PMInstance):
        self.instance = instance
        self.encoder = InauguralMaxSATEncoder(instance)
        self.wcnf = None

    def solve(self, solver_name: str = "g4", verbose: int = 0) -> SALB3PMSolution | None:
        """
        Encode and solve the instance using RC2 MaxSAT solver.

        Args:
            solver_name: Underlying SAT solver for RC2 (e.g. 'g4', 'cd15', 'm22', 'cadical153')
            verbose: Verbosity level for RC2 solver

        Returns:
            SALB3PMSolution if optimal/feasible solution found, None otherwise.
        """
        start_time = time.perf_counter()

        # 1. Encode into WCNF
        self.wcnf = self.encoder.encode()

        # 2. Run MaxSAT Solver
        with RC2(self.wcnf, solver=solver_name, verbose=verbose) as rc2:
            model = rc2.compute()
            solving_time = time.perf_counter() - start_time

            if model is None:
                return None

            # 3. Decode solution
            solution = self.encoder.decode_solution(model, solving_time=solving_time)
            return solution

    def export_wcnf(self, filepath: str) -> None:
        """
        Export the encoded formula to a standard DIMACS WCNF file.
        """
        if self.wcnf is None:
            self.wcnf = self.encoder.encode()
        self.wcnf.to_file(filepath)
