#!/usr/bin/env python3
"""Interactive text-based combat test."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sta.generators import generate_character, generate_starship
from sta.generators.starship import generate_enemy_ship
from sta.mechanics import task_roll
from sta.mechanics.actions import get_actions_for_position
from sta.models.enums import Position


def print_ship_status(ship, name="Ship"):
    """Print ship status summary."""
    breach_str = ""
    if ship.breaches:
        breach_str = " | Breaches: " + ", ".join(
            f"{b.system.value}({b.potency})" for b in ship.breaches
        )
    print(f"  {name}: Shields {ship.shields}/{ship.shields_max}{breach_str}")


def main():
    print("\n" + "=" * 60)
    print("STA STARSHIP COMBAT TEST")
    print("=" * 60)

    # Generate combatants
    print("\nGenerating player character...")
    player = generate_character()
    print(f"  {player.name} ({player.rank}) - {player.species}")

    print("\nGenerating player ship...")
    player_ship = generate_starship()
    print(f"  {player_ship.name} ({player_ship.ship_class}-class)")

    print("\nGenerating enemy ship...")
    enemy_ship = generate_enemy_ship(difficulty="standard")
    print(f"  {enemy_ship.name} ({enemy_ship.ship_class}-class)")

    # Choose position
    print("\nChoose your bridge position:")
    positions = list(Position)
    for i, pos in enumerate(positions, 1):
        print(f"  {i}. {pos.value.title()}")

    try:
        choice = int(input("\nEnter number (default 4 for Tactical): ") or "4")
        position = positions[choice - 1]
    except (ValueError, IndexError):
        position = Position.TACTICAL

    print(f"\nYou are at the {position.value.title()} station.")

    # Combat state
    momentum = 0
    threat = 2
    round_num = 1
    player_turn = True

    print("\n" + "-" * 60)
    print("COMBAT BEGINS!")
    print("-" * 60)

    # Main combat loop
    while True:
        print(f"\n=== ROUND {round_num} ===")
        print(f"Momentum: {momentum}/6 | Threat: {threat}")
        print_ship_status(player_ship, player_ship.name)
        print_ship_status(enemy_ship, enemy_ship.name)

        if player_turn:
            print(f"\n--- YOUR TURN ({position.value.title()}) ---")

            # Show available actions
            actions = get_actions_for_position(position)

            print("\nMajor Actions:")
            major_actions = [a for a in actions["major"] if position in a.positions or len(a.positions) == len(Position)]
            for i, action in enumerate(major_actions[:8], 1):
                diff_str = f" (Diff {action.difficulty})" if action.difficulty else ""
                print(f"  {i}. {action.name}{diff_str}")

            print(f"  0. End Turn")
            print(f"  q. Quit")

            choice = input("\nChoose action: ").strip().lower()

            if choice == "q":
                print("\nCombat ended.")
                break
            elif choice == "0":
                player_turn = False
                continue

            try:
                action_idx = int(choice) - 1
                if 0 <= action_idx < len(major_actions):
                    action = major_actions[action_idx]
                    print(f"\nAttempting: {action.name}")
                    print(f"  {action.description}")

                    # Determine attribute and discipline
                    attr = getattr(player.attributes, action.attribute or "control")
                    disc = getattr(player.disciplines, action.discipline or "security")

                    print(f"\nRolling: {action.attribute or 'control'} ({attr}) + {action.discipline or 'security'} ({disc})")
                    print(f"Target Number: {attr + disc}")
                    print(f"Difficulty: {action.difficulty}")

                    # Check for focus
                    focus = input("Focus applies? (y/n): ").lower() == "y"

                    # Buy extra dice?
                    bonus = 0
                    if momentum > 0:
                        extra = input(f"Buy extra dice with Momentum? (0-{min(3, momentum)}): ")
                        if extra.isdigit():
                            bonus = min(int(extra), momentum, 3)
                            momentum -= bonus

                    # Roll!
                    result = task_roll(
                        attribute=attr,
                        discipline=disc,
                        difficulty=action.difficulty,
                        focus=focus,
                        bonus_dice=bonus
                    )

                    print(f"\nRolls: {result.rolls}")
                    print(f"Successes: {result.successes}")

                    if result.complications:
                        print(f"COMPLICATIONS: {result.complications}")

                    if result.succeeded:
                        print("*** SUCCESS! ***")
                        if result.momentum_generated:
                            gained = min(result.momentum_generated, 6 - momentum)
                            momentum += gained
                            print(f"+{gained} Momentum (pool now {momentum})")

                        # Handle Fire action damage
                        if action.name == "Fire":
                            weapon = player_ship.weapons[0] if player_ship.weapons else None
                            if weapon:
                                damage = weapon.damage + player_ship.weapons_damage_bonus()
                                print(f"\nDealing {damage} damage with {weapon.name}!")
                                result = enemy_ship.take_damage(damage)
                                print(f"  Shield damage: {result['shield_damage']}")
                                if result['hull_damage']:
                                    print(f"  Hull damage: {result['hull_damage']}")
                                if result['breaches_caused']:
                                    print(f"  BREACHES: {result['breaches_caused']}!")
                    else:
                        print("*** FAILURE ***")

                    player_turn = False

            except (ValueError, IndexError):
                print("Invalid choice, try again.")

        else:
            # Enemy turn (simplified)
            print(f"\n--- ENEMY TURN ---")
            print(f"The {enemy_ship.name} attacks!")

            # Simple attack roll
            enemy_roll = task_roll(attribute=9, discipline=3, difficulty=2)
            print(f"Enemy rolls: {enemy_roll.rolls} -> {enemy_roll.successes} successes")

            if enemy_roll.succeeded:
                weapon = enemy_ship.weapons[0] if enemy_ship.weapons else None
                if weapon:
                    damage = weapon.damage + enemy_ship.weapons_damage_bonus()
                    print(f"Dealing {damage} damage with {weapon.name}!")
                    result = player_ship.take_damage(damage)
                    print(f"  Your shield damage: {result['shield_damage']}")
                    if result['hull_damage']:
                        print(f"  Your hull damage: {result['hull_damage']}")
            else:
                print("The attack misses!")

            # Add threat from NPC momentum
            if enemy_roll.momentum_generated:
                threat += enemy_roll.momentum_generated
                print(f"+{enemy_roll.momentum_generated} Threat (now {threat})")

            player_turn = True
            round_num += 1

        # Check for victory/defeat
        from sta.models.enums import SystemType
        if enemy_ship.is_system_disabled(SystemType.STRUCTURE):
            print("\n" + "=" * 60)
            print("VICTORY! The enemy ship is destroyed!")
            print("=" * 60)
            break
        if player_ship.is_system_disabled(SystemType.STRUCTURE):
            print("\n" + "=" * 60)
            print("DEFEAT! Your ship is destroyed!")
            print("=" * 60)
            break

    print("\nFinal Status:")
    print_ship_status(player_ship, player_ship.name)
    print_ship_status(enemy_ship, enemy_ship.name)


if __name__ == "__main__":
    main()
