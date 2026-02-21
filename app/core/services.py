from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .db import connect
from .models import ProgramExercise


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class WorkoutService:
    def __init__(self, db_path: str | Path):
        self.db_path = db_path

    def get_program_meta(self) -> dict[str, str]:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT key, value FROM program_meta").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def get_suggestion_rules(self) -> dict[str, Any]:
        meta = self.get_program_meta()
        raw = meta.get("suggestion_rules_json", "{}")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def get_workout_template(self, week: int, day: int) -> list[ProgramExercise]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT week, day, ex_order, exercise_name, target_sets, target_reps, notes
                FROM program_exercise
                WHERE week = ? AND day = ?
                ORDER BY ex_order ASC
                """,
                (week, day),
            ).fetchall()

        return [
            ProgramExercise(
                week=r["week"],
                day=r["day"],
                ex_order=r["ex_order"],
                name=r["exercise_name"],
                target_sets=r["target_sets"],
                target_reps=r["target_reps"],
                notes=r["notes"] or "",
            )
            for r in rows
        ]

    def start_session(self, week: int, day: int) -> int:
        started_at = _utc_now_iso()
        with connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO session(started_at, week, day) VALUES (?, ?, ?)",
                (started_at, week, day),
            )
            conn.commit()
            return int(cur.lastrowid)

    def set_exercise_difficulty(
        self,
        session_id: int,
        exercise_name: str,
        difficulty: str,
        notes: str = "",
    ) -> None:
        if difficulty not in ("easy", "normal", "hard"):
            raise ValueError("difficulty must be one of: easy, normal, hard")

        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO exercise_log(session_id, exercise_name, difficulty, notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id, exercise_name)
                DO UPDATE SET difficulty=excluded.difficulty, notes=excluded.notes
                """,
                (session_id, exercise_name, difficulty, notes),
            )
            conn.commit()

    def log_set(
        self,
        session_id: int,
        exercise_name: str,
        set_index: int,
        reps: int,
        weight: float,
    ) -> None:
        with connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO set_log(session_id, exercise_name, set_index, reps, weight)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, exercise_name, int(set_index), int(reps), float(weight)),
            )
            conn.commit()

    def get_last_exercise_summary(self, exercise_name: str) -> Optional[dict[str, Any]]:
        """
        Returns:
          {
            started_at, last_weight, last_reps, difficulty
          }
        Based on the most recent session where this exercise appears.
        """
        with connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT s.started_at,
                       sl.weight AS last_weight,
                       sl.reps AS last_reps,
                       COALESCE(el.difficulty, 'normal') AS difficulty
                FROM set_log sl
                JOIN session s ON s.id = sl.session_id
                LEFT JOIN exercise_log el
                  ON el.session_id = sl.session_id AND el.exercise_name = sl.exercise_name
                WHERE sl.exercise_name = ?
                ORDER BY s.started_at DESC, sl.set_index DESC
                LIMIT 1
                """,
                (exercise_name,),
            ).fetchone()

        if row is None:
            return None

        return {
            "started_at": row["started_at"],
            "last_weight": float(row["last_weight"]),
            "last_reps": int(row["last_reps"]),
            "difficulty": str(row["difficulty"]),
        }

    def get_exercise_history(self, exercise_name: str, limit: int = 10) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT s.started_at,
                       sl.set_index,
                       sl.reps,
                       sl.weight,
                       COALESCE(el.difficulty, 'normal') AS difficulty
                FROM set_log sl
                JOIN session s ON s.id = sl.session_id
                LEFT JOIN exercise_log el
                  ON el.session_id = sl.session_id AND el.exercise_name = sl.exercise_name
                WHERE sl.exercise_name = ?
                ORDER BY s.started_at DESC, sl.set_index ASC
                LIMIT ?
                """,
                (exercise_name, int(limit)),
            ).fetchall()

        return [
            {
                "started_at": r["started_at"],
                "set_index": int(r["set_index"]),
                "reps": int(r["reps"]),
                "weight": float(r["weight"]),
                "difficulty": str(r["difficulty"]),
            }
            for r in rows
        ]
        
    def list_workouts_for_week(self, week: int) -> list[tuple[int, str]]:
        """
        Returns list of (day, workout_name) for the given week, ordered by day.
        """
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT day, workout_name
                FROM program_workout
                WHERE week = ?
                ORDER BY day ASC
                """,
                (int(week),),
            ).fetchall()

        return [(int(r["day"]), str(r["workout_name"])) for r in rows]
    
    def replace_sets_for_exercise(
        self,
        session_id: int,
        exercise_name: str,
        reps_list: list[int],
        weights_list: list[float],
    ) -> int:
        """
        Overwrites all sets for (session_id, exercise_name) with the provided sets.
        Returns number of inserted sets.
        """
        if len(reps_list) != len(weights_list):
            raise ValueError("reps_list and weights_list must have same length")

        with connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM set_log WHERE session_id = ? AND exercise_name = ?",
                (int(session_id), str(exercise_name)),
            )
            inserted = 0
            for idx, (r, w) in enumerate(zip(reps_list, weights_list), start=1):
                conn.execute(
                    """
                    INSERT INTO set_log(session_id, exercise_name, set_index, reps, weight)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (int(session_id), str(exercise_name), int(idx), int(r), float(w)),
                )
                inserted += 1
            conn.commit()
        return inserted
    
    def get_last_session_for_exercise(self, exercise_name: str) -> dict | None:
        """
        Returns the most recent session for this exercise, including all sets in that session.

        {
          "started_at": str,
          "difficulty": "easy|normal|hard",
          "sets": [{"set_index": int, "reps": int, "weight": float}, ...]
        }
        """
        with connect(self.db_path) as conn:
            # 1) find last session_id for this exercise
            row = conn.execute(
                """
                SELECT s.id AS session_id, s.started_at,
                       COALESCE(el.difficulty, 'normal') AS difficulty
                FROM session s
                JOIN set_log sl ON sl.session_id = s.id
                LEFT JOIN exercise_log el
                  ON el.session_id = s.id AND el.exercise_name = sl.exercise_name
                WHERE sl.exercise_name = ?
                ORDER BY s.started_at DESC
                LIMIT 1
                """,
                (exercise_name,),
            ).fetchone()

            if row is None:
                return None

            session_id = int(row["session_id"])

            # 2) fetch all sets for that session + exercise
            sets_rows = conn.execute(
                """
                SELECT set_index, reps, weight
                FROM set_log
                WHERE session_id = ? AND exercise_name = ?
                ORDER BY set_index ASC
                """,
                (session_id, exercise_name),
            ).fetchall()

        return {
            "started_at": str(row["started_at"]),
            "difficulty": str(row["difficulty"]),
            "sets": [
                {"set_index": int(r["set_index"]), "reps": int(r["reps"]), "weight": float(r["weight"])}
                for r in sets_rows
            ],
        }
        
    def list_exercise_names(self) -> list[str]:
        """
        Returns a sorted list of unique exercise names known to the app.
        Includes both program template exercises and any logged exercises.
        """
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT exercise_name FROM program_exercise
                UNION
                SELECT exercise_name FROM set_log
                ORDER BY exercise_name ASC
                """
            ).fetchall()

        return [str(r["exercise_name"]) for r in rows]