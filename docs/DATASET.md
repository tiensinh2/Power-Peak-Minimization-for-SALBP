# Dataset notes

Keep tiny hand-authored instances under `data/instances/`; do not label them as benchmark data.

## Scholl 1993 SALBP benchmark

The downloaded benchmark files are organized locally under `data/benchmarks/scholl-1993/`. The archive's `precedence graphs/README.DOC` attributes the graph files to Armin Scholl, *Data of Assembly Line Balancing Problems* (Schriften zur Quantitativen Betriebswirtschaftslehre 16/93, TH Darmstadt, 1993). The project acquisition reference is the [SALBP benchmark data sets 1993 page](https://assembly-line-balancing.de/salbp/benchmark-data-sets-1993/).

The local copy contains 25 `.IN2` precedence-graph instances, the original format note, and the accompanying `SALBP data sets.xlsx` workbook. The `.IN2` format note defines the first line as task count, following lines as integer task times, then direct precedence pairs, optionally ending with `-1,-1`. The workbook is retained as received; its relationship to these graph files has not yet been documented. The local `SHA256SUMS.txt` records checksums for every raw file.

The dataset's reuse license has not yet been confirmed. Keep the raw corpus out of Git unless its terms and distribution size are reviewed. Do not treat the local checksum manifest as a substitute for recording a published release/version or license.

Before adding another benchmark family, record:

- original publication/repository and direct download URL;
- family and instance names, number of tasks, stations, cycle time, and precedence-arc count;
- file format and any conversion script/command;
- license or reuse terms, release/version, and SHA-256 checksum;
- known best objective values and their source, when available.

Keep downloads out of Git unless size and terms permit distribution. Commit metadata and a repeatable acquisition/conversion script so all group members can reconstruct the dataset. Store local downloads under `data/benchmarks/` (ignored by Git).
