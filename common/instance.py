"""
SALB3PM (Simple Assembly Line Balancing Problem with Power Peak Minimization)
Data structures and parser for problem instances.
"""

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class SALB3PMInstance:
    """
    Representation of an SALB3PM instance.

    Attributes:
        name: Instance name
        num_tasks (n): Number of tasks (indexed 1 to n)
        num_stations (m): Number of workstations (indexed 1 to m)
        cycle_time (c): Cycle time (time units 0 to c-1)
        processing_times (t): Processing time for each task (1-indexed list or dict)
        power_consumptions (w): Power consumption for each task (1-indexed list or dict)
        precedences (P): List of directed precedence pairs (i, j) meaning task i must precede task j (i ≺ j)
    """

    name: str
    num_tasks: int
    num_stations: int
    cycle_time: int
    processing_times: list[int]  # 1-indexed: index 0 unused, index 1..n for task 1..n
    power_consumptions: list[int]  # 1-indexed: index 0 unused, index 1..n for task 1..n
    precedences: list[tuple[int, int]]  # List of (i, j) with 1 <= i, j <= n

    @property
    def lower_bound(self) -> int:
        """
        LB = max_{i} w_i
        Lower bound on peak power consumption.
        """
        return max(self.power_consumptions[1:])

    @property
    def upper_bound(self) -> int:
        """
        UB = sum of m highest values of w_i.
        Since at most m tasks can be active simultaneously across m stations.
        """
        sorted_weights = sorted(self.power_consumptions[1:], reverse=True)
        return sum(sorted_weights[: self.num_stations])

    def feasible_start_times(self, task_i: int) -> range:
        """
        T_i = {0, ..., c - t_i}
        """
        t_i = self.processing_times[task_i]
        return range(self.cycle_time - t_i + 1)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SALB3PMInstance":
        # Handle schema format 1 (salb3pm.schema format)
        if "tasks" in data:
            raw_tasks = sorted(data["tasks"], key=lambda x: x["id"])
            n = len(raw_tasks)
            # Map task IDs to 1..n if necessary
            id_map = {task["id"]: idx + 1 for idx, task in enumerate(raw_tasks)}
            t = [0] + [task["duration"] for task in raw_tasks]
            w = [0] + [task["power"] for task in raw_tasks]
            raw_prec = data.get("precedence", data.get("precedences", []))
            p = [(id_map[pair[0]], id_map[pair[1]]) for pair in raw_prec]
            m = data.get("stations", data.get("num_stations", 1))
            name = str(data.get("id", data.get("name", "Instance")))
            return cls(
                name=name,
                num_tasks=n,
                num_stations=m,
                cycle_time=data["cycle_time"],
                processing_times=t,
                power_consumptions=w,
                precedences=p,
            )

        # Handle schema format 2 (direct arrays)
        n = data["num_tasks"]
        t = [0] + list(data["processing_times"])
        w = [0] + list(data["power_consumptions"])
        p = [tuple(pair) for pair in data.get("precedences", data.get("precedence", []))]
        return cls(
            name=data.get("name", data.get("id", "Instance")),
            num_tasks=n,
            num_stations=data.get("num_stations", data.get("stations", 1)),
            cycle_time=data["cycle_time"],
            processing_times=t,
            power_consumptions=w,
            precedences=p,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "num_tasks": self.num_tasks,
            "num_stations": self.num_stations,
            "cycle_time": self.cycle_time,
            "processing_times": self.processing_times[1:],
            "power_consumptions": self.power_consumptions[1:],
            "precedences": [list(pair) for pair in self.precedences],
        }

    @classmethod
    def load_json(cls, filepath: str) -> "SALB3PMInstance":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_json(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def create_paper_example(cls) -> "SALB3PMInstance":
        """
        Instance from Figure 1 of the paper:
        n = 4, m = 3, c = 5
        t = (3, 2, 2, 5)
        w = (4, 3, 4, 2)
        P = {(1,2), (1,3), (2,4), (3,4)}
        """
        return cls(
            name="Paper_Fig1_Example",
            num_tasks=4,
            num_stations=3,
            cycle_time=5,
            processing_times=[0, 3, 2, 2, 5],
            power_consumptions=[0, 4, 3, 4, 2],
            precedences=[(1, 2), (1, 3), (2, 4), (3, 4)],
        )


@dataclass
class SALB3PMSolution:
    """
    Representation of a solved SALB3PM assignment and schedule.
    """

    instance: SALB3PMInstance
    task_station: dict[int, int]  # task_i -> station s (1..m)
    task_start: dict[int, int]  # task_i -> start time t (0..c-1)
    peak_power: int
    power_at_time: list[int]  # power at time t in 0..c-1
    is_optimal: bool = True
    solving_time_sec: float = 0.0

    def validate(self) -> tuple[bool, list[str]]:
        """
        Check if the solution satisfies all problem constraints.
        """
        errors = []
        c = self.instance.cycle_time
        m = self.instance.num_stations

        # 1. Station assignments
        for i in range(1, self.instance.num_tasks + 1):
            if i not in self.task_station or not (1 <= self.task_station[i] <= m):
                errors.append(f"Task {i} invalid station assignment: {self.task_station.get(i)}")
            if i not in self.task_start:
                errors.append(f"Task {i} missing start time")
            else:
                s_time = self.task_start[i]
                t_i = self.instance.processing_times[i]
                if s_time < 0 or s_time + t_i > c:
                    errors.append(
                        f"Task {i} exceeds cycle time: start={s_time}, duration={t_i}, cycle={c}"
                    )

        # 2. Precedence constraints
        for i, j in self.instance.precedences:
            s_i = self.task_station[i]
            s_j = self.task_station[j]
            if s_i > s_j:
                errors.append(f"Precedence violation ({i} -> {j}): station {s_i} > station {s_j}")
            elif s_i == s_j:
                end_i = self.task_start[i] + self.instance.processing_times[i]
                start_j = self.task_start[j]
                if self.task_start[i] >= self.task_start[j]:
                    errors.append(
                        f"Precedence violation on same station ({i} -> {j}): start_{i}={self.task_start[i]} >= start_{j}={self.task_start[j]}"
                    )

        # 3. Non-overlapping on same station
        for s in range(1, m + 1):
            station_tasks = [
                i for i in range(1, self.instance.num_tasks + 1) if self.task_station.get(i) == s
            ]
            for idx1 in range(len(station_tasks)):
                for idx2 in range(idx1 + 1, len(station_tasks)):
                    i = station_tasks[idx1]
                    j = station_tasks[idx2]
                    start_i, end_i = (
                        self.task_start[i],
                        self.task_start[i] + self.instance.processing_times[i],
                    )
                    start_j, end_j = (
                        self.task_start[j],
                        self.task_start[j] + self.instance.processing_times[j],
                    )
                    if max(start_i, start_j) < min(end_i, end_j):
                        errors.append(
                            f"Overlap on station {s} between Task {i} [{start_i},{end_i}) and Task {j} [{start_j},{end_j})"
                        )

        # 4. Power profile verification
        calculated_power = [0] * c
        for i in range(1, self.instance.num_tasks + 1):
            st = self.task_start[i]
            dur = self.instance.processing_times[i]
            w = self.instance.power_consumptions[i]
            for t in range(st, st + dur):
                calculated_power[t] += w

        actual_peak = max(calculated_power) if calculated_power else 0
        if actual_peak != self.peak_power:
            errors.append(
                f"Reported peak ({self.peak_power}) does not match calculated peak ({actual_peak})"
            )

        return len(errors) == 0, errors
