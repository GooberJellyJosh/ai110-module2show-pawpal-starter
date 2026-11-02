# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output of `python main.py` (the CLI demo that exercises the logic layer before the UI):

```
Today's Schedule for Jordan
================================================================
  Time   Pet      Task                    Min  Priority Done
  --------------------------------------------------------------
  07:30  Mochi    Morning walk             30  high      
  08:00  Mochi    Breakfast                10  high      
  09:00  Luna     Heartworm pill            5  high      
  18:00  Luna     Play session             20  medium    
```

## 🧪 Testing PawPal+

Run the full suite from the project root:

```bash
python -m pytest
```

`tests/test_pawpal.py` holds 36 tests, grouped by behavior:

- **Task and Pet basics:** `mark_complete()` flips the status, adding a task raises the pet's task count and stamps `pet_name`, times are normalized (`"7:05"` → `"07:05"`), invalid times/priorities/frequencies/durations raise `ValueError`, and duplicate pet names are rejected.
- **Sorting correctness:** tasks come back in chronological order (even single-digit hours), date comes before time, and priority sorting puts high before medium before low with time as the tie-breaker.
- **Filtering:** by pet (case-insensitive), by completion status, both combined, and an unknown pet name returns an empty list.
- **Recurrence logic:** completing a daily task creates a new one due the next day (including across a month boundary). Weekly tasks move forward 7 days, one-off tasks create nothing, and completing the same task twice doesn't create a duplicate.
- **Conflict detection:** flags duplicate times across pets and within one pet, and flags partial overlaps. It does *not* flag back-to-back tasks, the same time on different days, or completed tasks. A long task is flagged against every task it covers.
- **Daily plan and slots:** the greedy plan keeps high-priority tasks within the time budget and explains what it skipped. The next-available-slot search finds the first gap that fits, or returns `None` when the day is full.
- **Persistence:** saving to JSON and loading back gives identical owners, pets, and tasks.
- **Edge cases:** a pet with no tasks gives an empty schedule and no conflicts.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.8, pytest-9.2.0, pluggy-1.7.0 -- /Users/joshualookshin/Documents/FAU/Fall 2026/CEN4010 - Princ. Software Eng./Codepath/Week 4/ai110-module2show-pawpal-starter/.venv/bin/python
cachedir: .pytest_cache
rootdir: .../ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.16.0
collecting ... collected 36 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  2%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [  5%]
tests/test_pawpal.py::test_task_normalizes_single_digit_hour PASSED      [  8%]
tests/test_pawpal.py::test_task_rejects_invalid_fields[kwargs0] PASSED   [ 11%]
tests/test_pawpal.py::test_task_rejects_invalid_fields[kwargs1] PASSED   [ 13%]
tests/test_pawpal.py::test_task_rejects_invalid_fields[kwargs2] PASSED   [ 16%]
tests/test_pawpal.py::test_task_rejects_invalid_fields[kwargs3] PASSED   [ 19%]
tests/test_pawpal.py::test_task_rejects_invalid_fields[kwargs4] PASSED   [ 22%]
tests/test_pawpal.py::test_owner_rejects_duplicate_pet_names PASSED      [ 25%]
tests/test_pawpal.py::test_owner_collects_tasks_from_all_pets PASSED     [ 27%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 30%]
tests/test_pawpal.py::test_sort_by_time_orders_by_date_before_time PASSED [ 33%]
tests/test_pawpal.py::test_sort_by_priority_then_time PASSED             [ 36%]
tests/test_pawpal.py::test_todays_tasks_only_includes_that_day PASSED    [ 38%]
tests/test_pawpal.py::test_pet_with_no_tasks_gives_empty_schedule PASSED [ 41%]
tests/test_pawpal.py::test_filter_by_pet_name_is_case_insensitive PASSED [ 44%]
tests/test_pawpal.py::test_filter_by_completion_status PASSED            [ 47%]
tests/test_pawpal.py::test_filter_combines_pet_and_status PASSED         [ 50%]
tests/test_pawpal.py::test_filter_unknown_pet_returns_empty PASSED       [ 52%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_day_task PASSED [ 55%]
tests/test_pawpal.py::test_completing_weekly_task_creates_task_one_week_later PASSED [ 58%]
tests/test_pawpal.py::test_completing_one_off_task_creates_nothing PASSED [ 61%]
tests/test_pawpal.py::test_completing_twice_does_not_duplicate PASSED    [ 63%]
tests/test_pawpal.py::test_daily_recurrence_crosses_month_boundary PASSED [ 66%]
tests/test_pawpal.py::test_conflict_flags_duplicate_times_across_pets PASSED [ 69%]
tests/test_pawpal.py::test_conflict_flags_same_pet PASSED                [ 72%]
tests/test_pawpal.py::test_conflict_flags_partial_overlap PASSED         [ 75%]
tests/test_pawpal.py::test_back_to_back_tasks_do_not_conflict PASSED     [ 77%]
tests/test_pawpal.py::test_same_time_on_different_days_does_not_conflict PASSED [ 80%]
tests/test_pawpal.py::test_completed_tasks_are_ignored_for_conflicts PASSED [ 83%]
tests/test_pawpal.py::test_long_task_conflicts_with_every_task_it_covers PASSED [ 86%]
tests/test_pawpal.py::test_daily_plan_keeps_high_priority_within_budget PASSED [ 88%]
tests/test_pawpal.py::test_daily_plan_skips_completed_tasks PASSED       [ 91%]
tests/test_pawpal.py::test_next_available_slot_finds_first_gap PASSED    [ 94%]
tests/test_pawpal.py::test_next_available_slot_returns_none_when_day_is_full PASSED [ 97%]
tests/test_pawpal.py::test_json_round_trip_preserves_data PASSED         [100%]

============================== 36 passed in 0.05s ==============================
```

**Confidence level: ★★★★☆ (4/5).** Every core behavior (sorting, filtering, recurrence, conflicts, planning, persistence) has happy-path and edge-case tests, and all pass. I'm holding back one star because the Streamlit UI is only smoke-tested by hand, and because the scheduler doesn't handle tasks that run past midnight or time zones (see `reflection.md`).

## 📐 Smarter Scheduling

All scheduling logic lives in `Scheduler` in `pawpal_system.py`. Each feature is shown in `main.py`.

| Feature | Method(s) | How it works |
|---------|-----------|--------------|
| **Sorting by time** | `Scheduler.sort_by_time()` | `sorted()` with a `lambda t: (t.due_date, t.time)` key. `Task` normalizes every time to zero-padded `"HH:MM"`, so string order is chronological (`"7:30"` becomes `"07:30"`). The sort is stable, so tasks at the same time keep the order they were added in. |
| **Priority scheduling** | `Scheduler.sort_by_priority()` | Sorts high → medium → low, then by time within each level. |
| **Filtering** | `Scheduler.filter_tasks(tasks=None, pet_name=None, completed=None)` | Filters by pet name (case-insensitive), by completion status, or both. `None` means "don't filter on this." |
| **Today's tasks** | `Scheduler.get_todays_tasks(day=None)` | Every task whose `due_date` is the given day, sorted by time. |
| **Recurring tasks** | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a `daily` or `weekly` task marks it done and adds a fresh copy to the same pet, due `due_date + timedelta(days=1)` or `timedelta(weeks=1)`. `once` tasks just complete. Completing an already-completed task does nothing, so a double click can't create duplicates. |
| **Conflict detection** | `Scheduler.detect_conflicts(tasks=None)` | Sorts pending tasks by start time, then checks each one against the tasks that start before it ends (`start < other.end`), on the same day. It catches exact time matches *and* partial overlaps, for the same pet or across pets. It returns readable warning strings and never raises. Completed tasks are ignored. |
| **Daily plan within a time budget** | `Scheduler.generate_daily_plan(day=None)` | Greedy: takes pending tasks in priority order and keeps each one that still fits in `Owner.available_minutes`. Returns a `DailyPlan` with the chosen tasks (in time order), the skipped tasks, and a one-line reason for every decision. |
| **Next available slot** | `Scheduler.find_next_available_slot(duration, day=None, earliest="07:00", latest="22:00")` | Walks the gaps between the day's pending tasks and returns the first start time where a task of that length fits, or `None` if the day is full. |
| **Persistence** | `Owner.save_to_json()`, `Owner.load_from_json()` | Custom `to_dict()` / `from_dict()` on `Task` and `Pet` (dates stored as ISO strings). The Streamlit app loads `data.json` on startup and saves after every change. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
