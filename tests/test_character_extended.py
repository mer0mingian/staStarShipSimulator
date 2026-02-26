"""Tests for extended character fields (Milestone 2)."""

import json
import pytest
from sta.database.schema import CharacterRecord


class TestExtendedCharacterFields:
    """Tests for extended character fields in CharacterRecord."""

    def test_character_record_has_extended_fields(self, test_session):
        """CharacterRecord should have extended fields."""
        character = CharacterRecord(
            name="Jean-Luc Picard",
            species="Human",
            rank="Captain",
            role="Command",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "fitness": 8,
                    "daring": 9,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 4,
                    "conn": 2,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 2,
                    "security": 1,
                }
            ),
            character_type="main",
            pronouns="he/him",
            description="Captain of the USS Enterprise",
            values_json=json.dumps(["Integrity", "Courage"]),
            equipment_json=json.dumps(["Phaser", "Communicator"]),
            environment="Starfleet Academy",
            upbringing="France, Earth",
            career_path="Starfleet Officer",
        )
        test_session.add(character)
        test_session.flush()

        assert character.character_type == "main"
        assert character.pronouns == "he/him"
        assert character.description == "Captain of the USS Enterprise"
        assert json.loads(character.values_json) == ["Integrity", "Courage"]
        assert json.loads(character.equipment_json) == ["Phaser", "Communicator"]
        assert character.environment == "Starfleet Academy"
        assert character.upbringing == "France, Earth"
        assert character.career_path == "Starfleet Officer"

    def test_character_record_extended_fields_default(self, test_session):
        """Extended fields should have sensible defaults."""
        character = CharacterRecord(
            name="Worf",
            species="Klingon",
            attributes_json=json.dumps(
                {
                    "control": 8,
                    "fitness": 11,
                    "daring": 12,
                    "insight": 7,
                    "presence": 9,
                    "reason": 8,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 1,
                    "conn": 2,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 1,
                    "security": 4,
                }
            ),
        )
        test_session.add(character)
        test_session.flush()

        assert character.character_type == "support"
        assert character.pronouns is None
        assert character.avatar_url is None
        assert character.description is None
        assert json.loads(character.values_json) == []
        assert json.loads(character.equipment_json) == []
        assert character.environment is None
        assert character.upbringing is None
        assert character.career_path is None

    def test_character_record_character_types(self, test_session):
        """Character type should accept main, support, or npc."""
        main_char = CharacterRecord(
            name="Main Char",
            attributes_json=json.dumps(
                {
                    "control": 7,
                    "fitness": 7,
                    "daring": 7,
                    "insight": 7,
                    "presence": 7,
                    "reason": 7,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 1,
                    "conn": 1,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 1,
                    "security": 1,
                }
            ),
            character_type="main",
        )
        test_session.add(main_char)

        support_char = CharacterRecord(
            name="Support Char",
            attributes_json=json.dumps(
                {
                    "control": 7,
                    "fitness": 7,
                    "daring": 7,
                    "insight": 7,
                    "presence": 7,
                    "reason": 7,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 1,
                    "conn": 1,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 1,
                    "security": 1,
                }
            ),
            character_type="support",
        )
        test_session.add(support_char)

        npc_char = CharacterRecord(
            name="NPC Char",
            attributes_json=json.dumps(
                {
                    "control": 7,
                    "fitness": 7,
                    "daring": 7,
                    "insight": 7,
                    "presence": 7,
                    "reason": 7,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 1,
                    "conn": 1,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 1,
                    "security": 1,
                }
            ),
            character_type="npc",
        )
        test_session.add(npc_char)
        test_session.flush()

        assert main_char.character_type == "main"
        assert support_char.character_type == "support"
        assert npc_char.character_type == "npc"


class TestCharacterModelExtendedFields:
    """Tests for Character model extended fields."""

    def test_character_model_has_extended_fields(self):
        """Character model should have extended fields."""
        from sta.models.character import Character, Attributes, Disciplines

        char = Character(
            name="Riker",
            attributes=Attributes(
                control=9, fitness=8, daring=10, insight=8, presence=11, reason=9
            ),
            disciplines=Disciplines(
                command=3, conn=3, engineering=1, medicine=1, science=2, security=2
            ),
            character_type="main",
            pronouns="he/him",
            values=["Duty", "Honor"],
            equipment=["Phaser", "Uniform"],
            environment="Alaska",
            upbringing="Sitka, Alaska",
            career_path="Starfleet",
        )

        assert char.character_type == "main"
        assert char.pronouns == "he/him"
        assert char.values == ["Duty", "Honor"]
        assert char.equipment == ["Phaser", "Uniform"]
        assert char.environment == "Alaska"
        assert char.upbringing == "Sitka, Alaska"
        assert char.career_path == "Starfleet"

    def test_character_model_extended_defaults(self):
        """Character model extended fields should have defaults."""
        from sta.models.character import Character, Attributes, Disciplines

        char = Character(
            name="Anonymous",
            attributes=Attributes(),
            disciplines=Disciplines(),
        )

        assert char.character_type == "support"
        assert char.pronouns is None
        assert char.avatar_url is None
        assert char.description is None
        assert char.values == []
        assert char.equipment == []


class TestCharacterRecordModelConversion:
    """Tests for converting between CharacterRecord and Character model."""

    def test_to_model_includes_extended_fields(self, test_session):
        """to_model() should include extended fields."""
        record = CharacterRecord(
            name="Data",
            species="Android",
            rank="Lieutenant Commander",
            role="Operations",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "fitness": 8,
                    "daring": 9,
                    "insight": 11,
                    "presence": 6,
                    "reason": 12,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 4,
                    "medicine": 1,
                    "science": 5,
                    "security": 2,
                }
            ),
            character_type="main",
            pronouns="it/its",
            description="Soong-type android",
            values_json=json.dumps(["Logic", "Self-improvement"]),
            equipment_json=json.dumps(["Phaser"]),
            environment="Lab",
            upbringing="Omicron Theta",
            career_path="Starfleet Officer",
        )
        test_session.add(record)
        test_session.flush()

        model = record.to_model()

        assert model.character_type == "main"
        assert model.pronouns == "it/its"
        assert model.description == "Soong-type android"
        assert model.values == ["Logic", "Self-improvement"]
        assert model.equipment == ["Phaser"]
        assert model.environment == "Lab"
        assert model.upbringing == "Omicron Theta"
        assert model.career_path == "Starfleet Officer"

    def test_from_model_includes_extended_fields(self):
        """from_model() should include extended fields."""
        from sta.models.character import Character, Attributes, Disciplines

        char = Character(
            name="Worf",
            attributes=Attributes(
                control=8, fitness=11, daring=12, insight=7, presence=9, reason=8
            ),
            disciplines=Disciplines(
                command=1, conn=2, engineering=1, medicine=1, science=1, security=4
            ),
            character_type="support",
            pronouns="he/him",
            values=["Honor", "Duty"],
            equipment=["Bat'leth", "Phaser"],
            environment="Qo'noS",
            upbringing="Earth",
            career_path="Warrior",
        )

        record = CharacterRecord.from_model(char)

        assert record.character_type == "support"
        assert record.pronouns == "he/him"
        assert json.loads(record.values_json) == ["Honor", "Duty"]
        assert json.loads(record.equipment_json) == ["Bat'leth", "Phaser"]
        assert record.environment == "Qo'noS"
        assert record.upbringing == "Earth"
        assert record.career_path == "Warrior"
