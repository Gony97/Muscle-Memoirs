from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db import connect, init_db


def import_program(db_path: str | Path, program_json_path: str | Path) -> dict[str, Any]:
    """
    Imports program template and suggestion rules into SQLite.
    Returns parsed program dict.
    """
    init_db(db_path)

    program_json_path = Path(program_json_path)
    program = json.loads(program_json_path.read_text(encoding="utf-8"))

    program_name = program.get("program_name", "Program")
    units = program.get("units", "kg")
    suggestion_rules = program.get("suggestion_rules", {})

    weeks = program.get("weeks", [])
    if not isinstance(weeks, list) or len(weeks) == 0:
        raise ValueError("program.json must include a non-empty 'weeks' list")

    with connect(db_path) as conn:
        # meta
        conn.execute(
            "INSERT OR REPLACE INTO program_meta(key, value) VALUES (?, ?)",
            ("program_name", str(program_name)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO program_meta(key, value) VALUES (?, ?)",
            ("units", str(units)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO program_meta(key, value) VALUES (?, ?)",
            ("suggestion_rules_json", json.dumps(suggestion_rules)),
        )

        # wipe & re-import templates (simple approach)
        conn.execute("DELETE FROM program_exercise")
        conn.execute("DELETE FROM program_workout")

        for w in weeks:
            week_num = int(w["week"])
            workouts = w.get("workouts", [])
            if len(workouts) != 3:
                # you can loosen this later, but matches your requirement
                raise ValueError(f"Week {week_num} must contain exactly 3 workouts")

            for wo in workouts:
                day = int(wo["day"])
                name = str(wo.get("name", f"Workout {day}"))
                conn.execute(
                    "INSERT INTO program_workout(week, day, workout_name) VALUES (?, ?, ?)",
                    (week_num, day, name),
                )

                exercises = wo.get("exercises", [])
                for idx, ex in enumerate(exercises, start=1):
                    conn.execute(
                        """
                        INSERT INTO program_exercise
                        (week, day, ex_order, exercise_name, target_sets, target_reps, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            week_num,
                            day,
                            idx,
                            str(ex["name"]),
                            ex.get("sets", None),
                            ex.get("reps", None),
                            str(ex.get("notes", "")),
                        ),
                    )

        conn.commit()

    return program