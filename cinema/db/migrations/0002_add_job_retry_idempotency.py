from __future__ import annotations

"""Add retry/idempotency fields and indexes to the jobs table.

This migration extends the logical jobs schema with:
- retry_count: number of times this job has been retried
- max_retries: maximum number of retries allowed
- idempotency_key: application-level key for de-duplicating logically identical jobs

All table names remain configurable via environment variables.
"""

import os
import sqlite3


MIGRATION_ID = "0002_add_job_retry_idempotency"
DESCRIPTION = "Add retry/idempotency fields and indexes to jobs table"


def _job_table_name() -> str:
    return os.getenv("CINEMA_JOB_TABLE", "jobs")


def upgrade(conn: sqlite3.Connection) -> None:
    job_table = _job_table_name()

    # Add retry-related columns with safe defaults if they do not exist yet.
    # SQLite has limited ALTER TABLE support; we defensively try-add columns.
    # If they already exist (e.g. in a manually migrated DB), we ignore errors.
    def _column_exists(name: str) -> bool:
        cur = conn.execute(f"PRAGMA table_info({job_table})")
        cols = [row[1] for row in cur.fetchall()]
        return name in cols

    if not _column_exists("retry_count"):
        conn.execute(
            f"ALTER TABLE {job_table} ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0"
        )

    if not _column_exists("max_retries"):
        conn.execute(
            f"ALTER TABLE {job_table} ADD COLUMN max_retries INTEGER NOT NULL DEFAULT 0"
        )

    if not _column_exists("idempotency_key"):
        conn.execute(
            f"ALTER TABLE {job_table} ADD COLUMN idempotency_key TEXT"
        )

    # Indexes to support efficient lookup by workflow and idempotency.
    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{job_table}_workflow_status
        ON {job_table}(workflow_id, status)
        """
    )

    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{job_table}_idempotency_key
        ON {job_table}(idempotency_key)
        """
    )
