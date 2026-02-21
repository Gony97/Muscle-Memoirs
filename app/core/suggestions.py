from __future__ import annotations

from typing import Any, Optional

from .services import WorkoutService


def _increment_for_exercise(rules: dict[str, Any], exercise_name: str) -> float:
    per = rules.get("per_exercise_increment", {}) or {}
    default_inc = float(rules.get("default_increment", 2.5))
    if exercise_name in per:
        try:
            return float(per[exercise_name])
        except Exception:
            return default_inc
    return default_inc


def suggest_weight(service: WorkoutService, exercise_name: str) -> Optional[float]:
    """
    Your MVP rule:
    - If no history: None
    - Else: last weight
      - if last difficulty was easy: add increment
    """
    last = service.get_last_exercise_summary(exercise_name)
    if not last:
        return None

    rules = service.get_suggestion_rules()
    weight = float(last["last_weight"])
    difficulty = str(last["difficulty"])
    easy_add = bool(rules.get("easy_add_increment", True))

    if difficulty == "easy" and easy_add:
        weight += _increment_for_exercise(rules, exercise_name)

    # Optional: rounding (keep it simple)
    return weight