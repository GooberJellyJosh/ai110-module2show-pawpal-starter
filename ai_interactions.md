# AI Interactions Log

> **Stretch features only.** This log covers the stretch features attempted: an advanced algorithmic capability (Challenge 1), data persistence (Challenge 2), priority scheduling (Challenge 3), and formatted output (Challenge 4).

---

## Agent Workflow (SF7)

**What task did you give the agent?**

I gave Claude Code (agent mode, in the Claude desktop app) the full PawPal+ project brief: fork and clone the starter repo, design the four classes in UML, build `pawpal_system.py` CLI-first, add sorting, filtering, recurrence, and conflict detection, write a pytest suite, connect the Streamlit UI, and document everything. For the stretch work it added three capabilities beyond the required algorithms: a **time-budgeted daily plan with explanations** (`Scheduler.generate_daily_plan`), a **next-available-slot finder** (`Scheduler.find_next_available_slot`), and **priority-then-time sorting** (`Scheduler.sort_by_priority`), plus **JSON persistence** (`Owner.save_to_json` / `Owner.load_from_json`).

**What did the agent do?**

Files created or modified:

| File | Change |
|------|--------|
| `diagrams/uml_draft.mmd`, `diagrams/uml_final.mmd`, `diagrams/uml.mmd` | Phase 1 draft and final class diagrams (Mermaid) |
| `pawpal_system.py` | Skeleton → full `Task`, `Pet`, `Owner`, `Scheduler`, `DailyPlan` implementation |
| `main.py` | CLI demo exercising every feature |
| `tests/test_pawpal.py`, `pytest.ini` | 36-test suite and pytest config |
| `app.py` | Streamlit UI wired to the logic layer, with `session_state` and `data.json` persistence |
| `README.md`, `reflection.md`, `requirements.txt`, `.gitignore` | Documentation, reflection, `streamlit>=1.36`, ignore `data.json` |

Steps, roughly in order (one commit per phase):

1. Forked and cloned the starter repo, read the starter files, and created a virtualenv.
2. Wrote the UML draft and dataclass skeleton, reviewed the skeleton, and added `due_date`, `pet_name`, and `Scheduler.mark_task_complete()`.
3. Implemented the core classes with validation, ran `main.py`, and wrote the first two tests.
4. Connected `app.py` using `st.session_state` and verified it headlessly with Streamlit's `AppTest`.
5. Implemented sorting, filtering, recurrence (`timedelta`), overlap-based conflict detection, the daily plan, the free-slot finder, and JSON save/load. Updated `main.py` to add tasks out of order and show each feature.
6. Wrote the full test suite (36 tests, all passing) and pasted the output into the README.
7. Polished the UI (filters, sort toggle, `st.warning` conflicts, complete button, plan metrics), checked it visually in a browser, and finalized the UML (verified it renders), README, and reflection.

**What did you have to verify or fix manually?**

Problems caught during the agent's own verification runs or design review (each was handled before the commit):

- **String sorting bug.** `"7:30"` sorted after `"10:00"`. Fixed by normalizing times in `Task.__post_init__` and locked in with a test.
- **Ambiguous UI labels.** The task form and the schedule filter both had a selectbox labeled "Pet". The scripted UI test selected the wrong one, so the filter was renamed "Show pet".
- **Midnight display.** A task ending after midnight showed `"25:00"`. Display times now wrap with `% (24*60)`.
- **Stale UI after "Complete" (avoided by design).** Streamlit draws top to bottom, so a button below the table would change data *after* the table had already drawn. The Complete button uses an `on_click` callback instead, so the table reflects the change on the same rerun.
- **Mermaid syntax.** Changed `Pet | None` return types to `Optional~Pet~` so the diagram parses reliably, then confirmed both `.mmd` files render.

Human review still needed: read through each phase's diff, confirm the design decisions in `reflection.md` match your own judgment, and run `streamlit run app.py` yourself to try the workflow in the README.

---
