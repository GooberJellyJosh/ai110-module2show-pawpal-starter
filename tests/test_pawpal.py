"""Tests for the PawPal+ logic layer."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2026, 11, 2)


@pytest.fixture
def owner():
    """An owner with two pets and no tasks."""
    o = Owner("Jordan", available_minutes=60)
    o.add_pet(Pet("Mochi", "dog", 3))
    o.add_pet(Pet("Luna", "cat", 5))
    return o


@pytest.fixture
def scheduler(owner):
    return Scheduler(owner)


def add(owner, pet, description, time, minutes=15, priority="medium", frequency="once", day=DAY):
    """Helper: create a task on a pet and return it."""
    task = Task(description, time, minutes, priority, frequency, due_date=day)
    owner.get_pet(pet).add_task(task)
    return task


# --- Task and Pet basics ---------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert pet.task_count == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert pet.task_count == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_task_normalizes_single_digit_hour():
    assert Task("Walk", "7:05").time == "07:05"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"time": "25:00"},
        {"time": "noon"},
        {"priority": "urgent"},
        {"frequency": "monthly"},
        {"duration_minutes": 0},
    ],
)
def test_task_rejects_invalid_fields(kwargs):
    fields = {"description": "Walk", "time": "08:00", **kwargs}
    with pytest.raises(ValueError):
        Task(**fields)


def test_owner_rejects_duplicate_pet_names(owner):
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "dog"))


def test_owner_collects_tasks_from_all_pets(owner):
    add(owner, "Mochi", "Walk", "08:00")
    add(owner, "Luna", "Feed", "09:00")
    assert {t.description for t in owner.get_all_tasks()} == {"Walk", "Feed"}


# --- Sorting ---------------------------------------------------------------

def test_sort_by_time_returns_chronological_order(owner, scheduler):
    add(owner, "Mochi", "Dinner", "18:00")
    add(owner, "Luna", "Early", "7:15")  # single-digit hour must still sort first
    add(owner, "Mochi", "Lunch", "12:30")
    add(owner, "Luna", "Late morning", "10:00")
    result = scheduler.sort_by_time(owner.get_all_tasks())
    assert [t.time for t in result] == ["07:15", "10:00", "12:30", "18:00"]


def test_sort_by_time_orders_by_date_before_time(owner, scheduler):
    add(owner, "Mochi", "Tomorrow early", "06:00", day=DAY + timedelta(days=1))
    add(owner, "Mochi", "Today late", "21:00")
    assert [t.description for t in scheduler.sort_by_time(owner.get_all_tasks())] == [
        "Today late",
        "Tomorrow early",
    ]


def test_sort_by_priority_then_time(owner, scheduler):
    add(owner, "Mochi", "Low", "07:00", priority="low")
    add(owner, "Mochi", "High late", "20:00", priority="high")
    add(owner, "Luna", "High early", "09:00", priority="high")
    add(owner, "Luna", "Medium", "08:00", priority="medium")
    result = scheduler.sort_by_priority(owner.get_all_tasks())
    assert [t.description for t in result] == ["High early", "High late", "Medium", "Low"]


def test_todays_tasks_only_includes_that_day(owner, scheduler):
    add(owner, "Mochi", "Today", "08:00")
    add(owner, "Mochi", "Tomorrow", "08:00", day=DAY + timedelta(days=1))
    assert [t.description for t in scheduler.get_todays_tasks(DAY)] == ["Today"]


def test_pet_with_no_tasks_gives_empty_schedule(scheduler):
    assert scheduler.get_todays_tasks(DAY) == []
    assert scheduler.detect_conflicts() == []


# --- Filtering -------------------------------------------------------------

def test_filter_by_pet_name_is_case_insensitive(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00")
    add(owner, "Luna", "Feed", "09:00")
    assert [t.description for t in scheduler.filter_tasks(pet_name="luna")] == ["Feed"]


def test_filter_by_completion_status(owner, scheduler):
    done = add(owner, "Mochi", "Walk", "08:00")
    add(owner, "Mochi", "Feed", "09:00")
    done.mark_complete()
    assert scheduler.filter_tasks(completed=True) == [done]
    assert [t.description for t in scheduler.filter_tasks(completed=False)] == ["Feed"]


def test_filter_combines_pet_and_status(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00").mark_complete()
    add(owner, "Mochi", "Feed", "09:00")
    add(owner, "Luna", "Brush", "10:00")
    result = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    assert [t.description for t in result] == ["Feed"]


def test_filter_unknown_pet_returns_empty(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00")
    assert scheduler.filter_tasks(pet_name="Rex") == []


# --- Recurring tasks -------------------------------------------------------

def test_completing_daily_task_creates_next_day_task(owner, scheduler):
    walk = add(owner, "Mochi", "Walk", "08:00", frequency="daily")
    upcoming = scheduler.mark_task_complete(walk)

    assert walk.completed is True
    assert upcoming is not None
    assert upcoming.due_date == DAY + timedelta(days=1)
    assert upcoming.completed is False
    assert (upcoming.description, upcoming.time, upcoming.pet_name) == ("Walk", "08:00", "Mochi")
    assert owner.get_pet("Mochi").task_count == 2


def test_completing_weekly_task_creates_task_one_week_later(owner, scheduler):
    pill = add(owner, "Luna", "Pill", "09:00", frequency="weekly")
    upcoming = scheduler.mark_task_complete(pill)
    assert upcoming.due_date == DAY + timedelta(weeks=1)
    assert upcoming in owner.get_pet("Luna").tasks


def test_completing_one_off_task_creates_nothing(owner, scheduler):
    vet = add(owner, "Mochi", "Vet", "12:00")
    assert scheduler.mark_task_complete(vet) is None
    assert owner.get_pet("Mochi").task_count == 1


def test_completing_twice_does_not_duplicate(owner, scheduler):
    walk = add(owner, "Mochi", "Walk", "08:00", frequency="daily")
    scheduler.mark_task_complete(walk)
    assert scheduler.mark_task_complete(walk) is None
    assert owner.get_pet("Mochi").task_count == 2


def test_daily_recurrence_crosses_month_boundary(owner, scheduler):
    walk = add(owner, "Mochi", "Walk", "08:00", frequency="daily", day=date(2026, 11, 30))
    assert scheduler.mark_task_complete(walk).due_date == date(2026, 12, 1)


# --- Conflict detection ----------------------------------------------------

def test_conflict_flags_duplicate_times_across_pets(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00")
    add(owner, "Luna", "Feed", "08:00")
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Feed" in warnings[0]


def test_conflict_flags_same_pet(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00")
    add(owner, "Mochi", "Bath", "08:00")
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "Mochi has two tasks" in warnings[0]


def test_conflict_flags_partial_overlap(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00", minutes=30)
    add(owner, "Luna", "Pill", "08:20", minutes=5)
    assert len(scheduler.detect_conflicts()) == 1


def test_back_to_back_tasks_do_not_conflict(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00", minutes=30)
    add(owner, "Luna", "Feed", "08:30")
    assert scheduler.detect_conflicts() == []


def test_same_time_on_different_days_does_not_conflict(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00")
    add(owner, "Mochi", "Walk", "08:00", day=DAY + timedelta(days=1))
    assert scheduler.detect_conflicts() == []


def test_completed_tasks_are_ignored_for_conflicts(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00").mark_complete()
    add(owner, "Luna", "Feed", "08:00")
    assert scheduler.detect_conflicts() == []


def test_long_task_conflicts_with_every_task_it_covers(owner, scheduler):
    add(owner, "Mochi", "Hike", "08:00", minutes=120)
    add(owner, "Luna", "Feed", "08:30")
    add(owner, "Luna", "Pill", "09:30")
    assert len(scheduler.detect_conflicts()) == 2


# --- Daily plan and slots --------------------------------------------------

def test_daily_plan_keeps_high_priority_within_budget(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00", minutes=30, priority="high")
    add(owner, "Luna", "Brush", "07:00", minutes=40, priority="low")
    add(owner, "Luna", "Pill", "09:00", minutes=20, priority="high")
    plan = scheduler.generate_daily_plan(DAY)  # budget is 60 min

    assert [t.description for t in plan.scheduled] == ["Walk", "Pill"]  # time order
    assert [t.description for t in plan.skipped] == ["Brush"]
    assert plan.minutes_used == 50
    assert len(plan.reasons) == 3


def test_daily_plan_skips_completed_tasks(owner, scheduler):
    add(owner, "Mochi", "Walk", "08:00").mark_complete()
    assert scheduler.generate_daily_plan(DAY).scheduled == []


def test_next_available_slot_finds_first_gap(owner, scheduler):
    add(owner, "Mochi", "Walk", "07:00", minutes=30)
    add(owner, "Luna", "Feed", "07:40", minutes=20)
    assert scheduler.find_next_available_slot(10, DAY) == "07:30"
    assert scheduler.find_next_available_slot(30, DAY) == "08:00"


def test_next_available_slot_returns_none_when_day_is_full(owner, scheduler):
    add(owner, "Mochi", "All day", "07:00", minutes=15 * 60)
    assert scheduler.find_next_available_slot(15, DAY) is None


# --- Persistence -----------------------------------------------------------

def test_json_round_trip_preserves_data(owner, tmp_path):
    add(owner, "Mochi", "Walk", "08:00", priority="high", frequency="daily").mark_complete()
    add(owner, "Luna", "Pill", "09:00", frequency="weekly")
    path = tmp_path / "data.json"

    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded.name == "Jordan"
    assert loaded.available_minutes == 60
    assert [p.name for p in loaded.pets] == ["Mochi", "Luna"]
    assert [t.to_dict() for t in loaded.get_all_tasks()] == [t.to_dict() for t in owner.get_all_tasks()]
