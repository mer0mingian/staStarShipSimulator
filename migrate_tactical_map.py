#!/usr/bin/env python3
"""Migration script to add tactical map columns to encounters table.

Run this script to add the tactical_map_json and ship_positions_json columns
to the encounters table for existing databases.

Usage:
    python migrate_tactical_map.py
"""

import sqlite3
import json
import os

# Default database path (can be overridden via environment)
DB_PATH = os.environ.get("STA_DATABASE", "sta_simulator.db")


def migrate():
    """Add tactical map columns to encounters table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(encounters)")
    columns = {row[1] for row in cursor.fetchall()}

    changes_made = False

    # Add tactical_map_json column if it doesn't exist
    if "tactical_map_json" not in columns:
        print("Adding tactical_map_json column...")
        cursor.execute("""
            ALTER TABLE encounters
            ADD COLUMN tactical_map_json TEXT DEFAULT '{}'
        """)
        changes_made = True
    else:
        print("tactical_map_json column already exists")

    # Add ship_positions_json column if it doesn't exist
    if "ship_positions_json" not in columns:
        print("Adding ship_positions_json column...")
        cursor.execute("""
            ALTER TABLE encounters
            ADD COLUMN ship_positions_json TEXT DEFAULT '{}'
        """)
        changes_made = True
    else:
        print("ship_positions_json column already exists")

    if changes_made:
        conn.commit()
        print("Migration completed successfully!")
    else:
        print("No migration needed - columns already exist")

    conn.close()


def initialize_existing_encounters():
    """Initialize tactical maps for existing encounters.

    Sets up default hex positions for player and enemy ships.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find encounters with empty tactical maps
    cursor.execute("""
        SELECT id, encounter_id, enemy_ship_ids_json
        FROM encounters
        WHERE tactical_map_json = '{}' OR tactical_map_json IS NULL
    """)
    encounters = cursor.fetchall()

    for enc_id, encounter_id, enemy_ids_json in encounters:
        print(f"Initializing tactical map for encounter {encounter_id}...")

        # Create default tactical map (radius 3)
        tactical_map = {"radius": 3, "tiles": []}

        # Set up default ship positions
        # Player at center, enemies spread around
        positions = {"player": {"q": 0, "r": 0}}

        try:
            enemy_ids = json.loads(enemy_ids_json) if enemy_ids_json else []
        except json.JSONDecodeError:
            enemy_ids = []

        # Position enemies around the player
        enemy_positions = [
            {"q": 2, "r": -1},
            {"q": -2, "r": 1},
            {"q": 1, "r": 1},
            {"q": -1, "r": -1},
        ]
        for i, _ in enumerate(enemy_ids):
            if i < len(enemy_positions):
                positions[f"enemy_{i}"] = enemy_positions[i]
            else:
                positions[f"enemy_{i}"] = {"q": 2, "r": i - 2}

        cursor.execute("""
            UPDATE encounters
            SET tactical_map_json = ?, ship_positions_json = ?
            WHERE id = ?
        """, (json.dumps(tactical_map), json.dumps(positions), enc_id))

    conn.commit()
    print(f"Initialized {len(encounters)} encounters")
    conn.close()


if __name__ == "__main__":
    print(f"Running tactical map migration on database: {DB_PATH}")
    migrate()
    initialize_existing_encounters()
