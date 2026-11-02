# 🐾 PawPal+

PawPal+ is a pet care planner for busy owners. It tracks each pet's walks, feedings, medications, and appointments, then works out the day for you: it sorts everything into time order, warns you when two tasks clash, re-creates daily and weekly tasks automatically, and builds a plan that fits the time you actually have.

The logic layer (`pawpal_system.py`) is plain object-oriented Python, verified first through a CLI demo (`main.py`) and a 36-test `pytest` suite, then connected to a Streamlit UI (`app.py`).

## ✨ Features

- **Multiple pets per owner.** Each pet keeps its own task list. Duplicate pet names are rejected.
- **Rich tasks.** Each task has a description, time, duration, priority (low/medium/high), frequency (once/daily/weekly), and due date. Bad input (e.g. `"25:00"`, priority `"urgent"`) is rejected when the task is created.
- **Sorting by time.** Chronological order across all pets. `"7:30"` is normalized to `"07:30"` so string sorting stays correct.
- **Priority scheduling.** An optional view sorts high → low priority, then by time.
- **Filtering.** Show one pet's tasks, only pending or only done tasks, or both.
- **Daily/weekly recurrence.** Completing a recurring task automatically schedules the next one (`+1 day` / `+7 days` with `timedelta`).
- **Conflict warnings.** Flags tasks whose time windows overlap (exact matches *and* partial overlaps), for one pet or across pets, as friendly warnings rather than errors.
- **Time-budgeted daily plan.** Given your available care minutes, picks the highest-priority tasks that fit and explains each keep/skip decision.
- **Next available slot.** Finds the earliest gap in today's schedule for a task of a given length.
- **Data persistence.** Pets and tasks are saved to `data.json` and reloaded when the app starts.
- **Readable output.** Aligned CLI tables with 🔴🟡🟢 priority markers. In the UI, `st.table`, `st.warning`, `st.success`, and `st.metric`.

## 🚀 Getting started

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

```bash
python main.py            # CLI demo of every scheduling feature
streamlit run app.py      # interactive app
python -m pytest          # test suite
```

## 🏗️ Architecture

| Class | Responsibility |
|-------|----------------|
| `Task` (dataclass) | One care activity. Validates its own fields, knows its start/end time, and can create its `next_occurrence()`. |
| `Pet` (dataclass) | A pet's details and the tasks it owns. `add_task()` stamps each task with the pet's name. |
| `Owner` | Holds pets and a daily care-time budget. `get_all_tasks()` is the single way to collect every task, and it saves/loads JSON. |
| `Scheduler` | The "brain." It stores nothing itself. It reads tasks from the `Owner`, then sorts, filters, completes, conflict-checks, and plans. |
| `DailyPlan` (dataclass) | The result of `generate_daily_plan()`: scheduled tasks, skipped tasks, reasons, and minutes used. |

UML diagrams (Mermaid source):

- [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd): the Phase 1 design
- [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd): matches the final code (also copied to `diagrams/uml.mmd`)

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

## 🖥️ Sample Output

Output of `python main.py`. Tasks are added out of order on purpose, and two pairs of tasks overlap:

```
Tasks as entered (unsorted)
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  07:30  Mochi  Morning walk           30  🔴 high   ·
  11/01  08:00  Mochi  Breakfast              10  🔴 high   ·
  11/01  12:00  Mochi  Vet appointment        45  🟡 medium ·
  11/01  18:00  Luna   Play session           20  🟡 medium ·
  11/01  12:00  Luna   Brush coat             15  🟢 low    ·
  11/01  07:45  Luna   Heartworm pill          5  🔴 high   ·

Today's Schedule for Jordan (sorted by time)
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  07:30  Mochi  Morning walk           30  🔴 high   ·
  11/01  07:45  Luna   Heartworm pill          5  🔴 high   ·
  11/01  08:00  Mochi  Breakfast              10  🔴 high   ·
  11/01  12:00  Mochi  Vet appointment        45  🟡 medium ·
  11/01  12:00  Luna   Brush coat             15  🟢 low    ·
  11/01  18:00  Luna   Play session           20  🟡 medium ·

Sorted by priority, then time
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  07:30  Mochi  Morning walk           30  🔴 high   ·
  11/01  07:45  Luna   Heartworm pill          5  🔴 high   ·
  11/01  08:00  Mochi  Breakfast              10  🔴 high   ·
  11/01  12:00  Mochi  Vet appointment        45  🟡 medium ·
  11/01  18:00  Luna   Play session           20  🟡 medium ·
  11/01  12:00  Luna   Brush coat             15  🟢 low    ·

Filter: Luna's tasks only
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  18:00  Luna   Play session           20  🟡 medium ·
  11/01  12:00  Luna   Brush coat             15  🟢 low    ·
  11/01  07:45  Luna   Heartworm pill          5  🔴 high   ·

Conflict check
==================================================================
  ⚠️  Conflict on Sun Nov 01: Mochi and Luna both need you — 'Morning walk' (07:30–08:00) overlaps 'Heartworm pill' (07:45–07:50).
  ⚠️  Conflict on Sun Nov 01: Mochi and Luna both need you — 'Vet appointment' (12:00–12:45) overlaps 'Brush coat' (12:00–12:15).

Marked 'Morning walk' complete → next one auto-created for Mon Nov 02.

Filter: completed tasks
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  07:30  Mochi  Morning walk           30  🔴 high   ✓

Filter: Mochi's pending tasks (all dates)
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  08:00  Mochi  Breakfast              10  🔴 high   ·
  11/01  12:00  Mochi  Vet appointment        45  🟡 medium ·
  11/02  07:30  Mochi  Morning walk           30  🔴 high   ·

Daily plan (80/90 min of care time)
==================================================================
  ✔ 07:45 Luna: Heartworm pill — high priority, 5 min (5/90 min used).
  ✔ 08:00 Mochi: Breakfast — high priority, 10 min (15/90 min used).
  ✔ 12:00 Mochi: Vet appointment — medium priority, 45 min (60/90 min used).
  ✔ 18:00 Luna: Play session — medium priority, 20 min (80/90 min used).
  ✘ 12:00 Luna: Brush coat — skipped: needs 15 min but only 10 min left after higher-priority tasks.

Next free 60-minute slot today: 08:10
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

## 📸 Demo Walkthrough

Run `streamlit run app.py`. The app has a sidebar and four main areas.

**Main UI features**

- **Sidebar: Owner.** Set your name and how many minutes of pet care you have today (slider). Your pets are listed with species emoji and task counts. Everything auto-saves to `data.json`.
- **➕ Add a pet.** Enter a name, species, and age. Duplicate names show an error instead of creating a second pet.
- **🗓️ Schedule a task.** Pick a pet and enter a task name, date, time, duration, priority, and repeat frequency. If the new task overlaps an existing one, a "Heads up" warning appears right away. Below the form, a **"Need a free slot?"** helper shows the next open time today for a task of the length you choose (`find_next_available_slot`).
- **📋 Schedule.** Pick a day, then filter by pet and status and sort by time or priority (`get_todays_tasks`, `filter_tasks`, `sort_by_time` / `sort_by_priority`). A yellow `st.warning` box lists every conflict in plain language, e.g. *"Mochi and Luna both need you — 'Morning walk' (07:30–08:00) overlaps 'Heartworm pill' (07:45–07:50)"*. If there are none, a green `st.success` box confirms it. Tasks are shown in an `st.table` with time ranges, 🔴🟡🟢 priority, repeat frequency, and ✅/⏳ status. A **Mark a task complete** dropdown and **✅ Complete** button call `mark_task_complete`. For a daily/weekly task, the confirmation says when the next occurrence was scheduled.
- **🧠 Daily plan.** **Generate plan** calls `generate_daily_plan` and shows three metrics (tasks planned, minutes used / available, tasks skipped), a table of the chosen tasks in time order, a warning naming what didn't fit, and a **"Why this plan?"** expander with the reason for every decision.

**Example workflow**

1. In the sidebar, set the owner name to *Jordan* and the care time to *90 minutes*.
2. Add a pet **Mochi** (dog, 3) and a pet **Luna** (cat, 5).
3. Schedule *Morning walk* for Mochi at 07:30 (30 min, high, daily).
4. Schedule *Heartworm pill* for Luna at 07:45 (5 min, high, weekly). A "Heads up" warning appears because it overlaps the walk.
5. Add *Breakfast* (08:00), *Vet appointment* (12:00, 45 min), *Brush coat* (12:00, 15 min, low), and *Play session* (18:00, 20 min). The schedule table sorts them by time no matter what order you entered them in, and the conflict box now lists two conflicts.
6. Switch **Sort by** to *Priority* to see high-priority tasks first, or set **Show pet** to *Luna* to see only her tasks.
7. Select *07:30 · Mochi · Morning walk* and click **✅ Complete**. The row turns ✅, the walk/pill conflict disappears, and the message says the next walk is scheduled for tomorrow (switch **Day** to tomorrow to see it).
8. Click **Generate plan**. With 90 minutes available, the plan keeps the high- and medium-priority tasks and skips *Brush coat*, and "Why this plan?" explains each choice.
9. Close and restart the app. Your pets and tasks are reloaded from `data.json`.

**Key Scheduler behaviors shown:** chronological sorting, priority sorting, filtering by pet and status, overlap-based conflict warnings, automatic daily/weekly recurrence, the time-budgeted plan with explanations, next-free-slot suggestions, and persistence.

**Sample CLI output** (excerpt from `python main.py`; the full run is under Sample Output above):

```
Today's Schedule for Jordan (sorted by time)
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  07:30  Mochi  Morning walk           30  🔴 high   ·
  11/01  07:45  Luna   Heartworm pill          5  🔴 high   ·
  11/01  08:00  Mochi  Breakfast              10  🔴 high   ·
  11/01  12:00  Mochi  Vet appointment        45  🟡 medium ·
  11/01  12:00  Luna   Brush coat             15  🟢 low    ·
  11/01  18:00  Luna   Play session           20  🟡 medium ·

Conflict check
==================================================================
  ⚠️  Conflict on Sun Nov 01: Mochi and Luna both need you — 'Morning walk' (07:30–08:00) overlaps 'Heartworm pill' (07:45–07:50).
  ⚠️  Conflict on Sun Nov 01: Mochi and Luna both need you — 'Vet appointment' (12:00–12:45) overlaps 'Brush coat' (12:00–12:15).

Marked 'Morning walk' complete → next one auto-created for Mon Nov 02.

Filter: Mochi's pending tasks (all dates)
==================================================================
  Date   Time   Pet    Task                  Min  Priority  Done
  ----------------------------------------------------------------
  11/01  08:00  Mochi  Breakfast              10  🔴 high   ·
  11/01  12:00  Mochi  Vet appointment        45  🟡 medium ·
  11/02  07:30  Mochi  Morning walk           30  🔴 high   ·

Daily plan (80/90 min of care time)
==================================================================
  ✔ 07:45 Luna: Heartworm pill — high priority, 5 min (5/90 min used).
  ✔ 08:00 Mochi: Breakfast — high priority, 10 min (15/90 min used).
  ✔ 12:00 Mochi: Vet appointment — medium priority, 45 min (60/90 min used).
  ✔ 18:00 Luna: Play session — medium priority, 20 min (80/90 min used).
  ✘ 12:00 Luna: Brush coat — skipped: needs 15 min but only 10 min left after higher-priority tasks.

Next free 60-minute slot today: 08:10
```

## 💾 Data persistence

- `Task.to_dict()` / `Task.from_dict()` and `Pet.to_dict()` / `Pet.from_dict()` turn objects into plain dicts (dates as ISO strings).
- `Owner.save_to_json(path)` writes the whole owner → pets → tasks tree. `Owner.load_from_json(path)` rebuilds it.
- `app.py` loads `data.json` the first time a session starts (if the file exists) and calls `save()` after every change: adding a pet or task, completing a task, or changing owner settings. `data.json` is git-ignored.
- Files involved: `pawpal_system.py` and `app.py`.

## 📁 Project structure

```
pawpal_system.py      # logic layer: Task, Pet, Owner, Scheduler, DailyPlan
main.py               # CLI demo
app.py                # Streamlit UI
tests/test_pawpal.py  # pytest suite
diagrams/             # Mermaid UML (draft + final)
reflection.md         # design and AI-collaboration reflection
ai_interactions.md    # stretch-feature AI log
```
