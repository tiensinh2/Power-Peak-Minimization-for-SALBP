"""Sparse time-indexed SALB3PM formulation shared by all exact baselines."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from salb3pm.schema import Instance

Placement = tuple[int, int, int]  # task ID, zero-based station, start time


@dataclass(frozen=True, slots=True)
class BaselineFormulation:
    placements: tuple[Placement, ...]
    by_task: dict[int, tuple[Placement, ...]]
    by_station: dict[int, tuple[Placement, ...]]
    by_station_time: dict[tuple[int, int], tuple[Placement, ...]]
    by_power_time: dict[int, tuple[Placement, ...]]
    precedence_same_station_pairs: tuple[tuple[Placement, Placement], ...]
    lower_bound: int
    upper_bound: int

    @classmethod
    def build(cls, instance: Instance) -> BaselineFormulation:
        durations = {task.id: task.duration for task in instance.tasks}
        powers = {task.id: task.power for task in instance.tasks}
        placements = tuple(
            (task.id, station, start)
            for task in instance.tasks
            for station in range(instance.stations)
            for start in range(instance.cycle_time - task.duration + 1)
        )

        by_task: dict[int, list[Placement]] = defaultdict(list)
        by_station: dict[int, list[Placement]] = defaultdict(list)
        by_station_time: dict[tuple[int, int], list[Placement]] = defaultdict(list)
        by_power_time: dict[int, list[Placement]] = defaultdict(list)
        for placement in placements:
            task_id, station, start = placement
            by_task[task_id].append(placement)
            by_station[station].append(placement)
            for time in range(start, start + durations[task_id]):
                by_station_time[(station, time)].append(placement)
                by_power_time[time].append(placement)

        temporal_pairs: list[tuple[Placement, Placement]] = []
        for predecessor, successor in instance.precedence:
            for station in range(instance.stations):
                pred_placements = [p for p in by_task[predecessor] if p[1] == station]
                succ_placements = [p for p in by_task[successor] if p[1] == station]
                for pred in pred_placements:
                    pred_end = pred[2] + durations[predecessor]
                    for succ in succ_placements:
                        if pred_end > succ[2]:
                            temporal_pairs.append((pred, succ))

        top_powers = sorted(powers.values(), reverse=True)[: instance.stations]
        return cls(
            placements=placements,
            by_task={key: tuple(value) for key, value in by_task.items()},
            by_station={key: tuple(value) for key, value in by_station.items()},
            by_station_time={key: tuple(value) for key, value in by_station_time.items()},
            by_power_time={key: tuple(value) for key, value in by_power_time.items()},
            precedence_same_station_pairs=tuple(temporal_pairs),
            lower_bound=max(powers.values()),
            upper_bound=sum(top_powers),
        )

    def station_occupancy_rows(self):
        return (placements for placements in self.by_station_time.values() if len(placements) > 1)

    def power_rows(self):
        return (placements for placements in self.by_power_time.values() if placements)
