from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS program_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS program_workout (
    week INTEGER NOT NULL,
    day INTEGER NOT NULL,
    workout_name TEXT NOT NULL,
    PRIMARY KEY (week, day)
);

CREATE TABLE IF NOT EXISTS program_exercise (
    week INTEGER NOT NULL,
    day INTEGER NOT NULL,
    ex_order INTEGER NOT NULL,
    exercise_name TEXT NOT NULL,
    target_sets INTEGER,
    target_reps INTEGER,
    notes TEXT,
    PRIMARY KEY (week, day, ex_order),
    FOREIGN KEY (week, day) REFERENCES program_workout(week, day) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL, -- ISO8601 string
    week INTEGER NOT NULL,
    day INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS exercise_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    exercise_name TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy','normal','hard')),
    notes TEXT,
    UNIQUE(session_id, exercise_name),
    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS set_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    exercise_name TEXT NOT NULL,
    set_index INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_setlog_exercise_time
ON set_log (exercise_name, session_id);

CREATE INDEX IF NOT EXISTS idx_exerciselog_exercise_time
ON exercise_log (exercise_name, session_id);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        
def reset_db(db_path: str | Path) -> None:
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    init_db(db_path)