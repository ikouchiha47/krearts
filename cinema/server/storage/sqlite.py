from __future__ import annotations

"""SQLite-backed implementation of the server `StorageBackend`.

This is intended primarily for local development and lightweight deployments.

It stores:
- Workflow states (serialized from `cinema.workflow.interface.WorkflowState`)
- Logical web/API jobs from `cinema.server.storage.interface.Job`

Notes
-----
- The interface is async, but the underlying driver (`sqlite3`) is sync.
  We wrap blocking calls with `asyncio.to_thread` so FastAPI endpoints can
  await these operations without blocking the event loop.
- This module is **server-only** and does not affect the existing CLI
  `cinema.pipeline.JobTracker`.
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from cinema.workflow.interface import WorkflowState, WorkflowType
from cinema.db import run_migrations

from .interface import Job, StorageBackend

if TYPE_CHECKING:
    from cinema.jobs.storage import JobRepository


WORKFLOW_TABLE = os.getenv("CINEMA_WORKFLOW_TABLE", "workflow_states")


class SQLiteStorage(StorageBackend):
    """SQLite implementation of `StorageBackend` for server use.

    Schema (conceptual)
    -------------------
    - workflow_states
        id TEXT PRIMARY KEY
        user_id TEXT
        type TEXT
        current_stage TEXT
        state_json TEXT      -- full serialized WorkflowState
        created_at TEXT
        updated_at TEXT

    - jobs
        id TEXT PRIMARY KEY
        workflow_id TEXT
        type TEXT
        status TEXT
        retry_count INTEGER
        max_retries INTEGER
        idempotency_key TEXT
        metadata TEXT
        output_path TEXT
        error TEXT
        created_at TEXT
        updated_at TEXT
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        job_repo: Optional["JobRepository"] = None,
    ) -> None:
        # Use environment variable if db_path not provided
        if db_path is None:
            db_path = os.getenv("WORKFLOW_STATE_SQLITE_PATH", "./cinema_server.db")
        
        self.db_path = db_path
        # Ensure schema is up-to-date before any access
        run_migrations(self.db_path)
        if job_repo is None:
            from cinema.jobs.storage import get_job_repository
            job_repo = get_job_repository()
        self._job_repo: "JobRepository" = job_repo

    # ------------------------------------------------------------------
    # Low-level helpers (sync)
    # ------------------------------------------------------------------

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_db(self) -> None:
        """Deprecated: schema is managed via migrations.

        Left in place for backward compatibility; no-op when using the
        migration system. New deployments should rely solely on
        `cinema.db.run_migrations`.
        """
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public async API (StorageBackend)
    # ------------------------------------------------------------------

    async def save_job(self, job: Job) -> None:  # type: ignore[override]
        job.updated_at = datetime.utcnow()
        await asyncio.to_thread(self._job_repo.save, job)

    async def load_job(self, job_id: str) -> Optional[Job]:  # type: ignore[override]
        return await asyncio.to_thread(self._job_repo.get, job_id)

    async def get_pending_jobs(self, limit: int = 10) -> List[Job]:  # type: ignore[override]
        """Get pending jobs to process, ordered by creation time."""
        return await asyncio.to_thread(self._get_pending_jobs_sync, limit)
    
    def _get_pending_jobs_sync(self, limit: int) -> List[Job]:
        """Synchronous implementation of get_pending_jobs."""
        # Query jobs with status="pending" directly
        return self._job_repo.list(status="pending")[:limit]

    async def save_state(self, state: WorkflowState) -> None:  # type: ignore[override]
        await asyncio.to_thread(self._save_state_sync, state)

    def _save_state_sync(self, state: WorkflowState) -> None:
        # Extract user_id from config if present
        user_id = None
        try:
            user_id = state.config.get("user_id")  # type: ignore[attr-defined]
        except Exception:
            user_id = None

        now = datetime.utcnow().isoformat()
        state_json = state.model_dump_json()

        with self._get_connection() as conn:
            conn.execute(
                f"""
                INSERT OR REPLACE INTO {WORKFLOW_TABLE} (
                    id, user_id, type, current_stage, state_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.id,
                    user_id,
                    state.type.value,
                    state.current_stage.value,
                    state_json,
                    now,
                    now,
                ),
            )

    async def load_state(
        self, workflow_id: str, workflow_type: WorkflowType
    ) -> Optional[WorkflowState]:  # type: ignore[override]
        return await asyncio.to_thread(self._load_state_sync, workflow_id, workflow_type)

    def _load_state_sync(
        self, workflow_id: str, workflow_type: WorkflowType
    ) -> Optional[WorkflowState]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                f"SELECT state_json FROM {WORKFLOW_TABLE} WHERE id = ?",
                (workflow_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            data = json.loads(row["state_json"])

            # Trust the stored JSON; caller also provides `workflow_type` for safety.
            # We do not override fields here, but could validate type if needed.
            return WorkflowState(**data)

    async def list_workflows(self, user_id: str) -> List[WorkflowState]:  # type: ignore[override]
        return await asyncio.to_thread(self._list_workflows_sync, user_id)

    def _list_workflows_sync(self, user_id: str) -> List[WorkflowState]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            # If user_id is empty, list all workflows (for development/admin)
            if user_id:
                cur = conn.execute(
                    f"SELECT state_json FROM {WORKFLOW_TABLE} WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,),
                )
            else:
                cur = conn.execute(
                    f"SELECT state_json FROM {WORKFLOW_TABLE} ORDER BY updated_at DESC"
                )
            rows = cur.fetchall()

        states: List[WorkflowState] = []
        for row in rows:
            try:
                data = json.loads(row["state_json"])
                states.append(WorkflowState(**data))
            except Exception:
                # Ignore corrupt rows; could be logged by the caller.
                continue

        return states
