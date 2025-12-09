from __future__ import annotations

"""Unified job repository over the logical `jobs` table.

This provides a backend-agnostic abstraction for job persistence that can be
used by both CLI flows and any future server components. It is intentionally
separate from `cinema.server` so core jobs are not tied to HTTP concerns.

The default implementation uses SQLite with a single database dedicated to
jobs, configured via environment variables:

- JOBS_SQLITE_PATH: path to the jobs database (default: "./cinema_jobs.db")
- CINEMA_JOB_TABLE: table name for logical jobs (default: "jobs")

The schema mirrors the migrated jobs table created by the DB migrator, but is
created locally here so that the jobs DB does not need the full migration set
(workflow_states, chapters, pages, etc.).
"""

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol

from cinema.server.storage.interface import Job


class JobRepository(Protocol):
    """Abstract repository for logical job persistence.

    Implementations operate on the Pydantic `Job` model from
    `cinema.server.storage.interface` so that both CLI and server components
    can share a single job schema.
    """

    def save(self, job: Job) -> None:  # pragma: no cover - protocol
        ...

    def get(self, job_id: str) -> Optional[Job]:  # pragma: no cover - protocol
        ...

    def list(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Job]:  # pragma: no cover - protocol
        ...


@dataclass
class SQLiteJobRepository:
    """SQLite-backed JobRepository.

    Uses a dedicated jobs database (JOBS_SQLITE_PATH), separate from the main
    content DB. Only the logical `jobs` table is managed here; other tables are
    not created so that this DB remains jobs-only.
    """

    db_path: str = os.getenv("JOBS_SQLITE_PATH", "./cinema_jobs.db")
    table_name: str = os.getenv("CINEMA_JOB_TABLE", "jobs")

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _ensure_schema(self) -> None:
        """Ensure the jobs table and indexes exist.

        This mirrors the logical schema from migrations 0001 and 0002 but is
        scoped only to the jobs table so we don't need full migrations in the
        jobs DB.
        """

        with self._get_connection() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT,
                    output_path TEXT,
                    error TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 0,
                    idempotency_key TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # Indexes to support efficient lookup by workflow and idempotency.
            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_workflow_status
                ON {self.table_name}(workflow_id, status)
                """
            )

            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_idempotency_key
                ON {self.table_name}(idempotency_key)
                """
            )

    def save(self, job: Job) -> None:
        """Insert or update a job record.

        Preserves the original created_at if the job already exists.
        """

        self._ensure_schema()

        now = datetime.now(timezone.utc).isoformat()
        created_at = job.created_at.isoformat() if job.created_at else now

        with self._get_connection() as conn:
            # If a row already exists, preserve its created_at.
            try:
                cur = conn.execute(
                    f"SELECT created_at FROM {self.table_name} WHERE id = ?",
                    (job.id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    created_at = row[0]
            except Exception:
                created_at = created_at

            payload = json.dumps(job.metadata) if job.metadata is not None else None

            conn.execute(
                f"""
                INSERT OR REPLACE INTO {self.table_name} (
                    id, workflow_id, type, status,
                    metadata, output_path, error,
                    retry_count, max_retries, idempotency_key,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.workflow_id,
                    job.type,
                    job.status,
                    payload,
                    job.output_path,
                    job.error,
                    job.retry_count,
                    job.max_retries,
                    job.idempotency_key,
                    created_at,
                    now,
                ),
            )

    def get(self, job_id: str) -> Optional[Job]:
        self._ensure_schema()
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (job_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            metadata: Dict[str, object] = {}
            if row["metadata"]:
                try:
                    metadata = json.loads(row["metadata"])
                except Exception:
                    metadata = {}

            return Job(
                id=row["id"],
                workflow_id=row["workflow_id"],
                type=row["type"],
                status=row["status"],
                retry_count=row["retry_count"],
                max_retries=row["max_retries"],
                idempotency_key=row["idempotency_key"],
                metadata=metadata,
                output_path=row["output_path"],
                error=row["error"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def list(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Job]:
        self._ensure_schema()

        clauses = []
        params: list[object] = []

        if workflow_id is not None:
            clauses.append("workflow_id = ?")
            params.append(workflow_id)

        if status is not None:
            clauses.append("status = ?")
            params.append(status)

        where = ""
        if clauses:
            where = " WHERE " + " AND ".join(clauses)

        sql = f"SELECT * FROM {self.table_name}{where} ORDER BY created_at DESC"

        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(sql, params)
            rows = cur.fetchall()

        jobs: List[Job] = []
        for row in rows:
            metadata: Dict[str, object] = {}
            if row["metadata"]:
                try:
                    metadata = json.loads(row["metadata"])
                except Exception:
                    metadata = {}

            jobs.append(
                Job(
                    id=row["id"],
                    workflow_id=row["workflow_id"],
                    type=row["type"],
                    status=row["status"],
                    retry_count=row["retry_count"],
                    max_retries=row["max_retries"],
                    idempotency_key=row["idempotency_key"],
                    metadata=metadata,
                    output_path=row["output_path"],
                    error=row["error"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )

        return jobs


def get_job_repository() -> JobRepository:
    """Factory for the default JobRepository implementation.

    For now this always returns a SQLite-backed repository pointed at the
    dedicated jobs database. In the future this can grow additional backends
    (e.g. Postgres) without changing callers.
    """

    return SQLiteJobRepository()
