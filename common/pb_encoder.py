"""
Pseudo-Boolean (PB) and Cardinality Constraint Encoders for SAT / MaxSAT.
Encodes constraints of the form:
  - sum(w_i * x_i) <= Bound
  - sum(w_i * x_i) >= Bound
  - sum(x_i) == 1 (Exactly-One)
  - sum(x_i) <= 1 (At-Most-One)
into Conjunctive Normal Form (CNF) clauses.
"""



class PBEncoder:
    """
    Encoder for Pseudo-Boolean constraints to CNF clauses using BDD / Sorting Tree techniques.
    """

    @staticmethod
    def encode_at_least_one(lits: list[int]) -> list[list[int]]:
        """sum(lits) >= 1"""
        if not lits:
            return [[]]  # Unsatisfiable
        return [lits]

    @staticmethod
    def encode_at_most_one_pairwise(lits: list[int]) -> list[list[int]]:
        """Pairwise encoding for sum(lits) <= 1: ~l1 or ~l2 for all pairs."""
        clauses = []
        n = len(lits)
        for i in range(n):
            for j in range(i + 1, n):
                clauses.append([-lits[i], -lits[j]])
        return clauses

    @classmethod
    def encode_exactly_one(cls, lits: list[int]) -> list[list[int]]:
        """sum(lits) == 1"""
        if not lits:
            return [[]]
        if len(lits) == 1:
            return [[lits[0]]]
        clauses = cls.encode_at_least_one(lits)
        clauses.extend(cls.encode_at_most_one_pairwise(lits))
        return clauses

    @classmethod
    def encode_pb_leq(
        cls, weights: list[int], lits: list[int], bound: int, top_id: int
    ) -> tuple[list[list[int]], int]:
        """
        Encodes sum(w_i * lits[i]) <= bound into CNF using BDD (Binary Decision Diagram).

        Args:
            weights: List of positive integer weights w_i
            lits: List of literal IDs
            bound: Upper bound integer
            top_id: Current highest variable ID

        Returns:
            (clauses, new_top_id)
        """
        # Filter terms with zero weight or simplify trivial cases
        active = [(w, lit) for w, lit in zip(weights, lits) if w > 0]
        if not active:
            if bound >= 0:
                return [], top_id
            else:
                return [[]], top_id  # Unsatisfiable

        total_weight = sum(w for w, _ in active)
        if total_weight <= bound:
            return [], top_id  # Always satisfied

        if bound < 0:
            return [[]], top_id  # Impossible

        # Single term
        if len(active) == 1:
            w, lit = active[0]
            if w > bound:
                return [[-lit]], top_id
            return [], top_id

        # Use BDD / DP-based encoding
        # Node variable S[i, v]: sum of a subset of active[0..i] equals or exceeds v.
        # We only need to track sums v up to bound + 1.
        clauses: list[list[int]] = []
        curr_top = top_id

        # state_map: (step_idx, accumulated_val) -> var_id
        # We can use layer-by-layer dynamic programming
        # Layer 0: before processing any variable (sum = 0)
        # S[i, v] represents whether the accumulated sum after item i is >= v.

        # We implement a classic compact BDD for PB constraints:
        # A node node(i, C) represents the condition: sum_{j=i}^n w_j * x_j >= C
        memo: dict[tuple[int, int], int] = {}

        def get_bdd_node(i: int, c_val: int) -> int:
            nonlocal curr_top, clauses
            if c_val <= 0:
                return None  # Tautologically True

            # Check maximum possible remaining sum
            rem_max = sum(active[k][0] for k in range(i, len(active)))
            if rem_max < c_val:
                return 0  # Impossible (False)

            key = (i, c_val)
            if key in memo:
                return memo[key]

            if i == len(active) - 1:
                # Last variable
                w, lit = active[i]
                if w >= c_val:
                    memo[key] = lit
                    return lit
                else:
                    return 0

            w_i, lit_i = active[i]

            # High branch (x_i = True): remaining must be >= c_val - w_i
            high_node = get_bdd_node(i + 1, c_val - w_i)
            # Low branch (x_i = False): remaining must be >= c_val
            low_node = get_bdd_node(i + 1, c_val)

            if high_node == low_node:
                memo[key] = high_node
                return high_node

            curr_top += 1
            node_var = curr_top
            memo[key] = node_var

            # Clauses encoding: node_var <=> (lit_i and high_node) or (~lit_i and low_node)
            # 1. lit_i and high_node => node_var:
            if high_node is None:
                # lit_i and True => node_var  ==>  ~lit_i or node_var
                clauses.append([-lit_i, node_var])
            elif high_node != 0:
                # lit_i and high => node_var  ==>  ~lit_i or ~high or node_var
                clauses.append([-lit_i, -high_node, node_var])

            # 2. ~lit_i and low_node => node_var:
            if low_node is None:
                # ~lit_i and True => node_var  ==>  lit_i or node_var
                clauses.append([lit_i, node_var])
            elif low_node != 0:
                # ~lit_i and low => node_var  ==>  lit_i or ~low or node_var
                clauses.append([lit_i, -low_node, node_var])

            # 3. node_var => (lit_i and high) or (~lit_i and low)
            if high_node == 0 and low_node == 0:
                clauses.append([-node_var])
            elif high_node == 0:
                # node_var => ~lit_i and low  ==> (~node_var or ~lit_i), (~node_var or low)
                clauses.append([-node_var, -lit_i])
                if low_node is not None:
                    clauses.append([-node_var, low_node])
            elif low_node == 0:
                # node_var => lit_i and high  ==> (~node_var or lit_i), (~node_var or high)
                clauses.append([-node_var, lit_i])
                if high_node is not None:
                    clauses.append([-node_var, high_node])
            else:
                # Both branches exist
                if high_node is not None and low_node is not None:
                    clauses.append([-node_var, high_node, low_node])
                    clauses.append([-node_var, lit_i, low_node])
                    clauses.append([-node_var, -lit_i, high_node])

            return node_var

        # We forbid sum >= bound + 1
        forbidden_root = get_bdd_node(0, bound + 1)
        if forbidden_root is None:
            # sum >= bound + 1 is always True => impossible to satisfy <= bound
            return [[]], curr_top
        elif forbidden_root != 0:
            # Forbid root: root must be False
            clauses.append([-forbidden_root])

        return clauses, curr_top

    @classmethod
    def encode_pb_geq(
        cls, weights: list[int], lits: list[int], bound: int, top_id: int
    ) -> tuple[list[list[int]], int]:
        """
        Encodes sum(w_i * lits[i]) >= bound into CNF.
        Note: sum(w_i * lits[i]) >= bound <=> sum(w_i * ~lits[i]) <= sum(w_i) - bound
        """
        total_w = sum(w for w in weights if w > 0)
        if bound <= 0:
            return [], top_id  # Always satisfied for non-negative weights
        if bound > total_w:
            return [[]], top_id  # Impossible

        neg_lits = [-lit for lit in lits]
        return cls.encode_pb_leq(weights, neg_lits, total_w - bound, top_id)
