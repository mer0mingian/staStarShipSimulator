"""Tests for M10.11 - Dice Resolution with Talent Modifiers.

Tests the complete STA 2E action resolution sequence:
1. Calculate Target Number = Attribute + Discipline
2. Roll 2d20 + bonus dice from Momentum/Threat
3. Calculate base successes (roll <= TN = 1, roll=1 = 2, roll<=focus=2)
4. Calculate base complications based on Complication Range
5. Apply MODIFIERS (Talents/Abilities AFTER initial calculation)
6. Present final outcome
7. Calculate Momentum generated = max(0, successes - difficulty)
"""

import pytest
from unittest.mock import patch

from sta.mechanics.dice import (
    roll_d20,
    count_successes,
    count_complications,
    task_roll,
    assisted_task_roll,
    resolve_action,
    resolve_action_extended,
    apply_talent_modifiers,
    TalentModifier,
    RollModifierResult,
    ExtendedTaskResult,
    DiceRoll,
)
from sta.models.combat import TaskResult


class TestRollD20:
    """Tests for roll_d20 function."""

    def test_roll_single_die(self):
        """test_roll_single_die - returns single integer in range 1-20."""
        result = roll_d20(1)
        assert isinstance(result, list)
        assert len(result) == 1
        assert 1 <= result[0] <= 20

    def test_roll_multiple_dice(self):
        """test_roll_multiple_dice - returns correct count."""
        result = roll_d20(5)
        assert len(result) == 5
        for roll in result:
            assert 1 <= roll <= 20

    def test_roll_zero_dice(self):
        """test_roll_zero_dice - returns empty list."""
        result = roll_d20(0)
        assert result == []


class TestCountSuccesses:
    """Tests for count_successes function."""

    def test_no_successes(self):
        """test_no_successes - all rolls above target number."""
        rolls = [15, 16, 17, 18]
        result = count_successes(rolls, target_number=10)
        assert result == 0

    def test_basic_successes(self):
        """test_basic_successes - rolls at or below target count."""
        rolls = [5, 10, 15]
        result = count_successes(rolls, target_number=10)
        assert result == 2  # 5 and 10 are successes

    def test_natural_one_always_two_successes(self):
        """test_natural_one_always_two_successes - roll of 1 counts as 2."""
        rolls = [1]
        result = count_successes(rolls, target_number=5)
        assert result == 2

    def test_multiple_ones(self):
        """test_multiple_ones - multiple natural 1s each count as 2."""
        rolls = [1, 1, 1]
        result = count_successes(rolls, target_number=5)
        assert result == 6

    def test_one_counts_more_than_success(self):
        """test_one_counts_more_than_success - natural 1 > regular success."""
        rolls = [1, 10]
        result = count_successes(rolls, target_number=10)
        assert result == 3  # 1 = 2, 10 = 1

    def test_focus_critical_on_discipline_value(self):
        """test_focus_critical_on_discipline_value - roll <= discipline = 2 successes."""
        rolls = [5]
        result = count_successes(rolls, target_number=12, focus_value=5)
        assert result == 2  # 5 <= 5 (discipline), so 2 successes

    def test_focus_no_effect_on_above_focus(self):
        """test_focus_no_effect_on_above_focus - roll > discipline = 1 success."""
        rolls = [8]
        result = count_successes(rolls, target_number=12, focus_value=5)
        assert result == 1  # 8 > 5, so only 1 success even though <= TN

    def test_focus_one_always_two_successes(self):
        """test_focus_one_always_two_successes - natural 1 takes priority."""
        rolls = [1]
        result = count_successes(rolls, target_number=12, focus_value=5)
        assert result == 2  # 1 always = 2, regardless of focus

    def test_no_focus_value(self):
        """test_no_focus_value - focus_value=None gives no focus bonuses."""
        rolls = [5]
        result = count_successes(rolls, target_number=12, focus_value=None)
        assert result == 1  # No focus, so just 1 success

    def test_mixed_successes(self):
        """test_mixed_successes - various success types combined."""
        rolls = [1, 3, 8, 15]  # 1=2, 3=2 (focus), 8=1, 15=0
        result = count_successes(rolls, target_number=12, focus_value=5)
        assert result == 5  # 2 + 2 + 1 + 0

    def test_edge_case_at_target(self):
        """test_edge_case_at_target - roll exactly at target number succeeds."""
        rolls = [12]
        result = count_successes(rolls, target_number=12)
        assert result == 1

    def test_edge_case_at_focus(self):
        """test_edge_case_at_focus - roll exactly at focus value = 2 successes."""
        rolls = [5]
        result = count_successes(rolls, target_number=12, focus_value=5)
        assert result == 2

    def test_all_ones(self):
        """test_all_ones - maximum criticals from all 1s."""
        rolls = [1, 1, 1, 1, 1]
        result = count_successes(rolls, target_number=5)
        assert result == 10  # 5 dice * 2 each

    def test_all_twenties(self):
        """test_all_twenties - maximum failures (no successes)."""
        rolls = [20, 20, 20]
        result = count_successes(rolls, target_number=15)
        assert result == 0


class TestCountComplications:
    """Tests for count_complications function."""

    def test_no_complications(self):
        """test_no_complications - rolls below threshold."""
        rolls = [1, 10, 15]
        result = count_complications(rolls, complication_range=1)
        assert result == 0

    def test_single_complication_range_one(self):
        """test_single_complication_range_one - only 20 causes complication."""
        rolls = [20]
        result = count_complications(rolls, complication_range=1)
        assert result == 1

    def test_no_complication_on_19(self):
        """test_no_complication_on_19 - 19 is not a complication with range 1."""
        rolls = [19]
        result = count_complications(rolls, complication_range=1)
        assert result == 0

    def test_range_two(self):
        """test_range_two - both 19 and 20 cause complications."""
        rolls = [19, 20]
        result = count_complications(rolls, complication_range=2)
        assert result == 2

    def test_range_three(self):
        """test_range_three - 18, 19, 20 cause complications."""
        rolls = [17, 18, 19, 20]
        result = count_complications(rolls, complication_range=3)
        assert result == 3

    def test_max_range_five(self):
        """test_max_range_five - up to 5 numbers from 20 cause complications."""
        rolls = [16, 17, 18, 19, 20]
        result = count_complications(rolls, complication_range=5)
        assert result == 5

    def test_mixed_complications(self):
        """test_mixed_complications - some rolls cause, some don't."""
        rolls = [5, 10, 19, 15, 20]
        result = count_complications(rolls, complication_range=2)
        assert result == 2  # 19 and 20

    def test_multiple_same_value(self):
        """test_multiple_same_value - multiple 20s each count."""
        rolls = [20, 20, 20]
        result = count_complications(rolls, complication_range=1)
        assert result == 3


class TestApplyTalentModifiers:
    """Tests for apply_talent_modifiers function."""

    def test_no_modifiers(self):
        """test_no_modifiers - returns original rolls unchanged."""
        rolls = [5, 10, 15]
        result = apply_talent_modifiers(rolls, [])
        assert result.final_rolls == rolls
        assert result.rerolled_indices == []
        assert result.dice_set_to_one == []
        assert result.criticals_added == 0

    def test_reroll_single_die(self):
        """test_reroll_single_die - replaces specified die with new roll."""
        rolls = [5, 10, 15]
        modifier = TalentModifier(
            modifier_type="REROLL",
            dice_indices=[1],
            source_talent="Moment of Inspiration",
        )
        with patch("sta.mechanics.dice.roll_d20", return_value=[12]):
            result = apply_talent_modifiers(rolls, [modifier])
        assert result.final_rolls == [5, 12, 15]
        assert 1 in result.rerolled_indices
        assert "Moment of Inspiration" in result.modifiers_applied

    def test_reroll_multiple_dice(self):
        """test_reroll_multiple_dice - replaces multiple dice."""
        rolls = [5, 10, 15, 20]
        modifier = TalentModifier(
            modifier_type="REROLL",
            dice_indices=[0, 2],
            source_talent="Moment of Inspiration",
        )
        with patch(
            "sta.mechanics.dice.roll_d20",
            side_effect=lambda n: [8, 18] if n == 1 else [8],
        ):
            result = apply_talent_modifiers(rolls, [modifier])
        assert result.final_rolls == [8, 10, 8, 20]
        assert 0 in result.rerolled_indices
        assert 2 in result.rerolled_indices

    def test_set_die_to_one(self):
        """test_set_die_to_one - sets die to 1 for guaranteed critical."""
        rolls = [15, 10, 5]
        modifier = TalentModifier(
            modifier_type="SET_TO_ONE",
            dice_indices=[0],
            source_talent="Perfect Opportunity",
        )
        result = apply_talent_modifiers(rolls, [modifier])
        assert result.final_rolls == [1, 10, 5]
        assert 0 in result.dice_set_to_one
        assert result.criticals_added == 1
        assert "Perfect Opportunity" in result.modifiers_applied

    def test_critical_conversion(self):
        """test_critical_conversion - adds extra critical success."""
        rolls = [5, 10, 15]
        modifier = TalentModifier(
            modifier_type="CRITICAL_CONVERSION",
            source_talent="Reroute Power",
        )
        result = apply_talent_modifiers(rolls, [modifier])
        assert result.final_rolls == rolls
        assert result.criticals_added == 1
        assert "Reroute Power" in result.modifiers_applied

    def test_reduce_complications(self):
        """test_reduce_complications - reduces complication range."""
        modifier = TalentModifier(
            modifier_type="REDUCE_COMPLICATIONS",
            complication_reduction=1,
            source_talent="Lucky",
        )
        result = apply_talent_modifiers([20], [modifier])
        assert result.complication_range_reduced_by == 1
        assert "Lucky" in result.modifiers_applied

    def test_multiple_modifiers_combined(self):
        """test_multiple_modifiers_combined - applies all modifier types."""
        rolls = [15, 10, 5, 20]
        modifiers = [
            TalentModifier(
                modifier_type="REROLL", dice_indices=[0], source_talent="MoI"
            ),
            TalentModifier(
                modifier_type="SET_TO_ONE", dice_indices=[2], source_talent="PO"
            ),
            TalentModifier(
                modifier_type="REDUCE_COMPLICATIONS",
                complication_reduction=1,
                source_talent="Lucky",
            ),
        ]
        with patch("sta.mechanics.dice.roll_d20", return_value=[8]):
            result = apply_talent_modifiers(rolls, modifiers)
        assert result.final_rolls == [8, 10, 1, 20]
        assert result.rerolled_indices == [0]
        assert result.dice_set_to_one == [2]
        assert result.criticals_added == 1
        assert result.complication_range_reduced_by == 1
        assert len(result.modifiers_applied) == 3

    def test_invalid_reroll_index_ignored(self):
        """test_invalid_reroll_index_ignored - out of bounds indices skipped."""
        rolls = [5, 10]
        modifier = TalentModifier(
            modifier_type="REROLL", dice_indices=[5, 10], source_talent="Test"
        )
        result = apply_talent_modifiers(rolls, [modifier])
        assert result.final_rolls == rolls
        assert result.rerolled_indices == []

    def test_reroll_replacement_not_addition(self):
        """test_reroll_replacement_not_addition - reroll replaces, doesn't add dice."""
        rolls = [15, 20]
        modifier = TalentModifier(
            modifier_type="REROLL", dice_indices=[0], source_talent="Test"
        )
        with patch("sta.mechanics.dice.roll_d20", return_value=[5]):
            result = apply_talent_modifiers(rolls, [modifier])
        assert len(result.final_rolls) == 2  # Still 2 dice, not 3


class TestResolveAction:
    """Tests for resolve_action function - full STA 2E resolution sequence."""

    def test_basic_resolution(self):
        """test_basic_resolution - complete resolution sequence."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[8, 12]):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=1,
            )
        assert isinstance(result, TaskResult)
        assert result.target_number == 8
        assert len(result.rolls) == 2

    def test_target_number_calculation(self):
        """test_target_number_calculation - TN = Attribute + Discipline."""
        result = resolve_action(attribute=9, discipline=4)
        assert result.target_number == 13

    def test_bonus_dice_added(self):
        """test_bonus_dice_added - bonus dice increase total dice count."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[5, 10, 15]):
            result = resolve_action(attribute=5, discipline=3, bonus_dice=1)
        assert len(result.rolls) == 3

    def test_success_counting_with_tn(self):
        """test_success_counting_with_tn - counts successes correctly."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[5, 15]):
            result = resolve_action(attribute=5, discipline=3, difficulty=1)
        assert result.successes == 1  # 5 <= 8, 15 > 8

    def test_natural_one_counts_double(self):
        """test_natural_one_counts_double - roll of 1 = 2 successes."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[1, 20]):
            result = resolve_action(attribute=5, discipline=3, difficulty=1)
        assert result.successes == 2

    def test_focus_critical_on_success(self):
        """test_focus_critical_on_success - focus doubles success when roll <= discipline."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[3]):
            result = resolve_action(
                attribute=5,
                discipline=3,
                focus_applies=True,
                difficulty=1,
            )
        assert result.successes == 2  # 3 <= 3 (discipline), so 2 successes

    def test_complication_range_default(self):
        """test_complication_range_default - only 20 causes complication."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[20, 19]):
            result = resolve_action(attribute=5, discipline=3, difficulty=1)
        assert result.complications == 1

    def test_complication_range_extended(self):
        """test_complication_range_extended - multiple complications possible."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[19, 20]):
            result = resolve_action(
                attribute=5,
                discipline=3,
                difficulty=1,
                complication_range=2,
            )
        assert result.complications == 2  # 19 and 20

    def test_momentum_generated_on_success(self):
        """test_momentum_generated_on_success - momentum = successes - difficulty."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[1, 1, 1]):
            result = resolve_action(attribute=5, discipline=3, difficulty=1)
        assert result.successes == 6
        assert result.momentum_generated == 5  # 6 - 1

    def test_no_momentum_on_failure(self):
        """test_no_momentum_on_failure - no momentum when failing."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[20, 20]):
            result = resolve_action(attribute=5, discipline=3, difficulty=3)
        assert result.successes == 0
        assert result.momentum_generated == 0

    def test_succeeded_flag(self):
        """test_succeeded_flag - correctly reports success/failure."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[1, 1]):
            result = resolve_action(attribute=5, discipline=3, difficulty=3)
        assert result.succeeded is True

        with patch("sta.mechanics.dice.roll_d20", return_value=[20, 20]):
            result = resolve_action(attribute=5, discipline=3, difficulty=3)
        assert result.succeeded is False

    def test_reroll_modifier_applied(self):
        """test_reroll_modifier_applied - reroll changes the roll."""
        rolls = [15, 20]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch("sta.mechanics.dice.apply_talent_modifiers") as mock_apply:
                mock_apply.return_value = RollModifierResult(
                    final_rolls=[5, 20],
                    rerolled_indices=[0],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["MoI"],
                )
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0],
                            source_talent="MoI",
                        )
                    ],
                )
        assert result.rolls == [5, 20]
        assert result.successes == 1  # Only 5 is a success

    def test_set_to_one_modifier(self):
        """test_set_to_one_modifier - sets die to 1 for guaranteed critical."""
        rolls = [15, 12]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch("sta.mechanics.dice.apply_talent_modifiers") as mock_apply:
                mock_apply.return_value = RollModifierResult(
                    final_rolls=[1, 12],
                    rerolled_indices=[],
                    dice_set_to_one=[0],
                    criticals_added=1,
                    complication_range_reduced_by=0,
                    modifiers_applied=["PO"],
                )
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="SET_TO_ONE",
                            dice_indices=[0],
                            source_talent="PO",
                        )
                    ],
                )
        assert result.rolls == [1, 12]
        assert result.successes == 3  # 1=2, +1 extra from crits_added, 12 fails

    def test_critical_conversion_modifier(self):
        """test_critical_conversion_modifier - adds extra critical (+1 success)."""
        rolls = [5, 8]  # TN=8, so 5=1 success, 8=1 success = 2 total
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch(
                "sta.mechanics.dice.apply_talent_modifiers",
                return_value=RollModifierResult(
                    final_rolls=rolls,
                    rerolled_indices=[],
                    dice_set_to_one=[],
                    criticals_added=1,
                    complication_range_reduced_by=0,
                    modifiers_applied=["Talent"],
                ),
            ):
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="CRITICAL_CONVERSION", source_talent="Talent"
                        )
                    ],
                )
        assert result.successes == 3  # 5=1, 8=1, +1 critical = 3

    def test_reduce_complication_range_modifier(self):
        """test_reduce_complication_range_modifier - reduces complications."""
        rolls = [19, 20]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch("sta.mechanics.dice.apply_talent_modifiers") as mock_apply:
                mock_apply.return_value = RollModifierResult(
                    final_rolls=rolls,
                    rerolled_indices=[],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=1,
                    modifiers_applied=["Lucky"],
                )
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
        assert result.complications == 1  # Only 20, 19 is now safe

    def test_extended_result_has_all_fields(self):
        """test_extended_result_has_all_fields - ExtendedTaskResult includes base data."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[5, 15]):
            result = resolve_action_extended(
                attribute=5,
                discipline=3,
                difficulty=1,
            )
        assert isinstance(result, ExtendedTaskResult)
        assert result.base_rolls == [5, 15]
        assert hasattr(result, "base_successes")
        assert hasattr(result, "base_complications")
        assert hasattr(result, "rerolled_indices")
        assert hasattr(result, "dice_set_to_one")
        assert hasattr(result, "modifiers_applied")

    def test_extended_result_tracks_modifiers(self):
        """test_extended_result_tracks_modifiers - extended result shows what was modified."""
        rolls = [15, 20]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch("sta.mechanics.dice.apply_talent_modifiers") as mock_apply:
                mock_apply.return_value = RollModifierResult(
                    final_rolls=[5, 1],
                    rerolled_indices=[0],
                    dice_set_to_one=[1],
                    criticals_added=1,
                    complication_range_reduced_by=0,
                    modifiers_applied=["MoI", "PO"],
                )
                result = resolve_action_extended(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0],
                            source_talent="MoI",
                        ),
                        TalentModifier(
                            modifier_type="SET_TO_ONE",
                            dice_indices=[1],
                            source_talent="PO",
                        ),
                    ],
                )
        assert 0 in result.rerolled_indices
        assert 1 in result.dice_set_to_one
        assert "MoI" in result.modifiers_applied
        assert "PO" in result.modifiers_applied


class TestResolveActionEdgeCases:
    """Edge case tests for resolve_action."""

    def test_all_ones_maximum_criticals(self):
        """test_all_ones_maximum_criticals - all natural 1s = max successes."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[1, 1, 1, 1, 1]):
            result = resolve_action(attribute=5, discipline=3, difficulty=1)
        assert result.successes == 10
        assert result.succeeded is True
        assert result.momentum_generated == 9

    def test_all_twenties_maximum_failures(self):
        """test_all_twenties_maximum_failures - all 20s = no successes."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[20, 20, 20]):
            result = resolve_action(attribute=5, discipline=3, difficulty=3)
        assert result.successes == 0
        assert result.succeeded is False
        assert result.momentum_generated == 0
        assert result.complications == 3

    def test_focus_crits_edge_case(self):
        """test_focus_crits_edge_case - focus at discipline boundary."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[2, 2]):
            result = resolve_action(
                attribute=10,
                discipline=2,
                focus_applies=True,
                difficulty=1,
            )
        assert result.successes == 4  # Both 2s are at discipline=2, so 2 successes each

    def test_high_attribute_and_discipline(self):
        """test_high_attribute_and_discipline - maximum TN."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[15, 18]):
            result = resolve_action(attribute=12, discipline=5, difficulty=1)
        assert result.target_number == 17
        assert result.successes == 1  # 15 <= 17, 18 > 17

    def test_no_bonus_dice(self):
        """test_no_bonus_dice - base 2 dice only."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[10, 10]):
            result = resolve_action(attribute=5, discipline=3)
        assert len(result.rolls) == 2

    def test_multiple_rerolls(self):
        """test_multiple_rerolls - reroll several dice."""
        rolls = [15, 20]
        with patch("sta.mechanics.dice.roll_d20", return_value=rolls):
            with patch("sta.mechanics.dice.apply_talent_modifiers") as mock_apply:
                mock_apply.return_value = RollModifierResult(
                    final_rolls=[1, 5],
                    rerolled_indices=[0, 1],
                    dice_set_to_one=[],
                    criticals_added=0,
                    complication_range_reduced_by=0,
                    modifiers_applied=["MoI"],
                )
                result = resolve_action(
                    attribute=5,
                    discipline=3,
                    difficulty=1,
                    talent_modifiers=[
                        TalentModifier(
                            modifier_type="REROLL",
                            dice_indices=[0, 1],
                            source_talent="MoI",
                        )
                    ],
                )
        assert result.rolls == [1, 5]
        assert result.successes == 3  # 1=2, 5=1

    def test_complication_range_one_only_twenty(self):
        """test_complication_range_one_only_twenty - only 20 triggers."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[19, 20]):
            result = resolve_action(attribute=5, discipline=3, complication_range=1)
        assert result.complications == 1  # Only 20

    def test_max_complication_range_five(self):
        """test_max_complication_range_five - maximum complication range."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[16, 17, 18, 19, 20]):
            result = resolve_action(attribute=5, discipline=3, complication_range=5)
        assert result.complications == 5

    def test_zero_difficulty(self):
        """test_zero_difficulty - trivial task always succeeds."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[20, 20]):
            result = resolve_action(attribute=5, discipline=3, difficulty=0)
        assert result.succeeded is True
        assert result.momentum_generated == 0

    def test_negative_difficulty(self):
        """test_negative_difficulty - negative difficulty is trivial."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[20, 20]):
            result = resolve_action(attribute=5, discipline=3, difficulty=-2)
        assert result.succeeded is True


class TestTaskRollBackwardCompatibility:
    """Tests to ensure backward compatibility with original task_roll."""

    def test_task_roll_still_works(self):
        """test_task_roll_still_works - original function unchanged."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[8, 12]):
            result = task_roll(attribute=5, discipline=3, difficulty=1)
        assert isinstance(result, TaskResult)
        assert result.target_number == 8

    def test_task_roll_with_focus(self):
        """test_task_roll_with_focus - original focus support preserved."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[3, 10]):
            result = task_roll(attribute=5, discipline=3, focus=True, difficulty=1)
        assert result.focus_value == 3
        assert result.successes == 2  # 3=2 (focus), 10=1

    def test_task_roll_with_bonus_dice(self):
        """test_task_roll_with_bonus_dice - original bonus dice support preserved."""
        with patch("sta.mechanics.dice.roll_d20", return_value=[5, 10, 15]):
            result = task_roll(attribute=5, discipline=3, bonus_dice=1)
        assert len(result.rolls) == 3


class TestAssistedTaskRoll:
    """Tests for assisted_task_roll with ship assistance."""

    def test_assisted_roll_includes_ship_die(self):
        """test_assisted_roll_includes_ship_die - ship assist adds a die."""
        with patch(
            "sta.mechanics.dice.roll_d20",
            side_effect=lambda n: [5, 10] if n == 2 else [8],
        ):
            result = assisted_task_roll(
                attribute=5, discipline=3, system=8, department=2, difficulty=1
            )
        assert len(result.rolls) == 3
        assert result.ship_target_number == 10
        assert result.ship_roll == 8

    def test_assisted_roll_ship_success(self):
        """test_assisted_roll_ship_success - ship die counts successes."""
        with patch(
            "sta.mechanics.dice.roll_d20",
            side_effect=lambda n: [20, 20] if n == 2 else [5],
        ):
            result = assisted_task_roll(
                attribute=5, discipline=3, system=8, department=2, difficulty=2
            )
        assert result.ship_successes == 1  # 5 <= 10
        assert result.successes == 1  # Only ship die succeeded


class TestDiceRollDataclass:
    """Tests for DiceRoll dataclass."""

    def test_dice_roll_creation(self):
        """test_dice_roll_creation - creates DiceRoll with metadata."""
        roll = DiceRoll(value=15, original_index=0)
        assert roll.value == 15
        assert roll.original_index == 0
        assert roll.is_rerolled is False
        assert roll.reroll_source is None

    def test_dice_roll_rerolled(self):
        """test_dice_roll_rerolled - marks die as rerolled."""
        roll = DiceRoll(
            value=5,
            original_index=0,
            is_rerolled=True,
            reroll_source="Moment of Inspiration",
        )
        assert roll.is_rerolled is True
        assert roll.reroll_source == "Moment of Inspiration"


class TestRollModifierResultDataclass:
    """Tests for RollModifierResult dataclass."""

    def test_result_creation(self):
        """test_result_creation - creates with all fields."""
        result = RollModifierResult(
            final_rolls=[5, 10, 15],
            rerolled_indices=[1],
            dice_set_to_one=[0],
            criticals_added=1,
            complication_range_reduced_by=1,
            modifiers_applied=["Test Talent"],
        )
        assert result.final_rolls == [5, 10, 15]
        assert 1 in result.rerolled_indices
        assert 0 in result.dice_set_to_one
        assert result.criticals_added == 1
        assert "Test Talent" in result.modifiers_applied


class TestTalentModifierDataclass:
    """Tests for TalentModifier dataclass."""

    def test_reroll_modifier(self):
        """test_reroll_modifier - creates reroll modifier."""
        modifier = TalentModifier(
            modifier_type="REROLL",
            dice_indices=[0, 1],
            source_talent="Moment of Inspiration",
        )
        assert modifier.modifier_type == "REROLL"
        assert 0 in modifier.dice_indices
        assert modifier.source_talent == "Moment of Inspiration"

    def test_set_to_one_modifier(self):
        """test_set_to_one_modifier - creates set to one modifier."""
        modifier = TalentModifier(
            modifier_type="SET_TO_ONE",
            dice_indices=[2],
            source_talent="Perfect Opportunity",
        )
        assert modifier.modifier_type == "SET_TO_ONE"
        assert 2 in modifier.dice_indices

    def test_critical_conversion_modifier(self):
        """test_critical_conversion_modifier - creates critical conversion."""
        modifier = TalentModifier(
            modifier_type="CRITICAL_CONVERSION", source_talent="Some Talent"
        )
        assert modifier.modifier_type == "CRITICAL_CONVERSION"
        assert modifier.dice_indices == []

    def test_reduce_complications_modifier(self):
        """test_reduce_complications_modifier - creates complication reducer."""
        modifier = TalentModifier(
            modifier_type="REDUCE_COMPLICATIONS",
            complication_reduction=2,
            source_talent="Lucky",
        )
        assert modifier.modifier_type == "REDUCE_COMPLICATIONS"
        assert modifier.complication_reduction == 2
