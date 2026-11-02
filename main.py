"""CLI demo for PawPal+: exercises the logic layer and prints the results."""

from pawpal_system import Owner, Pet, Scheduler, Task

PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def print_schedule(title: str, tasks: list[Task]) -> None:
    """Print tasks as an aligned table."""
    print(f"\n{title}")
    print("=" * 66)
    if not tasks:
        print("  (no tasks)")
        return
    print(f"  {'Date':<6} {'Time':<6} {'Pet':<6} {'Task':<20} {'Min':>4}  {'Priority':<9} Done")
    print("  " + "-" * 64)
    for t in tasks:
        done = "✓" if t.completed else "·"
        print(
            f"  {t.due_date:%m/%d}  {t.time:<6} {t.pet_name:<6} {t.description:<20} "
            f"{t.duration_minutes:>4}  {PRIORITY_ICON[t.priority]} {t.priority:<6} {done}"
        )


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of order to show sorting.
    luna.add_task(Task("Play session", "18:00", 20, "medium", "daily"))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    luna.add_task(Task("Brush coat", "12:00", 15, "low"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Heartworm pill", "07:45", 5, "high", "weekly"))  # overlaps the walk
    mochi.add_task(Task("Vet appointment", "12:00", 45, "medium"))  # same time as Brush coat

    scheduler = Scheduler(owner)

    print_schedule("Tasks as entered (unsorted)", owner.get_all_tasks())
    print_schedule(f"Today's Schedule for {owner.name} (sorted by time)", scheduler.get_todays_tasks())
    print_schedule("Sorted by priority, then time", scheduler.sort_by_priority(scheduler.get_todays_tasks()))
    print_schedule("Filter: Luna's tasks only", scheduler.filter_tasks(pet_name="Luna"))

    print("\nConflict check")
    print("=" * 66)
    for warning in scheduler.detect_conflicts() or ["No conflicts found."]:
        print(f"  ⚠️  {warning}")

    walk = next(t for t in mochi.tasks if t.description == "Morning walk")
    upcoming = scheduler.mark_task_complete(walk)
    print(f"\nMarked '{walk.description}' complete → next one auto-created for {upcoming.due_date:%a %b %d}.")
    print_schedule("Filter: completed tasks", scheduler.filter_tasks(completed=True))
    print_schedule("Filter: Mochi's pending tasks (all dates)",
                   scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi", completed=False)))

    plan = scheduler.generate_daily_plan()
    print(f"\nDaily plan ({plan.minutes_used}/{plan.minutes_available} min of care time)")
    print("=" * 66)
    for reason in plan.reasons:
        print(f"  {reason}")

    slot = scheduler.find_next_available_slot(60)
    print(f"\nNext free 60-minute slot today: {slot}")


if __name__ == "__main__":
    main()
