#!/usr/bin/env python3
"""
Migration script to add calibrate_weapons_active column to encounters table.

This is a simple migration for the Calibrate Weapons feature.
Run this script if you have an existing database.
"""

import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), "sta_simulator.db")

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    print("No migration needed - database will be created with the new column.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(encounters)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'calibrate_weapons_active' in columns:
        print("Column 'calibrate_weapons_active' already exists. No migration needed.")
    else:
        # Add the new column
        print("Adding 'calibrate_weapons_active' column to encounters table...")
        cursor.execute("""
            ALTER TABLE encounters
            ADD COLUMN calibrate_weapons_active BOOLEAN DEFAULT 0
        """)
        conn.commit()
        print("✓ Migration complete! Column added successfully.")

except sqlite3.Error as e:
    print(f"Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()
