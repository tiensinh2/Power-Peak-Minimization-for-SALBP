# Implementation plan

This plan is a shared checklist. Update task owners and status in pull requests; do not report an experiment as completed without a committed command/configuration and a result record.

## Work sequence

1. **Setup and contracts** — reproducible `uv` environment; document instance, schedule, and result schemas; establish independent validation.
2. **Paper model** — implement and review the inaugural unary MaxSAT model from Section III-A (Fig. 3, constraints 1–11) using PySAT PB encoding where applicable.
3. **Binary model** — implement Section III-B (Fig. 4) and compare variable/clause counts and objective values to the unary model.
4. **Baselines** — implement CP-SAT, MIP (Gurobi/CPLEX), and CP (CP Optimizer) variants when available; clearly mark unavailable solver/license combinations.
5. **Benchmark and experiments** — record dataset provenance, versions, hardware, seeds, timeout, status and metrics; preserve raw data and runner commands.
6. **Plots and report** — generate figures with `cnsplots`; write the paper-style report with repository link in Data Availability.

## Definition of done for a model

- Model formulation is mapped to paper equations and reviewed by another team member.
- Small instances are independently validated; infeasible and boundary cases are covered.
- Runs return a documented status (`OPTIMAL`, `FEASIBLE`, `UNSAT`, `TIMEOUT`, `ERROR`, or `NOT_RUN`) with objective and runtime where available.
- A reproducible command and machine-readable result record are provided.
- README/docs accurately describe implemented behavior and limitations.

## Current status

- [x] Starter directory layout, `uv` packaging and clone instructions
- [x] PySAT PB + RC2 environment smoke command
- [ ] Instance schema and independent solution validator
- [ ] Unary MaxSAT model
- [ ] Binary MaxSAT model
- [ ] CP-SAT, CPLEX CP/MIP and Gurobi baselines
- [ ] Benchmark corpus and experiment runner
- [ ] `cnsplots` figures and paper report
