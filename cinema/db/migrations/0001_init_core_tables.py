from __future__ import annotations

"""Initial DB schema for Cinema workflows and StoryBuilder flow state.

This migration creates two logical groups of tables:

- Workflow / job state tables for the server API
- StoryBuilder flow-state table for plot/novel generation

Table names are configurable via environment variables so deployments can
share a single DB or use different naming conventions.
"""

import os
import sqlite3


MIGRATION_ID = "0001_init_core_tables"
DESCRIPTION = "Create workflow/job tables and StoryBuilder flow-state table"


def _workflow_table_name() -> str:
    return os.getenv("CINEMA_WORKFLOW_TABLE", "workflow_states")


def _job_table_name() -> str:
    return os.getenv("CINEMA_JOB_TABLE", "jobs")


def _storybuilder_table_name() -> str:
    return os.getenv("STORYBUILDER_SQLITE_TABLE", "storybuilder_states")


def upgrade(conn: sqlite3.Connection) -> None:
    workflow_table = _workflow_table_name()
    job_table = _job_table_name()
    storybuilder_table = _storybuilder_table_name()

    # Workflow states table
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {workflow_table} (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            type TEXT NOT NULL,
            current_stage TEXT NOT NULL,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    # Jobs table
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {job_table} (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata TEXT,
            output_path TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{job_table}_workflow_id ON {job_table}(workflow_id)"
    )

    # StoryBuilder flow state table
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {storybuilder_table} (
            id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
