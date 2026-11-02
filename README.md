# PawPal+

PawPal+ is a pet care planner I built in Python. It keeps track of each pet's walks, meals, meds, and appointments, sorts them into a daily schedule, warns about time conflicts, and automatically repeats daily and weekly tasks.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
python main.py          # CLI demo
streamlit run app.py    # web app
python -m pytest        # tests
```

## Features

- Add multiple pets to an owner, each with their own task list
- Tasks have a time, duration, priority (low/medium/high), frequency (once/daily/weekly), and due date
- Sort the schedule by time, or by priority and then time
- Filter tasks by pet or by completed/pending
- Completing a daily or weekly task creates the next one automatically
- Warnings when two tasks overlap
- A daily plan that fits the highest-priority tasks into the time the owner has available and explains what got skipped
- Finds the next free time slot for a new task
- Pets and tasks are saved to `data.json` so they're still there after restarting the app
- Color-coded priorities (🔴🟡🟢) in the terminal output and the web app

## Smarter Scheduling

| Feature | Method | How it works |
|---------|--------|--------------|
| Sorting by time | `Scheduler.sort_by_time()` | Uses `sorted()` with a lambda key on `(due_date, time)`. Times are stored as zero-padded `"HH:MM"`, so `"7:30"` becomes `"07:30"` and sorts correctly. |
| Priority sorting | `Scheduler.sort_by_priority()` | High → medium → low, then by time. |
| Filtering | `Scheduler.filter_tasks()` | Filters by pet name, completion status, or both. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Marks the task done and adds a copy due the next day (`timedelta(days=1)`) or next week (`timedelta(weeks=1)`). |
| Conflict detection | `Scheduler.detect_conflicts()` | Flags tasks on the same day whose time windows overlap, for the same pet or different pets. Returns warning messages instead of raising an error. |
| Daily plan | `Scheduler.generate_daily_plan()` | Adds tasks in priority order as long as they fit in `Owner.available_minutes`. |
| Next free slot | `Scheduler.find_next_available_slot()` | Returns the first gap in the day that's long enough for the task. |
| Saving/loading | `Owner.save_to_json()`, `Owner.load_from_json()` | Converts owners, pets, and tasks to dictionaries and back. |

## Demo Walkthrough

In the web app you can:

- Set your name and how much time you have for pet care today (sidebar)
- Add a pet with a name, species, and age
- Schedule a task for a pet with a date, time, duration, priority, and repeat setting
- View the schedule for any day, filtered by pet or status and sorted by time or priority
- See conflict warnings at the top of the schedule
- Mark a task complete (repeating tasks show when the next one is scheduled)
- Generate a daily plan that shows which tasks fit and why others were skipped

Example workflow:

1. Add two pets, Mochi (dog) and Luna (cat).
2. Schedule a morning walk for Mochi at 07:30 (30 min, daily) and a heartworm pill for Luna at 07:45 (5 min, weekly). A conflict warning appears because they overlap.
3. Add a few more tasks in any order. The schedule always shows them sorted by time.
4. Mark the walk complete. It shows as done, and tomorrow's walk is created automatically.
5. Click **Generate plan** to see which tasks fit into your available time.

### Sample Output

Output from `python main.py`:

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

## Testing PawPal+

```bash
python -m pytest
```

The tests cover sorting (including times like `"7:15"`), filtering, daily and weekly recurrence, conflict detection (exact matches, partial overlaps, and back-to-back tasks that shouldn't be flagged), the daily plan, the free-slot search, saving and loading JSON, and edge cases like a pet with no tasks.

```
============================= test session starts ==============================
platform darwin -- Python 3.14.8, pytest-9.2.0, pluggy-1.7.0
rootdir: .../ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.16.0
collected 36 items

tests/test_pawpal.py ....................................                [100%]

============================== 36 passed in 0.06s ==============================
```

**Confidence level:** ★★★★☆. All 36 tests pass. The main gaps are tasks that run past midnight and the UI not having automated tests.
