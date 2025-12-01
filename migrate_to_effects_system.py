#!/usr/bin/env python3
"""
Migration script to convert from individual effect booleans to active_effects_json.

This migrates the database schema from the old calibrate_weapons_active field
to the new active_effects_json field that supports multiple effects.
"""

import sqlite3
import os
import json

# Get database path
db_path = os.path.join(os.path.dirname(__file__), "sta_simulator.db")

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    print("No migration needed - database will be created with the new schema.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if old column exists
    cursor.execute("PRAGMA table_info(encounters)")
    columns = {col[1]: col for col in cursor.fetchall()}

    if 'calibrate_weapons_active' in columns:
        print("Found old schema with calibrate_weapons_active field.")

        # Add new column if it doesn't exist
        if 'active_effects_json' not in columns:
            print("Adding active_effects_json column...")
            cursor.execute("""
                ALTER TABLE encounters
                ADD COLUMN active_effects_json TEXT DEFAULT '[]'
            """)

        # Migrate data: convert calibrate_weapons_active to active_effects_json
        print("Migrating active calibrate weapons buffs to effects system...")
        cursor.execute("""
            SELECT id, calibrate_weapons_active, round
            FROM encounters
            WHERE calibrate_weapons_active = 1
        """)
        active_buffs = cursor.fetchall()

        for encounter_id, _, round_num in active_buffs:
            effect = {
                "id": f"calibrate_weapons_{encounter_id}",
                "source_action": "Calibrate Weapons",
                "applies_to": "attack",
                "duration": "next_action",
                "damage_bonus": 1,
                "resistance_bonus": 0,
                "difficulty_modifier": 0,
                "can_reroll": False,
                "can_choose_system": False,
                "piercing": False,
                "created_round": round_num,
            }
            effects_json = json.dumps([effect])
            cursor.execute("""
                UPDATE encounters
                SET active_effects_json = ?
                WHERE id = ?
            """, (effects_json, encounter_id))

        print(f"Migrated {len(active_buffs)} active Calibrate Weapons buffs.")

        # Drop old column
        print("Dropping old calibrate_weapons_active column...")
        # SQLite doesn't support DROP COLUMN directly in older versions
        # We'll leave it for now - it will be ignored
        print("(Note: Old column left in place for compatibility)")

        conn.commit()
        print("✓ Migration complete!")

    elif 'active_effects_json' in columns:
        print("Database already using new effects system. No migration needed.")

    else:
        print("Database schema is unexpected. Please check manually.")

except sqlite3.Error as e:
    print(f"Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()
