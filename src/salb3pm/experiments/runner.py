"""Run one solver on one JSON instance and preserve reproducibility metadata."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from salb3pm.schema import Instance
from salb3pm.solvers import solve_instance
from salb3pm.validation import validate_instance


def run_one(
    instance_path: Path,
    solver_name: str,
    time_limit_seconds: float | None = 3600,
    output_path: Path | None = None,
    log_path: Path | None = None,
) -> dict:
    instance_path = instance_path.resolve()
    instance = Instance.read_json(instance_path)
    validate_instance(instance)
    input_hash = hashlib.sha256(instance_path.read_bytes()).hexdigest()
    stem = f"{instance.id}-{solver_name}"
    output_path = output_path or Path("results/raw") / f"{stem}.json"
    log_path = log_path or Path("results/logs") / f"{stem}.log"
    result = solve_instance(solver_name, instance, time_limit_seconds, log_path)

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path.cwd(), text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    output = {
        "run": {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "command": [
                "salb3pm",
                "solve",
                str(instance_path),
                "--solver",
                solver_name,
                "--time-limit",
                str(time_limit_seconds),
                "--output",
                str(output_path),
                "--log",
                str(log_path),
            ],
            "time_limit_seconds": time_limit_seconds,
            "instance_sha256": input_hash,
            "dataset_version": instance.dataset_version,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu": platform.processor() or None,
            "repository_commit": commit,
            "raw_result_path": str(output_path),
            "log_path": str(log_path),
        },
        "result": result.to_dict(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output
