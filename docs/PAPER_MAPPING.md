# Paper-to-code mapping

Reference: Z. Zheng, S. Cherif and R. S. Shibasaki, “Optimizing Power Peaks in Simple Assembly Line Balancing through Maximum Satisfiability,” ICTAI 2024, Sections II–IV. The supplied PDF is the source of truth; page numbers below are the printed conference pages.

## Problem objects

An instance has tasks `i`, stations `s`, discrete time units `t`, task duration `d[i]`, power `w[i]`, cycle time `c`, station count `m`, and precedence arcs `P`. Each task is assigned to exactly one station and one feasible start time. Precedence must hold across stations and, for tasks sharing a station, their executions cannot overlap. At every time unit, the total power of active tasks is measured; minimize the maximum such sum.

## Paper formulations

| Paper location | Model concept | Planned code location |
| --- | --- | --- |
| Section III-A, Fig. 3, constraints (1)–(11), pp. 365–366 | Inaugural MaxSAT model; unary threshold variables for peak | `src/salb3pm/models/maxsat_unary.py` |
| Section III-B, Fig. 4, constraints (1′)–(11′), p. 366 | Binary representation of peak; weighted soft literals | `src/salb3pm/models/maxsat_binary.py` |
| Section IV-A, pp. 366–367 | Benchmark families, solver setup, 3600 second cutoff | `docs/EXPERIMENT_PROTOCOL.md` |

The paper's notation and indices should be preserved in model comments/docstrings. In particular, its `B[i,t]` is a task start trigger, `A[i,t]` is task activity, `X[i,s]` is station assignment, and peak variables encode a nonnegative upper bound on time-wise power.

## Encoding notes for implementation

- Constraints (2)–(8) encode station assignment, station precedence, within-station temporal precedence, one feasible start, feasible start windows, activity, and station non-overlap.
- Constraints (9)–(11) connect the peak representation with lower/upper bounds and total active power. The paper expresses these as pseudo-Boolean inequalities; use PySAT `PBEnc` with an explicitly recorded encoding choice.
- The unary model uses ordered threshold literals and unit-weight soft clauses. The binary model replaces them with weighted soft literals whose weights are powers of two.
- Verify variable indices, half-open task intervals, time-window boundaries, and the final partial binary digit carefully against the figures/equations. The paper's text extraction can flatten summation limits; consult the PDF figure for exact symbols.

No model is implemented yet. This note is a design aid, not a claim of equivalence or experimental reproduction.
