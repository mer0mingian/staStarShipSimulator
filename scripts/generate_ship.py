#!/usr/bin/env python3
"""Generate and display a random starship."""

import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sta.generators import generate_starship
from sta.generators.starship import generate_enemy_ship


def main():
    parser = argparse.ArgumentParser(description="Generate a random starship")
    parser.add_argument("--enemy", action="store_true", help="Generate an enemy ship")
    parser.add_argument("--faction", choices=["Federation", "Klingon", "Romulan"],
                        default="Federation", help="Ship faction")
    parser.add_argument("--difficulty", choices=["easy", "standard", "hard"],
                        default="standard", help="Enemy difficulty (only with --enemy)")
    args = parser.parse_args()

    print("=" * 50)
    if args.enemy:
        print("RANDOM ENEMY SHIP GENERATOR")
        ship = generate_enemy_ship(difficulty=args.difficulty, faction=args.faction)
    else:
        print("RANDOM STARSHIP GENERATOR")
        ship = generate_starship(faction=args.faction)
    print("=" * 50)

    print(f"\nName: {ship.name}")
    print(f"Class: {ship.ship_class}-class")
    print(f"Registry: {ship.registry}")
    print(f"Scale: {ship.scale}")

    print("\n--- SYSTEMS ---")
    print(f"  Comms:     {ship.systems.comms:2d}")
    print(f"  Computers: {ship.systems.computers:2d}")
    print(f"  Engines:   {ship.systems.engines:2d}")
    print(f"  Sensors:   {ship.systems.sensors:2d}")
    print(f"  Structure: {ship.systems.structure:2d}")
    print(f"  Weapons:   {ship.systems.weapons:2d}")

    print("\n--- DEPARTMENTS ---")
    print(f"  Command:     {ship.departments.command}")
    print(f"  Conn:        {ship.departments.conn}")
    print(f"  Engineering: {ship.departments.engineering}")
    print(f"  Medicine:    {ship.departments.medicine}")
    print(f"  Science:     {ship.departments.science}")
    print(f"  Security:    {ship.departments.security}")

    print("\n--- COMBAT STATS ---")
    print(f"  Shields: {ship.shields}/{ship.shields_max}")
    print(f"  Resistance: {ship.resistance}")
    print(f"  Weapons Damage Bonus: +{ship.weapons_damage_bonus()}")

    print("\n--- WEAPONS ---")
    for weapon in ship.weapons:
        quals = ", ".join(weapon.qualities) if weapon.qualities else "None"
        print(f"  - {weapon.name}")
        print(f"    Type: {weapon.weapon_type.value.title()}, Damage: {weapon.damage}, Range: {weapon.range.value.title()}")
        print(f"    Qualities: {quals}")

    print("\n--- TALENTS ---")
    for talent in ship.talents:
        print(f"  - {talent}")

    print("\n--- TRAITS ---")
    for trait in ship.traits:
        print(f"  - {trait}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
