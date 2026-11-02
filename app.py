from datetime import date
from pathlib import Path

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

DATA_FILE = Path(__file__).with_name("data.json")
PRIORITY_ICON = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}
SPECIES_ICON = {"dog": "🐶", "cat": "🐱", "other": "🐾"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


def save() -> None:
    """Persist the owner so pets and tasks survive an app restart."""
    st.session_state.owner.save_to_json(DATA_FILE)


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into rows for st.table / st.dataframe."""
    return [
        {
            "Time": f"{t.time}–{t.end_time}",
            "Pet": t.pet_name,
            "Task": t.description,
            "Min": t.duration_minutes,
            "Priority": PRIORITY_ICON[t.priority],
            "Repeats": t.frequency,
            "Status": "✅ done" if t.completed else "⏳ pending",
        }
        for t in tasks
    ]


# Streamlit reruns this script on every interaction, so the Owner lives in
# session_state and is only created (or loaded from disk) the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner.load_from_json(DATA_FILE) if DATA_FILE.exists() else Owner("Jordan")

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
st.caption("Plan your pets' day: walks, meals, meds, and appointments, sorted and checked for clashes.")

# --- Sidebar: owner settings ---------------------------------------------
with st.sidebar:
    st.header("Owner")
    name = st.text_input("Owner name", value=owner.name)
    budget = st.slider("Pet care time available today (min)", 15, 600, owner.available_minutes, step=15)
    if (name, budget) != (owner.name, owner.available_minutes):
        owner.name, owner.available_minutes = name, budget
        save()
    st.divider()
    st.subheader("Pets")
    if owner.pets:
        for pet in owner.pets:
            st.write(f"{SPECIES_ICON.get(pet.species, '🐾')} **{pet.name}** · {pet.species}, {pet.age} yr · {pet.task_count} tasks")
    else:
        st.caption("No pets yet.")
    st.caption(f"Data is saved automatically to `{DATA_FILE.name}`.")

# --- Add a pet -----------------------------------------------------------
with st.expander("➕ Add a pet", expanded=not owner.pets):
    with st.form("add_pet", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        pet_name = col1.text_input("Pet name")
        species = col2.selectbox("Species", ["dog", "cat", "other"])
        age = col3.number_input("Age", min_value=0, max_value=40, value=1)
        if st.form_submit_button("Add pet"):
            if not pet_name.strip():
                st.error("Please enter a pet name.")
            else:
                try:
                    owner.add_pet(Pet(pet_name.strip(), species, int(age)))
                    save()
                    st.success(f"Added {pet_name.strip()}!")
                except ValueError as e:
                    st.error(str(e))

if not owner.pets:
    st.info("Add your first pet above to start scheduling tasks.")
    st.stop()

# --- Schedule a task -----------------------------------------------------
with st.expander("🗓️ Schedule a task", expanded=True):
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        target = col1.selectbox("Pet", [p.name for p in owner.pets])
        title = col2.text_input("Task", value="Morning walk")
        col3, col4, col5 = st.columns(3)
        task_day = col3.date_input("Date", value=date.today())
        time_value = col4.time_input("Time")
        duration = col5.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        col6, col7 = st.columns(2)
        priority = col6.selectbox("Priority", ["low", "medium", "high"], index=2)
        frequency = col7.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            if not title.strip():
                st.error("Please enter a task name.")
            else:
                new_task = Task(title.strip(), time_value.strftime("%H:%M"), int(duration),
                                priority, frequency, due_date=task_day)
                owner.get_pet(target).add_task(new_task)
                save()
                st.success(f"Scheduled '{new_task.description}' for {target} at {new_task.time}.")
                clashes = [w for w in scheduler.detect_conflicts() if f"'{new_task.description}'" in w]
                for warning in clashes:
                    st.warning(f"Heads up: {warning}")

    slot_minutes = st.number_input("Need a free slot? Length (min)", min_value=5, max_value=240, value=30, step=5)
    slot = scheduler.find_next_available_slot(int(slot_minutes))
    if slot:
        st.caption(f"💡 Next free {int(slot_minutes)}-minute slot today: **{slot}**")
    else:
        st.caption(f"No free {int(slot_minutes)}-minute slot left today between 07:00 and 22:00.")

st.divider()

# --- Schedule view -------------------------------------------------------
st.subheader("📋 Schedule")
col1, col2, col3, col4 = st.columns(4)
view_day = col1.date_input("Day", value=date.today(), key="view_day")
pet_filter = col2.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
status_filter = col3.selectbox("Status", ["All", "Pending", "Done"])
sort_mode = col4.selectbox("Sort by", ["Time", "Priority"])

day_tasks = scheduler.get_todays_tasks(view_day)
shown = scheduler.filter_tasks(
    day_tasks,
    pet_name=None if pet_filter == "All pets" else pet_filter,
    completed={"All": None, "Pending": False, "Done": True}[status_filter],
)
shown = scheduler.sort_by_priority(shown) if sort_mode == "Priority" else scheduler.sort_by_time(shown)

conflicts = scheduler.detect_conflicts(day_tasks)
if conflicts:
    st.warning(f"**{len(conflicts)} scheduling conflict(s)** — you can't be in two places at once:")
    for warning in conflicts:
        st.markdown(f"- {warning}")
elif day_tasks:
    st.success("No conflicts: every pending task has its own time slot.")

if shown:
    st.table(task_rows(shown))
else:
    st.info("No tasks match these filters for this day.")

# --- Complete a task -----------------------------------------------------
pending = scheduler.filter_tasks(day_tasks, completed=False)
if pending:
    labels = {f"{t.time} · {t.pet_name} · {t.description}": t for t in pending}

    def complete_selected() -> None:
        task = labels[st.session_state.task_to_complete]
        upcoming = scheduler.mark_task_complete(task)
        save()
        msg = f"Marked '{task.description}' done."
        if upcoming:
            msg += f" Next {task.frequency} occurrence scheduled for {upcoming.due_date:%a %b %d}."
        st.session_state.flash = msg

    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    col1.selectbox("Mark a task complete", list(labels), key="task_to_complete")
    col2.button("✅ Complete", on_click=complete_selected)

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

st.divider()

# --- Daily plan ----------------------------------------------------------
st.subheader("🧠 Daily plan")
st.caption(
    f"Fits the day's pending tasks into your {owner.available_minutes} minutes of care time, "
    "highest priority first, and explains each choice."
)
if st.button("Generate plan", type="primary"):
    plan = scheduler.generate_daily_plan(view_day)
    if not plan.scheduled and not plan.skipped:
        st.info("Nothing pending for this day.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Tasks planned", len(plan.scheduled))
        m2.metric("Minutes used", f"{plan.minutes_used}/{plan.minutes_available}")
        m3.metric("Skipped", len(plan.skipped))
        if plan.scheduled:
            st.table(task_rows(plan.scheduled))
        if plan.skipped:
            st.warning(
                "Not enough time for: " + ", ".join(f"{t.pet_name}'s {t.description}" for t in plan.skipped)
                + ". Raise your available time in the sidebar or reschedule them."
            )
        with st.expander("Why this plan?"):
            for reason in plan.reasons:
                st.write(reason)
