"""Scene lifecycle validation logic."""

from typing import List


class SceneValidationError(Exception):
    """Raised when scene validation fails."""

    pass


def validate_scene_for_ready(scene: dict) -> List[str]:
    """Validate scene has required fields for 'ready' status."""
    errors = []
    if not scene.get("name"):
        errors.append("Scene must have a name (title)")
    if not scene.get("gm_short_description"):
        errors.append("Scene must have a GM short description")
    player_chars = scene.get("player_character_list", [])
    if not player_chars or player_chars == "[]":
        errors.append("Scene must have at least one player character")
    return errors


def validate_scene_for_active(scene: dict) -> List[str]:
    """Validate scene can be activated."""
    errors = []
    return errors


def validate_state_transition(
    current_status: str, new_status: str, scene: dict
) -> List[str]:
    """Validate state transition is allowed."""
    errors = []

    valid_transitions = {
        "draft": ["ready"],
        "ready": ["active"],
        "active": ["completed"],
        "completed": ["ready"],
    }

    if current_status == new_status:
        return []

    allowed = valid_transitions.get(current_status, [])
    if new_status not in allowed:
        errors.append(f"Cannot transition from '{current_status}' to '{new_status}'")
        return errors

    if new_status == "ready":
        errors.extend(validate_scene_for_ready(scene))
    elif new_status == "active":
        errors.extend(validate_scene_for_active(scene))

    return errors
