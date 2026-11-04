"""
Iterative SAT Model for SALB3PM (Py et al. 2024 / Zheng et al. 2024 Section II-C).
Constructs base feasibility CNF formula and dynamically enforces power peak upper bounds.
"""

from common.instance import SALB3PMInstance, SALB3PMSolution
from common.pb_encoder import PBEncoder
from pysat.formula import CNF


class IterativeSATEncoder:
    """
    Encoder for the Iterative SAT approach (Py et al. 2024).

    Variables:
      - X_{i,s}: task i assigned to station s (1 <= i <= n, 1 <= s <= m)
      - B_{i,t}: task i starts at time t (1 <= i <= n, 0 <= t < c)
      - A_{i,t}: task i active at time t (1 <= i <= n, 0 <= t < c)
    """

    def __init__(self, instance: SALB3PMInstance):
        self.instance = instance
        self.var_count = 0

        # Variable mapping tables
        self.x_var: dict[tuple[int, int], int] = {}  # (i, s) -> var_id
        self.b_var: dict[tuple[int, int], int] = {}  # (i, t) -> var_id
        self.a_var: dict[tuple[int, int], int] = {}  # (i, t) -> var_id

        self._allocate_variables()

    def _new_var(self) -> int:
        self.var_count += 1
        return self.var_count

    def _allocate_variables(self) -> None:
        inst = self.instance
        n, m, c = inst.num_tasks, inst.num_stations, inst.cycle_time

        # 1. X_{i,s} variables
        for i in range(1, n + 1):
            for s in range(1, m + 1):
                self.x_var[(i, s)] = self._new_var()

        # 2. B_{i,t} variables
        for i in range(1, n + 1):
            for t in range(c):
                self.b_var[(i, t)] = self._new_var()

        # 3. A_{i,t} variables
        for i in range(1, n + 1):
            for t in range(c):
                self.a_var[(i, t)] = self._new_var()

    def encode_base_feasibility(self) -> CNF:
        """
        Build the base feasibility CNF (Constraints 2-8 from the paper, without energy bounds).
        """
        inst = self.instance
        n, m, c = inst.num_tasks, inst.num_stations, inst.cycle_time
        cnf = CNF()

        # (2) Exactly one station per task
        for i in range(1, n + 1):
            station_lits = [self.x_var[(i, s)] for s in range(1, m + 1)]
            for cl in PBEncoder.encode_exactly_one(station_lits):
                cnf.append(cl)

        # (3) Precedence between stations
        for i, j in inst.precedences:
            for s1 in range(1, m + 1):
                for s2 in range(1, s1):
                    cnf.append([-self.x_var[(i, s1)], -self.x_var[(j, s2)]])

        # (4) Precedence on same station
        for i, j in inst.precedences:
            for s in range(1, m + 1):
                for t1 in range(c):
                    for t2 in range(t1):
                        cnf.append(
                            [
                                -self.x_var[(i, s)],
                                -self.x_var[(j, s)],
                                -self.b_var[(i, t1)],
                                -self.b_var[(j, t2)],
                            ]
                        )

        # (5) Exactly one start time
        for i in range(1, n + 1):
            start_lits = [self.b_var[(i, t)] for t in range(c)]
            for cl in PBEncoder.encode_exactly_one(start_lits):
                cnf.append(cl)

        # (6) Feasible start windows
        for i in range(1, n + 1):
            t_i = inst.processing_times[i]
            for t in range(max(0, c - t_i + 1), c):
                cnf.append([-self.b_var[(i, t)]])

        # (7) Activity activation
        for i in range(1, n + 1):
            t_i = inst.processing_times[i]
            for t in inst.feasible_start_times(i):
                for eps in range(t_i):
                    if t + eps < c:
                        cnf.append([-self.b_var[(i, t)], self.a_var[(i, t + eps)]])

            for t in range(c):
                covering_starts = [
                    self.b_var[(i, tau)]
                    for tau in range(max(0, t - t_i + 1), t + 1)
                    if tau in inst.feasible_start_times(i)
                ]
                if covering_starts:
                    cnf.append([-self.a_var[(i, t)]] + covering_starts)
                else:
                    cnf.append([-self.a_var[(i, t)]])

        # (8) No simultaneous execution on same station
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                for s in range(1, m + 1):
                    for t in range(c):
                        cnf.append(
                            [
                                -self.x_var[(i, s)],
                                -self.x_var[(j, s)],
                                -self.a_var[(i, t)],
                                -self.a_var[(j, t)],
                            ]
                        )

        return cnf

    def encode_power_bound(self, bound: int) -> tuple[list[list[int]], int]:
        """
        Generate CNF clauses to enforce: sum_{i=1}^n w_i * A_{i,t} <= bound, for all t in T.
        """
        inst = self.instance
        n, c = inst.num_tasks, inst.cycle_time
        clauses: list[list[int]] = []
        top = self.var_count

        for t in range(c):
            pb_weights = [inst.power_consumptions[i] for i in range(1, n + 1)]
            pb_lits = [self.a_var[(i, t)] for i in range(1, n + 1)]

            pb_clauses, top = PBEncoder.encode_pb_leq(pb_weights, pb_lits, bound, top)
            clauses.extend(pb_clauses)

        self.var_count = top
        return clauses, top

    def decode_solution(self, model: list[int], solving_time: float = 0.0) -> SALB3PMSolution:
        """
        Decode a Boolean assignment from SAT solver into SALB3PMSolution.
        """
        inst = self.instance
        n, m, c = inst.num_tasks, inst.num_stations, inst.cycle_time
        model_set = set(model)

        task_station: dict[int, int] = {}
        for i in range(1, n + 1):
            for s in range(1, m + 1):
                if self.x_var[(i, s)] in model_set:
                    task_station[i] = s
                    break

        task_start: dict[int, int] = {}
        for i in range(1, n + 1):
            for t in range(c):
                if self.b_var[(i, t)] in model_set:
                    task_start[i] = t
                    break

        power_at_time = [0] * c
        for i in range(1, n + 1):
            st = task_start.get(i, 0)
            dur = inst.processing_times[i]
            w = inst.power_consumptions[i]
            for t in range(st, st + dur):
                if t < c:
                    power_at_time[t] += w

        peak = max(power_at_time) if power_at_time else 0

        return SALB3PMSolution(
            instance=inst,
            task_station=task_station,
            task_start=task_start,
            peak_power=peak,
            power_at_time=power_at_time,
            is_optimal=True,
            solving_time_sec=solving_time,
        )
