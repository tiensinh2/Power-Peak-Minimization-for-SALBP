"""
Enhanced MaxSAT Model with Binary Representation for SALB3PM (Section III-B, Figure 4).
Reference: Zheng et al., "Optimizing Power Peaks in Simple Assembly Line Balancing through Maximum Satisfiability", IEEE ICTAI 2024.
"""

import math

from common.instance import SALB3PMInstance, SALB3PMSolution
from common.pb_encoder import PBEncoder
from pysat.formula import WCNF


class BinaryMaxSATEncoder:
    """
    Encoder for the Enhanced MaxSAT model with Binary Representation (Figure 4 of the paper).

    Variables:
      - X_{i,s}: task i assigned to station s (1 <= i <= n, 1 <= s <= m)
      - B_{i,t}: task i starts at time t (1 <= i <= n, 0 <= t < c)
      - A_{i,t}: task i active at time t (1 <= i <= n, 0 <= t < c)
      - binU_j: binary representation bits of peak power (0 <= j <= K, where K = ceil(log2(UB)))
    """

    def __init__(self, instance: SALB3PMInstance):
        self.instance = instance
        self.wcnf = WCNF()
        self.var_count = 0

        # Number of bits needed to represent UB: 2^(K+1) - 1 >= UB
        ub = max(1, instance.upper_bound)
        self.k_bits = math.ceil(math.log2(ub + 1))  # number of bits (indices 0 .. k_bits - 1)
        if (1 << self.k_bits) - 1 < ub:
            self.k_bits += 1

        # Variable mapping tables
        self.x_var: dict[tuple[int, int], int] = {}  # (i, s) -> var_id
        self.b_var: dict[tuple[int, int], int] = {}  # (i, t) -> var_id
        self.a_var: dict[tuple[int, int], int] = {}  # (i, t) -> var_id
        self.bin_u_var: dict[int, int] = {}  # bit_j -> var_id

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

        # 4. binU_j variables (binary bits of W_peak)
        for j in range(self.k_bits):
            self.bin_u_var[j] = self._new_var()

    def encode(self) -> WCNF:
        """
        Build and return the complete WCNF formula representing the Binary MaxSAT Model.
        """
        inst = self.instance
        n, m, c = inst.num_tasks, inst.num_stations, inst.cycle_time
        lb = inst.lower_bound
        ub_prime = (1 << self.k_bits) - 1  # sum_{j=0}^{K} 2^j

        # -------------------------------------------------------------
        # Soft Constraints (1'): (~binU_j, weight = 2^j) for j in 0..K
        # Minimize W_peak = sum_{j=0}^K 2^j * binU_j
        # -------------------------------------------------------------
        for j in range(self.k_bits):
            weight = 1 << j
            self.wcnf.append([-self.bin_u_var[j]], weight=weight)

        # -------------------------------------------------------------
        # Hard Constraints (2'): Each task assigned to exactly one station
        # sum_{s in S} X_{i,s} = 1 for all i in N
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            station_lits = [self.x_var[(i, s)] for s in range(1, m + 1)]
            for cl in PBEncoder.encode_exactly_one(station_lits):
                self.wcnf.append(cl)

        # -------------------------------------------------------------
        # Hard Constraints (3'): Precedence between stations
        # ~X_{i,s1} or ~X_{j,s2} for all (i, j) in P and s1 > s2
        # -------------------------------------------------------------
        for i, j in inst.precedences:
            for s1 in range(1, m + 1):
                for s2 in range(1, s1):
                    self.wcnf.append([-self.x_var[(i, s1)], -self.x_var[(j, s2)]])

        # -------------------------------------------------------------
        # Hard Constraints (4'): Precedence on the same station
        # If assigned to same station s and i < j, i cannot start after j
        # ~X_{i,s} or ~X_{j,s} or ~B_{i,t1} or ~B_{j,t2} for (i, j) in P, t1 > t2
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
        # Hard Constraints (5'): Each task starts at exactly one time unit
        # sum_{t in T} B_{i,t} = 1 for all i in N
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            start_lits = [self.b_var[(i, t)] for t in range(c)]
            for cl in PBEncoder.encode_exactly_one(start_lits):
                self.wcnf.append(cl)

        # -------------------------------------------------------------
        # Hard Constraints (6'): Feasible start time window
        # ~B_{i,t} for all t in T \ T_i (i.e. t > c - t_i)
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            t_i = inst.processing_times[i]
            for t in range(max(0, c - t_i + 1), c):
                self.wcnf.append([-self.b_var[(i, t)]])

        # -------------------------------------------------------------
        # Hard Constraints (7'): Task activity activation
        # ~B_{i,t} or A_{i, t+eps} for all i in N, t in T_i, eps in 0..t_i-1
        # Also enforce exact equivalence: A_{i,t} => exists tau in [t-t_i+1, t] B_{i,tau}
        # -------------------------------------------------------------
        for i in range(1, n + 1):
            t_i = inst.processing_times[i]
            for t in inst.feasible_start_times(i):
                for eps in range(t_i):
                    if t + eps < c:
                        self.wcnf.append([-self.b_var[(i, t)], self.a_var[(i, t + eps)]])

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
        # Hard Constraints (8'): No simultaneous tasks on same station
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
        # Hard Constraints (9'): Lower bound enforcement on binary sum
        # sum_{j=0}^K 2^j * binU_j >= LB
        # -------------------------------------------------------------
        top = self.var_count
        bin_weights = [1 << j for j in range(self.k_bits)]
        bin_lits = [self.bin_u_var[j] for j in range(self.k_bits)]

        lb_clauses, top = PBEncoder.encode_pb_geq(bin_weights, bin_lits, lb, top)
        for cl in lb_clauses:
            self.wcnf.append(cl)

        # -------------------------------------------------------------
        # Hard Constraints (11'): Power consumption constraint
        # sum_{i=1}^n w_i * A_{i,t} + sum_{j=0}^K 2^j * ~binU_j <= UB', for all t in T
        # (where UB' = sum_{j=0}^K 2^j = 2^(K+1) - 1)
        # -------------------------------------------------------------
        for t in range(c):
            pb_weights = [inst.power_consumptions[i] for i in range(1, n + 1)] + [
                1 << j for j in range(self.k_bits)
            ]
            pb_lits = [self.a_var[(i, t)] for i in range(1, n + 1)] + [
                -self.bin_u_var[j] for j in range(self.k_bits)
            ]

            pb_clauses, top = PBEncoder.encode_pb_leq(pb_weights, pb_lits, ub_prime, top)
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

        # Peak power from binU_j bits
        bin_peak = sum((1 << j) for j in range(self.k_bits) if self.bin_u_var[j] in model_set)
        actual_peak = max(power_at_time) if power_at_time else 0
        peak = max(bin_peak, actual_peak)

        return SALB3PMSolution(
            instance=inst,
            task_station=task_station,
            task_start=task_start,
            peak_power=peak,
            power_at_time=power_at_time,
            is_optimal=True,
            solving_time_sec=solving_time,
        )
