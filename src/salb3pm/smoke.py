"""Small environment check; this does not solve an SALB3PM instance."""

from __future__ import annotations

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from pysat.pb import EncType, PBEnc
from pysat.solvers import Solver


def run_smoke() -> None:
    """Exercise one PB encoding and one weighted MaxSAT call."""
    # At most one of the three variables may be true.
    pb = PBEnc.atmost(lits=[1, 2, 3], bound=1, encoding=EncType.seqcounter)
    with Solver(name="g3", bootstrap_with=pb.clauses) as solver:
        assert solver.solve(assumptions=[1, 2]) is False
        assert solver.solve(assumptions=[1, -2]) is True

    formula = WCNF()
    formula.append([1])
    formula.append([-1], weight=1)
    with RC2(formula) as solver:
        model = solver.compute()
        assert model is not None
        assert solver.cost == 1

    print("PySAT PB encoding + MaxSAT RC2: OK")


if __name__ == "__main__":
    run_smoke()
