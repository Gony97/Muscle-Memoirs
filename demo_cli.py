from pathlib import Path

from app.core.db import init_db
from app.core.import_program import import_program
from app.core.services import WorkoutService
from app.core.suggestions import suggest_weight


def main() -> None:
    root = Path(__file__).parent
    db_path = root / "data" / "fworkout.db"
    program_path = root / "program.json"

    init_db(db_path)
    import_program(db_path, program_path)

    service = WorkoutService(db_path)

    week, day = 1, 1
    print(f"\n=== Template Week {week} Day {day} ===")
    template = service.get_workout_template(week, day)
    for ex in template:
        print(f"- {ex.ex_order}. {ex.name} ({ex.target_sets}x{ex.target_reps})")

    # Start a session and log a fake workout for testing
    session_id = service.start_session(week, day)
    print(f"\nStarted session_id={session_id}")

    for ex in template:
        # log sets
        sets = ex.target_sets or 3
        reps = ex.target_reps or 8
        base_weight = 20.0 + ex.ex_order * 2.5
        for s in range(1, sets + 1):
            service.log_set(session_id, ex.name, s, reps, base_weight)

        # difficulty per exercise
        diff = "easy" if ex.ex_order == 1 else "normal"
        service.set_exercise_difficulty(session_id, ex.name, diff)

    print("\n=== Suggestions (based on last session) ===")
    for ex in template:
        last = service.get_last_exercise_summary(ex.name)
        sug = suggest_weight(service, ex.name)
        print(f"\n{ex.name}")
        print(f"  last: {last}")
        print(f"  suggested: {sug}")


if __name__ == "__main__":
    main()