import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant.")

# Streamlit reruns this script on every interaction, so the Owner lives in
# session_state and is only created the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Add a pet")
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
                st.success(f"Added {pet_name.strip()}!")
            except ValueError as e:
                st.error(str(e))

if not owner.pets:
    st.info("No pets yet. Add one above to start scheduling tasks.")
    st.stop()

st.subheader("Schedule a task")
with st.form("add_task", clear_on_submit=True):
    col1, col2 = st.columns(2)
    target = col1.selectbox("Pet", [p.name for p in owner.pets])
    title = col2.text_input("Task", value="Morning walk")
    col3, col4, col5 = st.columns(3)
    time_value = col3.time_input("Time")
    duration = col4.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    priority = col5.selectbox("Priority", ["low", "medium", "high"], index=2)
    frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
    if st.form_submit_button("Add task"):
        owner.get_pet(target).add_task(
            Task(title, time_value.strftime("%H:%M"), int(duration), priority, frequency)
        )
        st.success(f"Scheduled '{title}' for {target}.")

st.subheader("Today's tasks")
todays = scheduler.get_todays_tasks()
if todays:
    st.table(
        [
            {"Time": t.time, "Pet": t.pet_name, "Task": t.description,
             "Minutes": t.duration_minutes, "Priority": t.priority}
            for t in todays
        ]
    )
else:
    st.info("Nothing scheduled for today yet.")
