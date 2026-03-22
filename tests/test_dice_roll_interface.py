"""
Tests for Player Console & Dice Roll Interface (M10.6).

Tests verify:
- Dice roll mechanics (success counting, criticals, complications)
- Value status transitions (Available/Used/Challenged/Complied)
- Determination spends (re-roll, perfect opportunity)
- Player resources (stress, determination, values)
"""

import json
import pytest
from unittest.mock import patch

from sta.database.vtt_schema import VTTCharacterRecord
from sta.mechanics.dice import (
    count_successes,
    count_complications,
    player_task_roll,
    reroll_selected,
    apply_perfect_opportunity,
)


class TestDiceMechanics:
    """Tests for core dice mechanics."""

    def test_count_successes_basic(self):
        """Test basic success counting."""
        rolls = [10, 15, 20]
        # 10 <= 12 = 1 success, 15 > 12 = 0, 20 > 12 = 0
        assert count_successes(rolls, 12) == 1

    def test_count_successes_with_criticals(self):
        """Test that roll of 1 always counts as 2 successes."""
        rolls = [1, 5, 20]
        assert count_successes(rolls, 12) == 3  # 1=2, 5=1, 20=0

    def test_count_successes_with_focus(self):
        """Test focus critical: roll <= discipline = 2 successes."""
        rolls = [3, 8, 15]  # Discipline is 4
        # 3 <= 4 (focus) = 2 successes, 8 <= 12 = 1 success, 15 > 12 = 0
        assert count_successes(rolls, 12, focus_value=4) == 3

    def test_count_successes_all_failures(self):
        """Test all failures return 0."""
        rolls = [13, 14, 20]
        assert count_successes(rolls, 12) == 0

    def test_count_complications_range_1(self):
        """Test complication range 1 (only 20)."""
        rolls = [10, 19, 20]
        assert count_complications(rolls, 1) == 1  # Only 20

    def test_count_complications_range_2(self):
        """Test complication range 2 (19-20)."""
        rolls = [10, 19, 20]
        assert count_complications(rolls, 2) == 2  # 19 and 20

    def test_count_complications_range_3(self):
        """Test complication range 3 (18-20)."""
        rolls = [17, 18, 20]
        assert count_complications(rolls, 3) == 2  # 18 and 20

    def test_count_complications_no_complications(self):
        """Test no complications when roll is below threshold."""
        rolls = [10, 15, 19]
        assert count_complications(rolls, 1) == 0  # Only 20


class TestPlayerTaskRoll:
    """Tests for player_task_roll function."""

    def test_basic_roll(self):
        """Test basic roll returns expected structure."""
        result = player_task_roll(
            attribute=10,
            discipline=3,
            difficulty=1,
        )

        assert "rolls" in result
        assert len(result["rolls"]) == 2  # Default dice count
        assert result["target_number"] == 13
        assert "successes" in result
        assert "complications" in result
        assert result["difficulty"] == 1
        assert result["complication_range"] == 1

    def test_roll_with_bonus_dice(self):
        """Test roll with bonus dice."""
        result = player_task_roll(
            attribute=10,
            discipline=3,
            difficulty=1,
            bonus_dice=2,
        )

        assert result["total_dice"] == 4
        assert len(result["rolls"]) == 4

    def test_roll_details_structure(self):
        """Test roll_details has correct structure."""
        result = player_task_roll(
            attribute=10,
            discipline=3,
            difficulty=1,
        )

        for detail in result["roll_details"]:
            assert "value" in detail
            assert "type" in detail
            assert "reason" in detail
            assert 1 <= detail["value"] <= 20

    def test_roll_with_focus(self):
        """Test roll with focus applied."""
        result = player_task_roll(
            attribute=10,
            discipline=4,
            difficulty=1,
            focus=True,
        )

        assert result["focus_applied"] is True
        assert result["focus_value"] == 4
        # Focus crits should be tracked
        assert "focus_criticals" in result["successes"]

    def test_success_breakdown(self):
        """Test success breakdown in result."""
        result = player_task_roll(
            attribute=10,
            discipline=3,
            difficulty=1,
        )

        successes = result["successes"]
        assert "total" in successes
        assert "normal" in successes
        assert "criticals" in successes
        assert "focus_criticals" in successes
        # Total should equal sum of components (when no focus)
        assert successes["total"] == successes["normal"] + successes["criticals"]

    def test_succeeded_calculation(self):
        """Test succeeded is True when successes >= difficulty."""
        with patch("random.randint", return_value=1):
            result = player_task_roll(
                attribute=10,
                discipline=3,
                difficulty=1,
            )

        assert result["succeeded"] is True
        assert result["successes"]["total"] >= result["difficulty"]

    def test_momentum_calculation(self):
        """Test momentum is successes - difficulty (minimum 0)."""
        with patch("random.randint", return_value=1):
            result = player_task_roll(
                attribute=10,
                discipline=3,
                difficulty=1,
            )

        expected_momentum = max(0, result["successes"]["total"] - result["difficulty"])
        assert result["momentum_generated"] == expected_momentum

    def test_complication_threshold_calculation(self):
        """Test complication threshold from range."""
        result = player_task_roll(
            attribute=10,
            discipline=3,
            difficulty=1,
            complication_range=2,
        )

        assert result["complication_threshold"] == 19  # 21 - 2


class TestRerollSelected:
    """Tests for reroll_selected function."""

    def test_reroll_single_die(self):
        """Test rerolling a single die."""
        original = [10, 15, 20]
        new_rolls, details = reroll_selected(original, [1], 12)

        assert len(new_rolls) == 3
        assert len(details) == 1
        assert details[0]["index"] == 1
        assert details[0]["old_value"] == 15
        assert 1 <= details[0]["new_value"] <= 20

    def test_reroll_multiple_dice(self):
        """Test rerolling multiple dice."""
        original = [10, 15, 20]
        new_rolls, details = reroll_selected(original, [0, 2], 12)

        assert len(new_rolls) == 3
        assert len(details) == 2

    def test_reroll_preserves_original_indices(self):
        """Test that only specified indices are rerolled."""
        original = [10, 15, 20]
        with patch("random.randint", return_value=8):
            new_rolls, _ = reroll_selected(original, [1], 12)

        assert new_rolls[0] == 10  # Unchanged
        assert new_rolls[2] == 20  # Unchanged


class TestPerfectOpportunity:
    """Tests for apply_perfect_opportunity function."""

    def test_set_die_to_one(self):
        """Test setting a die to 1."""
        rolls = [10, 15, 20]
        new_rolls, detail = apply_perfect_opportunity(rolls, 1, 12)

        assert new_rolls[1] == 1
        assert detail["old_value"] == 15
        assert detail["new_value"] == 1
        assert detail["successes_added"] == 2

    def test_preserves_other_dice(self):
        """Test that only the specified die is changed."""
        rolls = [10, 15, 20]
        new_rolls, _ = apply_perfect_opportunity(rolls, 1, 12)

        assert new_rolls[0] == 10
        assert new_rolls[2] == 20


@pytest.mark.characters
class TestDiceRollAPI:
    """Tests for dice roll API endpoints."""

    async def test_roll_dice_endpoint(self, client, test_session):
        """Test POST /api/characters/{id}/roll."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/roll",
            json={
                "attribute": "control",
                "department": "science",
                "difficulty": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "rolls" in data
        assert data["target_number"] == 14  # 10 + 4
        assert data["attribute_used"] == "control"
        assert data["discipline_used"] == "science"

    async def test_roll_dice_invalid_attribute(self, client, test_session):
        """Test roll with invalid attribute."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/roll",
            json={
                "attribute": "invalid_attr",
                "department": "science",
            },
        )
        assert response.status_code == 400

    async def test_roll_dice_invalid_department(self, client, test_session):
        """Test roll with invalid department."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/roll",
            json={
                "attribute": "control",
                "department": "invalid_dept",
            },
        )
        assert response.status_code == 400

    async def test_roll_dice_with_focus(self, client, test_session):
        """Test roll with focus applied."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/roll",
            json={
                "attribute": "control",
                "department": "science",
                "focus": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["focus_applied"] is True
        assert data["focus_value"] == 4


@pytest.mark.characters
class TestSpendDeterminationAPI:
    """Tests for determination spend API endpoints."""

    async def test_spend_determination_moment_of_inspiration(
        self, client, test_session
    ):
        """Test spending determination for re-roll."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=2,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/spend-determination",
            json={
                "spend_type": "moment_of_inspiration",
                "rolls": [10, 15, 20],
                "dice_indices": [1],
                "target_number": 12,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["spend_type"] == "moment_of_inspiration"
        assert data["determination_spent"] == 1
        assert data["determination_remaining"] == 1

    async def test_spend_determination_perfect_opportunity(self, client, test_session):
        """Test spending determination to set die to 1."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=2,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/spend-determination",
            json={
                "spend_type": "perfect_opportunity",
                "rolls": [10, 15, 20],
                "die_index": 1,
                "target_number": 12,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["spend_type"] == "perfect_opportunity"
        assert data["new_rolls"][1] == 1
        assert data["determination_spent"] == 1

    async def test_spend_determination_no_remaining(self, client, test_session):
        """Test cannot spend determination when none remaining."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=0,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/spend-determination",
            json={
                "spend_type": "moment_of_inspiration",
                "rolls": [10, 15, 20],
                "dice_indices": [1],
                "target_number": 12,
            },
        )
        assert response.status_code == 400
        assert "No Determination" in response.json()["detail"]


@pytest.mark.characters
class TestValueInteractionAPI:
    """Tests for Value interaction API endpoints."""

    async def test_value_interaction_use(self, client, test_session):
        """Test using a Value (costs Determination)."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=2,
            determination_max=3,
            values_json=json.dumps(
                [
                    {
                        "name": "Logic Above All",
                        "description": "Trust in rational analysis",
                        "helpful": True,
                        "used_this_session": False,
                    }
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/value-interaction",
            json={
                "value_name": "Logic Above All",
                "action": "use",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "use"
        assert data["value"]["used_this_session"] is True
        assert data["determination"] == 1  # Reduced by 1

    async def test_value_interaction_challenge(self, client, test_session):
        """Test challenging a Value (gains Determination)."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=1,
            determination_max=3,
            values_json=json.dumps(
                [
                    {
                        "name": "Logic Above All",
                        "description": "Trust in rational analysis",
                        "helpful": True,
                        "used_this_session": False,
                    }
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/value-interaction",
            json={
                "value_name": "Logic Above All",
                "action": "challenge",
                "description": "Had to make an emotional appeal",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "challenge"
        assert data["value"]["last_challenged_session"] is True
        assert data["determination"] == 2  # Increased by 1

    async def test_value_interaction_comply(self, client, test_session):
        """Test complying with a Value (gains Determination)."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=1,
            determination_max=3,
            values_json=json.dumps(
                [
                    {
                        "name": "Protect the Crew",
                        "description": "Safety is paramount",
                        "helpful": True,
                        "used_this_session": False,
                    }
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/value-interaction",
            json={
                "value_name": "Protect the Crew",
                "action": "comply",
                "description": "Had to follow orders despite the risk",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "comply"
        assert data["value"]["last_complied_session"] is True
        assert data["determination"] == 2  # Increased by 1

    async def test_value_interaction_use_already_used(self, client, test_session):
        """Test cannot use a Value twice in same session."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=2,
            determination_max=3,
            values_json=json.dumps(
                [
                    {
                        "name": "Logic Above All",
                        "description": "Trust in rational analysis",
                        "helpful": True,
                        "used_this_session": True,  # Already used
                    }
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/value-interaction",
            json={
                "value_name": "Logic Above All",
                "action": "use",
            },
        )
        assert response.status_code == 400
        assert "already been used" in response.json()["detail"]

    async def test_value_interaction_not_found(self, client, test_session):
        """Test interacting with non-existent Value."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=2,
            determination_max=3,
            values_json=json.dumps([]),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/value-interaction",
            json={
                "value_name": "NonExistent Value",
                "action": "use",
            },
        )
        assert response.status_code == 404


@pytest.mark.characters
class TestCharacterResourcesAPI:
    """Tests for character resources API endpoint."""

    async def test_get_character_resources(self, client, test_session):
        """Test GET /api/characters/{id}/resources."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                }
            ),
            stress=3,
            stress_max=8,
            determination=2,
            determination_max=3,
            values_json=json.dumps(
                [
                    {
                        "name": "Logic Above All",
                        "description": "Trust in rational analysis",
                        "helpful": True,
                        "used_this_session": False,
                    },
                    {
                        "name": "Protect the Crew",
                        "description": "Safety is paramount",
                        "helpful": True,
                        "last_challenged_session": True,
                    },
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.get(f"/api/characters/{char.id}/resources")
        assert response.status_code == 200
        data = response.json()

        assert data["character_name"] == "Test Character"
        assert data["stress"]["current"] == 3
        assert data["stress"]["max"] == 8
        assert data["stress"]["max_from_fitness"] == 8
        assert data["determination"]["current"] == 2
        assert data["determination"]["max"] == 3

        assert len(data["values"]) == 2
        value_names = [v["name"] for v in data["values"]]
        assert "Logic Above All" in value_names
        assert "Protect the Crew" in value_names

        # Check status
        for v in data["values"]:
            if v["name"] == "Logic Above All":
                assert v["status"] == "Available"
                assert v["can_use"] is True
            elif v["name"] == "Protect the Crew":
                assert v["status"] == "Challenged"
                assert v["can_use"] is True
