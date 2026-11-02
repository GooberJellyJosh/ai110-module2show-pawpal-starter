"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timedelta
from pathlib import Path

PRIORITIES = ("low", "medium", "high")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = ("once", "daily", "weekly")
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def _to_minutes(hhmm: str) -> int:
    """Convert "HH:MM" to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _to_hhmm(minutes: int) -> str:
    """Convert minutes after midnight to "HH:MM"."""
    minutes %= 24 * 60  # a task ending after midnight displays as early-morning time
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """A single pet care activity scheduled at a time on a given day."""

    description: str
    time: str  # "HH:MM", 24-hour clock
    duration_minutes: int = 15
    priority: str = "medium"  # "low" | "medium" | "high"
    frequency: str = "once"  # "once" | "daily" | "weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""  # filled in by Pet.add_task

    def __post_init__(self) -> None:
        """Validate fields and normalize time to zero-padded "HH:MM"."""
        # Normalizing matters: "7:30" would otherwise sort after "10:00" as a string.
        self.time = datetime.strptime(self.time, "%H:%M").strftime("%H:%M")
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    @property
    def start_minutes(self) -> int:
        """Start time as minutes after midnight."""
        return _to_minutes(self.time)

    @property
    def end_minutes(self) -> int:
        """End time as minutes after midnight."""
        return self.start_minutes + self.duration_minutes

    @property
    def end_time(self) -> str:
        """End time as "HH:MM"."""
        return _to_hhmm(self.end_minutes)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Return a fresh copy due on the next recurrence date, or None for one-off tasks."""
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        return replace(self, due_date=self.due_date + step, completed=False)

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict."""
        data = asdict(self)
        data["due_date"] = self.due_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Rebuild a Task from to_dict() output."""
        return cls(**{**data, "due_date": date.fromisoformat(data["due_date"])})


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and stamp it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet (no-op if it isn't there)."""
        if task in self.tasks:
            self.tasks.remove(task)

    @property
    def task_count(self) -> int:
        """Number of tasks assigned to this pet."""
        return len(self.tasks)

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        """Rebuild a Pet (and its tasks) from to_dict() output."""
        pet = cls(data["name"], data["species"], data.get("age", 0))
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str, available_minutes: int = 180) -> None:
        """Create an owner with no pets and a daily time budget for pet care."""
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet; pet names must be unique per owner."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name (case-insensitive), or None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def save_to_json(self, path: str | Path = "data.json") -> None:
        """Write the owner, pets, and tasks to a JSON file."""
        data = {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [p.to_dict() for p in self.pets],
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load_from_json(cls, path: str | Path = "data.json") -> Owner:
        """Load an owner from a JSON file written by save_to_json()."""
        data = json.loads(Path(path).read_text())
        owner = cls(data["name"], data.get("available_minutes", 180))
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner


@dataclass
class DailyPlan:
    """Result of Scheduler.generate_daily_plan(): what fits, what doesn't, and why."""

    scheduled: list[Task]
    skipped: list[Task]
    reasons: list[str]
    minutes_used: int
    minutes_available: int


class Scheduler:
    """The 'brain' that retrieves, organizes, and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that reads tasks from the given owner."""
        self.owner = owner

    def get_todays_tasks(self, day: date | None = None) -> list[Task]:
        """Return all tasks due on `day` (defaults to today), sorted by time."""
        day = day or date.today()
        return self.sort_by_time([t for t in self.owner.get_all_tasks() if t.due_date == day])

    # --- Sorting -----------------------------------------------------------

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in chronological order (date, then "HH:MM" time).

        Times are normalized to zero-padded "HH:MM", so plain string comparison
        is chronological. Python's sort is stable, so tasks at the same time keep
        the order they were added in.
        """
        return sorted(tasks, key=lambda t: (t.due_date, t.time))

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks with high priority first, breaking ties by time."""
        return sorted(tasks, key=lambda t: (PRIORITY_RANK[t.priority], t.due_date, t.time))

    # --- Filtering ---------------------------------------------------------

    def filter_tasks(
        self,
        tasks: list[Task] | None = None,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Filter tasks by pet name and/or completion status.

        `None` means "don't filter on this". With no `tasks` argument, filters
        every task the owner has.
        """
        tasks = self.owner.get_all_tasks() if tasks is None else tasks
        return [
            t
            for t in tasks
            if (pet_name is None or t.pet_name.lower() == pet_name.lower())
            and (completed is None or t.completed == completed)
        ]

    # --- Recurring tasks ---------------------------------------------------

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task; for daily/weekly tasks, schedule and return the next occurrence.

        Completing an already-completed task does nothing, so a double click in
        the UI can't create duplicate future tasks.
        """
        if task.completed:
            return None
        task.mark_complete()
        upcoming = task.next_occurrence()
        if upcoming is not None:
            pet = self.owner.get_pet(task.pet_name)
            if pet is None:
                raise ValueError(f"Task {task.description!r} is not attached to a known pet")
            pet.add_task(upcoming)
        return upcoming

    # --- Conflict detection ------------------------------------------------

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning for every pair of pending tasks whose time windows overlap.

        Two tasks conflict when they are on the same day and one starts before
        the other ends (an exact time match is the simplest case). Completed
        tasks are ignored. This never raises; an empty list means no conflicts.
        """
        tasks = self.owner.get_all_tasks() if tasks is None else tasks
        pending = self.sort_by_time([t for t in tasks if not t.completed])
        warnings = []
        for i, first in enumerate(pending):
            for second in pending[i + 1:]:
                if second.due_date != first.due_date or second.start_minutes >= first.end_minutes:
                    break  # sorted by start, so nothing later can overlap `first`
                who = (
                    f"{first.pet_name} has two tasks"
                    if first.pet_name == second.pet_name
                    else f"{first.pet_name} and {second.pet_name} both need you"
                )
                warnings.append(
                    f"Conflict on {first.due_date:%a %b %d}: {who} — "
                    f"'{first.description}' ({first.time}–{first.end_time}) overlaps "
                    f"'{second.description}' ({second.time}–{second.end_time})."
                )
        return warnings

    # --- Planning (stretch) ------------------------------------------------

    def find_next_available_slot(
        self,
        duration_minutes: int,
        day: date | None = None,
        earliest: str = "07:00",
        latest: str = "22:00",
    ) -> str | None:
        """Return the earliest "HH:MM" start where a task of this length fits with no overlap.

        Searches the gaps between pending tasks on `day` within [earliest, latest].
        Returns None if the day is full.
        """
        day = day or date.today()
        busy = [t for t in self.get_todays_tasks(day) if not t.completed]
        cursor = _to_minutes(earliest)
        for task in busy:
            if task.start_minutes - cursor >= duration_minutes:
                return _to_hhmm(cursor)
            cursor = max(cursor, task.end_minutes)
        if _to_minutes(latest) - cursor >= duration_minutes:
            return _to_hhmm(cursor)
        return None

    def generate_daily_plan(self, day: date | None = None) -> DailyPlan:
        """Choose which of the day's pending tasks fit the owner's time budget.

        Greedy: take tasks in priority order (high → low, earlier first within a
        priority) and keep each one that still fits in `owner.available_minutes`.
        The chosen tasks come back sorted by time, with a reason for every decision.
        """
        day = day or date.today()
        budget = self.owner.available_minutes
        pending = [t for t in self.get_todays_tasks(day) if not t.completed]
        scheduled, skipped, reasons = [], [], []
        used = 0
        for task in self.sort_by_priority(pending):
            label = f"{task.time} {task.pet_name}: {task.description}"
            if used + task.duration_minutes <= budget:
                scheduled.append(task)
                used += task.duration_minutes
                reasons.append(
                    f"✔ {label} — {task.priority} priority, {task.duration_minutes} min "
                    f"({used}/{budget} min used)."
                )
            else:
                skipped.append(task)
                reasons.append(
                    f"✘ {label} — skipped: needs {task.duration_minutes} min but only "
                    f"{budget - used} min left after higher-priority tasks."
                )
        return DailyPlan(self.sort_by_time(scheduled), skipped, reasons, used, budget)
