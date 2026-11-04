"""
Inaugural MaxSAT Model for SALB3PM (Section III-A, Figure 3).
Reference: Zheng et al., "Optimizing Power Peaks in Simple Assembly Line Balancing through Maximum Satisfiability", IEEE ICTAI 2024.
"""

from common.instance import SALB3PMInstance, SALB3PMSolution
from common.pb_encoder import PBEncoder
from pysat.formula import WCNF


class InauguralMaxSATEncoder:
    """
    Encoder for the Inaugural MaxSAT model (Figure 3 of the paper).

    Variables:
      - X_{i,s}: task i assigned to station s (1 <= i <= n, 1 <= s <= m)
      - B_{i,t}: task i starts at time t (1 <= i <= n, 0 <= t < c)
      - A_{i,t}: task i active at time t (1 <= i <= n, 0 <= t < c)
      - U_j: peak power is at least j (1 <= j <= UB)
    """

    def __init__(self, instance: SALB3PMInstance):
        self.instance = instance
        self.wcnf = WCNF()
        self.var_count = 0

        # Variable mapping tables
        self.x_var: dict[tuple[int, int], int] = {}  # (i, s) -> var_id
        self.b_var: dict[tuple[int, int], int] = {}  # (i, t) -> var_id
        self.a_var: dict[tuple[int, int], int] = {}  # (i, t) -> var_id
        self.u_var: dict[int, int] = {}  # j -> var_id

        self._allocate_variables()

    def _new_var(self) -> int:
        self.var_count += 1
        return self.var_count

    def _allocate_variables(self) -> None:
        inst = self.instance
        n, m, c = inst.num_tasks, inst.num_stations, inst.cycle_time
        ub = inst.upper_bound

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

        # 4. U_j variables
        for j in range(1, ub + 1):
            self.u_var[j] = self._new_var()

    def encode(self) -> WCNF:
        """
        Build and return the complete WCNF formula representing the Inaugural Model.
        """
        inst = self.instance
        n, m, c = inst.num_tasks, inst.num_stations, inst.cycle_time
        lb = inst.lower_bound
        ub = inst.upper_bound

        # -------------------------------------------------------------
        # Soft Constraints (1): ~U_j with weight 1 for each j in 1..UB
        # Minimize W_peak = sum_{j=1}^UB U_j
        # -------------------------------------------------------------
        for j in range(1, ub + 1):
            self.wcnf.append([-self.u_var[j]], weight=1)

        # -------------------------------------------------------------
        # Hard Constraints (2): Each task assigned to exactly one station
        # sum_{s in S} X_{i,s} = 1 for all i in N
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            station_lits = [self.x_var[(i, s)] for s in range(1, m + 1)]
            for cl in PBEncoder.encode_exactly_one(station_lits):
                self.wcnf.append(cl)

        # -------------------------------------------------------------
        # Hard Constraints (3): Precedence between stations
        # ~X_{i,s1} or ~X_{j,s2} for all (i, j) in P and s1 > s2
        # -------------------------------------------------------------
        for i, j in inst.precedences:
            for s1 in range(1, m + 1):
                for s2 in range(1, s1):
                    self.wcnf.append([-self.x_var[(i, s1)], -self.x_var[(j, s2)]])

        # -------------------------------------------------------------
        # Hard Constraints (4): Precedence on the same station
        # If assigned to same station s and i < j, i cannot start after j
        # ~X_{i,s} or ~X_{j,s} or ~B_{i,t1} or ~B_{j,t2} for (i, j) in P, t1 > t2
        # (Combined with non-overlapping constraint 8, this ensures i precedes j)
        # -------------------------------------------------------------
        for i, j in inst.precedences:
            for s in range(1, m + 1):
                for t1 in range(c):
                    for t2 in range(t1):
                        self.wcnf.append(
                            [
                                -self.x_var[(i, s)],
                                -self.x_var[(j, s)],
                                -self.b_var[(i, t1)],
                                -self.b_var[(j, t2)],
                            ]
                        )

        # -------------------------------------------------------------
        # Hard Constraints (5): Each task starts at exactly one time unit
        # sum_{t in T} B_{i,t} = 1 for all i in N
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            start_lits = [self.b_var[(i, t)] for t in range(c)]
            for cl in PBEncoder.encode_exactly_one(start_lits):
                self.wcnf.append(cl)

        # -------------------------------------------------------------
        # Hard Constraints (6): Feasible start time window
        # ~B_{i,t} for all t in T \ T_i (i.e. t > c - t_i)
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            t_i = inst.processing_times[i]
            for t in range(max(0, c - t_i + 1), c):
                self.wcnf.append([-self.b_var[(i, t)]])

        # -------------------------------------------------------------
        # Hard Constraints (7): Task activity activation
        # ~B_{i,t} or A_{i, t+eps} for all i in N, t in T_i, eps in 0..t_i-1
        # Also enforce exact equivalence: A_{i,t} => exists tau in [t-t_i+1, t] B_{i,tau}
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            t_i = inst.processing_times[i]
            # Forward: B_{i,t} => A_{i, t+eps}
            for t in inst.feasible_start_times(i):
                for eps in range(t_i):
                    if t + eps < c:
                        self.wcnf.append([-self.b_var[(i, t)], self.a_var[(i, t + eps)]])

            # Backward: A_{i,t} => one of the valid start triggers
            for t in range(c):
                covering_starts = [
                    self.b_var[(i, tau)]
                    for tau in range(max(0, t - t_i + 1), t + 1)
                    if tau in inst.feasible_start_times(i)
                ]
                if covering_starts:
                    self.wcnf.append([-self.a_var[(i, t)]] + covering_starts)
                else:
                    self.wcnf.append([-self.a_var[(i, t)]])

        # -------------------------------------------------------------
        # Hard Constraints (8): No simultaneous tasks on same station
        # ~X_{i,s} or ~X_{j,s} or ~A_{i,t} or ~A_{j,t} for i < j, s in S, t in T
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                for s in range(1, m + 1):
                    for t in range(c):
                        self.wcnf.append(
                            [
                                -self.x_var[(i, s)],
                                -self.x_var[(j, s)],
                                -self.a_var[(i, t)],
                                -self.a_var[(j, t)],
                            ]
                        )

        # -------------------------------------------------------------
        # Hard Constraints (9): Lower bound enforcement
        # U_j for all j in 1..LB
        # -------------------------------------------------------------
        for j in range(1, lb + 1):
            self.wcnf.append([self.u_var[j]])

        # -------------------------------------------------------------
        # Hard Constraints (10): Monotonicity / Order of power units
        # ~U_j or U_{j-1} for all j in 2..UB (i.e. U_j => U_{j-1})
        # -------------------------------------------------------------
        for j in range(2, ub + 1):
            self.wcnf.append([-self.u_var[j], self.u_var[j - 1]])

        # -------------------------------------------------------------
        # Hard Constraints (11): Power consumption constraint
        # sum_{i=1}^n w_i * A_{i,t} + sum_{j=1}^UB ~U_j <= UB, for all t in T
        # -------------------------------------------------------------
        top = self.var_count
        for t in range(c):
            pb_weights = [inst.power_consumptions[i] for i in range(1, n + 1)] + [1] * ub
            pb_lits = [self.a_var[(i, t)] for i in range(1, n + 1)] + [
                -self.u_var[j] for j in range(1, ub + 1)
            ]

            pb_clauses, top = PBEncoder.encode_pb_leq(pb_weights, pb_lits, ub, top)
            for cl in pb_clauses:
                self.wcnf.append(cl)

        self.var_count = top
        return self.wcnf

    def decode_solution(self, model: list[int], solving_time: float = 0.0) -> SALB3PMSolution:
        """
        Decode a Boolean assignment from the MaxSAT solver into an SALB3PMSolution.
        """
        inst = self.instance
        n, m, c = inst.num_tasks, inst.num_stations, inst.cycle_time
        ub = inst.upper_bound

        model_set = set(model)

        # Decode station assignment
        task_station: dict[int, int] = {}
        for i in range(1, n + 1):
            for s in range(1, m + 1):
                if self.x_var[(i, s)] in model_set:
                    task_station[i] = s
                    break

        # Decode start times
        task_start: dict[int, int] = {}
        for i in range(1, n + 1):
            for t in range(c):
                if self.b_var[(i, t)] in model_set:
                    task_start[i] = t
                    break

        # Calculate power profile
        power_at_time = [0] * c
        for i in range(1, n + 1):
            st = task_start.get(i, 0)
            dur = inst.processing_times[i]
            w = inst.power_consumptions[i]
            for t in range(st, st + dur):
                if t < c:
                    power_at_time[t] += w

        # Peak power from U_j or power_at_time
        u_peak = sum(1 for j in range(1, ub + 1) if self.u_var[j] in model_set)
        actual_peak = max(power_at_time) if power_at_time else 0
        peak = max(u_peak, actual_peak)

        return SALB3PMSolution(
            instance=inst,
            task_station=task_station,
            task_start=task_start,
            peak_power=peak,
            power_at_time=power_at_time,
            is_optimal=True,
            solving_time_sec=solving_time,
        )
