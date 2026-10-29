# Experiment protocol

Use this protocol for every solver comparison and report experiment.

## Record for each run

- instance ID and dataset version/checksum;
- solver/model name, version, options, and encoding settings;
- operating system, CPU, memory, Python version and repository commit;
- time limit, seed, wall time, status, objective, best bound/gap if available;
- command line and path to raw machine-readable output/log.

Use consistent hardware and timeout limits when comparing methods. The reference paper uses a 3600 second cutoff, which can be adopted if practical; state any deviation. Distinguish `OPTIMAL`, `FEASIBLE`, `UNSAT`, `TIMEOUT`, `ERROR`, and `NOT_RUN`. Missing commercial solver licenses or unavailable solver installations are `NOT_RUN` with a reason, never `TIMEOUT`.

Report both objective quality and runtime. Validate every returned schedule independently before using its objective. Preserve raw CSV/JSON under `results/raw/` and logs under `results/logs/`; figures in `results/figures/` should be generated from those raw records with documented scripts/commands. Use `cnsplots` for report visualizations as requested by the assignment.

## Optional solver groups

Python packages installed through `uv` expose APIs; they do not guarantee all solver binaries, licenses or configurations. Record those separately. In particular, `docplex` is a modeling API and does not itself install IBM CPLEX Optimizer or CP Optimizer.

## Exact baseline formulation

The baseline adapters use a common sparse time-indexed formulation. A binary placement variable chooses one task, station and integer start time. The model enforces one placement per task, cycle-time capacity, station non-overlap, station order along precedence arcs, temporal precedence when connected tasks share a station, and a power-peak bound at each time unit. Task intervals use `[start, start + duration)`. Returned schedules are independently checked and their peak objective is recomputed before results are accepted.

Run one baseline with `uv run salb3pm solve <instance.json> --solver <name>`. Solver names are `cp-sat`, `cplex-cp`, `cplex-mip` and `gurobi`. The runner writes a JSON record under `results/raw/` and a solver log under `results/logs/` by default. The hand-authored JSON example is a software fixture, not benchmark data or an experimental finding.
