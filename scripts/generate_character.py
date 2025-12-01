#!/usr/bin/env python3
"""Generate and display a random character."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sta.generators import generate_character


def main():
    print("=" * 50)
    print("RANDOM CHARACTER GENERATOR")
    print("=" * 50)

    char = generate_character()

    print(f"\nName: {char.name}")
    print(f"Species: {char.species}")
    print(f"Rank: {char.rank}")
    print(f"Role: {char.role}")

    print("\n--- ATTRIBUTES ---")
    print(f"  Control:  {char.attributes.control:2d}")
    print(f"  Fitness:  {char.attributes.fitness:2d}")
    print(f"  Daring:   {char.attributes.daring:2d}")
    print(f"  Insight:  {char.attributes.insight:2d}")
    print(f"  Presence: {char.attributes.presence:2d}")
    print(f"  Reason:   {char.attributes.reason:2d}")
    print(f"  Total:    {char.attributes.total()}")

    print("\n--- DISCIPLINES ---")
    print(f"  Command:     {char.disciplines.command}")
    print(f"  Conn:        {char.disciplines.conn}")
    print(f"  Engineering: {char.disciplines.engineering}")
    print(f"  Medicine:    {char.disciplines.medicine}")
    print(f"  Science:     {char.disciplines.science}")
    print(f"  Security:    {char.disciplines.security}")
    print(f"  Total:       {char.disciplines.total()}")

    print("\n--- FOCUSES ---")
    for focus in char.focuses:
        print(f"  - {focus}")

    print("\n--- TALENTS ---")
    for talent in char.talents:
        print(f"  - {talent}")

    print(f"\nStress: {char.stress}/{char.stress_max}")
    print(f"Determination: {char.determination}/{char.determination_max}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
