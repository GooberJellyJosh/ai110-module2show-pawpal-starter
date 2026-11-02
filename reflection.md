# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

1. **Add a pet** – the owner enters a pet's name, species, and age so PawPal+ knows who it is planning for.
2. **Schedule a care task** – the owner adds a task (walk, feeding, medication, appointment) to a pet with a time, duration, priority, and how often it repeats.
3. **See today's schedule** – the owner views every task due today across all pets, in time order, with warnings when two tasks clash.

**a. Initial design**

My first UML (`diagrams/uml_draft.mmd`) had four classes:

- **`Task`** (dataclass) – one care activity: description, time (`"HH:MM"`), duration, priority, frequency, and a `completed` flag. Its only behavior is `mark_complete()`.
- **`Pet`** (dataclass) – a pet's details plus the list of tasks that belong to it. Responsible for adding and removing its own tasks.
- **`Owner`** – holds a list of pets and is the single entry point for "give me every task across all my pets."
- **`Scheduler`** – the "brain." It does not store tasks itself; it asks the `Owner` for them and then sorts, filters, and checks them for conflicts.

Relationships: an `Owner` *has* many `Pet`s (aggregation), a `Pet` *owns* many `Task`s (composition), and the `Scheduler` *reads from* one `Owner`. I kept the `Scheduler` stateless on purpose so the data lives in one place (the owner/pet tree) and there's no second copy of the task list to keep in sync.

**b. Design changes**

Yes. When I had the AI review the skeleton for missing relationships and bottlenecks, it raised three problems, and I changed the skeleton for each:

1. **`Task` had no date.** Without a `due_date`, "today's schedule" can't tell today's tasks from tomorrow's, and a daily task can't work out when it happens next. I added `due_date` (defaulting to today) and a `next_occurrence()` method.
2. **Tasks didn't know which pet they belonged to.** `Owner.get_all_tasks()` returned a flat list of `Task`s, so once the scheduler had sorted them it couldn't print "Mochi – Morning walk" or filter by pet. I added a `pet_name` field that `Pet.add_task()` fills in. A full back-reference to the `Pet` object would also have worked, but it creates a reference cycle and makes the dataclass harder to print and serialize, so I went with the name.
3. **Who creates the next recurring task?** The task itself can't add a copy of itself to its pet, because it doesn't hold the pet. I put `mark_task_complete()` on the `Scheduler`. It marks the task done, asks the task for its `next_occurrence()`, and adds that to the right pet through the owner.

The AI also pointed out that `Owner.get_pet()` is a linear scan. I kept it: an owner has a handful of pets, so a dict index would add complexity for no real gain.

Later in the build the design grew in three more ways, all reflected in `diagrams/uml_final.mmd`:

- `Task` gained `start_minutes` / `end_minutes` / `end_time` properties once conflict detection moved from "same time" to "overlapping windows."
- `Owner` gained `available_minutes` (a daily care-time budget) so the scheduler could build a plan that respects the owner's real constraint, which the scenario asks for.
- A small `DailyPlan` dataclass was added so `generate_daily_plan()` returns scheduled tasks, skipped tasks, and reasons together instead of a loose tuple.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four constraints:

1. **Time of day.** Every task has a start time and duration. That's the backbone of sorting, conflict detection, and the free-slot search.
2. **Date.** Only tasks due on the chosen day are shown or planned. Recurrence moves tasks forward by date.
3. **Priority** (high/medium/low). This decides what survives when there isn't enough time.
4. **The owner's available minutes.** A hard budget for the daily plan.

I treated **priority as the most important constraint** for the daily plan, because missing a high-priority task (a medication, a vet appointment) has real consequences for the pet, while skipping a low-priority grooming session doesn't. Time of day matters most for *display*: once the plan picks which tasks to keep, it shows them in time order, because that's how an owner actually walks through their day.

**b. Tradeoffs**

**The daily plan is greedy, not optimal.** `generate_daily_plan()` walks tasks from highest to lowest priority and keeps each one that still fits in the remaining minutes. It never backtracks. That means it can leave time on the table. With 60 minutes, a 50-minute medium task scheduled before two 30-minute medium tasks would be kept on its own, even though the two 30s together would fill the hour and finish twice as many tasks. A true best-fit would be a knapsack problem.

That's reasonable here because an owner has maybe 5–15 tasks a day, the greedy rule is easy to explain ("high priority first, as long as it fits"), and the plan prints a reason for every decision. A pet owner can trust and override a plan they understand more easily than an "optimal" one that skipped their dog's walk for reasons they can't see.

A second, related tradeoff: **conflicts are warnings, not blockers.** `detect_conflicts()` catches overlapping time windows, not just exact matches. But it doesn't stop you from saving a clashing task, and the daily plan doesn't automatically move tasks to resolve clashes. Sometimes overlap is fine (you can give the cat a pill while the dog eats breakfast), so the app tells the owner and lets them decide. It also only compares tasks on the same calendar day, so a task that runs past midnight won't be flagged against an early-morning task the next day.

**Readability vs. "Pythonic" (Phase 4 evaluation).** For `detect_conflicts()`, the most compact version is a one-liner over `itertools.combinations(tasks, 2)` that checks every pair. It's shorter and arguably more Pythonic, but it always does O(n²) comparisons and hides the overlap rule inside a long condition. I kept the explicit version: sort by start time, then for each task scan forward only while later tasks start before it ends, and `break` as soon as one doesn't. It's a few lines longer, but each step has a comment, it stops early, and the overlap condition (`second.start < first.end`) reads like the English definition.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code (Anthropic's coding agent, running in the Claude desktop app) in agent mode, handing it the full project brief and letting it work phase by phase: reading the starter repo, forking and cloning it, drafting the UML, writing the skeleton, implementing the classes, writing tests, wiring the Streamlit UI, and drafting the docs. It committed at the end of each phase, so the history doubles as a log of what changed when.

The most effective features were:

- **Agent mode with a terminal.** The agent didn't just write code. It ran `python main.py` and `python -m pytest` after every change and read the output, so problems surfaced right away instead of at the end.
- **Multi-file edits.** The recurrence feature touched `Task`, `Scheduler`, `main.py`, the tests, and the UI at once, and the agent kept them consistent.
- **Headless UI checks.** It used Streamlit's `AppTest` to click through the app (add pets, add tasks, complete a task, generate a plan) without me opening a browser, then took screenshots in the browser pane to check layout.

The most useful prompts were concrete design questions, e.g. "How should the `Scheduler` retrieve all tasks from the `Owner`'s pets?" and "Review this skeleton for missing relationships or logic bottlenecks." These produced specific, checkable answers (the missing `due_date` and `pet_name` fields) rather than generic advice.

**b. Judgment and verification**

- **Rejected: a back-reference from `Task` to its `Pet` object.** The obvious fix for "tasks don't know their pet" was to store the `Pet` on each `Task`. I went with a `pet_name` string instead, because a two-way object link creates a reference cycle, makes dataclass `repr`/equality messier, and complicates JSON saving. The name is enough for display, filtering, and finding the pet again through `Owner.get_pet()`.
- **Rejected: indexing pets in a dict** for faster lookup. That's real but pointless optimization for a household with a few pets, and it would mean keeping two structures in sync.
- **Modified: the sorting approach.** A plain `sorted(tasks, key=lambda t: t.time)` looks correct and passes simple tests, but `"7:30"` sorts *after* `"10:00"` as a string. Instead of trusting it, the fix went into `Task.__post_init__`, which normalizes every time to zero-padded `"HH:MM"`. A specific test (`test_sort_by_time_returns_chronological_order` with a `"7:15"` input) proves it.

I verified everything by running it: the CLI demo output was checked by eye against the expected order and conflicts, the 36 tests cover happy paths and edge cases, and the UI was driven through a full workflow with `AppTest`. That UI check caught a real issue: the schedule filter and the task form both had a selectbox labeled "Pet", which was ambiguous (I renamed the filter to "Show pet"). It also exposed that a task ending after midnight displayed as `"25:00"`, which I fixed.

**Separate chat sessions.** I ran the phases in one agent session rather than opening a new chat per phase, and used a commit at the end of each phase as the checkpoint instead. In hindsight, separate sessions (one for algorithm planning, one for testing) would have been cleaner. A testing-only session would review the code without the "memory" of having written it, which makes it more likely to question assumptions instead of confirming them. The per-phase commits did give me clear points to review each phase's diff on its own.

---

## 4. Testing and Verification

**a. What you tested**

The 36 tests in `tests/test_pawpal.py` cover:

- **Basics:** `mark_complete()`, adding tasks updates `task_count`, time normalization, validation of bad times/priorities/frequencies/durations, duplicate pet names.
- **Sorting:** chronological order (including single-digit hours), date before time, priority-then-time.
- **Filtering:** by pet (case-insensitive), by status, combined, unknown pet.
- **Recurrence:** daily → next day, weekly → +7 days, once → nothing, completing twice doesn't duplicate, and a daily task on Nov 30 rolls to Dec 1.
- **Conflicts:** same time across pets, same pet, partial overlap, back-to-back (no conflict), same time on different days (no conflict), completed tasks ignored, one long task overlapping several others.
- **Planning:** greedy plan respects the budget and returns tasks in time order. The free-slot search finds the first gap and returns `None` for a full day.
- **Persistence:** a JSON save/load round trip gives identical data.

These matter because they're exactly the places a scheduler silently goes wrong. A string sort that looks right until 7 a.m. meets 10 a.m., an off-by-one at a month boundary, a "conflict" between back-to-back tasks that isn't one, or a double click creating duplicate recurring tasks. None of those crash; they just give the owner a wrong schedule, so only tests catch them.

**b. Confidence**

**4 out of 5.** All 36 tests pass, and each core algorithm has both happy-path and edge-case coverage. What keeps it from a 5:

- The Streamlit UI is checked with scripted `AppTest` runs and screenshots, not an automated UI test suite.
- Tasks that cross midnight aren't compared against the next day's tasks for conflicts.
- Editing an existing task (rather than deleting and re-adding it) isn't supported yet.

Next I'd test: tasks spanning midnight, a weekly task completed late (should the next one be a week after the due date or after the completion date?), very large task lists for performance, and loading a corrupted or hand-edited `data.json`.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the **separation between the logic layer and the UI**. Because `pawpal_system.py` was built and tested from the CLI first, wiring up Streamlit was mostly calling methods that already worked. The UI never re-implements scheduling logic. It just calls `Scheduler` methods and formats the results. The conflict detector is the piece I like best: one small method catches exact clashes and partial overlaps for one pet or across pets, and it explains each one in a sentence a pet owner can act on.

**b. What you would improve**

- Let the owner **edit and delete tasks** from the UI, and choose whether a recurring task's next date is based on the due date or the completion date.
- Make the daily plan **conflict-aware**: when two kept tasks overlap, suggest moving the lower-priority one to `find_next_available_slot()`.
- Give tasks a stable `id`. Right now the UI identifies a task by its time/pet/description label, which works but would be fragile if two identical tasks existed.
- Handle midnight-spanning tasks properly by comparing full `datetime` ranges instead of minutes-after-midnight.

**c. Key takeaway**

Being the "lead architect" with a capable AI means the bottleneck moves from *writing* code to *deciding and verifying*. The AI can produce a working `Scheduler` in seconds. But whether `Task` should hold a pet name or a `Pet`, whether conflicts should block or warn, and whether a greedy plan is acceptable are design decisions with tradeoffs, and the AI will happily go either way. The most valuable things I did were keep the UML as the source of truth, insist on a CLI demo and tests before the UI, and treat every AI output as a draft to check by running it. The `"7:30"` sorting bug is the perfect example: the code looked correct, a quick glance would have approved it, and only a deliberate edge-case test showed it was wrong.
