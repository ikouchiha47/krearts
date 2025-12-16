from __future__ import annotations

"""Add character_images table for character image metadata.

This migration adds storage for character image metadata (front, back, side, full_body views).
Character data itself lives in storybuilder_states, but image file paths are tracked here
for efficient querying and to support configurable asset storage (local/S3/CDN).

Table name is configurable via COMIC_METADATA_SQLITE_CHARACTER_TABLE environment variable.
"""

import os
import sqlite3


MIGRATION_ID = "0004_add_character_images"
DESCRIPTION = "Add character_images table for character image metadata"


def _character_images_table_name() -> str:
    return os.getenv("COMIC_METADATA_SQLITE_CHARACTER_TABLE", "character_images")


def upgrade(conn: sqlite3.Connection) -> None:
    table = _character_images_table_name()

    # Character images table - stores metadata about generated character images
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            character_name TEXT NOT NULL,
            view_type TEXT NOT NULL,
            image_path TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(workflow_id, character_id, view_type)
        )
        """
    )

    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{table}_workflow
        ON {table}(workflow_id)
        """
    )

    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{table}_character
        ON {table}(workflow_id, character_id)
        """
    )
