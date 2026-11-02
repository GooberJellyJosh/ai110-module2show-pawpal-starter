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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

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
