"""Game mechanics for STA Starship Simulator (2nd Edition)."""

from .dice import (
    roll_d20,
    count_successes,
    count_complications,
    task_roll,
    assisted_task_roll,
)

__all__ = [
    "roll_d20",
    "count_successes",
    "count_complications",
    "task_roll",
    "assisted_task_roll",
]
