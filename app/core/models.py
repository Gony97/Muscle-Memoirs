from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProgramExercise:
    week: int
    day: int
    ex_order: int
    name: str
    target_sets: Optional[int] = None
    target_reps: Optional[int] = None
    notes: str = ""


@dataclass(frozen=True)
class ExerciseHistoryEntry:
    started_at: str
    weight: float
    reps: int
    difficulty: str  # easy/normal/hard