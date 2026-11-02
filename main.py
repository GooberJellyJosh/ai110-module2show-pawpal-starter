"""CLI demo for PawPal+: builds a sample owner and prints today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(title: str, tasks: list[Task]) -> None:
    """Print tasks as an aligned table."""
    print(f"\n{title}")
    print("=" * 64)
    if not tasks:
        print("  (no tasks)")
        return
    print(f"  {'Time':<6} {'Pet':<8} {'Task':<22} {'Min':>4}  {'Priority':<8} Done")
    print("  " + "-" * 62)
    for t in tasks:
        done = "✓" if t.completed else " "
        print(
            f"  {t.time:<6} {t.pet_name:<8} {t.description:<22} "
            f"{t.duration_minutes:>4}  {t.priority:<8} {done}"
        )


def main() -> None:
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Heartworm pill", "09:00", 5, "high", "weekly"))
    luna.add_task(Task("Play session", "18:00", 20, "medium", "daily"))

    scheduler = Scheduler(owner)
    print_schedule(f"Today's Schedule for {owner.name}", scheduler.get_todays_tasks())


if __name__ == "__main__":
    main()
