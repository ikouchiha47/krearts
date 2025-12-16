from __future__ import annotations

"""Add characters table for storing parsed character data from storyline.

This migration adds the characters table which stores structured character information
parsed from the plotbuilder storyline output. This data is used for:
- BookWriter input (character details)
- Character image generation (prompts)
- UI display (character listings)

The character_id format is {workflow_id}_{character_number} (e.g., "c778f39d_1")
which matches the character_id used in character_images table for linking.
"""

import sqlite3


MIGRATION_ID = "0005_add_characters_table"
DESCRIPTION = "Add characters table for parsed character data"


def upgrade(conn: sqlite3.Connection) -> None:
    # Characters table - stores parsed character data from storyline
    # Note: TEXT is used for SQLite, will need VARCHAR for Postgres migration
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            character_number INTEGER NOT NULL,
            character_name TEXT NOT NULL,
            character_data TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(workflow_id, character_number)
        )
        """
    )

    # Index for filtering by workflow
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_characters_workflow
        ON characters(workflow_id)
        """
    )

    # Index for character name search (for future FTS)
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_characters_name
        ON characters(character_name)
        """
    )

    # Index for ordering within a workflow
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_characters_workflow_number
        ON characters(workflow_id, character_number)
        """
    )


def downgrade(conn: sqlite3.Connection) -> None:
    """Rollback migration"""
    conn.execute("DROP TABLE IF EXISTS characters")
