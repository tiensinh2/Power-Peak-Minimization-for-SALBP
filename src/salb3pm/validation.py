"""Independent validation and objective recomputation for returned schedules."""

from __future__ import annotations

from itertools import pairwise

from salb3pm.schema import Instance, Schedule


def validate_instance(instance: Instance) -> None:
    if not instance.id:
        raise ValueError("Instance ID must not be empty")
    if instance.cycle_time <= 0 or instance.stations <= 0:
        raise ValueError("Cycle time and station count must be positive")
    if not instance.tasks:
        raise ValueError("Instance must contain at least one task")

    task_ids = [task.id for task in instance.tasks]
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("Task IDs must be unique")
    if any(task_id <= 0 for task_id in task_ids):
        raise ValueError("Task IDs must be positive integers")
    tasks = {task.id: task for task in instance.tasks}
    for task in instance.tasks:
        if task.duration <= 0 or task.power <= 0:
            raise ValueError(f"Task {task.id} must have positive duration and power")
        if task.duration > instance.cycle_time:
            raise ValueError(f"Task {task.id} is longer than the cycle time")

    seen_arcs: set[tuple[int, int]] = set()
    successors: dict[int, list[int]] = {task_id: [] for task_id in task_ids}
    indegree = {task_id: 0 for task_id in task_ids}
    for predecessor, successor in instance.precedence:
        if predecessor not in tasks or successor not in tasks:
            raise ValueError(f"Precedence arc references unknown task: {(predecessor, successor)}")
        if predecessor == successor:
            raise ValueError("A task cannot precede itself")
        if (predecessor, successor) in seen_arcs:
            raise ValueError(f"Duplicate precedence arc: {(predecessor, successor)}")
        seen_arcs.add((predecessor, successor))
        successors[predecessor].append(successor)
        indegree[successor] += 1

    ready = [task_id for task_id, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        task_id = ready.pop()
        visited += 1
        for successor in successors[task_id]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    if visited != len(tasks):
        raise ValueError("Precedence graph must be acyclic")


def validate_schedule(instance: Instance, schedule: Schedule) -> int:
    """Validate a schedule and return its independently recomputed peak power."""
    validate_instance(instance)
    tasks = {task.id: task for task in instance.tasks}
    expected = set(tasks)
    actual = set(schedule.assignments)
    if actual != expected:
        raise ValueError(
            f"Schedule task IDs differ: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )

    station_tasks: dict[int, list[tuple[int, int, int]]] = {
        station: [] for station in range(instance.stations)
    }
    for task_id, assignment in schedule.assignments.items():
        task = tasks[task_id]
        if not 0 <= assignment.station < instance.stations:
            raise ValueError(f"Task {task_id} has invalid station {assignment.station}")
        if assignment.start < 0 or assignment.start + task.duration > instance.cycle_time:
            raise ValueError(f"Task {task_id} violates the cycle-time window")
        station_tasks[assignment.station].append(
            (assignment.start, assignment.start + task.duration, task_id)
        )

    for station, intervals in station_tasks.items():
        intervals.sort()
        for previous, current in pairwise(intervals):
            if previous[1] > current[0]:
                raise ValueError(
                    f"Tasks {previous[2]} and {current[2]} overlap on station {station}"
                )

    for predecessor, successor in instance.precedence:
        before = schedule.assignments[predecessor]
        after = schedule.assignments[successor]
        if before.station > after.station:
            raise ValueError(f"Precedence {predecessor}->{successor} reverses station order")
        if before.station == after.station:
            end = before.start + tasks[predecessor].duration
            if end > after.start:
                raise ValueError(f"Precedence {predecessor}->{successor} is violated in time")

    power_by_time = [0] * instance.cycle_time
    for task_id, assignment in schedule.assignments.items():
        task = tasks[task_id]
        for time in range(assignment.start, assignment.start + task.duration):
            power_by_time[time] += task.power
    return max(power_by_time, default=0)
