# Dataset notes

The repository starts without an external benchmark corpus. Keep tiny hand-authored instances under `data/instances/`; do not label them as benchmark data.

Before adding a benchmark family, record:

- original publication/repository and direct download URL;
- family and instance names, number of tasks, stations, cycle time, and precedence-arc count;
- file format and any conversion script/command;
- license or reuse terms, release/version, and SHA-256 checksum;
- known best objective values and their source, when available.

Keep downloads out of Git unless size and terms permit distribution. Commit metadata and a repeatable acquisition/conversion script so all group members can reconstruct the dataset. Store local downloads under `data/benchmarks/` (ignored by Git).
