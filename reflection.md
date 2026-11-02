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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
