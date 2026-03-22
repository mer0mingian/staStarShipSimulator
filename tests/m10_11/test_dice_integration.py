"""Integration tests for M10.11 - Dice Resolution Resource Flows.

Tests the integration between dice resolution and game resources
(Determination, Momentum, Threat) following STA 2E rules.
"""

import pytest
from unittest.mock import patch, MagicMock

from sta.mechanics.dice import (
    resolve_action,
    resolve_action_extended,
    apply_talent_modifiers,
    TalentModifier,
    RollModifierResult,
)


class TestDeterminationFlows:
    """Tests for Determination-related dice flows."""

    def test_moment_of_inspiration_reroll(self):
        """test_moment_of_inspiration_reroll - spend Determination to reroll."""
        rolls = [15, 20]  # Both fail
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[3, 5],
                    rerolled_indices=[0, 1],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Moment of Inspiration"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0, 1],
                            source_talent="Moment of Inspiration",
                        )
                    ],
                )
        assert result.succeeded is True
        assert result.successes == 2  # 3 + 5 = 2 successes

    def test_perfect_opportunity_critical(self):
        """test_perfect_opportunity_critical - set die to 1 for guaranteed critical."""
        rolls = [12, 18]  # Both fail
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[1, 18],
                    rerolled_indices=[],
                    dice_set_to_one=[0],
                    criticals_added=1,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Perfect Opportunity"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="SET_TO_ONE",
                            dice_indices=[0],
                            source_talent="Perfect Opportunity",
                        )
                    ],
                )
        assert result.succeeded is True
        assert result.rolls == [1, 18]

    def test_determination_spend_for_crit(self):
        """test_determination_spend_for_crit - spend Det for critical conversion."""
        rolls = [8, 10]  # TN=8, 8 is success, 10 is not
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=rolls,
                    rerolled_indices=[],
                    dice_set_to_one=[],
                    criticals_added=1,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Determination Spend"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="CRITICAL_CONVERSION",
                            source_talent="Determination Spend",
                        )
                    ],
                )
        assert result.successes == 2  # 8=1, +1 critical = 2


class TestMomentumFlows:
    """Tests for Momentum-related dice flows."""

    def test_bonus_dice_from_momentum(self):
        """test_bonus_dice_from_momentum - extra dice from Momentum."""
        rolls = [5, 10, 15]  # TN=8, only 5 is success
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=1,
                bonus_dice=1,
            )
        assert len(result.rolls) == 3
        assert result.successes == 1  # Only 5 is success

    def test_momentum_generated_on_success(self):
        """test_momentum_generated_on_success - momentum = successes - difficulty."""
        rolls = [1, 1, 5]  # 1=2, 1=2, 5=1
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=2,
            )
        assert result.succeeded is True
        assert result.momentum_generated == 3  # 5 - 2 = 3

    def test_momentum_not_generated_on_failure(self):
        """test_momentum_not_generated_on_failure - no momentum when failing."""
        rolls = [15, 18]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=2,
            )
        assert result.succeeded is False
        assert result.momentum_generated == 0

    def test_momentum_reroll_spend(self):
        """test_momentum_reroll_spend - spend Momentum for reroll."""
        rolls = [15, 20]  # Both fail
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[3, 20],
                    rerolled_indices=[0],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Momentum Reroll"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0],
                            source_talent="Momentum Reroll",
                        )
                    ],
                )
        assert result.succeeded is True


class TestThreatFlows:
    """Tests for Threat-related dice flows."""

    def test_threat_modifies_difficulty(self):
        """test_threat_modifies_difficulty - GM Threat can increase difficulty."""
        rolls = [8, 10]  # TN=8, only 8 is success
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=2,  # GM used Threat to increase difficulty
            )
        assert result.successes == 1
        assert result.succeeded is False  # Need 2, only have 1

    def test_threat_extends_complication_range(self):
        """test_threat_extends_complication_range - GM Threat increases complication chance."""
        rolls = [19, 10]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=1,
                complication_range=2,  # GM used Threat to extend range
            )
        assert result.complications == 1  # 19 causes complication

    def test_gm_threat_trait_application(self):
        """test_gm_threat_trait_application - traits modify roll parameters."""
        rolls = [12, 15, 20]  # TN=8, all fail, 20 causes complication
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=2,  # Trait increased difficulty by 1
                complication_range=3,  # Trait extended complication range
            )
        assert result.successes == 0
        assert result.complications == 1  # 20 only


class TestTalentIntegration:
    """Tests for talent integration with dice resolution."""

    def test_talent_provides_reroll(self):
        """test_talent_provides_reroll - talent grants reroll ability."""
        rolls = [18, 20]  # Both fail
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[2, 10],
                    rerolled_indices=[0],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Bold"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0],
                            source_talent="Bold",
                        )
                    ],
                )
        assert result.successes == 1  # 2 is success

    def test_talent_provides_critical_conversion(self):
        """test_talent_provides_critical_conversion - talent adds extra success."""
        rolls = [8, 12]  # TN=8, 8 is success, 12 is not
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=rolls,
                    rerolled_indices=[],
                    dice_set_to_one=[],
                    criticals_added=1,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Spotless"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="CRITICAL_CONVERSION",
                            source_talent="Spotless",
                        )
                    ],
                )
        assert result.successes == 2  # 8=1, +1 critical = 2

    def test_talent_reduces_complications(self):
        """test_talent_reduces_complications - talent lowers complication risk."""
        rolls = [18, 19]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=rolls,
                    rerolled_indices=[],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=1,
                    modifiers_applied=["Lucky"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    complication_range=2,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REDUCE_COMPLICATIONS",
                            complication_reduction=1,
                            source_talent="Lucky",
                        )
                    ],
                )
        assert result.complications == 0  # Reduced to range 1, only 20 triggers

    def test_multiple_talents_combined(self):
        """test_multiple_talents_combined - several talents modify same roll."""
        rolls = [15, 18, 5]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[3, 18, 1],
                    rerolled_indices=[0],
                    dice_set_to_one=[2],
                    criticals_added=1,
                    complication_range_reduced_by=1,
                    modifiers_applied=["Bold", "Lucky"],
                ),
            ):
                result = resolve_action_extended(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    complication_range=2,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0],
                            source_talent="Bold",
                        ),
                        TalentModifier(
                            modifier_type="SET_TO_ONE",
                            dice_indices=[2],
                            source_talent="Perfect Opportunity",
                        ),
                        TalentModifier(
                            modifier_type="REDUCE_COMPLICATIONS",
                            complication_reduction=1,
                            source_talent="Lucky",
                        ),
                    ],
                )
        assert result.successes == 4  # 3=1, 1=2, +1 crit = 4
        assert result.complications == 0
        assert "Bold" in result.modifiers_applied
        assert "Lucky" in result.modifiers_applied

    def test_talent_requires_choice(self):
        """test_talent_requires_choice - set_to_one allows choosing which die."""
        rolls = [15, 5]  # Only 5 is a success
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[1, 5],
                    rerolled_indices=[],
                    dice_set_to_one=[0],
                    criticals_added=1,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Perfect Opportunity"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="SET_TO_ONE",
                            dice_indices=[0],
                            source_talent="Perfect Opportunity",
                        )
                    ],
                )
        assert result.rolls == [1, 5]
        assert result.successes == 4  # 1=2, 5=1, +1 crit = 4


class TestFocusIntegration:
    """Tests for Focus integration with dice resolution."""

    def test_focus_applies_to_task(self):
        """test_focus_applies_to_task - focus doubles successes on discipline rolls."""
        rolls = [
            3,
            8,
            12,
        ]  # TN=8, discipline=3. 3<=3 (focus), 8<=8 (normal), 12>8 (fail)
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=1,
                focus_applies=True,
            )
        assert result.successes == 3  # 3=2 (focus), 8=1, 12=0

    def test_focus_does_not_apply(self):
        """test_focus_does_not_apply - no focus = normal success counting."""
        rolls = [3, 8, 12]  # 3 and 8 are <= TN=8
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=1,
                focus_applies=False,
            )
        assert result.successes == 2  # 3=1, 8=1, 12=0

    def test_focus_with_talent_modifier(self):
        """test_focus_with_talent_modifier - focus and talent both apply."""
        rolls = [8, 15]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[8, 3],  # Rerolled 15 to 3
                    rerolled_indices=[1],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["MoI"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    focus_applies=True,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[1],
                            source_talent="MoI",
                        )
                    ],
                )
        # 8=1 (no focus - 8>3), 3=2 (focus - 3<=3)
        assert result.successes == 3


class TestExtendedResultTransparency:
    """Tests for ExtendedTaskResult providing full transparency."""

    def test_extended_shows_base_rolls(self):
        """test_extended_shows_base_rolls - shows rolls before modifiers."""
        rolls = [15, 20]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[3, 20],
                    rerolled_indices=[0],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Test"],
                ),
            ):
                result = resolve_action_extended(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0],
                            source_talent="Test",
                        )
                    ],
                )
        assert result.base_rolls == rolls
        assert result.rolls == [3, 20]

    def test_extended_shows_base_successes(self):
        """test_extended_shows_base_successes - shows successes before modifiers."""
        rolls = [8, 15]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[8, 5],
                    rerolled_indices=[1],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Test"],
                ),
            ):
                result = resolve_action_extended(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[1],
                            source_talent="Test",
                        )
                    ],
                )
        assert result.base_successes == 1  # Only 8 <= 8
        assert result.successes == 2  # Both 8 and 5 <= 8

    def test_extended_tracks_all_modifications(self):
        """test_extended_tracks_all_modifications - full modification history."""
        rolls = [15, 18, 20]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[2, 5, 1],
                    rerolled_indices=[0, 1],
                    dice_set_to_one=[2],
                    criticals_added=1,
                    complication_range_reduced_by=2,
                    modifiers_applied=["MoI", "PO", "Lucky"],
                ),
            ):
                result = resolve_action_extended(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    complication_range=3,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0, 1],
                            source_talent="MoI",
                        ),
                        TalentModifier(
                            modifier_type="SET_TO_ONE",
                            dice_indices=[2],
                            source_talent="PO",
                        ),
                        TalentModifier(
                            modifier_type="REDUCE_COMPLICATIONS",
                            complication_reduction=2,
                            source_talent="Lucky",
                        ),
                    ],
                )
        assert 0 in result.rerolled_indices
        assert 1 in result.rerolled_indices
        assert 2 in result.dice_set_to_one
        assert result.complication_range == 3
        assert result.effective_complication_range == 1


class TestEdgeCases:
    """Edge case tests for resource flows."""

    def test_all_resources_used(self):
        """test_all_resources_used - multiple modifiers applied."""
        rolls = [15, 18, 20]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=[1, 3, 18],
                    rerolled_indices=[0, 1],
                    dice_set_to_one=[],
                    criticals_added=2,
                    complication_range_reduced_by=2,
                    modifiers_applied=["MoI", "Determination", "Talent", "Lucky"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=2,
                    complication_range=3,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0],
                            source_talent="MoI",
                        ),
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[1],
                            source_talent="Determination",
                        ),
                        TalentModifier(
                            modifier_type="CRITICAL_CONVERSION", source_talent="Talent"
                        ),
                        TalentModifier(
                            modifier_type="REDUCE_COMPLICATIONS",
                            complication_reduction=2,
                            source_talent="Lucky",
                        ),
                    ],
                )
        assert result.successes >= 5  # 1=2, 3=1, +2 crits = 5
        assert result.complications == 0

    def test_no_resources_needed(self):
        """test_no_resources_needed - natural success without modifiers."""
        rolls = [1, 1, 1]  # All natural 1s = 6 successes
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=1,
            )
        assert result.succeeded is True
        assert result.momentum_generated == 5

    def test_maximum_complications_mitigated(self):
        """test_maximum_complications_mitigated - talent reduces many complications."""
        rolls = [16, 17, 18, 19, 20]  # TN=8, none are successes
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=rolls,
                    rerolled_indices=[],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=4,
                    modifiers_applied=["Lucky"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    complication_range=5,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REDUCE_COMPLICATIONS",
                            complication_reduction=4,
                            source_talent="Lucky",
                        )
                    ],
                )
        # complication_range=5, reduced by 4 = effective 1, so only 20 triggers complication
        assert result.complications == 1
